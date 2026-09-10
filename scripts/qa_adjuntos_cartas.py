"""QA de adjuntos: certifica cartas (tamano + logo) y anexo antes del envio."""
from pathlib import Path

CAR = Path(__file__).resolve().parent.parent / "cartas_comerciales"
ANEXO = "anexo_proyeccion_platano_alcala_MLP.pdf"

DESTINOS = [
    ("1 Valle (Dra. Angela Reyes)", "carta_1_secretaria_valle.pdf",
     "correo_1_valle.txt", "ayreyes@valledelcauca.gov.co"),
    ("2 MinTIC Gobierno Digital", "carta_2_mintic_adquisicion.pdf",
     "correo_2_mintic.txt", "minticresponde@mintic.gov.co"),
    ("3 CiberPaz (Unipamplona)", "carta_3_ciberpaz_educativa.pdf",
     "correo_3_ciberpaz.txt", "mesa.ayuda1@unipamplona.edu.co"),
]

todo_ok = True
for nombre, fc, fm, mail in DESTINOS:
    pc, pm, pa = CAR / fc, CAR / fm, CAR / ANEXO
    ok_carta = pc.exists() and pc.stat().st_size > 5000 and b"/Subtype /Image" in pc.read_bytes()
    ok_correo = pm.exists()
    ok_anexo = pa.exists() and pa.stat().st_size > 5000
    todo_ok &= ok_carta & ok_correo & ok_anexo
    print(f"\n{nombre} -> {mail}")
    print(f"  {'✅' if ok_carta else '❌'} carta PDF (con logo): {fc}")
    print(f"  {'✅' if ok_correo else '❌'} correo presentacion: {fm}")
    print(f"  {'✅' if ok_anexo else '❌'} anexo proyeccion: {ANEXO}")

print("\n🚀 LISTO PARA ENVIAR los 3 correos" if todo_ok
      else "\n⛔ FALTA algo: completa lo marcado ❌ antes de enviar")