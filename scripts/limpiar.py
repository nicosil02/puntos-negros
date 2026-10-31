"""Limpia la base de siniestros fatales del ONSV (2021-2025) y la guarda como CSV."""
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "datos" / "crudos" / "onsv_siniestros_fatales_2021_2025.xlsx"
SALIDA = RAIZ / "datos" / "procesados" / "siniestros.csv"

NOMBRES = ["codigo", "fecha", "hora", "clase", "fallecidos", "lesionados", "vehiculos", "departamento", "provincia",
           "distrito", "zona", "tipo_via", "red_vial", "cod_carretera", "lat", "lon", "clima", "zonificacion",
           "caracteristica_via", "perfil_via", "superficie", "senal_vertical", "senal_vertical_1", "senal_vertical_2",
           "senal_horizontal", "causa", "causa_especifica"]


def limpiar():
    x = pd.read_excel(CRUDO, header=None)
    fila = x.index[x.notna().sum(axis=1) > 15][0]  # la cabecera viene después de unas notas
    x = x.iloc[fila + 1:].copy()
    x.columns = NOMBRES
    x = x.dropna(subset=["codigo"])
    x["fecha"] = pd.to_datetime(x["fecha"].astype(str).str[:10], format="mixed", dayfirst=True, errors="coerce")
    for c in ("lat", "lon", "fallecidos", "lesionados", "vehiculos"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x[x.lat.between(-18.5, 0) & x.lon.between(-81.5, -68.5) & x.fecha.notna()]
    texto = x.select_dtypes(include=["object", "str"]).columns
    x[texto] = x[texto].apply(lambda s: s.str.strip().str.upper())
    x["anio"] = x.fecha.dt.year
    x["hora_n"] = pd.to_numeric(x.hora.astype(str).str[:2], errors="coerce")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    x.to_csv(SALIDA, index=False)
    return x


if __name__ == "__main__":
    d = limpiar()
    print(len(d), "siniestros;", d.anio.value_counts().sort_index().to_dict())
    assert len(d) > 9000 and d.lat.notna().all()
