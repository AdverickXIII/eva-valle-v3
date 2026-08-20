"""Agrega checkbox para filtrar LQ por participacion municipal >= 5%."""
from pathlib import Path

p = Path("ui/pages/2_Descriptivo.py")
c = p.read_text(encoding="utf-8")

old = "        df_lq = lq_top(df_f, 20)"
new = (
    "        solo_pesadas = st.checkbox("
    "\"Solo vocaciones con peso (participacion municipal >= 5%)\", value=True)\n"
    "        df_lq = lq_top(df_f, 200)\n"
    "        if solo_pesadas:\n"
    "            df_lq = df_lq[df_lq['share_municipio_pct'] >= 5].head(20)\n"
    "        else:\n"
    "            df_lq = df_lq.head(20)"
)
if old in c:
    p.write_text(c.replace(old, new, 1), encoding="utf-8")
    print("[OK] Checkbox de filtro agregado a la tabla LQ")
else:
    print("[INFO] Linea no encontrada; revisa manualmente")