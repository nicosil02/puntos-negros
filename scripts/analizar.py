"""Arma los datos del dashboard: siniestros, puntos negros, prueba del azar y entorno de cada lugar."""
from pathlib import Path
import json
import numpy as np, pandas as pd, shapefile, tifffile
from scipy.spatial import cKDTree
import vias as V

RAIZ = Path(__file__).resolve().parents[1]
OSM = RAIZ / "datos" / "crudos" / "osm"
RADIO = 200  # metros alrededor de cada punto para contar lo que hay cerca
LUGARES = {
    "paradero": {"bus_stop", "bus_station"},
    "mercado": {"marketplace", "supermarket", "mall"},
    "colegio": {"school", "kindergarten", "college", "university"},
}


def leer_lugares():
    """Paraderos, mercados y colegios de OSM (puntos y el centro de los polígonos)."""
    pts = {k: [] for k in LUGARES}
    for f in ("gis_osm_pois_free_1", "gis_osm_pois_a_free_1", "gis_osm_transport_free_1"):
        r = shapefile.Reader(str(OSM / f))
        for i, rec in enumerate(r.iterRecords(fields=["fclass"])):
            for k, clases in LUGARES.items():
                if rec["fclass"] in clases:
                    try:
                        s = r.shape(i)
                    except shapefile.ShapefileException:  # polígonos vacíos en el archivo de OSM
                        continue
                    b = s.bbox if s.shapeType != shapefile.POINT else s.points[0] * 2
                    pts[k].append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
    return {k: cKDTree(np.c_[V.xy(*np.array(v).T)]) for k, v in pts.items()}


def poblacion():
    """WorldPop 2020, personas por km² (celdas de 1 km)."""
    p = tifffile.TiffFile(RAIZ / "datos" / "crudos" / "worldpop" / "per_ppp_2020_1km_Aggregated.tif").pages[0]
    a = p.asarray()
    a[a < 0] = 0
    dx, dy = p.tags["ModelPixelScaleTag"].value[:2]
    x0, y0 = p.tags["ModelTiepointTag"].value[3:5]

    def valor(lon, lat):
        i = np.clip(((y0 - np.asarray(lat)) / dy).astype(int), 0, a.shape[0] - 1)
        j = np.clip(((np.asarray(lon) - x0) / dx).astype(int), 0, a.shape[1] - 1)
        return a[i, j]
    return valor


def puesta_de_sol(fecha, lat, lon):
    """Hora local (UTC-5) de la puesta de sol, fórmula simplificada de la NOAA."""
    d = pd.to_datetime(fecha).dt.dayofyear.values
    g = 2 * np.pi / 365 * (d - 1)
    ecu = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    dec = 0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g)
    la = np.radians(lat)
    ha = np.degrees(np.arccos(np.cos(np.radians(90.833)) / (np.cos(la) * np.cos(dec)) - np.tan(la) * np.tan(dec)))
    return (720 - 4 * (lon - ha) - ecu) / 60 - 5, (720 - 4 * (lon + ha) - ecu) / 60 - 5  # puesta, salida


def entorno(lon, lat, arboles, pob):
    X = np.c_[V.xy(lon, lat)]
    out = {k: np.array([len(v) > 0 for v in t.query_ball_point(X, RADIO)]) for k, t in arboles.items()}
    out["poblacion"] = pob(lon, lat)
    return pd.DataFrame(out)


def grupo(c):
    if c.startswith("ATROPELLO"):
        return "Atropello"
    if c.startswith("CHOQUE"):
        return "Choque"
    return {"DESPISTE": "Despiste", "VOLCADURA": "Despiste"}.get(c, "Otro")


def main():
    x = pd.read_csv(RAIZ / "datos" / "procesados" / "siniestros.csv")
    x, lineas, info, X = V.unir(x)
    x["pn"] = V.puntos_negros(X)
    puesta, salida = puesta_de_sol(x.fecha, x.lat.values, x.lon.values)
    h = pd.to_datetime(x.hora.astype(str).str[:5], format="%H:%M", errors="coerce")
    hora = h.dt.hour + h.dt.minute / 60
    x["noche"] = np.where(hora.isna(), np.nan, ((hora > puesta) | (hora < salida)).astype(float))

    arboles, pob = leer_lugares(), poblacion()
    x = pd.concat([x, entorno(x.lon.values, x.lat.values, arboles, pob)], axis=1)

    # Prueba del azar: mismos siniestros, repartidos al azar sobre la misma vía.
    sims, ent_azar = [], []
    for k, (P, orden) in enumerate(V.azar(x, lineas, info)):
        lab = V.puntos_negros(P)
        n = pd.Series(lab[lab >= 0]).value_counts()
        sims.append({"pn": len(n), "pn5": int((n >= 5).sum()), "pn8": int((n >= 8).sum()), "pct": float((lab >= 0).mean())})
        if k < 5:
            lon, lat = P[:, 0] / (111320 * V.COS), P[:, 1] / 110540
            e = entorno(lon, lat, arboles, pob)
            ent_azar.append(e[(x.loc[orden, "pn"] >= 0).values].mean())  # otro lugar del mismo tramo de vía que cada punto negro
    sims = pd.DataFrame(sims)
    ent_azar = pd.concat(ent_azar, axis=1).mean(axis=1)

    pn = x[x.pn >= 0]
    lugares = pn.groupby("pn").agg(
        n=("codigo", "size"), muertos=("fallecidos", "sum"), heridos=("lesionados", "sum"), anios=("anio", "nunique"),
        lat=("lat", "mean"), lon=("lon", "mean"), dep=("departamento", "first"), prov=("provincia", "first"),
        dist=("distrito", "first"), via=("cod_carretera", lambda s: s.mode()[0]), nombre=("nombre_via", lambda s: s.mode()[0] if s.notna().any() else ""),
        atropellos=("clase", lambda s: int(s.str.startswith("ATROPELLO").sum())), desde=("anio", "min"), hasta=("anio", "max"),
    ).reset_index()

    comparar = {}
    for k in ["paradero", "mercado", "colegio"]:
        comparar[k] = {"pn": float(pn[k].mean()), "resto": float(x[x.pn < 0][k].mean()), "azar": float(ent_azar[k])}
    comparar["poblacion"] = {"pn": float(pn.poblacion.mean()), "resto": float(x[x.pn < 0].poblacion.mean()), "azar": float(ent_azar["poblacion"])}

    s = x.assign(g=x.clase.map(grupo))
    datos = {
        "siniestros": [[round(r.lat, 5), round(r.lon, 5), int(r.anio), r.g, int(r.fallecidos or 0), int(r.pn),
                        int(r.hora_n) if pd.notna(r.hora_n) else -1, -1 if pd.isna(r.noche) else int(r.noche), r.departamento,
                        r.zona if isinstance(r.zona, str) else "", r.fclass in ("motorway", "trunk") and r.zona == "URBANA"]
                       for r in s.itertuples()],
        "campos": ["lat", "lon", "anio", "clase", "muertos", "pn", "hora", "noche", "dep", "zona", "expresa_urbana"],
        "lugares": json.loads(lugares.to_json(orient="records")),
        "azar": {"real": {"pn": int(lugares.shape[0]), "pn5": int((lugares.n >= 5).sum()), "pn8": int((lugares.n >= 8).sum()), "pct": float((x.pn >= 0).mean())},
                 "media": sims.mean().round(3).to_dict(), "max": sims.max().to_dict(), "reps": len(sims)},
        "entorno": comparar,
    }
    (RAIZ / "docs").mkdir(exist_ok=True)
    (RAIZ / "docs" / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    x.to_csv(RAIZ / "datos" / "procesados" / "siniestros_completo.csv", index=False)
    return x, datos


if __name__ == "__main__":
    x, d = main()
    print("puntos negros:", d["azar"]["real"], "| azar:", d["azar"]["media"], "máx", d["azar"]["max"])
    print("entorno:", json.dumps(d["entorno"], indent=1))
    print("noche:", x.groupby(x.pn >= 0).noche.mean().round(3).to_dict())
    assert d["azar"]["real"]["pn5"] > d["azar"]["max"]["pn5"]
