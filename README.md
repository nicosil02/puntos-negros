# Puntos negros

**¿Los siniestros fatales en las vías del Perú se repiten en los mismos lugares? ¿Es casualidad, es el tráfico o es el lugar?**

En el Perú hay 286 lugares donde los siniestros fatales se repiten una y otra vez. Ahí se registró 1 de cada 9 fallecidos en siniestros entre 2021 y 2025. No es casualidad. Si los mismos siniestros cayeran al azar sobre las mismas vías, habría bastantes menos lugares así de letales (31 en vez de 55). La mitad de los siniestros en puntos negros son atropellos, y en Lima la mitad de los puntos negros está sobre la Panamericana.

- Dashboard: https://nicosil02.github.io/puntos-negros/
- Reel: [`reel/salidas/reel_remotion.mp4`](reel/salidas/reel_remotion.mp4), también en la publicación de LinkedIn
- Publicación en LinkedIn: (enlace pendiente)

## Hallazgos

1. **1 de cada 9 fallecidos se registra en un punto negro.** Son 286 lugares de 200 metros con 3 o más siniestros fatales entre 2021 y 2025. 146 se repiten en 3 años distintos o más.
2. **No es casualidad, el lugar importa.** Hay 55 lugares con 5 o más siniestros fatales. Si los mismos siniestros se repartieran al azar sobre la misma vía y el mismo tramo, habría 31 en promedio y nunca más de 40 en 20 repeticiones.
3. **Son carreteras que cruzan la ciudad.** En los puntos negros, 50% de los siniestros son atropellos (28% en el resto) y 41% ocurre en una vía expresa o carretera dentro de la ciudad (13% en el resto).
4. **Hay un paradero cerca.** 44% de los siniestros en puntos negros ocurrió a menos de 200 metros de un paradero de bus. En el resto de la misma carretera, 26%. También hay más mercados (18% frente a 12%) y colegios (47% frente a 36%) cerca.
5. **Temprano en la mañana y de noche.** Hay dos picos, a las 5 de la mañana y a las 7 de la noche, cuando la gente va y vuelve del trabajo. En los puntos negros el de la mañana es el más alto (7.4% de los siniestros a las 5 h, frente a 5.5% en el resto). 60% ocurre de noche, frente a 51% del resto.
6. **Se podía predecir.** De los 149 puntos negros de 2021-2023, 38% volvió a tener un siniestro fatal a menos de 200 metros en 2024-2025. En un lugar con un solo siniestro en 2021-2023 pasó en 5% de los casos.
7. **El Estado ya los había identificado.** De los 83 tramos que el ONSV publicó en 2022, 61 volvieron a tener siniestros fatales después, con 203 fallecidos.
8. **Desde el satélite.** En 28 pares de punto negro y un tramo de la misma carretera 1.5 km después, revisados a ciegas, el punto negro tenía comercio pegado a la vía en 13 casos y el control en 1. También tenía más paraderos (14 frente a 7) y más puentes peatonales (13 frente a 7). La vía es la misma, cambia lo que hay al costado.

## Datos

| Fuente | Qué se usa | Enlace |
|---|---|---|
| Observatorio Nacional de Seguridad Vial (MTC) | Siniestros de tránsito fatales 2021-2025, con coordenadas | https://www.onsv.gob.pe/datosabiertos |
| OpenStreetMap (Geofabrik) | Vías, cruces, paraderos, mercados y colegios | https://download.geofabrik.de/south-america/peru.html |
| WorldPop | Población 2020 en celdas de 1 km | https://hub.worldpop.org/geodata/summary?id=31824 |
| Esri World Imagery | Fotos satelitales para la auditoría | https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9 |

## Método

1. **Limpieza** (`scripts/limpiar.py`). 9,105 siniestros fatales con ubicación válida, de enero de 2021 a diciembre de 2025.
2. **Vía de cada siniestro** (`scripts/vias.py`). Cada siniestro se une con la vía más cercana de OpenStreetMap (la mediana está a 3 metros).
3. **Puntos negros.** Grupos de 3 o más siniestros a menos de 200 metros uno de otro, con DBSCAN.
4. **Prueba del azar.** Cada siniestro se mueve a un lugar al azar de la misma vía, en el mismo tramo (2 km a cada lado) y la misma provincia, de modo que el tráfico sea parecido. Se recalculan los puntos negros. Se repite 20 veces.
5. **Entorno** (`scripts/analizar.py`). Paraderos, mercados y colegios a menos de 200 metros, población de WorldPop, y si era de noche según la salida y la puesta del sol de ese día y lugar. Los puntos negros se comparan con un lugar al azar de la misma carretera.
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
`python scripts/panamericana.py` genera `docs/panamericana.geojson`, el trazado que se resalta en el mapa de Lima.

Para verlo en local, `python -m http.server -d docs` y abrir http://localhost:8000.

### Reel

El reel (74 s, 1080×1920) se arma con código. Necesita GPU para la voz.

1. `reel/guion.json` tiene el texto de cada escena.
2. `python reel/voz.py` narra el guion con una voz clonada de una nota de voz mía (Qwen3-TTS 0.6B) y saca el tiempo de cada palabra con Whisper. Usa `reel.py` de la sesión 15 del curso ([d2cml-ai/Data-Science-Python](https://github.com/d2cml-ai/Data-Science-Python), `sessions/15-texto-a-reel`), que debe estar clonado al lado de este repo.
3. `python reel/voz_escenas.py 2 5 7 --tomas 6` vuelve a narrar escenas sueltas y se queda con la toma que Whisper entiende mejor y suena más clara.
4. `python reel/remotion_datos.py` pasa la narración y los subtítulos a Remotion.
5. En `reel/remotion`, `npm install` y `npx remotion render Reel ../salidas/reel_remotion.mp4 --crf=26`.

Los clips del mapa se grabaron del dashboard cuadro por cuadro con Playwright. Música: "Floating Cities", Kevin MacLeod (incompetech.com), licencia CC BY 4.0.

## Trabajos relacionados

- ONSV y MTC, [Documento de trabajo 001. DBSCAN, explorando la densidad espacial de siniestros fatales](https://cdn.www.gob.pe/uploads/document/file/4505475/Documento%20de%20Trabajo%20001%20DBSCAN%20Explorando%20la%20densidad%20espacial%20de%20siniestros%20fatales%20para%20la%20identificaci%C3%B3n%20y%20priorizaci%C3%B3n%20de%20intervenciones%20en%20la%20Red%20Vial%20Nacional.pdf). Usa el mismo método para priorizar intervenciones en la Red Vial Nacional.
- ONSV, informes regionales de víctimas fatales y puntos de alta siniestralidad 2021-2025, por ejemplo [Ayacucho](https://www.onsv.gob.pe/post/informe-de-victimas-fatales-en-siniestros-de-transito-e-identificacion-de-puntos-de-alta-siniestralidad-en-la-region-ayacucho-2021-2025/).
- [carloxmd/siniestralidad_vial](https://github.com/carloxmd/siniestralidad_vial), patrones espaciales en Lima y Callao 2021-2024.

**Comparación con el documento del ONSV** (`scripts/comparar_onsv.py`). Ese estudio usó DBSCAN con 500 metros y 3 siniestros sobre la Red Vial Nacional, de enero de 2021 a junio de 2022, y encontró 83 tramos. Con los mismos parámetros sobre nuestra base salen 70. De sus 83 tramos, 45 coinciden con nuestros puntos negros, y en 61 volvió a haber siniestros fatales después de junio de 2022 (183 siniestros y 203 fallecidos, a menos de 250 metros). Los puntos de sus tramos vienen de su [mapa publicado](https://patriciaig.github.io/SeguridadVialPeru/mapa_tramos_alta_densidad_fatalidades.html) y están en `datos/crudos/onsv_dt001_tramos.csv`.

Este proyecto suma tres cosas a esos trabajos. Cubre todas las vías del país, no solo la red nacional. Compara cada punto negro con otros tramos de la misma vía para descartar que sea solo tráfico. Y revisa con imágenes satelitales qué hay alrededor.

## Limitaciones

- Solo hay siniestros fatales. Los que dejan heridos no tienen ubicación pública.
- La base con ubicación cubre 70% de los fallecidos que reporta el ONSV para 2021-2025 (10,858 de 15,568). La cobertura baja con los años, de 93% en 2021 a 63% en 2024 y 27% en 2025. Los puntos negros recientes están subestimados. Totales oficiales del ONSV citados por PerúCheck (Caretas, 8 de abril de 2026): https://caretas.pe/?p=801787
- No hay conteos públicos de autos ni peatones por calle. La prueba del azar sobre la misma vía es la mejor aproximación al tráfico.
- OpenStreetMap no tiene todos los paraderos, sobre todo los informales.
- La auditoría satelital tiene 28 pares y un solo codificador. "Paradero" incluye buses detenidos, que también pueden ser tráfico.
- Muestra asociación, no causalidad.

## Uso de IA

Usé Claude (Anthropic), a través de Claude Code, como asistente de programación. Me ayudó a escribir y depurar los scripts de limpieza y análisis, el código del dashboard y del reel, y a revisar la redacción. Las preguntas, las decisiones de método y la revisión de las fotos satelitales son mías. Verifiqué las cifras del dashboard y del README contra los datos. La voz del reel es sintética, clonada de mi propia voz con Qwen3-TTS.

