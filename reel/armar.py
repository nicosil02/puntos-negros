"""Arma el reel vertical (1080x1920) a partir de la narración (voz.py), los clips del dashboard y los recursos.

    python reel/voz.py      # narración con la voz clonada
    python reel/armar.py    # video: reel/salidas/reel.mp4 y reel.srt

Fondos por escena: titulares de prensa, vuelos del mapa del dashboard (grabados con Playwright),
el panel del MTC, pares satelitales de Esri y un recorrido del dashboard en el celular.
"""
import json, re, subprocess
from pathlib import Path
import numpy as np
import imageio_ffmpeg
from num2words import num2words
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent
R, SAL, DOCS = AQUI / "recursos", AQUI / "salidas", AQUI.parent / "docs"
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 30
FONDO, TINTA, SUAVE, ACENTO, CAJA = (17, 19, 22), (245, 245, 245), (175, 181, 190), (234, 88, 12), (28, 31, 36)
M = 72                      # margen lateral
CREDITOS = 3.0              # segundos de créditos al final
MUSICA = R / "musica" / "Floating_Cities.mp3"
AUTOR = "Nicolás Silva Andújar"


def fuente(tam, peso=500):
    f = ImageFont.truetype(str(R / "fuentes" / "Geist.ttf"), tam)
    f.set_variation_by_axes([peso])
    return f


def envolver(d, texto, f, ancho):
    lineas, act = [], ""
    for p in texto.split():
        if d.textlength(f"{act} {p}".strip(), font=f) <= ancho:
            act = f"{act} {p}".strip()
        else:
            lineas.append(act); act = p
    return lineas + [act]


def cubrir(img, ancho=W, alto=H):
    """Escala y recorta al centro para llenar el cuadro."""
    e = max(ancho / img.width, alto / img.height)
    img = img.resize((round(img.width * e), round(img.height * e)), Image.LANCZOS)
    x, y = (img.width - ancho) // 2, (img.height - alto) // 2
    return img.crop((x, y, x + ancho, y + alto))


# Fondos ----------------------------------------------------------------------

class Clip:
    """Tramo [a, b] de un video, estirado o comprimido a la duración de la escena."""
    def __init__(self, archivo, a, b):
        self.archivo, self.a, self.b = archivo, a, b

    def abrir(self, n):
        self.n, self.ult = n, None
        f = n / FPS / (self.b - self.a)
        self.p = subprocess.Popen([FF, "-v", "error", "-ss", str(self.a), "-t", str(self.b - self.a), "-i", str(self.archivo),
                                   "-vf", f"setpts={f}*PTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                                   "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)

    def cuadro(self, k):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            self.ult = Image.frombuffer("RGB", (W, H), b)
        return self.ult.copy()


class Fijo:
    """Fondo dibujado con Pillow según el avance de la escena (0 a 1)."""
    def __init__(self, dibujar):
        self.dibujar = dibujar

    def abrir(self, n):
        self.n = n

    def cuadro(self, k):
        return self.dibujar(k / max(1, self.n - 1), k / FPS)


def entrar(t, t0, dur=0.45):
    """0 a 1 con suavizado, desde el segundo t0."""
    x = min(1, max(0, (t - t0) / dur))
    return 1 - (1 - x) ** 3


def titulares():
    fuentes = json.loads((R / "titulares" / "fuentes.json").read_text(encoding="utf-8"))
    tarjetas = []
    for s in fuentes:
        img = Image.open(R / "titulares" / s["img"]).convert("RGB")
        ancho = W - 2 * M - 56
        img = img.resize((ancho, round(img.height * ancho / img.width)), Image.LANCZOS)
        c = Image.new("RGB", (W - 2 * M, img.height + 84), "white")
        d = ImageDraw.Draw(c)
        d.text((28, 18), f"{s['medio']} · {s['fecha']}".upper(), font=fuente(26, 700), fill=(150, 40, 0))
        c.paste(img, (28, 58))
        tarjetas.append(c)

    def dibujar(p, t):
        img = Image.new("RGB", (W, H), FONDO)
        y = 230
        for i, c in enumerate(tarjetas):
            a = entrar(t, 0.2 + i * 0.9)
            if a > 0:
                capa = c.copy(); capa.putalpha(int(255 * a))
                img.paste(capa, (M, int(y + 50 * (1 - a))), capa)
            y += c.height + 16
        return img
    return Fijo(dibujar)


def panel(archivo):
    base = Image.open(archivo).convert("RGB")
    ancho = W - 2 * M
    base = base.resize((ancho, round(base.height * ancho / base.width)), Image.LANCZOS)

    def dibujar(p, t):
        img = Image.new("RGB", (W, H), FONDO)
        e = 1 + 0.04 * p
        pn = base.resize((round(base.width * e), round(base.height * e)), Image.LANCZOS)
        a = entrar(t, 0.1)
        capa = pn.copy(); capa.putalpha(int(255 * a))
        img.paste(capa, ((W - pn.width) // 2, int(300 + 40 * (1 - a))), capa)
        return img
    return Fijo(dibujar)


def satelite(pares):
    """Pares punto negro / misma vía a 1.5 km, uno tras otro."""
    lug = {l["pn"]: l for l in json.loads((DOCS / "datos.json").read_text(encoding="utf-8"))["lugares"]}
    lado = (W - 2 * M - 24) // 2
    fotos = [(Image.open(DOCS / "img" / f"sat_{n}_pn.jpg").resize((lado, lado)),
              Image.open(DOCS / "img" / f"sat_{n}_ctrl.jpg").resize((lado, lado)), lug[n]) for n in pares]

    def dibujar(p, t):
        img = Image.new("RGB", (W, H), FONDO)
        i = min(len(fotos) - 1, int(p * len(fotos)))
        pn, ctrl, l = fotos[i]
        t0 = i * (1 / len(fotos))
        d = ImageDraw.Draw(img)
        d.text((M, 330), f"{l['dist'].title()} · {l['via']}", font=fuente(46, 700), fill=TINTA)
        d.text((M, 392), f"{l['muertos']} fallecidos en 200 metros", font=fuente(34, 500), fill=SUAVE)
        y = 470
        img.paste(pn, (M, y)); img.paste(ctrl, (M + lado + 24, y))
        d.rectangle((M, y, M + lado - 1, y + lado - 1), outline=ACENTO, width=5)
        d.text((M, y + lado + 18), "Punto negro", font=fuente(34, 700), fill=ACENTO)
        d.text((M + lado + 24, y + lado + 18), "Misma vía, 1.5 km después", font=fuente(30, 500), fill=SUAVE)
        return img
    return Fijo(dibujar)


CLIPS = R / "clips"
FONDOS = [
    titulares(),
    Clip(CLIPS / "todo.webm", 17.2, 28.2),          # Lima y vuelo a Comas
    Clip(CLIPS / "todo.webm", 5.7, 17.2),           # el Perú, siniestros y columnas
    Clip(CLIPS / "todo.webm", 28.2, 34.2),          # solo lugares con 5 o más
    panel(R / "panel_onsv.png"),
    satelite([59, 191, 170]),
    Clip(CLIPS / "dashboard.webm", 3.0, 20.5),
]
CON_CIFRA = [True, True, True, True, False, True, True]


# Capas fijas -------------------------------------------------------------------

def velo():
    """Oscurece arriba y abajo para que el texto se lea sobre el mapa."""
    a = np.zeros((H, 1), np.float32)
    y = np.arange(H)
    a[:, 0] = np.clip((300 - y) / 300, 0, 1) * 0.85 + np.clip((y - 1150) / 500, 0, 1) * 0.92
    a = np.clip(a, 0, 0.95)
    capa = np.zeros((H, W, 4), np.uint8)
    capa[..., :3] = FONDO
    capa[..., 3] = (np.repeat(a, W, axis=1) * 255).astype(np.uint8)
    return Image.fromarray(capa, "RGBA")


def marco(guion):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    d.text((M, 120), guion["titulo"].upper(), font=fuente(40, 800), fill=ACENTO)
    f = fuente(26, 600)
    aviso = "VOZ GENERADA CON IA"
    x1 = W - M
    x0 = x1 - d.textlength(aviso, font=f) - 36
    d.rounded_rectangle((x0, 118, x1, 166), radius=24, outline=SUAVE, width=2)
    d.text(((x0 + x1) / 2, 142), aviso, font=f, fill=SUAVE, anchor="mm")
    pie = fuente(26, 500)
    for i, l in enumerate(envolver(d, f"{AUTOR} · Fuente: {guion['fuente']}", pie, W - 2 * M)):
        d.text((M, 1800 + i * 36), l, font=pie, fill=SUAVE)
    return capa


def tarjeta(e):
    """Cifra grande y su etiqueta, con la base en y = 1480."""
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    fe = fuente(40, 500)
    lineas = envolver(d, e["etiqueta"], fe, W - 2 * M)
    tam = 170
    while d.textlength(e["cifra"], font=fuente(tam, 800)) > W - 2 * M:
        tam -= 10
    fc = fuente(tam, 800)
    y = 1480 - len(lineas) * 52
    for i, l in enumerate(lineas):
        d.text((M, y + i * 52), l, font=fe, fill=TINTA)
    d.text((M, y - 18), e["cifra"], font=fc, fill=ACENTO, anchor="ls")
    return capa


# Subtítulos ------------------------------------------------------------------

def hablado(s):
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s).replace("%", " por ciento")
    return re.sub(r"\d+", lambda m: num2words(int(m.group()), lang="es"), s)


def bloques(texto, palabras, ini, fin, maxp=4, maxl=24):
    """Corta el subtítulo (con cifras) en bloques y les da el tiempo de las palabras que oyó Whisper."""
    bl, act = [], []
    for p in texto.split():
        act.append(p)
        if len(act) >= maxp or len(" ".join(act)) >= maxl or p[-1] in ".,;?!":
            bl.append(" ".join(act)); act = []
    if act:
        bl.append(" ".join(act))
    n = np.array([len(hablado(b).split()) for b in bl])
    corte = np.concatenate([[0], np.cumsum(n)]) / n.sum()
    ws = [p for p in palabras if ini - 0.3 <= p[0] <= fin + 0.1]
    def tiempo(x):   # x en [0, 1] del texto hablado
        if not ws:
            return ini + (fin - ini) * x
        i = min(len(ws) - 1, int(round(x * len(ws))))
        return ws[i][0] if x < 1 else ws[-1][1]
    return [(tiempo(corte[i]), tiempo(corte[i + 1]), b) for i, b in enumerate(bl)]


def a_srt(subs, ruta):
    hms = lambda t: f"{int(t // 3600):02}:{int(t % 3600 // 60):02}:{int(t % 60):02},{int(t % 1 * 1000):03}"
    ruta.write_text("\n".join(f"{i}\n{hms(a)} --> {hms(b)}\n{s}\n" for i, (a, b, s) in enumerate(subs, 1)), encoding="utf-8")


def creditos(guion):
    img = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(img)
    d.text((M, 520), "¿Hay uno en tu ruta diaria?", font=fuente(58, 800), fill=TINTA)
    d.text((M, 600), "Búscalo en el dashboard. Enlace en la publicación.", font=fuente(34, 500), fill=ACENTO)
    tit = json.loads((R / "titulares" / "fuentes.json").read_text(encoding="utf-8"))
    lineas = [("Datos", guion["fuente"].replace(";", ",")),
              ("Titulares", ", ".join(f"{s['medio']} ({s['fecha'][-4:]})" for s in tit)),
              ("Voz", "generada con IA (Qwen3-TTS) a partir de la voz del autor"),
              ("Música", "\"Floating Cities\", Kevin MacLeod (incompetech.com), licencia CC BY 4.0"),
              ("Autor", AUTOR)]
    y, f1, f2 = 800, fuente(30, 700), fuente(30, 400)
    for k, v in lineas:
        d.text((M, y), k.upper(), font=f1, fill=SUAVE)
        for l in envolver(d, v, f2, W - 2 * M):
            y += 42
            d.text((M, y), l, font=f2, fill=TINTA)
        y += 70
    return img


# Video -----------------------------------------------------------------------

if __name__ == "__main__":
    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    import sys
    borrador = "--borrador" in sys.argv   # sin voz: tiempos estimados a 2.6 palabras por segundo, solo música
    if borrador:
        esc, t = [], 0.3
        for e in guion["escenas"]:
            d = len(e["frase"].split()) / 2.6
            esc.append((t, t + d)); t += d + 0.35
        nar = {"escenas": esc, "palabras": []}
    else:
        nar = json.loads((SAL / "narracion.json").read_text(encoding="utf-8"))
    esc, palabras = nar["escenas"], nar["palabras"]
    habla = esc[-1][1] + 0.6
    total = habla + CREDITOS
    # cada escena va desde la mitad de la pausa anterior hasta la mitad de la siguiente
    cortes = [0] + [(esc[i - 1][1] + esc[i][0]) / 2 for i in range(1, len(esc))] + [habla]
    subs = [s for i, e in enumerate(guion["escenas"]) for s in bloques(e["subtitulo"], palabras, *esc[i])]
    a_srt(subs, SAL / "reel.srt")

    base_velo, base_marco = velo(), marco(guion)
    tarjetas = [tarjeta(e) if c else None for e, c in zip(guion["escenas"], CON_CIFRA)]
    fin_img = creditos(guion)
    fs = fuente(58, 700)

    cmd = [FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           *(["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono"] if borrador else ["-i", str(SAL / "narracion.wav")]), "-i", str(MUSICA),
           "-filter_complex", f"[1]loudnorm=I=-14:TP=-1.5:LRA=11,apad[v];[2]volume=0.13,afade=t=in:d=1.5,"
                              f"afade=t=out:st={total - 2.5:.2f}:d=2.5[m];[v][m]amix=inputs=2:normalize=0[a]",
           "-map", "0:v", "-map", "[a]", "-t", f"{total:.2f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", str(SAL / ("borrador.mp4" if borrador else "reel.mp4"))]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i, fondo in enumerate(FONDOS):
        k0, k1 = round(cortes[i] * FPS), round(cortes[i + 1] * FPS)
        fondo.abrir(k1 - k0)
        for k in range(k0, k1):
            t = k / FPS
            img = fondo.cuadro(k - k0).convert("RGBA")
            img.alpha_composite(base_velo)
            img.alpha_composite(base_marco)
            if tarjetas[i]:
                a = entrar(t, cortes[i] + 0.15)
                capa = tarjetas[i] if a >= 1 else Image.fromarray((np.asarray(tarjetas[i]) * [1, 1, 1, a]).astype(np.uint8), "RGBA")
                img.alpha_composite(capa, (0, int(30 * (1 - a))))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle((M, 80, W - M, 86), radius=3, fill=CAJA)
            d.rounded_rectangle((M, 80, M + (W - 2 * M) * t / total, 86), radius=3, fill=ACENTO)
            s = next((s for a, b, s in subs if a - 0.05 <= t <= b + 0.15), None)
            if s:
                w = d.textlength(s, font=fs)
                x, y = (W - w) / 2, 1585
                d.rounded_rectangle((x - 34, y - 22, x + w + 34, y + 84), radius=26, fill=CAJA)
                d.text((x, y), s, font=fs, fill=TINTA)
            proc.stdin.write(img.convert("RGB").tobytes())
        if hasattr(fondo, "p"):
            fondo.p.kill()
    for k in range(round(habla * FPS), round(total * FPS)):
        proc.stdin.write(fin_img.tobytes())
    proc.stdin.close(); proc.wait()
    print(f"listo ({total:.1f} s)")
