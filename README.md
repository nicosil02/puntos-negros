# Puntos negros

**¿Los siniestros fatales en las vías del Perú se repiten en los mismos lugares? ¿Es casualidad, es el tráfico o es el lugar?**

En el Perú hay 286 lugares donde los siniestros fatales se repiten una y otra vez. Ahí se registró 1 de cada 9 fallecidos en siniestros entre 2021 y 2025. No es solo tráfico. Con los mismos siniestros repartidos al azar sobre las mismas vías, habría casi la mitad de lugares así de letales. La mayoría está donde la Panamericana atraviesa la ciudad, y ahí mueren sobre todo peatones.

- Dashboard: https://nicosil02.github.io/puntos-negros/
- Reel: (enlace pendiente)
- Publicación en LinkedIn: (enlace pendiente)

## Hallazgos

1. **1 de cada 9 fallecidos se registra en un punto negro.** Son 286 lugares de 200 metros con 3 o más siniestros fatales entre 2021 y 2025. 146 se repiten en 3 años distintos o más.
2. **El lugar importa, no solo el tráfico.** Hay 55 lugares con 5 o más siniestros fatales. Si los mismos siniestros se repartieran al azar sobre la misma vía y el mismo tramo, habría 31 en promedio y nunca más de 40 en 20 repeticiones.
3. **Son carreteras que cruzan la ciudad.** En los puntos negros, 50% de los siniestros son atropellos (28% en el resto) y 41% ocurre en una vía expresa o carretera dentro de la ciudad (13% en el resto).
4. **Hay un paradero cerca.** 44% de los siniestros en puntos negros ocurrió a menos de 200 metros de un paradero de bus. En otros lugares de la misma vía, 26%. También hay más mercados (18% frente a 12%) y colegios (47% frente a 36%) cerca.
5. **De noche.** 60% de los siniestros en puntos negros ocurre de noche, frente a 51% del resto.
6. **Se podía predecir.** De los 149 puntos negros de 2021-2023, 38% volvió a tener un siniestro fatal a menos de 200 metros en 2024-2025. En un lugar con un solo siniestro en 2021-2023 pasó en 5% de los casos.
7. **Desde el satélite.** En 28 pares de punto negro y un lugar de la misma vía a 1.5 km, revisados a ciegas, el punto negro tenía comercio pegado a la vía en 13 casos y el control en 1. También tenía más paraderos (14 frente a 7) y más puentes peatonales (13 frente a 7). La vía es la misma, cambia lo que hay al costado.

## Datos

| Fuente | Qué se usa | Enlace |
|---|---|---|
| Observatorio Nacional de Seguridad Vial (MTC) | Siniestros de tránsito fatales 2021-2025, con coordenadas | https://www.onsv.gob.pe/datosabiertos |
| OpenStreetMap (Geofabrik) | Vías, cruces, paraderos, mercados y colegios | https://download.geofabrik.de/south-america/peru.html |
| WorldPop | Población 2020 en celdas de 1 km | https://hub.worldpop.org/geodata/summary?id=31824 |
| Esri World Imagery | Fotos satelitales para la auditoría | https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9 |

## Método

1. **Limpieza** (`scripts/limpiar.py`). 9,105 siniestros fatales con ubicación válida, de enero de 2021 a agosto de 2025.
2. **Vía de cada siniestro** (`scripts/vias.py`). Cada siniestro se une con la vía más cercana de OpenStreetMap (la mediana está a 3 metros).
3. **Puntos negros.** Grupos de 3 o más siniestros a menos de 200 metros uno de otro, con DBSCAN.
4. **Prueba del azar.** Cada siniestro se mueve a un lugar al azar de la misma vía, en el mismo tramo (2 km a cada lado) y la misma provincia, de modo que el tráfico sea parecido. Se recalculan los puntos negros. Se repite 20 veces.
5. **Entorno** (`scripts/analizar.py`). Paraderos, mercados y colegios a menos de 200 metros, población de WorldPop, y si era de noche según la salida y la puesta del sol de ese día y lugar. Los puntos negros se comparan con otro lugar al azar de la misma vía.

6. **Predicción.** Puntos negros calculados solo con 2021-2023 y comparados con los siniestros de 2024-2025.
7. **Auditoría satelital** (`scripts/auditoria.py`). Para los 30 puntos negros más letales, un lugar de control en la misma vía a 1-2.5 km sin siniestros fatales en 200 metros (hasta 5 km si no había). Fotos de Esri World Imagery con un código al azar, revisadas sin saber cuál era punto negro, con la lista de `datos/procesados/auditoria_protocolo.txt`. Resultado en `datos/procesados/auditoria.csv`.

## Cómo reproducirlo

```bash
pip install -r requirements.txt
python scripts/obtener.py    # descarga los datos (unos 630 MB)
python scripts/limpiar.py
python scripts/analizar.py   # escribe docs/datos.json
```

El dashboard es `docs/index.html` (D3, MapLibre y deck.gl) y lee `docs/datos.json`.

## Limitaciones

- Solo hay siniestros con muertos. Los que dejan heridos no tienen ubicación pública.
- El registro de 2024 y 2025 es más incompleto, y 2025 llega hasta agosto.
- No hay conteos públicos de autos ni peatones por calle. La prueba del azar sobre la misma vía es la mejor aproximación al tráfico.
- OpenStreetMap no tiene todos los paraderos, sobre todo los informales.
- La auditoría satelital tiene 28 pares y un solo codificador. "Paradero" incluye buses detenidos, que también pueden ser tráfico.
- Muestra asociación, no causalidad.
