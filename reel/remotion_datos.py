"""Pasa la narración y el guion a reel/remotion/src/datos.json y copia el audio a public/.

    python reel/remotion_datos.py [narracion_17b]

Tiempos de cada escena (de voz.py) y subtítulos en bloques cortos con las cifras en dígitos.
"""
import json, re, shutil, sys
from pathlib import Path
import numpy as np
from num2words import num2words

AQUI = Path(__file__).parent
REM = AQUI / "remotion"


def hablado(s):
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s).replace("%", " por ciento")
    return re.sub(r"\d+", lambda m: num2words(int(m.group()), lang="es"), s)


def bloques(texto, palabras, ini, fin, maxp=4, maxl=24):
    """Corta el subtítulo en bloques y les da el tiempo de las palabras que oyó Whisper."""
    bl, act = [], []
    for p in texto.split():
        act.append(p)
        if len(act) >= maxp or len(" ".join(act)) >= maxl or p[-1] in ".,;?!":
            bl.append(act); act = []
    if act:
        bl.append(act)
    n = np.array([len(hablado(" ".join(b)).split()) for b in bl])
    corte = np.concatenate([[0], np.cumsum(n)]) / n.sum()
    ws = [p for p in palabras if ini - 0.3 <= p[0] <= fin + 0.1]
    def tiempo(x):
        if not ws:
            return ini + (fin - ini) * x
        i = min(len(ws) - 1, int(round(x * len(ws))))
        return ws[i][0] if x < 1 else ws[-1][1]
    out = []
    for i, b in enumerate(bl):
        a, z = tiempo(corte[i]), tiempo(corte[i + 1])
        pesos = np.array([len(hablado(w)) for w in b], float)
        c = a + (z - a) * np.concatenate([[0], np.cumsum(pesos)]) / pesos.sum()
        out.append({"ini": round(a, 3), "fin": round(z, 3), "palabras": [{"t": w, "ini": round(c[j], 3)} for j, w in enumerate(b)]})
    return out


if __name__ == "__main__":
    nombre = sys.argv[1] if len(sys.argv) > 1 else "narracion"
    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    nar = json.loads((AQUI / "salidas" / f"{nombre}.json").read_text(encoding="utf-8"))
    esc = nar["escenas"]
    habla = esc[-1][1] + 0.6
    cortes = [0] + [(esc[i - 1][1] + esc[i][0]) / 2 for i in range(1, len(esc))] + [habla]
    subs = [s for i, e in enumerate(guion["escenas"]) for s in bloques(e["subtitulo"], nar["palabras"], *esc[i])]
    datos = {"habla": round(habla, 3), "cortes": [round(c, 3) for c in cortes], "escenas": esc, "subtitulos": subs,
             "fuente": guion["fuente"], "titulares": json.loads((AQUI / "recursos" / "titulares" / "fuentes.json").read_text(encoding="utf-8"))}
    (REM / "src" / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.copy(AQUI / "salidas" / f"{nombre}.wav", REM / "public" / "narracion.wav")
    print(f"{len(subs)} bloques; voz {habla:.1f} s")
