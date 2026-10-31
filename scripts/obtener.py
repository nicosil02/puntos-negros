"""Descarga los datos crudos: siniestros del ONSV, vías y lugares de OpenStreetMap y población de WorldPop."""
from pathlib import Path
import urllib.request, zipfile

CRUDOS = Path(__file__).resolve().parents[1] / "datos" / "crudos"
ONSV = "https://www.onsv.gob.pe/estaticos/excel/BBDD%20ONSV%20-%20SINIESTROS%20FATALES%202021-2025%20(preliminar).xlsx"
OSM = "https://download.geofabrik.de/south-america/peru-latest-free.shp.zip"
WORLDPOP = "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/PER/per_ppp_2020_1km_Aggregated.tif"
CAPAS = ["gis_osm_roads_free_1", "gis_osm_traffic_free_1", "gis_osm_transport_free_1", "gis_osm_pois_free_1", "gis_osm_pois_a_free_1"]


def bajar(url, destino):
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        print("descargando", destino.name)
        urllib.request.urlretrieve(url, destino)
    return destino


if __name__ == "__main__":
    bajar(ONSV, CRUDOS / "onsv_siniestros_fatales_2021_2025.xlsx")
    bajar(WORLDPOP, CRUDOS / "worldpop" / "per_ppp_2020_1km_Aggregated.tif")
    z = bajar(OSM, CRUDOS / "osm" / "peru-latest-free.shp.zip")  # unos 620 MB
    with zipfile.ZipFile(z) as f:
        f.extractall(CRUDOS / "osm", [n for n in f.namelist() if n.split(".")[0] in CAPAS])
