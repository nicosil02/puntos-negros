"""Comparación con el Documento de trabajo 001 del ONSV-MTC (DBSCAN en la Red Vial Nacional, 2021 a junio de 2022).

1. Réplica: el mismo método (500 m, 3 siniestros) sobre nuestra base, solo Red Vial Nacional hasta junio de 2022.
2. Sus 83 tramos (puntos del mapa publicado en patriciaig.github.io/SeguridadVialPeru, en datos/crudos/onsv_dt001_tramos.csv):
   ¿cuántos coinciden con nuestros puntos negros y en cuántos volvió a haber siniestros fatales después de junio de 2022?
Agrega el resultado a docs/datos.json.
"""
import json
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN
from vias import RAIZ, xy

CERCA = 250  # m desde cualquiera de los siniestros que forman el tramo del ONSV

if __name__ == "__main__":
    d = pd.read_csv(RAIZ / "datos" / "procesados" / "siniestros_completo.csv")
    d["f"] = pd.to_datetime(d.fecha)
    r = d[(d.red_vial == "NACIONAL") & (d.f < "2022-07-01")]
    c = DBSCAN(eps=500, min_samples=3).fit_predict(np.c_[xy(r.lon, r.lat)])
    o = pd.read_csv(RAIZ / "datos" / "crudos" / "onsv_dt001_tramos.csv")
    O = np.c_[xy(o.lon, o.lat)]
    pn = d[d.pn >= 0]
    o["coincide"] = cKDTree(np.c_[xy(pn.lon, pn.lat)]).query(O)[0] < CERCA
    despues = d[d.f >= "2022-07-01"].reset_index(drop=True)
    arbol = cKDTree(np.c_[xy(despues.lon, despues.lat)])
    idx = {c_: {i for v in arbol.query_ball_point(O[g.index], CERCA) for i in v} for c_, g in o.groupby("c")}
    todos = set().union(*idx.values())
    via = pn.groupby("pn").agg(rv=("red_vial", lambda s: s.mode().iat[0]), m=("fallecidos", "sum"))
    res = {
        "replica": {"siniestros": int(len(r)), "tramos": int(c.max() + 1), "agrupados": int((c >= 0).sum())},
        "tramos": int(o.c.nunique()),
        "coinciden": int(o.groupby("c").coincide.any().sum()),
        "volvieron": int(sum(1 for v in idx.values() if v)),
        "siniestros_despues": len(todos),
        "fallecidos_despues": int(despues.loc[list(todos), "fallecidos"].sum()),
        "fuera_rvn": int((via.rv != "NACIONAL").sum()),
        "fuera_rvn_fallecidos": int(via[via.rv != "NACIONAL"].m.sum()),
    }
    print(json.dumps(res, indent=1))
    ruta = RAIZ / "docs" / "datos.json"
    D = json.load(open(ruta, encoding="utf-8"))
    D["onsv"] = res
    json.dump(D, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
