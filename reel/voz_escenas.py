"""Vuelve a narrar algunas escenas con varias tomas y se queda con la mejor; el resto de la narración no cambia.

    python reel/voz_escenas.py 2 5 7 --tomas 5 --velocidad 1.08

Criterio: que Whisper entienda la frase (WER bajo) y, entre esas, la toma menos apagada
(centroide espectral alto en sus partes más oscuras). En una pregunta, la que más sube el tono al final.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parents[1] / "Data-Science-Python" / "sessions" / "15-texto-a-reel"))
import reel


def claridad(w, sr):
    """Percentil 10 del centroide espectral en tramos con voz: bajo = partes apagadas."""
    c = librosa.feature.spectral_centroid(y=w, sr=sr)[0]
    e = librosa.feature.rms(y=w)[0]
    return float(np.percentile(c[e > 0.3 * e.max()], 10))


def sube(w, sr):
    """Cuánto sube el tono en el último medio segundo con voz frente a toda la frase."""
    f0, voz, _ = librosa.pyin(w, fmin=70, fmax=400, sr=sr)
    f0 = f0[voz]
    return float(np.nanmedian(f0[-12:]) / np.nanmedian(f0)) if len(f0) > 24 else 0.0


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("escenas", type=int, nargs="+", help="números de escena, desde 1")
    a.add_argument("--tomas", type=int, default=5)
    a.add_argument("--velocidad", type=float, default=1.08)
    a = a.parse_args()
    sal = AQUI / "salidas"
    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    audio, sr = sf.read(sal / "narracion.wav", dtype="float32")
    nar = json.loads((sal / "narracion.json").read_text(encoding="utf-8"))
    partes = [audio[int(i * sr):int(f * sr)] for i, f in nar["escenas"]]
    wer = nar["wer"]

    voz = reel.Voz(next(AQUI.glob("mi_voz.*")), modelo="Qwen/Qwen3-TTS-12Hz-0.6B-Base", device="cuda")
    for n in a.escenas:
        e = guion["escenas"][n - 1]
        # una pregunta se narra aparte para elegir la toma que sube el tono al final
        frases = [x.strip() + "?" for x in e["frase"].split("?")[:-1]] + [e["frase"].split("?")[-1].strip()]
        trozos, wers = [], []
        for frase in filter(None, frases):
            tomas = []
            for _ in range(a.tomas):
                w = voz.decir([frase])[0]
                w = reel._acelerar(w, voz.sr, a.velocidad) if a.velocidad != 1 else np.asarray(w, np.float32)
                w = np.interp(np.arange(0, len(w), voz.sr / sr), np.arange(len(w)), w).astype(np.float32) if voz.sr != sr else w
                tomas.append((reel._wer(frase, reel._a16k(w, sr)), w))
            buenas = [t for t in tomas if t[0] <= 0.08] or sorted(tomas, key=lambda t: t[0])[:1]
            nota = (lambda w: sube(w, sr)) if frase.endswith("?") else (lambda w: claridad(w, sr))
            puntajes = [nota(w) for _, w in buenas]
            k = int(np.argmax(puntajes))
            print(f"escena {n}, «{frase[:30]}»: {len(buenas)} de {a.tomas} tomas con WER bajo; puntajes {[round(p, 2) for p in puntajes]}; elijo {k}", flush=True)
            wers.append(buenas[k][0]); trozos += [librosa.effects.trim(buenas[k][1], top_db=35)[0], np.zeros(int(0.3 * sr), np.float32)]  # sin silencios propios de la toma
        wer[n - 1], partes[n - 1] = max(wers), np.concatenate(trozos[:-1])

    # se vuelve a armar con las mismas pausas que reel.narrar
    trozos, esc, t = [np.zeros(int(reel.INICIO * sr), np.float32)], [], reel.INICIO
    for w in partes:
        esc.append((t, t + len(w) / sr))
        trozos += [w, np.zeros(int(reel.PAUSA * sr), np.float32)]
        t += len(w) / sr + reel.PAUSA
    trozos.append(np.zeros(int(reel.FINAL * sr), np.float32))
    n = reel.Narracion(np.concatenate(trozos), sr, esc)
    reel.subtitulos(n, guion)
    sf.write(sal / "narracion.wav", n.audio, sr)
    (sal / "narracion.json").write_text(json.dumps({"sr": sr, "escenas": esc, "palabras": n.palabras, "wer": wer}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"duración {n.duracion:.1f} s; WER {[round(x, 2) for x in wer]}")
