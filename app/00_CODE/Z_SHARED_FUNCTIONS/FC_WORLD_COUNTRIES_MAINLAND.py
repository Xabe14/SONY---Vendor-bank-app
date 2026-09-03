"""Mainland-only country shapes for the choropleth map.

The public world-atlas topojson (vega-datasets world-110m.json) draws each
country's full sovereign territory. For a country whose overseas department
sits on another continent (e.g. France includes French Guiana, in South
America), that puts a small, disconnected, misleadingly-coloured blob far
from the country a SAP LAND1 code actually means. SAP's LAND1 is just a
country key ('FR' = France as a whole) — it carries no information tying a
vendor to French Guiana specifically, so lighting that blob up is pure noise
from the geometry, not something the underlying data says.

This module fetches that same topojson once, keeps only the single largest
polygon per requested country (its mainland), and returns plain GeoJSON
Polygons keyed by ISO 3166-1 numeric id — so those overseas fragments never
render at all.
"""

import json
import urllib.request

import streamlit as PI_STREAMLIT

ZV_ST_TOPOJSON_URL = 'https://cdn.jsdelivr.net/npm/vega-datasets@2/data/world-110m.json'


def FC_SHOELACE_AREA(ZVFCI_LI_TU_POINTS) -> float:
    ZV_NU_AREA = 0.0
    ZV_NU_N = len(ZVFCI_LI_TU_POINTS)
    for ZV_NU_I in range(ZV_NU_N):
        ZV_NU_X1, ZV_NU_Y1 = ZVFCI_LI_TU_POINTS[ZV_NU_I]
        ZV_NU_X2, ZV_NU_Y2 = ZVFCI_LI_TU_POINTS[(ZV_NU_I + 1) % ZV_NU_N]
        ZV_NU_AREA += ZV_NU_X1 * ZV_NU_Y2 - ZV_NU_X2 * ZV_NU_Y1
    return abs(ZV_NU_AREA) / 2.0


@PI_STREAMLIT.cache_data(show_spinner=False)
def FC_LOAD_MAINLAND_GEOJSON(ZVFCI_TU_NUMERIC_IDS: tuple) -> dict:
    """Return {numeric_id: GeoJSON Polygon}, mainland (largest ring) only."""
    with urllib.request.urlopen(ZV_ST_TOPOJSON_URL, timeout=15) as ZV_OB_RESPONSE:
        ZV_DI_TOPOLOGY = json.loads(ZV_OB_RESPONSE.read())

    ZV_LI_ARCS = ZV_DI_TOPOLOGY['arcs']
    ZV_TU_SCALE = ZV_DI_TOPOLOGY['transform']['scale']
    ZV_TU_TRANSLATE = ZV_DI_TOPOLOGY['transform']['translate']

    def FC_DECODE_ARC(ZVFCI_LI_ARC):
        ZV_NU_X, ZV_NU_Y = 0, 0
        ZV_LI_PTS = []
        for ZV_NU_DX, ZV_NU_DY in ZVFCI_LI_ARC:
            ZV_NU_X += ZV_NU_DX
            ZV_NU_Y += ZV_NU_DY
            ZV_LI_PTS.append([
                ZV_NU_X * ZV_TU_SCALE[0] + ZV_TU_TRANSLATE[0],
                ZV_NU_Y * ZV_TU_SCALE[1] + ZV_TU_TRANSLATE[1],
            ])
        return ZV_LI_PTS

    def FC_RING_COORDS(ZVFCI_LI_ARC_IDX):
        ZV_LI_COORDS = []
        for ZV_NU_IDX in ZVFCI_LI_ARC_IDX:
            ZV_NU_REAL_IDX = ZV_NU_IDX if ZV_NU_IDX >= 0 else ~ZV_NU_IDX
            ZV_LI_PTS = FC_DECODE_ARC(ZV_LI_ARCS[ZV_NU_REAL_IDX])
            if ZV_NU_IDX < 0:
                ZV_LI_PTS = ZV_LI_PTS[::-1]
            if ZV_LI_COORDS and ZV_LI_COORDS[-1] == ZV_LI_PTS[0]:
                ZV_LI_COORDS.extend(ZV_LI_PTS[1:])
            else:
                ZV_LI_COORDS.extend(ZV_LI_PTS)
        return ZV_LI_COORDS

    ZV_DI_OUT = {}
    for ZV_DI_GEOM in ZV_DI_TOPOLOGY['objects']['countries']['geometries']:
        ZV_NU_ID = int(ZV_DI_GEOM['id'])
        if ZV_NU_ID not in ZVFCI_TU_NUMERIC_IDS:
            continue
        if ZV_DI_GEOM['type'] == 'Polygon':
            ZV_LI_POLYGONS = [ZV_DI_GEOM['arcs']]
        elif ZV_DI_GEOM['type'] == 'MultiPolygon':
            ZV_LI_POLYGONS = ZV_DI_GEOM['arcs']
        else:
            continue

        ZV_LI_BEST_RINGS = None
        ZV_NU_BEST_AREA = -1.0
        for ZV_LI_POLY_RINGS in ZV_LI_POLYGONS:
            ZV_LI_RINGS_COORDS = [
                FC_RING_COORDS(ZV_LI_RING) for ZV_LI_RING in ZV_LI_POLY_RINGS
            ]
            ZV_NU_AREA = FC_SHOELACE_AREA(ZV_LI_RINGS_COORDS[0])
            if ZV_NU_AREA > ZV_NU_BEST_AREA:
                ZV_NU_BEST_AREA = ZV_NU_AREA
                ZV_LI_BEST_RINGS = ZV_LI_RINGS_COORDS

        ZV_DI_OUT[ZV_NU_ID] = {'type': 'Polygon', 'coordinates': ZV_LI_BEST_RINGS}
    return ZV_DI_OUT
