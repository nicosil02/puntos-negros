"""Trazado de la Panamericana (PE-1N y PE-1S) desde OpenStreetMap, simplificado, para resaltarla en el mapa del relato.

Guarda docs/panamericana.geojson.
"""
import json
import shapefile
from shapely import LineString, MultiLineString, line_merge, unary_union
from vias import OSM, RAIZ

if __name__ == "__main__":
    r = shapefile.Reader(str(OSM / "gis_osm_roads_free_1"))
    lineas = [LineString(s.points) for s, rec in zip(r.iterShapes(), r.iterRecords(fields=["ref"]))
              if any(x.strip() in ("PE-1N", "PE-1S") for x in (rec["ref"] or "").split(";"))]
    g = line_merge(unary_union(lineas)).simplify(0.0003)
    partes = list(g.geoms) if isinstance(g, MultiLineString) else [g]
    coords = [[[round(x, 5), round(y, 5)] for x, y in p.coords] for p in partes if p.length > 0.002]
    geo = {"type": "Feature", "properties": {}, "geometry": {"type": "MultiLineString", "coordinates": coords}}
    (RAIZ / "docs" / "panamericana.geojson").write_text(json.dumps(geo, separators=(",", ":")), encoding="utf-8")
    print(len(lineas), "tramos de OSM;", len(coords), "líneas;", sum(len(c) for c in coords), "puntos")
