"""¿Se podía saber dónde iba a volver a morir gente?

Puntos negros calculados solo con 2021-2023. Para cada lugar: ¿hubo un siniestro fatal a menos de 200 m en 2024-2025?
Se compara con lugares de 2021-2023 que tuvieron 1 o 2 siniestros. Agrega el resultado a docs/datos.json.
"""
import json
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from vias import RAIZ, xy, puntos_negros, EPS

if __name__ == "__main__":
    d = pd.read_csv(RAIZ / "datos" / "procesados" / "siniestros.csv")
    X = np.c_[xy(d.lon, d.lat)]
    antes, despues = (d.anio <= 2023).values, (d.anio >= 2024).values
    A, B = X[antes], X[despues]
    c = puntos_negros(A)
    vuelve = np.array([len(r) > 0 for r in cKDTree(B).query_ball_point(A, EPS)])
    vecinos = np.array([len(r) - 1 for r in cKDTree(A).query_ball_point(A, EPS)])
    pn = pd.Series(vuelve[c >= 0]).groupby(c[c >= 0]).any()
    uno, dos = vuelve[(c < 0) & (vecinos == 0)], vuelve[(c < 0) & (vecinos == 1)]
    cerca = cKDTree(A[c >= 0]).query(B)[0] < EPS
    res = {
        "filas": [
            {"t": "Punto negro (3 o más siniestros)", "n": int(len(pn)), "p": float(pn.mean())},
            {"t": "Lugar con 2 siniestros", "n": int(len(dos)) // 2, "p": float(dos.mean())},  # se mide por siniestro: cada lugar aparece dos veces
            {"t": "Lugar con 1 siniestro", "n": int(len(uno)), "p": float(uno.mean())},
        ],
        "despues": int(despues.sum()), "en_pn": int(cerca.sum()),
    }
    print(json.dumps(res, ensure_ascii=False, indent=1))
    ruta = RAIZ / "docs" / "datos.json"
    D = json.load(open(ruta, encoding="utf-8"))
    D["prediccion"] = res
    json.dump(D, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
