"""Vendor bank app.

Audit question: does Sony have vendors where the Sony company country, the vendor
country and the bank country are all three different?

Layout follows page 4 of the vendor bank app definition; tables, fields and join
path follow page 5. Streamlit patterns follow the 300Framework Streamlit chapter:
shared functions for every reusable object, sidebar layout as in the current apps,
Vega-Lite params for cross-filtering, session_state to survive a rerun.
"""

import io as PI_IO

import polars as PI_POLARS
import streamlit as PI_STREAMLIT

from FC_APP_CONFIG import ZV_BO_USE_WIDTH
from Z_SHARED_FUNCTIONS.FC_IMPORT_TEXT import FC_IMPORT_TEXT
from Z_SHARED_FUNCTIONS.FC_FILE_UPLOADER import FC_FILE_UPLOADER
from Z_SHARED_FUNCTIONS.FC_GET_SELECTION_VALUE import FC_GET_SELECTION_VALUE
from Z_SHARED_FUNCTIONS.FC_FILTER_BY_CATEGORY_SELECTION import (
    FC_FILTER_BY_CATEGORY_SELECTION,
)
from Z_SHARED_FUNCTIONS.FC_GET_EXCEL_BYTES import FC_GET_EXCEL_BYTES
from Z_SHARED_FUNCTIONS.FC_DOWNLOAD_BUTTON import FC_DOWNLOAD_BUTTON
from Z_SHARED_FUNCTIONS.FC_COUNTRY_COORDINATES import FC_COUNTRY_COORDINATES
from Z_SHARED_FUNCTIONS.FC_UI_STYLE import (
    FC_INJECT_CSS,
    FC_SECTION_HEADER,
    FC_STATUS_PILL,
)
from Z_SHARED_FUNCTIONS.FC_STORAGE import (
    FC_SNAPSHOT_CLEAR,
    FC_SNAPSHOT_EXISTS,
    FC_SNAPSHOT_LOAD,
    FC_SNAPSHOT_SAVE,
    FC_STORAGE_BACKEND_LABEL,
)

PI_STREAMLIT.set_page_config(page_title='Vendor bank app', layout='wide')

FC_INJECT_CSS()

ZV_DI_WIDTH = {'width': 'stretch'} if ZV_BO_USE_WIDTH else {}

# ------------------------------------------------------- required tables/fields
ZV_DI_REQUIRED_TABLES = {
    'LFA1':  ['LIFNR', 'NAME1', 'LAND1', 'ORT01', 'STRAS', 'LOEVM', 'SPERR'],
    'LFB1':  ['LIFNR', 'BUKRS', 'AKONT'],
    'T001':  ['BUKRS', 'BUTXT', 'LAND1'],
    'LFBK':  ['LIFNR', 'BANKS', 'BANKL', 'BANKN', 'KOINH', 'BVTYP'],
    'BSIK':  ['BUKRS', 'LIFNR', 'BELNR', 'GJAHR', 'BUDAT', 'WRBTR', 'WAERS',
              'SHKZG', 'BLART', 'BVTYP'],
    'BSAK':  ['BUKRS', 'LIFNR', 'BELNR', 'GJAHR', 'BUDAT', 'WRBTR', 'WAERS',
              'SHKZG', 'BLART', 'BVTYP', 'AUGDT', 'AUGBL'],
    'REGUH': ['ZBUKR', 'LIFNR', 'VBLNR', 'VALUT', 'ZBNKS', 'ZBNKL', 'ZBNKN',
              'RZAWE'],
    'T005T': ['LAND1', 'LANDX'],
    'T003T': ['BLART', 'LTEXT'],
}

ZV_ST_KEY_TABLES = 'ZV_VB_TABLES'
ZV_ST_KEY_RESULTS = 'ZV_VB_RESULTS'
ZV_ST_KEY_STATUS = 'ZV_VB_STATUS'
ZV_ST_KEY_RESTORE = 'ZV_VB_RESTORE_PENDING'

for ZV_ST_KEY, ZV_OB_DEFAULT in ((ZV_ST_KEY_TABLES, None),
                                 (ZV_ST_KEY_RESULTS, None),
                                 (ZV_ST_KEY_STATUS, 'not_started'),
                                 (ZV_ST_KEY_RESTORE, False)):
    if ZV_ST_KEY not in PI_STREAMLIT.session_state:
        PI_STREAMLIT.session_state[ZV_ST_KEY] = ZV_OB_DEFAULT


# ------------------------------------------------------- app-specific functions
def FC_BUILD_TEMPLATE_BYTES() -> bytes:
    """Headings only, tab-delimited, one block per table (definition p.4)."""
    ZV_OB_BUFFER = PI_IO.StringIO()
    for ZV_ST_TABLE, ZV_LI_FIELDS in ZV_DI_REQUIRED_TABLES.items():
        ZV_OB_BUFFER.write(f'# {ZV_ST_TABLE}\n')
        ZV_OB_BUFFER.write('\t'.join(ZV_LI_FIELDS) + '\n\n')
    return ZV_OB_BUFFER.getvalue().encode('utf-8')


def FC_READ_UPLOADS(ZVFCI_LI_OB_FILES) -> dict:
    """Match each uploaded file to a table by its file stem: LFA1.txt -> LFA1."""
    ZV_DI_TABLES = {}
    ZV_LI_OB_FILES = list(ZVFCI_LI_OB_FILES or [])
    ZV_OB_BAR = PI_STREAMLIT.progress(0)
    for ZV_NU_INDEX, ZV_OB_FILE in enumerate(ZV_LI_OB_FILES):
        ZV_ST_STEM = ZV_OB_FILE.name.rsplit('.', 1)[0].strip().upper()
        if ZV_ST_STEM in ZV_DI_REQUIRED_TABLES:
            try:
                ZV_DI_TABLES[ZV_ST_STEM] = FC_IMPORT_TEXT(ZV_OB_FILE)
            except Exception:
                ZV_DI_TABLES[ZV_ST_STEM] = None
        ZV_OB_BAR.progress((ZV_NU_INDEX + 1) / max(len(ZV_LI_OB_FILES), 1))
    ZV_OB_BAR.empty()
    return ZV_DI_TABLES


def FC_CHECK_TABLES_AND_FIELDS(ZVFCI_DI_TABLES: dict) -> list:
    """Empty list means every required table and field is present."""
    ZV_LI_PROBLEMS = []
    for ZV_ST_TABLE, ZV_LI_FIELDS in ZV_DI_REQUIRED_TABLES.items():
        ZV_DF = ZVFCI_DI_TABLES.get(ZV_ST_TABLE)
        if ZV_DF is None:
            ZV_LI_PROBLEMS.append(f'Table {ZV_ST_TABLE} is missing.')
            continue
        ZV_LI_MISSING = [
            ZV_ST_FIELD for ZV_ST_FIELD in ZV_LI_FIELDS
            if ZV_ST_FIELD not in ZV_DF.columns
        ]
        if ZV_LI_MISSING:
            ZV_LI_PROBLEMS.append(
                f'Table {ZV_ST_TABLE} is missing field(s): '
                + ', '.join(ZV_LI_MISSING)
            )
    return ZV_LI_PROBLEMS


def FC_ADD_DESCRIPTION(ZVFCI_DF, ZVFCI_ST_CODE_COLUMN: str, ZVFCI_DF_TEXT,
                       ZVFCI_ST_TEXT_KEY: str, ZVFCI_ST_TEXT_COLUMN: str,
                       ZVFCI_ST_TARGET: str):
    """Code-description rule: every code is shown next to its description."""
    ZV_DF_LOOKUP = (
        ZVFCI_DF_TEXT
        .select([ZVFCI_ST_TEXT_KEY, ZVFCI_ST_TEXT_COLUMN])
        .unique(subset=[ZVFCI_ST_TEXT_KEY])
        .rename({ZVFCI_ST_TEXT_KEY: ZVFCI_ST_CODE_COLUMN,
                 ZVFCI_ST_TEXT_COLUMN: ZVFCI_ST_TARGET})
    )
    return ZVFCI_DF.join(ZV_DF_LOOKUP, on=ZVFCI_ST_CODE_COLUMN, how='left')


def FC_RUN_ANALYSIS(ZVFCI_DI_TABLES: dict) -> dict:
    """Join path and test rule exactly as defined on pages 3 and 5."""
    ZV_DF_LFA1 = ZVFCI_DI_TABLES['LFA1']
    ZV_DF_LFB1 = ZVFCI_DI_TABLES['LFB1']
    ZV_DF_T001 = ZVFCI_DI_TABLES['T001']
    ZV_DF_LFBK = ZVFCI_DI_TABLES['LFBK']
    ZV_DF_BSIK = ZVFCI_DI_TABLES['BSIK']
    ZV_DF_BSAK = ZVFCI_DI_TABLES['BSAK']
    ZV_DF_REGUH = ZVFCI_DI_TABLES['REGUH']
    ZV_DF_T005T = ZVFCI_DI_TABLES['T005T']
    ZV_DF_T003T = ZVFCI_DI_TABLES['T003T']

    # LFA1.LIFNR = LFB1.LIFNR    and    LFB1.BUKRS = T001.BUKRS
    ZV_DF_BASE = (
        ZV_DF_LFA1
        .rename({'LAND1': 'VENDOR_LAND1'})
        .join(ZV_DF_LFB1.select(['LIFNR', 'BUKRS']), on='LIFNR', how='inner')
        .join(
            ZV_DF_T001.select(['BUKRS', 'BUTXT', 'LAND1'])
                      .rename({'LAND1': 'SONY_LAND1'}),
            on='BUKRS', how='inner'
        )
    )

    # LFA1.LIFNR = LFBK.LIFNR   (LFBK is client level and holds no BUKRS)
    ZV_DF_VENDOR_BANK = ZV_DF_BASE.join(
        ZV_DF_LFBK.select(['LIFNR', 'BANKS', 'BANKL', 'BANKN', 'KOINH', 'BVTYP']),
        on='LIFNR', how='inner'
    )

    # test rule: all three countries different from one another
    ZV_DF_VENDOR_BANK = ZV_DF_VENDOR_BANK.with_columns(
        (
            (PI_POLARS.col('SONY_LAND1') != PI_POLARS.col('VENDOR_LAND1'))
            & (PI_POLARS.col('SONY_LAND1') != PI_POLARS.col('BANKS'))
            & (PI_POLARS.col('VENDOR_LAND1') != PI_POLARS.col('BANKS'))
        ).alias('IS_EXCEPTION')
    )

    ZV_NU_KPI1 = ZV_DF_VENDOR_BANK.select('LIFNR').n_unique()
    ZV_DF_EXCEPTIONS = ZV_DF_VENDOR_BANK.filter(PI_POLARS.col('IS_EXCEPTION'))
    ZV_NU_KPI2 = ZV_DF_EXCEPTIONS.select('LIFNR').n_unique()
    ZV_NU_KPI3 = (ZV_NU_KPI2 / ZV_NU_KPI1 * 100) if ZV_NU_KPI1 else 0.0

    for ZV_ST_CODE, ZV_ST_TARGET in (('SONY_LAND1', 'SONY_COUNTRY'),
                                     ('VENDOR_LAND1', 'VENDOR_COUNTRY'),
                                     ('BANKS', 'BANK_COUNTRY')):
        ZV_DF_EXCEPTIONS = FC_ADD_DESCRIPTION(
            ZV_DF_EXCEPTIONS, ZV_ST_CODE, ZV_DF_T005T, 'LAND1', 'LANDX',
            ZV_ST_TARGET
        )

    ZV_DF_EXCEPTION_KEYS = ZV_DF_EXCEPTIONS.select(['LIFNR', 'BUKRS']).unique()

    # BSIK / BSAK .LIFNR + .BUKRS = LFB1 .LIFNR + .BUKRS
    ZV_LI_DOC_COLUMNS = ['BUKRS', 'LIFNR', 'BELNR', 'GJAHR', 'BUDAT', 'WRBTR',
                         'WAERS', 'SHKZG', 'BLART', 'BVTYP']
    ZV_DF_DOCS = PI_POLARS.concat([
        ZV_DF_BSIK.select(ZV_LI_DOC_COLUMNS)
                  .with_columns(PI_POLARS.lit('BSIK').alias('SOURCE'),
                                PI_POLARS.lit('').alias('AUGBL')),
        ZV_DF_BSAK.select(ZV_LI_DOC_COLUMNS + ['AUGBL'])
                  .with_columns(PI_POLARS.lit('BSAK').alias('SOURCE')),
    ], how='diagonal')

    ZV_DF_TRANSACTIONS = (
        ZV_DF_DOCS
        .join(ZV_DF_EXCEPTION_KEYS, on=['LIFNR', 'BUKRS'], how='inner')
        .join(ZV_DF_LFA1.select(['LIFNR', 'NAME1']), on='LIFNR', how='left')
    )
    ZV_DF_TRANSACTIONS = FC_ADD_DESCRIPTION(
        ZV_DF_TRANSACTIONS, 'BLART', ZV_DF_T003T, 'BLART', 'LTEXT',
        'DOCUMENT_TYPE'
    )

    # REGUH .LIFNR + .ZBUKR = LFB1 .LIFNR + .BUKRS
    ZV_DF_SETTLEMENTS = (
        ZV_DF_REGUH
        .rename({'ZBUKR': 'BUKRS'})
        .join(ZV_DF_EXCEPTION_KEYS, on=['LIFNR', 'BUKRS'], how='inner')
        .join(ZV_DF_LFA1.select(['LIFNR', 'NAME1']), on='LIFNR', how='left')
        .with_columns(PI_POLARS.col('VALUT').str.slice(0, 4).alias('VALUT_YEAR'))
    )
    ZV_DF_SETTLEMENTS = FC_ADD_DESCRIPTION(
        ZV_DF_SETTLEMENTS, 'ZBNKS', ZV_DF_T005T, 'LAND1', 'LANDX',
        'PAID_BANK_COUNTRY'
    )

    # REGUH .LIFNR + .ZBNKN = LFBK .LIFNR + .BANKN
    # Left join on purpose: payments to an account that is not on the vendor
    # master are the exceptions, so they must be kept, not dropped.
    ZV_DF_MASTER_ACCOUNTS = (
        ZV_DF_LFBK.select(['LIFNR', 'BANKN'])
                  .unique()
                  .rename({'BANKN': 'ZBNKN'})
                  .with_columns(PI_POLARS.lit('Y').alias('PAYEE_ON_MASTER'))
    )
    ZV_DF_SETTLEMENTS = (
        ZV_DF_SETTLEMENTS
        .join(ZV_DF_MASTER_ACCOUNTS, on=['LIFNR', 'ZBNKN'], how='left')
        .with_columns(PI_POLARS.col('PAYEE_ON_MASTER').fill_null('N'))
    )

    return {
        'KPI1': ZV_NU_KPI1,
        'KPI2': ZV_NU_KPI2,
        'KPI3': ZV_NU_KPI3,
        'EXCEPTIONS': ZV_DF_EXCEPTIONS,
        'TRANSACTIONS': ZV_DF_TRANSACTIONS,
        'SETTLEMENTS': ZV_DF_SETTLEMENTS,
    }


def FC_MAP_GRAPH(ZVFCI_DF, ZVFCI_ST_CODE_COLUMN: str, ZVFCI_ST_NAME_COLUMN: str,
                 ZVFCI_ST_TITLE: str, ZVFCI_ST_PARAM_NAME: str):
    """Bubble map: one circle per country, sized and coloured by vendor count.

    Uses the Vega-Lite params / select pattern so the chart is clickable, and
    on_select='rerun' so a click re-runs the file and cross-filters everything.
    """
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

    return PI_STREAMLIT.vega_lite_chart(
        {
            'title': ZVFCI_ST_TITLE,
            'height': 230,
            'projection': {'type': 'equalEarth'},
            'layer': [
                {
                    'data': {
                        'url': 'https://cdn.jsdelivr.net/npm/vega-datasets@2/'
                               'data/world-110m.json',
                        'format': {'type': 'topojson', 'feature': 'countries'},
                    },
                    'mark': {'type': 'geoshape', 'fill': '#E6E8EC',
                             'stroke': '#FFFFFF', 'strokeWidth': 0.5},
                },
                {
                    'data': {'values': ZV_LI_DI_POINTS},
                    'params': [{
                        'name': ZVFCI_ST_PARAM_NAME,
                        'select': {'type': 'point', 'fields': ['code']},
                    }],
                    'mark': {'type': 'circle', 'tooltip': True,
                             'opacity': 0.82},
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
            ],
        },
        use_container_width=True,
        on_select='rerun',
        key=f'chart_{ZVFCI_ST_PARAM_NAME}',
    )


def FC_SHOW_TABLE(ZVFCI_ST_TITLE: str, ZVFCI_DF, ZVFCI_ST_FILENAME: str,
                  ZVFCI_ST_KEY: str) -> None:
    """Table with a Download Excel button, per the shared-function standard."""
    with PI_STREAMLIT.container(border=True):
        PI_STREAMLIT.markdown(
            f'**{ZVFCI_ST_TITLE}**   *:grey[{ZVFCI_DF.height:,} rows]*'
        )
        FC_DOWNLOAD_BUTTON(
            ZVFCI_BY_DATA=FC_GET_EXCEL_BYTES(ZVFCI_DF=ZVFCI_DF),
            ZVFCI_ST_FILENAME=ZVFCI_ST_FILENAME,
            ZVFCI_ST_LABEL='Download Excel',
            ZVFCI_ST_KEY=ZVFCI_ST_KEY,
        )
        PI_STREAMLIT.dataframe(ZVFCI_DF, hide_index=True, **ZV_DI_WIDTH)


# ------------------------------------------------------------------- sidebar
with PI_STREAMLIT.sidebar:
    PI_STREAMLIT.markdown(
        '<div class="zv-sidebar-brand"><h3>Vendor bank app</h3>'
        '<p>Risk &amp; Control Department</p></div>',
        unsafe_allow_html=True,
    )
    PI_STREAMLIT.markdown('---')

    ZV_LI_ST_COMPANY_FILTER = []
    ZV_DI_TABLES_STATE = PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES] or {}
    if ZV_DI_TABLES_STATE.get('T001') is not None:
        ZV_LI_DI_COMPANIES = (
            ZV_DI_TABLES_STATE['T001'].select(['BUKRS', 'BUTXT'])
                                      .unique().sort('BUKRS').to_dicts()
        )
        ZV_LI_ST_ALL = [ZV_DI['BUKRS'] for ZV_DI in ZV_LI_DI_COMPANIES]
        ZV_LI_ST_COMPANY_FILTER = PI_STREAMLIT.multiselect(
            'Company code (BUKRS)',
            ZV_LI_ST_ALL,
            default=ZV_LI_ST_ALL,
            format_func=lambda ZV_ST_CODE: next(
                (f"{ZV_DI['BUKRS']} - {ZV_DI['BUTXT']}"
                 for ZV_DI in ZV_LI_DI_COMPANIES
                 if ZV_DI['BUKRS'] == ZV_ST_CODE), ZV_ST_CODE
            ),
        )
    else:
        PI_STREAMLIT.markdown(
            '*:grey[The company code filter appears once T001 is uploaded.]*'
        )

    PI_STREAMLIT.markdown('---')
    PI_STREAMLIT.markdown('*:grey[Status]*')
    ZV_ST_STATUS_RAW = PI_STREAMLIT.session_state[ZV_ST_KEY_STATUS]
    if ZV_ST_STATUS_RAW == 'analysis_run':
        FC_STATUS_PILL('Analysis complete', 'ok')
    elif ZV_DI_TABLES_STATE:
        FC_STATUS_PILL('Data uploaded', 'warn')
    else:
        FC_STATUS_PILL('Waiting for data', 'neutral')
    PI_STREAMLIT.markdown(
        '<div class="zv-sidebar-footer">SAP extracts &middot; '
        'three-country vendor audit</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------- 1. input & configuration
PI_STREAMLIT.title('Vendor bank app')
PI_STREAMLIT.caption(
    'Audit question: does Sony have vendors where the Sony company country, '
    'the vendor country and the bank country are all three different?'
)

FC_SECTION_HEADER(
    '1',
    'Input & Configuration',
    'Upload the SAP extracts, check the required tables and grab the templates.',
)

ZV_OB_COL_UPLOAD, ZV_OB_COL_INFO, ZV_OB_COL_TEMPLATE = PI_STREAMLIT.columns(
    [2, 1, 1]
)

with ZV_OB_COL_UPLOAD:
    with PI_STREAMLIT.container(border=True):
        PI_STREAMLIT.markdown('**1.1 Upload the SAP extracts.**')
        ZV_LI_OB_UPLOADS = FC_FILE_UPLOADER(
            ZVFCI_LI_ALLOWED_TYPES=['txt', 'csv', 'tsv'],
            ZVFCI_BO_ACCEPT_MUL_FILES=True,
            ZVFCI_ST_LABEL='Drag and drop the files',
            ZVFCI_ST_KEY='vb_uploads',
        )

with ZV_OB_COL_INFO:
    with PI_STREAMLIT.container(border=True):
        PI_STREAMLIT.markdown('**1.2 Required tables and fields.**')
        with PI_STREAMLIT.expander('Show the list'):
            for ZV_ST_TABLE, ZV_LI_FIELDS in ZV_DI_REQUIRED_TABLES.items():
                PI_STREAMLIT.markdown(
                    f'**{ZV_ST_TABLE}** — {", ".join(ZV_LI_FIELDS)}'
                )

with ZV_OB_COL_TEMPLATE:
    with PI_STREAMLIT.container(border=True):
        PI_STREAMLIT.markdown('**1.3 Template files.**')
        FC_DOWNLOAD_BUTTON(
            ZVFCI_BY_DATA=FC_BUILD_TEMPLATE_BYTES(),
            ZVFCI_ST_FILENAME='VENDOR_BANK_TEMPLATES.txt',
            ZVFCI_ST_LABEL='Download headings',
            ZVFCI_ST_KEY='vb_template',
        )
        PI_STREAMLIT.markdown(
            '*:grey[Headings only, technical names, tab-delimited.]*'
        )

if ZV_LI_OB_UPLOADS:
    PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES] = FC_READ_UPLOADS(
        ZV_LI_OB_UPLOADS
    )
    if PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES]:
        FC_SNAPSHOT_SAVE(
            PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES],
            PI_STREAMLIT.session_state.get(ZV_ST_KEY_RESULTS),
            PI_STREAMLIT.session_state.get(ZV_ST_KEY_STATUS, 'not_started'),
        )

# ---------- auto-restore a saved session (page reload / server restart) -------
# If nothing was uploaded this run and state is empty but a snapshot exists,
# restore it automatically so reloading the page keeps the data. "Start Over"
# clears the snapshot and starts fresh.
if (not ZV_LI_OB_UPLOADS
        and not PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES]
        and not PI_STREAMLIT.session_state[ZV_ST_KEY_RESTORE]
        and FC_SNAPSHOT_EXISTS()):
    ZV_TU_LOADED = FC_SNAPSHOT_LOAD()
    if ZV_TU_LOADED[0] is not None:
        PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES] = ZV_TU_LOADED[0]
        PI_STREAMLIT.session_state[ZV_ST_KEY_RESULTS] = ZV_TU_LOADED[1]
        PI_STREAMLIT.session_state[ZV_ST_KEY_STATUS] = ZV_TU_LOADED[2]
    PI_STREAMLIT.session_state[ZV_ST_KEY_RESTORE] = True
    # rerun so the sidebar (company filter) and all sections see the data;
    # RESTORE=True keeps this from looping back into the restore block.
    PI_STREAMLIT.rerun()

ZV_DI_TABLES = PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES] or {}

# one-run confirmation right after an auto-restore
if (PI_STREAMLIT.session_state.get(ZV_ST_KEY_RESTORE) is True
        and ZV_DI_TABLES):
    PI_STREAMLIT.success(
        'Restored saved data from the previous session '
        f'(backend: {FC_STORAGE_BACKEND_LABEL()}). '
        'Click Start Over to clear it.'
    )
    PI_STREAMLIT.session_state[ZV_ST_KEY_RESTORE] = False

with PI_STREAMLIT.container(border=True):
    PI_STREAMLIT.markdown('**1.4 Files uploaded.**')
    if not ZV_LI_OB_UPLOADS:
        PI_STREAMLIT.markdown('*:grey[No files uploaded yet.]*')
    else:
        PI_STREAMLIT.success(f'Selected {len(ZV_LI_OB_UPLOADS)} file(s)')
        for ZV_OB_FILE in ZV_LI_OB_UPLOADS:
            ZV_ST_STEM = ZV_OB_FILE.name.rsplit('.', 1)[0].strip().upper()
            ZV_DF_PREVIEW = ZV_DI_TABLES.get(ZV_ST_STEM)
            ZV_ST_ROWS = (f'{ZV_DF_PREVIEW.height:,} rows'
                          if ZV_DF_PREVIEW is not None else 'not recognised')
            with PI_STREAMLIT.expander(f'{ZV_OB_FILE.name}  —  {ZV_ST_ROWS}'):
                if ZV_DF_PREVIEW is not None:
                    PI_STREAMLIT.dataframe(ZV_DF_PREVIEW.head(20),
                                           hide_index=True, **ZV_DI_WIDTH)
                else:
                    PI_STREAMLIT.warning(
                        'The file name does not match a required table.'
                    )

ZV_LI_PROBLEMS = FC_CHECK_TABLES_AND_FIELDS(ZV_DI_TABLES)
ZV_BO_DATA_COMPLETE = len(ZV_LI_PROBLEMS) == 0

# Run Analysis gets most of the space, Start Over stays compact on the right
ZV_OB_COL_RUN, ZV_OB_COL_CLEAR = PI_STREAMLIT.columns([5, 1])

with ZV_OB_COL_RUN:
    ZV_BO_RUN_PROCESSING = PI_STREAMLIT.button(
        'Run Analysis', type='primary', disabled=not ZV_BO_DATA_COMPLETE,
        **ZV_DI_WIDTH
    )
with ZV_OB_COL_CLEAR:
    ZV_BO_CLEAR = PI_STREAMLIT.button('Start Over', type='secondary',
                                      **ZV_DI_WIDTH)

if ZV_BO_CLEAR:
    FC_SNAPSHOT_CLEAR()
    PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES] = None
    PI_STREAMLIT.session_state[ZV_ST_KEY_RESULTS] = None
    PI_STREAMLIT.session_state[ZV_ST_KEY_STATUS] = 'not_started'
    PI_STREAMLIT.session_state[ZV_ST_KEY_RESTORE] = False
    PI_STREAMLIT.rerun()

if ZV_LI_OB_UPLOADS and not ZV_BO_DATA_COMPLETE:
    PI_STREAMLIT.error('Cannot go forward — ' + '  '.join(ZV_LI_PROBLEMS))
elif ZV_LI_OB_UPLOADS:
    PI_STREAMLIT.success('All required tables and fields are present.')

if ZV_BO_RUN_PROCESSING and ZV_BO_DATA_COMPLETE:
    PI_STREAMLIT.session_state[ZV_ST_KEY_RESULTS] = FC_RUN_ANALYSIS(ZV_DI_TABLES)
    PI_STREAMLIT.session_state[ZV_ST_KEY_STATUS] = 'analysis_run'
    FC_SNAPSHOT_SAVE(
        ZV_DI_TABLES,
        PI_STREAMLIT.session_state[ZV_ST_KEY_RESULTS],
        PI_STREAMLIT.session_state[ZV_ST_KEY_STATUS],
    )

ZV_DI_RESULTS = PI_STREAMLIT.session_state[ZV_ST_KEY_RESULTS]

if ZV_DI_RESULTS is None:
    PI_STREAMLIT.info(
        'Upload the extracts and run the analysis to see the KPIs, maps and '
        'tables.'
    )
    PI_STREAMLIT.stop()


# ----------------------------------------------------- 2. processing results
FC_SECTION_HEADER(
    '2',
    'Processing Results',
    'The maps and tables below show the exceptions only — the vendors for '
    'which the three countries all differ.',
)

ZV_DF_EXCEPTIONS = ZV_DI_RESULTS['EXCEPTIONS']
ZV_DF_TRANSACTIONS = ZV_DI_RESULTS['TRANSACTIONS']
ZV_DF_SETTLEMENTS = ZV_DI_RESULTS['SETTLEMENTS']

if ZV_LI_ST_COMPANY_FILTER:
    ZV_DF_EXCEPTIONS = ZV_DF_EXCEPTIONS.filter(
        PI_POLARS.col('BUKRS').is_in(ZV_LI_ST_COMPANY_FILTER))
    ZV_DF_TRANSACTIONS = ZV_DF_TRANSACTIONS.filter(
        PI_POLARS.col('BUKRS').is_in(ZV_LI_ST_COMPANY_FILTER))
    ZV_DF_SETTLEMENTS = ZV_DF_SETTLEMENTS.filter(
        PI_POLARS.col('BUKRS').is_in(ZV_LI_ST_COMPANY_FILTER))

with PI_STREAMLIT.container(border=True):
    FC_SECTION_HEADER(
        '2.1', 'Overview Results',
        'Three KPIs on the flagged population.'
    )
    ZV_OB_KPI1, ZV_OB_KPI2, ZV_OB_KPI3 = PI_STREAMLIT.columns(3)
    ZV_OB_KPI1.metric('Vendors', f"{ZV_DI_RESULTS['KPI1']:,}",
                      help='KPI 1 — total vendors in scope')
    ZV_OB_KPI2.metric('Vendors flagged', f"{ZV_DI_RESULTS['KPI2']:,}",
                      help='KPI 2 — vendors with three different countries')
    ZV_OB_KPI3.metric('Flagged share', f"{ZV_DI_RESULTS['KPI3']:.1f}%",
                      help='KPI 3 — KPI 2 as a share of KPI 1')

with PI_STREAMLIT.container(border=True):
    FC_SECTION_HEADER(
        '2.2', 'Map graphs',
        'Click a bubble on any map to cross-filter the other maps and the '
        'tables below. Click it again to clear.'
    )
    ZV_OB_MAP1, ZV_OB_MAP2, ZV_OB_MAP3 = PI_STREAMLIT.columns(3)
    with ZV_OB_MAP1:
        ZV_OB_CHART_SONY = FC_MAP_GRAPH(
            ZV_DF_EXCEPTIONS, 'SONY_LAND1', 'SONY_COUNTRY',
            'Sony country (T001_LAND1)', 'ZV_SONY_SELECTION'
        )
    with ZV_OB_MAP2:
        ZV_OB_CHART_VENDOR = FC_MAP_GRAPH(
            ZV_DF_EXCEPTIONS, 'VENDOR_LAND1', 'VENDOR_COUNTRY',
            'Vendor country (LFA1_LAND1)', 'ZV_VENDOR_SELECTION'
        )
    with ZV_OB_MAP3:
        ZV_OB_CHART_BANK = FC_MAP_GRAPH(
            ZV_DF_EXCEPTIONS, 'BANKS', 'BANK_COUNTRY',
            'Vendor bank (LFBK_BANKS)', 'ZV_BANK_SELECTION'
        )

# cross-filtering, per the shared-function pattern in the Streamlit chapter
for ZV_OB_CHART, ZV_ST_PARAM, ZV_ST_COLUMN in (
        (ZV_OB_CHART_SONY, 'ZV_SONY_SELECTION', 'SONY_LAND1'),
        (ZV_OB_CHART_VENDOR, 'ZV_VENDOR_SELECTION', 'VENDOR_LAND1'),
        (ZV_OB_CHART_BANK, 'ZV_BANK_SELECTION', 'BANKS')):
    ZV_OB_SELECTION = FC_GET_SELECTION_VALUE(
        ZVFCI_OB_CHART_DATA=ZV_OB_CHART,
        ZVFCI_ST_PARAM_NAME=ZV_ST_PARAM,
    )
    ZV_DF_EXCEPTIONS = FC_FILTER_BY_CATEGORY_SELECTION(
        ZVFCI_DF=ZV_DF_EXCEPTIONS,
        ZVFCI_OB_SELECTION=ZV_OB_SELECTION,
        ZVFCI_ST_CATEGORY_COLUMN=ZV_ST_COLUMN,
    )

ZV_LI_ST_SELECTED_VENDORS = (
    ZV_DF_EXCEPTIONS.select('LIFNR').unique().to_series().to_list()
)
ZV_DF_TRANSACTIONS = ZV_DF_TRANSACTIONS.filter(
    PI_POLARS.col('LIFNR').is_in(ZV_LI_ST_SELECTED_VENDORS)
)
ZV_DF_SETTLEMENTS = ZV_DF_SETTLEMENTS.filter(
    PI_POLARS.col('LIFNR').is_in(ZV_LI_ST_SELECTED_VENDORS)
)

FC_SECTION_HEADER(
    '2.3', 'Detail tables',
    'Download each table to Excel, or browse it here.'
)

ZV_OB_TAB_VENDORS, ZV_OB_TAB_DOCS, ZV_OB_TAB_PAY = PI_STREAMLIT.tabs(
    ['Vendors', 'Transactions', 'Payment settlements']
)

with ZV_OB_TAB_VENDORS:
    FC_SHOW_TABLE(
        'Table 1 — List of vendors',
        ZV_DF_EXCEPTIONS.select([
            'BUKRS', 'BUTXT', 'SONY_LAND1', 'SONY_COUNTRY',
            'LIFNR', 'NAME1', 'VENDOR_LAND1', 'VENDOR_COUNTRY', 'ORT01', 'STRAS',
            'BANKS', 'BANK_COUNTRY', 'BANKL', 'BANKN', 'KOINH', 'BVTYP',
            'LOEVM', 'SPERR',
        ]),
        'VENDOR_BANK_VENDORS.xlsx', 'download_button_1'
    )

with ZV_OB_TAB_DOCS:
    FC_SHOW_TABLE(
        'Table 2 — List of vendor transactions (BSAK / BSIK)',
        ZV_DF_TRANSACTIONS.select([
            'BUKRS', 'LIFNR', 'NAME1', 'BELNR', 'GJAHR', 'BUDAT',
            'BLART', 'DOCUMENT_TYPE', 'WRBTR', 'WAERS', 'SHKZG',
            'BVTYP', 'AUGBL', 'SOURCE',
        ]),
        'VENDOR_BANK_TRANSACTIONS.xlsx', 'download_button_2'
    )

with ZV_OB_TAB_PAY:
    FC_SHOW_TABLE(
        'Table 3 — List of payment settlements (REGUH)',
        ZV_DF_SETTLEMENTS.select([
            'BUKRS', 'LIFNR', 'NAME1', 'VBLNR', 'VALUT', 'VALUT_YEAR',
            'ZBNKS', 'PAID_BANK_COUNTRY', 'ZBNKL', 'ZBNKN',
            'PAYEE_ON_MASTER', 'RZAWE',
        ]),
        'VENDOR_BANK_SETTLEMENTS.xlsx', 'download_button_3'
    )
    PI_STREAMLIT.markdown(
        "*:grey[**Note:** PAYEE_ON_MASTER = N means the payment went to an "
        "account that is not on the vendor master (LFBK).]*"
    )
