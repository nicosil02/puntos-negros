"""Auditoría satelital: los 30 puntos negros más letales frente a un lugar de control sobre la misma vía.

El control está a 1-2.5 km del punto negro (hasta 5 km si no hay), en la misma vía de OpenStreetMap (misma ref o nombre)
y sin siniestros fatales dentro de su círculo de 200 m. Así el tráfico es parecido y lo que cambia es el lugar.
Baja la foto satelital de Esri (zoom 18, ~600 m de lado) con un círculo de 200 m, y les pone un código al azar
para codificarlas a ciegas. La clave queda en datos/crudos/auditoria/clave.csv.
"""
import io, json, subprocess
from pathlib import Path
import numpy as np, pandas as pd
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from shapely import STRtree, Point
from vias import RAIZ, leer_vias, xy, COS

SAL = RAIZ / "datos" / "crudos" / "auditoria"
TESELA = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
Z, LADO = 18, 1024
lonlat = lambda X: (X[0] / (111320 * COS), X[1] / 110540)


def control(p, lineas, clave, k, sin):
    """Punto de la misma vía a 1-2.5 km de p (o hasta 5 km), sin siniestros en 200 m; el más cercano a 1.5 km."""
    cand = [i for i in range(len(lineas)) if clave[i] == k and lineas[i].distance(Point(p)) < 5500]
    pts = np.vstack([np.array([lineas[i].interpolate(d).coords[0] for d in np.arange(0, lineas[i].length, 50)]) for i in cand if lineas[i].length > 0])
    d = np.hypot(*(pts - p).T)
    libre = sin.query(pts)[0] > 200
    for lo, hi in [(1000, 2500), (800, 5000)]:
        ok = libre & (d >= lo) & (d <= hi)
        if ok.any():
            return pts[ok][np.argmin(abs(d[ok] - 1500))]
    return None


def foto(lon, lat):
    """Prueba zoom 18; donde Esri no tiene esa resolución (zonas rurales) baja a 17 o 16."""
    for z in (Z, 17, 16):
        img = foto_z(lon, lat, z)
        if (np.asarray(img)[::8, ::8] == 204).all(axis=2).mean() < 0.2:  # 204 = gris de "Map data not yet available"
            return img, z
    return img, z


def foto_z(lon, lat, Z):
    n = 2 ** Z
    fx, fy = (lon + 180) / 360 * n, (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * n
    x0, y0 = int(fx) - 2, int(fy) - 2
    img = Image.new("RGB", (256 * 5, 256 * 5))
    for i in range(5):
        for j in range(5):
            b = subprocess.run(["curl", "-s", "--max-time", "30", "--retry", "3", TESELA.format(z=Z, x=x0 + i, y=y0 + j)], capture_output=True, check=True).stdout
            img.paste(Image.open(io.BytesIO(b)), (256 * i, 256 * j))
    cx, cy = (fx - x0) * 256, (fy - y0) * 256
    img = img.crop((int(cx - LADO / 2), int(cy - LADO / 2), int(cx + LADO / 2), int(cy + LADO / 2)))
    r = 200 / (156543.03 * np.cos(np.radians(lat)) / n)  # 200 m en píxeles
    c = LADO / 2
    dib = ImageDraw.Draw(img)
    dib.ellipse((c - r, c - r, c + r, c + r), outline=(255, 255, 0), width=3)
    dib.line((c - 12, c, c + 12, c), fill=(255, 255, 0), width=3); dib.line((c, c - 12, c, c + 12), fill=(255, 255, 0), width=3)
    return img


if __name__ == "__main__":
    SAL.mkdir(parents=True, exist_ok=True)
    lug = pd.DataFrame(json.load(open(RAIZ / "docs" / "datos.json", encoding="utf-8"))["lugares"])
    top = lug.sort_values(["muertos", "n"], ascending=False).head(30)
    s = pd.read_csv(RAIZ / "datos" / "procesados" / "siniestros.csv")
    sin = cKDTree(np.c_[xy(s.lon, s.lat)])
    m = 0.05
    lineas, info, _ = leer_vias((top.lon.min() - m, top.lat.min() - m, top.lon.max() + m, top.lat.max() + m))
    clave = info["ref"].where(info["ref"].str.len() > 0, info["nombre_via"]).fillna("").values
    arbol = STRtree(lineas)
    filas = []
    for _, l in top.iterrows():
        p = np.array(xy(l.lon, l.lat), dtype=float)
        k = clave[arbol.nearest(Point(p))]
        q = control(p, lineas, clave, k, sin) if k else None
        filas.append(dict(pn=l.pn, tipo="punto negro", lon=l.lon, lat=l.lat, via=k, muertos=l.muertos))
        if q is not None:
            lo, la = lonlat(q)
            filas.append(dict(pn=l.pn, tipo="control", lon=lo, lat=la, via=k, muertos=0))
        else:
            print("sin control:", l.pn, k)
    t = pd.DataFrame(filas)
    t["codigo"] = [f"F{i:02d}" for i in np.random.default_rng(7).permutation(len(t)) + 1]  # a ciegas
    zs = []
    for _, f in t.iterrows():
        img, z = foto(f.lon, f.lat)
        img.save(SAL / f"{f.codigo}.jpg", quality=88); zs.append(z)
    t["zoom"] = zs
    t.to_csv(SAL / "clave.csv", index=False)
    print(len(t), "fotos;", (t.tipo == "control").sum(), "controles")
