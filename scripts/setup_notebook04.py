"""Genera el notebook completo del Modulo 4 (CNN sobre imagenes municipio x cultivo).

Cambios respecto a la version original:
- kmeans() ahora retorna tambien la inercia real (antes se imprimia un valor sin sentido).
- Las imagenes ya no rellenan con 0.0 silenciosamente cuando falta un cultivo-anio;
  el municipio se excluye y se reporta explicitamente (evita contaminar los z-scores).
- Se eliminó el bloque muerto ("top cultivos por filtro") que no imprimia nada y
  partia de una premisa incorrecta (un kernel 3x3 no corresponde a "un cultivo").
  Se reemplazo por una interpretacion correcta: fuerza de activacion por filtro
  y la region (vecindario cultivo x anio) donde cada filtro responde mas fuerte.
- vmin/vmax de los heatmaps ahora usan max(abs(.)) para evitar vmin > vmax
  cuando todos los pesos de un filtro son negativos.
- label_map ahora desambigua nombres de cluster repetidos (mismo cultivo dominante).
- Split train/test ahora es estratificado por clase para garantizar que las 3
  vocaciones esten representadas en entrenamiento.
"""
import json
from pathlib import Path

cells = []
def md(src):
    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": src.splitlines(keepends=True)})
def code(src):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": src.splitlines(keepends=True)})

md(r"""# Módulo 4 — CNNs: patrones espaciales del agro vallecaucano
## Laboratorio: clasificar "vocación productiva" de cada municipio

**Objetivos**
1. Convertir el panel EVA (municipio × cultivo × año) en **imágenes** 12×7.
2. Descubrir clusters de vocación con k-means (k=3) como etiquetas.
3. Entrenar la CNN desde cero (Conv3x3 → ReLU → MaxPool → Dense → softmax).
4. **Visualizar los filtros** aprendidos para leer qué patrones definen cada vocación.

**Arquitectura:** invariante a traslaciones, ~100× menos parámetros que MLP.
Con n=42 municipios, la CNN puede aprender patrones sin memorizar.""")

code(r"""import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd()
while ROOT != ROOT.parent and not (ROOT / "app.py").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from core.ml.cnn_scratch import CNN
from core.ml.io_utils import save_json, save_csv, save_png, RESULTS
from config.settings import settings

df = pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                 low_memory=False)
print(f"Panel EVA: {df.shape[0]:,} filas, {df.municipio.nunique()} municipios")""")

md(r"""## 4.1 Construcción de imágenes (12 cultivos top × 7 años)

Seleccionamos los 12 cultivos con mayor producción total en el Valle (caña, plátano, etc.).
Cada municipio = una imagen 12×7 normalizada por cultivo (z-score).
Así la CNN ve **cómo se mueve cada cultivo respecto a su propio promedio histórico**.

Un municipio solo entra al dataset si tiene los 7 años **para cada uno** de los 12
cultivos top; de lo contrario se excluye explícitamente (no se rellena con 0, que
en z-score significaría "exactamente el promedio histórico" y contaminaría la señal).""")

code(r"""total_por_cultivo = df.groupby("cultivo").produccion_t.sum().sort_values(ascending=False)
TOP12 = total_por_cultivo.head(12).index.tolist()
print("Top 12 cultivos departamentales:")
for i, c in enumerate(TOP12, 1):
    print(f"  {i:2d}. {c}: {total_por_cultivo[c]/1e6:,.1f} M t")

g = df[df.cultivo.isin(TOP12)].groupby(
    ["municipio", "cultivo", "ano"]).produccion_t.sum().reset_index()

# Z-score por cultivo (normalizacion global)
medias = g.groupby("cultivo").produccion_t.transform("mean")
sds = g.groupby("cultivo").produccion_t.transform("std").clip(lower=1e-6)
g["z"] = (g.produccion_t - medias) / sds

# Pivotar: cada municipio -> matriz (12, 7) con anos 2019-2025
ANIOS = list(range(2019, 2026))
muns = sorted(g.municipio.unique())
imagenes = {}
excluidos = {}
for m in muns:
    sub = g[g.municipio == m]
    M = np.full((len(TOP12), 7), np.nan)
    for i, c in enumerate(TOP12):
        s = sub[(sub.cultivo == c) & (sub.ano.isin(ANIOS))].sort_values("ano")
        s = s.drop_duplicates("ano")
        for _, row in s.iterrows():
            M[i, ANIOS.index(row.ano)] = row.z
    n_faltantes = int(np.isnan(M).sum())
    if n_faltantes > 0:
        excluidos[m] = n_faltantes
        continue
    imagenes[m] = M

print(f"\nMunicipios con imagen completa (12 cultivos x 7 anos): {len(imagenes)} / {len(muns)}")
if excluidos:
    print(f"Excluidos por datos incompletos ({len(excluidos)}):")
    for m, n in sorted(excluidos.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {m}: faltan {n} celdas cultivo-anio")""")

md(r"""## 4.2 K-means desde cero para descubrir vocaciones (k=3)
Inicializacion k-means++, 50 iteraciones, 10 restarts.""")

code(r"""def kmeans(X, k, n_restart=10, n_iter=50, seed=0):
    rng = np.random.RandomState(seed)
    n, d = X.shape
    best, best_inertia = None, np.inf
    for _ in range(n_restart):
        # k-means++
        cent = [X[rng.randint(n)]]
        for _ in range(1, k):
            D = np.min(np.stack([np.sum((X - c) ** 2, 1) for c in cent], 1), 0)
            prob = D / D.sum()
            cent.append(X[rng.choice(n, p=prob)])
        C = np.array(cent)
        L = None
        for _ in range(n_iter):
            D = np.sqrt(((X[:, None] - C[None]) ** 2).sum(2))
            L = D.argmin(1)
            new_C = np.array([X[L == j].mean(0) if (L == j).any() else C[j] for j in range(k)])
            if np.allclose(C, new_C):
                break
            C = new_C
        inertia = sum(np.sum((X[L == j] - C[j]) ** 2) for j in range(k))
        if inertia < best_inertia:
            best_inertia, best = inertia, (L, C)
    labels, centroids = best
    return labels, centroids, best_inertia

X = np.array([imagenes[m].flatten() for m in muns if m in imagenes])
labels, centroids, inertia = kmeans(X, k=3, seed=42)
print(f"Vocaciones descubiertas: k=3, inercia total = {inertia:.2f}")
mun_orden = [m for m in muns if m in imagenes]
voc = {m: int(labels[i]) for i, m in enumerate(mun_orden)}

# Renombrar clusters por el cultivo dominante de cada uno (desambiguando repetidos)
centroids_reshaped = centroids.reshape(-1, len(TOP12), 7)
nombres = {}
usados = {}
for k, c in enumerate(centroids_reshaped):
    media_anual = c.mean(1)
    cult_dom = TOP12[int(np.argmax(media_anual))]
    if cult_dom in usados:
        usados[cult_dom] += 1
        cult_dom = f"{cult_dom} ({usados[cult_dom]})"
    else:
        usados[cult_dom] = 1
    nombres[k] = cult_dom
print("Vocaciones renombradas por cultivo dominante:")
for k, n in nombres.items():
    print(f"  Cluster {k} -> '{n}' (z medio: {centroids_reshaped[k].mean():.2f})")

voc_n = {m: nombres[voc[m]] for m in voc}
save_json("m4_clusters_vocacion.json", {
    "municipios": voc_n, "centroids_z_mean": centroids_reshaped.mean((1, 2)).tolist(),
    "nombres": nombres, "inercia": float(inertia)})""")

md(r"""## 4.3 Entrenamiento de la CNN (3 clases de vocación)
Imagen: (1, 12, 7). Arquitectura: Conv3x3(1→4) → ReLU → MaxPool2 → Dense → 3.
Split estratificado: 30 train / resto test (garantiza las 3 clases en ambos sets),
40 epochs, lr 0.01.""")

code(r"""rng = np.random.RandomState(0)
label_map = {n: i for i, n in enumerate(nombres.values())}

muns_by_clase = {}
for m in voc:
    muns_by_clase.setdefault(voc[m], []).append(m)

N_TRAIN = 30
muns_train = []
for clase, ms in muns_by_clase.items():
    n_clase_train = max(1, round(N_TRAIN * len(ms) / len(voc)))
    elegidos = rng.choice(ms, size=min(n_clase_train, len(ms)), replace=False).tolist()
    muns_train.extend(elegidos)
muns_train = muns_train[:N_TRAIN] if len(muns_train) > N_TRAIN else muns_train
muns_test = [m for m in voc if m not in muns_train]
print(f"train: {len(muns_train)} | test: {len(muns_test)}")
print("Distribucion train por clase:", {k: sum(1 for m in muns_train if voc[m] == k)
                                         for k in muns_by_clase})

y_train = np.array([label_map[voc_n[m]] for m in muns_train])
y_test  = np.array([label_map[voc_n[m]] for m in muns_test])

net = CNN(C=1, F=4, n_classes=len(label_map), seed=42)
for ep in range(40):
    order = rng.permutation(len(muns_train))
    tot = 0.0; ok = 0
    for k in order:
        x = imagenes[muns_train[k]][None]  # (1, 12, 7)
        lg, _ = net.logits(x)
        loss, d = net.loss_grad(lg, y_train[k])
        net.backward(d)
        net.step(0.01)
        tot += loss
        if int(np.argmax(lg)) == y_train[k]:
            ok += 1
    if (ep + 1) % 5 == 0:
        print(f"Epoch {ep+1:2d} | loss {tot/len(muns_train):.3f} | acc {ok/len(muns_train):.2%}")""")

md(r"""## 4.4 Evaluación vs baseline (clase mayoritaria)""")

code(r"""ok_train = sum(net.predict(imagenes[m][None]) == y_train[k] for k, m in enumerate(muns_train))
ok_test  = sum(net.predict(imagenes[m][None]) == y_test[k] for k, m in enumerate(muns_test))

maj = int(np.bincount(y_train).argmax())
acc_base_train = float((y_train == maj).mean())
acc_base_test  = float((y_test  == maj).mean())

print(f"CNN  acc:  train {ok_train/len(muns_train):.2%}  | test {ok_test/len(muns_test):.2%}")
print(f"Base acc:  train {acc_base_train:.2%}  | test {acc_base_test:.2%}")
print(f"Ganancia sobre baseline en test: {(ok_test/len(muns_test) - acc_base_test):+.2%}")
save_json("m4_cnn_accuracy.json", {
    "cnn_train": float(ok_train/len(muns_train)),
    "cnn_test":  float(ok_test/len(muns_test)),
    "baseline_train": acc_base_train,
    "baseline_test":  acc_base_test,
    "n_train": len(muns_train), "n_test": len(muns_test)})""")

md(r"""## 4.5 Visualización de filtros — leyendo la CNN
El kernel de la capa conv tiene forma `(F, 1, 3, 3)`: cada uno de los `F` filtros
es una ventana de **3×3 local** sobre la imagen 12×7 (3 cultivos consecutivos ×
3 años consecutivos), no "un cultivo completo". Por eso no tiene sentido asignarle
un único cultivo a cada filtro; en su lugar mostramos el heatmap del kernel y,
para cada filtro, la posición (cultivos/años) donde su activación es más fuerte
sobre las imágenes reales.""")

code(r"""fig, axs = plt.subplots(1, 4, figsize=(16, 4))
for f, ax in enumerate(axs):
    filt = net.conv.K[f, 0]   # (3, 3)
    vmax = np.abs(filt).max()
    vmax = vmax if vmax > 0 else 1.0
    im = ax.imshow(filt, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_title(f"Filtro {f+1}")
    ax.set_xticks(range(filt.shape[1])); ax.set_xticklabels(range(filt.shape[1]), fontsize=8)
    ax.set_yticks([])
    for i in range(filt.shape[0]):
        for j in range(filt.shape[1]):
            ax.text(j, i, f"{filt[i, j]:+.1f}", ha="center", va="center", fontsize=6)
plt.suptitle("Filtros aprendidos (1 canal x 12 cultivos x 7 anos, kernel 3x3 local)", fontsize=11)
plt.colorbar(im, ax=axs, fraction=0.02, pad=0.02)
plt.tight_layout()
save_png("m4_filtros_cnn.png", fig)
plt.show()

# Para cada filtro: en que municipio y en que posicion (cultivo, anio) de la
# imagen produce la activacion mas fuerte (antes de ReLU/pool), usando el set completo.
print("\nActivacion maxima por filtro (municipio y ventana cultivo/anio de origen):")
kh, kw = net.conv.K.shape[-2:]
for f in range(net.conv.K.shape[0]):
    mejor = (None, -np.inf, None)
    for m, img in imagenes.items():
        H, W = img.shape
        for i in range(H - kh + 1):
            for j in range(W - kw + 1):
                ventana = img[i:i + kh, j:j + kw]
                act = float((ventana * net.conv.K[f, 0]).sum())
                if act > mejor[1]:
                    mejor = (m, act, (i, j))
    m, act, (i, j) = mejor
    cult_ini = TOP12[i] if i < len(TOP12) else "?"
    print(f"  Filtro {f+1}: max activacion {act:+.2f} en {m}, "
          f"ventana cultivos[{i}:{i+kh}] (~{cult_ini}...) x anios[{ANIOS[j]}:{ANIOS[j]+kw-1}]")""")

md(r"""## 4.6 Interpretación
- La CNN aprende a clasificar vocación con la accuracy reportada arriba vs el baseline
  de clase mayoritaria (con n≈42 municipios, y menos tras excluir los que tenían
  datos incompletos — ver conteo en 4.1).
- Los filtros muestran **patrones locales** (vecindarios 3×3 de cultivo×año) que activan la red;
  la celda anterior identifica en qué municipio y ventana concreta se activa más cada filtro.
- Limitación honesta: con pocas decenas de muestras, la CNN no necesariamente supera a un
  baseline fuerte por potencia estadística.
- La lección científica: **CNN es la arquitectura correcta para patrones espaciales**;
  necesita más datos (panel nacional) o transferencia desde otro dataset para brillar.
- En el Módulo 5 (Transformers) usaremos **atención** que no requiere vecindarios fijos
  y puede capturar interdependencias globales entre cultivos.""")

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
Path("notebooks/curso/04_cnn_patrones_espaciales.ipynb").write_text(
    json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("[OK] notebooks/curso/04_cnn_patrones_espaciales.ipynb (version optimizada)")