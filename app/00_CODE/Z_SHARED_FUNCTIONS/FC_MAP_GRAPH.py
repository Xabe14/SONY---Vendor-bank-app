"""Streamlit: country bubble map, per the shared-function standard."""

import polars as PI_POLARS
import streamlit as PI_STREAMLIT

from Z_SHARED_FUNCTIONS.FC_COUNTRY_COORDINATES import FC_COUNTRY_COORDINATES
from Z_SHARED_FUNCTIONS.FC_COUNTRY_ISO_NUMERIC import FC_COUNTRY_ISO_NUMERIC
from Z_SHARED_FUNCTIONS.FC_WORLD_COUNTRIES_MAINLAND import (
    FC_LOAD_MAINLAND_GEOJSON,
)
from Z_SHARED_FUNCTIONS.FC_UI_STYLE import (
    ZV_ST_COLOR_PRIMARY,
    ZV_ST_COLOR_SUCCESS,
    ZV_ST_COLOR_DANGER,
)


def FC_MAP_GRAPH(ZVFCI_DF, ZVFCI_ST_CODE_COLUMN: str, ZVFCI_ST_NAME_COLUMN: str,
                 ZVFCI_ST_TITLE: str, ZVFCI_ST_PARAM_NAME: str,
                 ZVFCI_ST_WIDGET_KEY: str = None):
    """Bubble map: one circle per country, sized and coloured by vendor count.

    Uses the Vega-Lite params / select pattern so the chart is clickable, and
    on_select='rerun' so a click re-runs the file and cross-filters everything.

    ZVFCI_ST_WIDGET_KEY lets the caller change the widget key when clearing
    filters: a fresh key forces Streamlit to rebuild the chart component, so
    the browser-side Vega-Lite selection (the highlighted bubble) is cleared
    too — popping session_state alone is not enough.
    """
    if ZVFCI_ST_WIDGET_KEY is None:
        ZVFCI_ST_WIDGET_KEY = f'chart_{ZVFCI_ST_PARAM_NAME}'
    ZV_DF_COUNTS = (
        ZVFCI_DF
        .group_by([ZVFCI_ST_CODE_COLUMN, ZVFCI_ST_NAME_COLUMN])
        .agg(PI_POLARS.col('LIFNR').n_unique().alias('VENDORS'))
    )

    ZV_LI_DI_POINTS = []
    for ZV_DI_ROW in ZV_DF_COUNTS.to_dicts():
        ZV_TU_COORD = FC_COUNTRY_COORDINATES(ZV_DI_ROW[ZVFCI_ST_CODE_COLUMN])
        if ZV_TU_COORD is None:
            continue
        ZV_LI_DI_POINTS.append({
            'code': ZV_DI_ROW[ZVFCI_ST_CODE_COLUMN],
            'country': ZV_DI_ROW[ZVFCI_ST_NAME_COLUMN],
            'vendors': ZV_DI_ROW['VENDORS'],
            'lat': ZV_TU_COORD[0],
            'lon': ZV_TU_COORD[1],
        })

    if not ZV_LI_DI_POINTS:
        PI_STREAMLIT.info(f'{ZVFCI_ST_TITLE}: nothing to plot.')
        return None

    # Single view, no world-outline background layer: the Streamlit version
    # bundled with the stlite build this app targets (needed for a working
    # Polars-in-Pyodide setup on GitHub Pages) raises StreamlitAPIException on
    # any chart selection when the spec has a top-level 'layer' (or hconcat /
    # vconcat / concat) key, i.e. any chart composed of more than one view.
    # A bare, single-mark spec with 'params' at the top level is the only
    # shape that still supports on_select='rerun' there.
    return PI_STREAMLIT.vega_lite_chart(
        {
            'title': ZVFCI_ST_TITLE,
            'height': 230,
            'background': '#F5F6F8',
            'projection': {'type': 'equalEarth'},
            'data': {'values': ZV_LI_DI_POINTS},
            'params': [{
                'name': ZVFCI_ST_PARAM_NAME,
                'select': {'type': 'point', 'fields': ['code']},
            }],
            'mark': {'type': 'circle', 'tooltip': True, 'opacity': 0.82},
            'encoding': {
                'longitude': {'field': 'lon', 'type': 'quantitative'},
                'latitude': {'field': 'lat', 'type': 'quantitative'},
                'size': {'field': 'vendors', 'type': 'quantitative',
                         'scale': {'range': [16, 260]}, 'legend': None},
                'color': {
                    'condition': {
                        'param': ZVFCI_ST_PARAM_NAME,
                        'field': 'vendors', 'type': 'quantitative',
                        'scale': {'scheme': 'blues'},
                        'legend': {'title': 'Vendors'},
                    },
                    'value': '#C8CFDA',
                },
                'tooltip': [
                    {'field': 'country', 'title': 'Country'},
                    {'field': 'code', 'title': 'Key'},
                    {'field': 'vendors', 'title': 'Vendors'},
                ],
            },
        },
        use_container_width=True,
        on_select='rerun',
        key=ZVFCI_ST_WIDGET_KEY,
    )


def FC_ROLE_CATEGORY_CODES(ZVFCI_DF) -> dict:
    """{category: [country codes]} for the role-overlap map — same grouping
    FC_MAP_ROLE_OVERLAP renders (SONY / VENDOR / BANK / OVERLAP_2 /
    OVERLAP_3), factored out so a caller can turn a role-legend click into a
    country filter before the map itself has drawn this run (e.g. to also
    move KPIs, not just the map). Keep this in sync with the grouping logic
    inside FC_MAP_ROLE_OVERLAP if that ever changes."""
    ZV_LI_DF_ROLES = []
    for ZV_ST_CODE_COLUMN, ZV_ST_NAME_COLUMN, ZV_ST_ROLE in (
            ('SONY_LAND1', 'SONY_COUNTRY', 'SONY'),
            ('VENDOR_LAND1', 'VENDOR_COUNTRY', 'VENDOR'),
            ('BANKS', 'BANK_COUNTRY', 'BANK')):
        ZV_LI_DF_ROLES.append(
            ZVFCI_DF
            .select([
                PI_POLARS.col(ZV_ST_CODE_COLUMN).alias('CODE'),
                PI_POLARS.col(ZV_ST_NAME_COLUMN).alias('COUNTRY'),
                PI_POLARS.lit(ZV_ST_ROLE).alias('ROLE'),
            ])
            .unique()
        )
    ZV_DF_ROLES = PI_POLARS.concat(ZV_LI_DF_ROLES).unique()

    ZV_DF_CATEGORY = (
        ZV_DF_ROLES
        .group_by(['CODE', 'COUNTRY'])
        .agg(PI_POLARS.col('ROLE').sort().alias('ROLES'))
        .with_columns(PI_POLARS.col('ROLES').list.len().alias('ROLE_COUNT'))
        .with_columns(
            PI_POLARS.when(PI_POLARS.col('ROLE_COUNT') == 1)
                      .then(PI_POLARS.col('ROLES').list.first())
                      .when(PI_POLARS.col('ROLE_COUNT') == 2)
                      .then(PI_POLARS.lit('OVERLAP_2'))
                      .otherwise(PI_POLARS.lit('OVERLAP_3'))
                      .alias('CATEGORY')
        )
    )

    ZV_DI_CATEGORY_CODES = {}
    for ZV_DI_ROW in ZV_DF_CATEGORY.to_dicts():
        if FC_COUNTRY_ISO_NUMERIC(ZV_DI_ROW['CODE']) is None:
            continue  # not plottable on the map, so never clickable either
        ZV_DI_CATEGORY_CODES.setdefault(ZV_DI_ROW['CATEGORY'], []).append(
            ZV_DI_ROW['CODE']
        )
    return ZV_DI_CATEGORY_CODES


def FC_MAP_ROLE_OVERLAP(ZVFCI_DF, ZVFCI_ST_WIDGET_KEY: str = 'chart_role_overlap'):
    """Choropleth: whole country filled in, one colour per role (Sony /
    vendor / bank country), grey when a country plays more than one role at
    once — lighter for 2 roles, darker for 3. Reacts to clicks on the three
    bubble maps like they cross-filter each other, since the caller passes
    it the same already-filtered data.

    The legend is itself clickable (bind='legend'): click a role to dim every
    other country on this map, and the caller uses the same click to filter
    the tables below to vendors touching a country with that role. Returns
    (chart_data, {category: [country codes]}) — (None, {}) when empty.

    ZVFCI_ST_WIDGET_KEY lets the caller force a fresh component (and a cleared
    browser-side selection) when filters are reset.
    """
    ZV_LI_DF_ROLES = []
    for ZV_ST_CODE_COLUMN, ZV_ST_NAME_COLUMN, ZV_ST_ROLE in (
            ('SONY_LAND1', 'SONY_COUNTRY', 'SONY'),
            ('VENDOR_LAND1', 'VENDOR_COUNTRY', 'VENDOR'),
            ('BANKS', 'BANK_COUNTRY', 'BANK')):
        ZV_LI_DF_ROLES.append(
            ZVFCI_DF
            .select([
                PI_POLARS.col(ZV_ST_CODE_COLUMN).alias('CODE'),
                PI_POLARS.col(ZV_ST_NAME_COLUMN).alias('COUNTRY'),
                PI_POLARS.lit(ZV_ST_ROLE).alias('ROLE'),
            ])
            .unique()
        )
    ZV_DF_ROLES = PI_POLARS.concat(ZV_LI_DF_ROLES).unique()

    ZV_DF_CATEGORY = (
        ZV_DF_ROLES
        .group_by(['CODE', 'COUNTRY'])
        .agg(PI_POLARS.col('ROLE').sort().alias('ROLES'))
        .with_columns(PI_POLARS.col('ROLES').list.len().alias('ROLE_COUNT'))
        .with_columns(
            PI_POLARS.when(PI_POLARS.col('ROLE_COUNT') == 1)
                      .then(PI_POLARS.col('ROLES').list.first())
                      .when(PI_POLARS.col('ROLE_COUNT') == 2)
                      .then(PI_POLARS.lit('OVERLAP_2'))
                      .otherwise(PI_POLARS.lit('OVERLAP_3'))
                      .alias('CATEGORY')
        )
        .with_columns(PI_POLARS.col('ROLES').list.join(' + ').alias('ROLES_TEXT'))
        .sort('CODE')
    )

    ZV_LI_DI_POINTS = []
    for ZV_DI_ROW in ZV_DF_CATEGORY.to_dicts():
        ZV_NU_ID = FC_COUNTRY_ISO_NUMERIC(ZV_DI_ROW['CODE'])
        if ZV_NU_ID is None:
            continue
        ZV_LI_DI_POINTS.append({
            'id': ZV_NU_ID,
            'code': ZV_DI_ROW['CODE'],
            'country': ZV_DI_ROW['COUNTRY'],
            'roles': ZV_DI_ROW['ROLES_TEXT'],
            'category': ZV_DI_ROW['CATEGORY'],
        })

    if not ZV_LI_DI_POINTS:
        PI_STREAMLIT.info('Country role overlap: nothing to plot.')
        return None, {}

    ZV_DI_CATEGORY_CODES = {}
    for ZV_DI_POINT in ZV_LI_DI_POINTS:
        ZV_DI_CATEGORY_CODES.setdefault(ZV_DI_POINT['category'], []).append(
            ZV_DI_POINT['code']
        )

    ZV_DI_TOPOJSON = {
        'url': 'https://cdn.jsdelivr.net/npm/vega-datasets@2/'
               'data/world-110m.json',
        'format': {'type': 'topojson', 'feature': 'countries'},
    }

    # Mainland-only shapes for the coloured layer: a SAP LAND1 code like 'FR'
    # just means the country as a whole, with no location detail — filling in
    # the full sovereign territory would also light up disconnected overseas
    # pieces (e.g. France's shape reaches into French Guiana), which looks
    # like data that isn't there. Falls back to the full-territory lookup (old
    # behaviour) if the topojson can't be fetched/parsed for some reason.
    try:
        ZV_DI_MAINLAND = FC_LOAD_MAINLAND_GEOJSON(
            tuple(sorted(ZV_DI_POINT['id'] for ZV_DI_POINT in ZV_LI_DI_POINTS))
        )
        ZV_LI_DI_FEATURES = []
        for ZV_DI_POINT in ZV_LI_DI_POINTS:
            ZV_DI_GEOM = ZV_DI_MAINLAND.get(ZV_DI_POINT['id'])
            if ZV_DI_GEOM is None:
                continue
            ZV_LI_DI_FEATURES.append({
                'type': 'Feature',
                'geometry': ZV_DI_GEOM,
                'properties': {
                    'code': ZV_DI_POINT['code'],
                    'country': ZV_DI_POINT['country'],
                    'roles': ZV_DI_POINT['roles'],
                    'category': ZV_DI_POINT['category'],
                },
            })
        ZV_DI_COLOR_LAYER = {
            'data': {'values': ZV_LI_DI_FEATURES},
            'params': [{
                'name': 'ZV_ROLE_SELECTION',
                'select': {'type': 'point', 'fields': ['properties.code']},
            }],
            'mark': {'type': 'geoshape', 'stroke': '#FFFFFF',
                     'strokeWidth': 0.5, 'tooltip': True},
            'encoding': {
                'color': {
                    'field': 'properties.category', 'type': 'nominal',
                    'scale': {
                        'domain': ['SONY', 'VENDOR', 'BANK',
                                   'OVERLAP_2', 'OVERLAP_3'],
                        'range': [ZV_ST_COLOR_PRIMARY, ZV_ST_COLOR_SUCCESS,
                                  ZV_ST_COLOR_DANGER, '#9CA3AF', '#4B5563'],
                    },
                    'legend': {
                        'title': 'Role — click a country to filter by it',
                        'labelExpr': (
                            "datum.label == 'SONY' ? 'Sony country' : "
                            "datum.label == 'VENDOR' ? 'Vendor country' : "
                            "datum.label == 'BANK' ? 'Bank country' : "
                            "datum.label == 'OVERLAP_2' ? '2 roles overlap' : "
                            "'3 roles overlap'"
                        ),
                    },
                },
                'tooltip': [
                    {'field': 'properties.country', 'title': 'Country'},
                    {'field': 'properties.code', 'title': 'Key'},
                    {'field': 'properties.roles', 'title': 'Roles'},
                ],
            },
        }
    except Exception:
        ZV_DI_COLOR_LAYER = {
            'data': ZV_DI_TOPOJSON,
            'transform': [
                {
                    'lookup': 'id',
                    'from': {
                        'data': {'values': ZV_LI_DI_POINTS},
                        'key': 'id',
                        'fields': ['code', 'country', 'roles', 'category'],
                    },
                },
                {'filter': 'datum.category != null'},
            ],
            'params': [{
                'name': 'ZV_ROLE_SELECTION',
                'select': {'type': 'point', 'fields': ['code']},
            }],
            'mark': {'type': 'geoshape', 'stroke': '#FFFFFF',
                     'strokeWidth': 0.5, 'tooltip': True},
            'encoding': {
                'color': {
                    'field': 'category', 'type': 'nominal',
                    'scale': {
                        'domain': ['SONY', 'VENDOR', 'BANK',
                                   'OVERLAP_2', 'OVERLAP_3'],
                        'range': [ZV_ST_COLOR_PRIMARY, ZV_ST_COLOR_SUCCESS,
                                  ZV_ST_COLOR_DANGER, '#9CA3AF', '#4B5563'],
                    },
                    'legend': {
                        'title': 'Role — click a country to filter by it',
                        'labelExpr': (
                            "datum.label == 'SONY' ? 'Sony country' : "
                            "datum.label == 'VENDOR' ? 'Vendor country' : "
                            "datum.label == 'BANK' ? 'Bank country' : "
                            "datum.label == 'OVERLAP_2' ? '2 roles overlap' : "
                            "'3 roles overlap'"
                        ),
                    },
                },
                'tooltip': [
                    {'field': 'country', 'title': 'Country'},
                    {'field': 'code', 'title': 'Key'},
                    {'field': 'roles', 'title': 'Roles'},
                ],
            },
        }

    ZV_DI_COLOR_LAYER['encoding']['opacity'] = {
        'condition': {'param': 'ZV_ROLE_SELECTION', 'value': 1},
        'value': 0.25,
    }

    # Single view, no separate background/click-target layers: the Streamlit
    # version bundled with the stlite build this app targets (needed for a
    # working Polars-in-Pyodide setup on GitHub Pages) raises
    # StreamlitAPIException on any chart selection when the spec has a
    # top-level 'layer' key, i.e. any chart composed of more than one view.
    # The selection now lives directly
    # on the coloured country shape, so clicking a jagged/small coastline is
    # less forgiving than the old dedicated click-target circle was — the
    # legend and tooltip still make it clear which country is which.
    ZV_DI_COLOR_LAYER['title'] = 'Country role overlap (Sony / vendor / bank)'
    ZV_DI_COLOR_LAYER['height'] = 230
    ZV_DI_COLOR_LAYER['background'] = '#F5F6F8'
    ZV_DI_COLOR_LAYER['projection'] = {'type': 'equalEarth'}

    ZV_OB_CHART = PI_STREAMLIT.vega_lite_chart(
        ZV_DI_COLOR_LAYER,
        use_container_width=True,
        on_select='rerun',
        key=ZVFCI_ST_WIDGET_KEY,
    )
    return ZV_OB_CHART, ZV_DI_CATEGORY_CODES
