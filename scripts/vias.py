"""Une cada siniestro con la vía de OpenStreetMap donde ocurrió y mide qué tan cerca hay un cruce seguro.

También arma la prueba del azar: si los mismos siniestros se repartieran al azar a lo largo de la misma vía
(mismo tráfico, más o menos), ¿se juntarían igual en puntos negros?
"""
from pathlib import Path
import numpy as np, pandas as pd, shapefile
from shapely import STRtree, LineString, Point, line_interpolate_point
from sklearn.cluster import DBSCAN

RAIZ = Path(__file__).resolve().parents[1]
OSM = RAIZ / "datos" / "crudos" / "osm"
COS = np.cos(np.radians(-10))
xy = lambda lon, lat: (np.asarray(lon) * 111320 * COS, np.asarray(lat) * 110540)  # metros, aproximado para Perú
CON_AUTOS = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link",
             "tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service", "track"}
A_PIE = {"footway", "steps", "pedestrian", "path"}
EPS, MIN = 200, 3  # punto negro: 3 o más siniestros fatales a menos de 200 m


def puntos_negros(X):
    return DBSCAN(eps=EPS, min_samples=MIN).fit_predict(X)


def leer_vias(bbox):
    r = shapefile.Reader(str(OSM / "gis_osm_roads_free_1"))
    lineas, info, puentes = [], [], []
    for s, rec in zip(r.iterShapes(), r.iterRecords(fields=["fclass", "name", "ref", "maxspeed", "bridge"])):
        b = s.bbox
        if b[2] < bbox[0] or b[0] > bbox[2] or b[3] < bbox[1] or b[1] > bbox[3]:
            continue
        p = np.array(s.points)
        g = LineString(np.c_[xy(p[:, 0], p[:, 1])])
        if rec["fclass"] in CON_AUTOS or rec["fclass"].startswith("track"):
            lineas.append(g); info.append((rec["fclass"], rec["name"], rec["ref"], rec["maxspeed"]))
        elif rec["fclass"] in A_PIE and rec["bridge"] == "T":
            puentes.append(g)
    return lineas, pd.DataFrame(info, columns=["fclass", "nombre_via", "ref", "maxspeed"]), puentes


def leer_cruces():
    r = shapefile.Reader(str(OSM / "gis_osm_traffic_free_1"))
    out = {"pedestrian_crossing": [], "traffic_signals": []}
    for s, rec in zip(r.iterShapes(), r.iterRecords(fields=["fclass"])):
        if rec["fclass"] in out:
            out[rec["fclass"]].append(s.points[0])
    return {k: np.c_[xy(*np.array(v).T)] for k, v in out.items()}


def distancia(X, P):
    from scipy.spatial import cKDTree
    return cKDTree(P).query(X)[0]


def unir(x):
    X = np.c_[xy(x.lon, x.lat)]
    m = 0.05  # grados de margen
    lineas, info, puentes = leer_vias((x.lon.min() - m, x.lat.min() - m, x.lon.max() + m, x.lat.max() + m))
    arbol = STRtree(lineas)
    pts = [Point(p) for p in X]
    idx = arbol.nearest(pts)
    x = x.copy()
    x[["fclass", "nombre_via", "ref", "maxspeed"]] = info.iloc[idx].values
    x["dist_via"] = [lineas[i].distance(p) for i, p in zip(idx, pts)]
    x["via_id"] = idx
    c = leer_cruces()
    x["dist_cruce"] = distancia(X, c["pedestrian_crossing"])
    x["dist_semaforo"] = distancia(X, c["traffic_signals"])
    x["dist_puente"] = distancia(X, np.vstack([np.array(g.coords) for g in puentes]))  # vértices del puente: basta
    return x, lineas, info, X


def azar(x, lineas, info, reps=20, margen=2000, seed=0):
    """Reparte los siniestros de cada vía al azar sobre esa misma vía, en el mismo tramo (±2 km). Devuelve los puntos y, para cada uno, el siniestro que reubica."""
    rng = np.random.default_rng(seed)
    clave = info["ref"].where(info["ref"].str.len() > 0, info["nombre_via"]).fillna("")
    X = np.c_[xy(x.lon, x.lat)]
    arbol = STRtree(lineas)
    grupos, orden = [], []
    for (k, pv), h in x.assign(clave=clave.iloc[x.via_id].values).groupby(["clave", "provincia"]):
        Xi = X[x.index.get_indexer(h.index)]
        lo, hi = Xi.min(0) - margen, Xi.max(0) + margen
        cand = arbol.query(LineString([lo, hi]).envelope)
        cand = [i for i in cand if (clave.iloc[i] == k if k else i in set(h.via_id))] or list(set(h.via_id))
        largo = np.array([lineas[i].length for i in cand])
        grupos.append((len(h), cand, largo / largo.sum()))
        orden.extend(h.index)
    for _ in range(reps):
        sim = []
        for n, cand, w in grupos:
            for i in rng.choice(cand, size=n, p=w):
                q = line_interpolate_point(lineas[i], rng.random(), normalized=True)
                sim.append((q.x, q.y))
        yield np.array(sim), np.array(orden)


if __name__ == "__main__":
    x = pd.read_csv(RAIZ / "datos" / "procesados" / "siniestros.csv")
    x, lineas, info, X = unir(x)
    x["punto_negro"] = puntos_negros(X)
    real = (x.punto_negro >= 0).mean()
    sim = np.array([(puntos_negros(P) >= 0).mean() for P, _ in azar(x, lineas, info)])
    print(f"en puntos negros: real {100 * real:.1f}% | al azar sobre la misma vía {100 * sim.mean():.1f}% (máx {100 * sim.max():.1f}%)")
    print("distancia a la vía (m), mediana:", round(x.dist_via.median()))
    assert real > sim.max(), "los puntos negros no superan al azar"
