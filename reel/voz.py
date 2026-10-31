"""Narración con la voz clonada (Qwen3-TTS 0.6B) y tiempos de cada palabra (Whisper).

Usa reel.py de la sesión 15 del curso (d2cml-ai/Data-Science-Python/sessions/15-texto-a-reel).
Guarda reel/salidas/narracion.wav y narracion.json (escenas, palabras y WER por escena).
"""
import json, sys
from pathlib import Path
AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parents[1] / "Data-Science-Python" / "sessions" / "15-texto-a-reel"))
import reel, soundfile as sf

if __name__ == "__main__":
    sal = AQUI / "salidas"; sal.mkdir(exist_ok=True)
    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    voz = reel.Voz(next(AQUI.glob("mi_voz.*")), modelo="Qwen/Qwen3-TTS-12Hz-0.6B-Base", device="cuda")
    print("referencia:", voz.texto_ref, flush=True)
    vel = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    n = reel.narrar(voz, guion, velocidad=vel)
    reel.subtitulos(n, guion)
    sf.write(sal / "narracion.wav", n.audio, n.sr)
    (sal / "narracion.json").write_text(json.dumps({"sr": n.sr, "escenas": n.escenas, "palabras": n.palabras,
        "wer": [e["wer"] for e in guion["escenas"]]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"duración {n.duracion:.1f} s; WER", [round(e["wer"], 2) for e in guion["escenas"]])
