"""Vendor bank app.

Audit question: does Sony have vendors where the Sony company country, the vendor
country and the bank country are all three different?

Layout follows page 4 of the vendor bank app definition; tables, fields and join
path follow page 5. Streamlit patterns follow the 300Framework Streamlit chapter:
shared functions for every reusable object, sidebar layout as in the current apps,
Vega-Lite params for cross-filtering, session_state to survive a rerun.
"""

import hashlib
import time

import polars as PI_POLARS
import streamlit as PI_STREAMLIT

from FC_APP_CONFIG import ZV_BO_USE_WIDTH
from Z_SHARED_FUNCTIONS.FC_FILE_UPLOADER import FC_FILE_UPLOADER
from Z_SHARED_FUNCTIONS.FC_GET_SELECTION_VALUE import FC_GET_SELECTION_VALUE
from Z_SHARED_FUNCTIONS.FC_CATEGORY_MULTISELECT import FC_CATEGORY_MULTISELECT
from Z_SHARED_FUNCTIONS.FC_DOWNLOAD_BUTTON import FC_DOWNLOAD_BUTTON
from Z_SHARED_FUNCTIONS.FC_UI_STYLE import (
    FC_INJECT_CSS,
    FC_SECTION_HEADER,
    FC_STATUS_PILL,
)
from Z_SHARED_FUNCTIONS.FC_STORAGE import (
    FC_SNAPSHOT_CLEAR,
    FC_SNAPSHOT_EXISTS,
    FC_SNAPSHOT_IS_ENCRYPTED,
    FC_SNAPSHOT_LOAD,
    FC_SNAPSHOT_SAVE,
    FC_STORAGE_BACKEND_LABEL,
)
from Z_SHARED_FUNCTIONS.FC_ADD_DESCRIPTION import (
    FC_ADD_DESCRIPTION,
    FC_MERGE_CODE_DESCRIPTION,
)
from Z_SHARED_FUNCTIONS.FC_MAP_GRAPH import (
    FC_MAP_GRAPH,
    FC_MAP_ROLE_OVERLAP,
)
from Z_SHARED_FUNCTIONS.FC_SHOW_TABLE import FC_SHOW_TABLE
from Z_SHARED_FUNCTIONS.FC_BUILD_TEMPLATE_BYTES import FC_BUILD_TEMPLATE_BYTES
from Z_SHARED_FUNCTIONS.FC_READ_UPLOADS import FC_READ_UPLOADS
from Z_SHARED_FUNCTIONS.FC_CHECK_TABLES_AND_FIELDS import (
    FC_CHECK_TABLES_AND_FIELDS,
    FC_CHECK_TABLE_WARNINGS,
)
from Z_SHARED_FUNCTIONS.FC_TYPECAST import FC_TYPECAST_TABLES

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
ZV_ST_KEY_UPLOAD_ERRORS = 'ZV_VB_UPLOAD_ERRORS'
ZV_ST_KEY_TYPECAST_WARNINGS = 'ZV_VB_TYPECAST_WARNINGS'
ZV_ST_KEY_DATA_WARNINGS = 'ZV_VB_DATA_WARNINGS'
ZV_ST_KEY_HASHES = 'ZV_VB_HASHES'
ZV_ST_KEY_RUN_META = 'ZV_VB_RUN_META'
ZV_ST_KEY_CHART_RESET = 'ZV_VB_CHART_RESET'

for ZV_ST_KEY, ZV_OB_DEFAULT in ((ZV_ST_KEY_TABLES, None),
                                 (ZV_ST_KEY_RESULTS, None),
                                 (ZV_ST_KEY_STATUS, 'not_started'),
                                 (ZV_ST_KEY_RESTORE, False),
                                 (ZV_ST_KEY_UPLOAD_ERRORS, []),
                                 (ZV_ST_KEY_TYPECAST_WARNINGS, []),
                                 (ZV_ST_KEY_DATA_WARNINGS, []),
                                 (ZV_ST_KEY_HASHES, {}),
                                 (ZV_ST_KEY_RUN_META, None),
                                 (ZV_ST_KEY_CHART_RESET, 0)):
    if ZV_ST_KEY not in PI_STREAMLIT.session_state:
        PI_STREAMLIT.session_state[ZV_ST_KEY] = ZV_OB_DEFAULT


# ------------------------------------------------------- app-specific functions
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

    # country descriptions go on the full population first, so the maps (which
    # plot every supplier, not just the three-country exceptions) have them too
    for ZV_ST_CODE, ZV_ST_TARGET in (('SONY_LAND1', 'SONY_COUNTRY'),
                                     ('VENDOR_LAND1', 'VENDOR_COUNTRY'),
                                     ('BANKS', 'BANK_COUNTRY')):
        ZV_DF_VENDOR_BANK = FC_ADD_DESCRIPTION(
            ZV_DF_VENDOR_BANK, ZV_ST_CODE, ZV_DF_T005T, 'LAND1', 'LANDX',
            ZV_ST_TARGET
        )

    ZV_NU_KPI1 = ZV_DF_VENDOR_BANK.select('LIFNR').n_unique()
    ZV_DF_EXCEPTIONS = ZV_DF_VENDOR_BANK.filter(PI_POLARS.col('IS_EXCEPTION'))
    ZV_NU_KPI2 = ZV_DF_EXCEPTIONS.select('LIFNR').n_unique()
    ZV_NU_KPI3 = (ZV_NU_KPI2 / ZV_NU_KPI1 * 100) if ZV_NU_KPI1 else 0.0

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
        .join(ZV_DF_T001.select(['BUKRS', 'BUTXT']), on='BUKRS', how='left')
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
        .join(ZV_DF_T001.select(['BUKRS', 'BUTXT']), on='BUKRS', how='left')
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
                  .with_columns(PI_POLARS.lit('Y').alias('ACCOUNT_ON_MASTER'))
    )
    ZV_DF_SETTLEMENTS = (
        ZV_DF_SETTLEMENTS
        .join(ZV_DF_MASTER_ACCOUNTS, on=['LIFNR', 'ZBNKN'], how='left')
        .with_columns(PI_POLARS.col('ACCOUNT_ON_MASTER').fill_null('N'))
    )

    return {
        'KPI1': ZV_NU_KPI1,
        'KPI2': ZV_NU_KPI2,
        'KPI3': ZV_NU_KPI3,
        'ALL_VENDORS': ZV_DF_VENDOR_BANK,
        'EXCEPTIONS': ZV_DF_EXCEPTIONS,
        'TRANSACTIONS': ZV_DF_TRANSACTIONS,
        'SETTLEMENTS': ZV_DF_SETTLEMENTS,
    }


# ------------------------------------------------------------------- sidebar
with PI_STREAMLIT.sidebar:
    PI_STREAMLIT.markdown(
        '<div class="zv-sidebar-brand"><h3>Vendor bank app</h3>'
        '<p>Risk &amp; Control Department</p></div>',
        unsafe_allow_html=True,
    )
    PI_STREAMLIT.markdown('---')

    ZV_DI_TABLES_STATE = PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES] or {}

    PI_STREAMLIT.markdown(
        '<p style="color:#FFFFFF; font-style: italic; margin: 0;">Status</p>',
        unsafe_allow_html=True,
    )
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
        PI_STREAMLIT.markdown('**1.2 Required tables/fields.**')
        with PI_STREAMLIT.expander('Show the list'):
            for ZV_ST_TABLE, ZV_LI_FIELDS in ZV_DI_REQUIRED_TABLES.items():
                PI_STREAMLIT.markdown(
                    f'**{ZV_ST_TABLE}** — {", ".join(ZV_LI_FIELDS)}'
                )
        PI_STREAMLIT.markdown(
            '*:grey[tables and field names required for each table.]*'
        )

with ZV_OB_COL_TEMPLATE:
    with PI_STREAMLIT.container(border=True):
        PI_STREAMLIT.markdown('**1.3 Template files.**')
        FC_DOWNLOAD_BUTTON(
            ZVFCI_BY_DATA=FC_BUILD_TEMPLATE_BYTES(ZV_DI_REQUIRED_TABLES),
            ZVFCI_ST_FILENAME='VENDOR_BANK_TEMPLATES.txt',
            ZVFCI_ST_LABEL='Download headings',
            ZVFCI_ST_KEY='vb_template',
        )
        PI_STREAMLIT.markdown(
            '*:grey[Headings only, technical names, tab-delimited.]*'
        )

if ZV_LI_OB_UPLOADS:
    ZV_DI_UPLOADED, ZV_LI_UPLOAD_ERRS, ZV_DI_HASHES = FC_READ_UPLOADS(
        ZV_LI_OB_UPLOADS, ZV_DI_REQUIRED_TABLES
    )
    ZV_DI_UPLOADED, ZV_LI_TYPECAST_WARN = FC_TYPECAST_TABLES(ZV_DI_UPLOADED)
    PI_STREAMLIT.session_state[ZV_ST_KEY_TABLES] = ZV_DI_UPLOADED
    PI_STREAMLIT.session_state[ZV_ST_KEY_UPLOAD_ERRORS] = ZV_LI_UPLOAD_ERRS
    PI_STREAMLIT.session_state[ZV_ST_KEY_TYPECAST_WARNINGS] = ZV_LI_TYPECAST_WARN
    PI_STREAMLIT.session_state[ZV_ST_KEY_HASHES] = ZV_DI_HASHES
    if ZV_DI_UPLOADED:
        FC_SNAPSHOT_SAVE(
            ZV_DI_UPLOADED,
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
        ZV_DI_HASHES = PI_STREAMLIT.session_state.get(ZV_ST_KEY_HASHES, {})
        for ZV_OB_FILE in ZV_LI_OB_UPLOADS:
            ZV_ST_STEM = ZV_OB_FILE.name.rsplit('.', 1)[0].strip().upper()
            ZV_DF_PREVIEW = ZV_DI_TABLES.get(ZV_ST_STEM)
            ZV_ST_HASH = ZV_DI_HASHES.get(ZV_ST_STEM, '')
            ZV_ST_ROWS = (f'{ZV_DF_PREVIEW.height:,} rows'
                          if ZV_DF_PREVIEW is not None else 'not recognised')
            ZV_ST_HASH_TXT = (f' · sha256 {ZV_ST_HASH}'
                              if ZV_ST_HASH else '')
            with PI_STREAMLIT.expander(
                    f'{ZV_OB_FILE.name}  —  {ZV_ST_ROWS}{ZV_ST_HASH_TXT}'):
                if ZV_DF_PREVIEW is not None:
                    PI_STREAMLIT.dataframe(ZV_DF_PREVIEW.head(20),
                                           hide_index=True, **ZV_DI_WIDTH)
                else:
                    PI_STREAMLIT.warning(
                        'The file name does not match a required table.'
                    )
        # loud upload errors
        for ZV_ST_FNAME, ZV_ST_REASON in PI_STREAMLIT.session_state.get(
                ZV_ST_KEY_UPLOAD_ERRORS, []):
            PI_STREAMLIT.error(f'{ZV_ST_FNAME}: {ZV_ST_REASON}')

ZV_LI_PROBLEMS = FC_CHECK_TABLES_AND_FIELDS(ZV_DI_TABLES, ZV_DI_REQUIRED_TABLES)
ZV_BO_DATA_COMPLETE = len(ZV_LI_PROBLEMS) == 0

# data-quality warnings (not blockers): typecast + table checks
ZV_LI_DATA_WARN = FC_CHECK_TABLE_WARNINGS(ZV_DI_TABLES, ZV_DI_REQUIRED_TABLES)
ZV_LI_DATA_WARN += [
    f"Table {ZV_DI['table']}: column {ZV_DI['column']} has "
    f"{ZV_DI['failed']:,} unparsable value(s)"
    + (f" (e.g. '{ZV_DI['example']}')" if ZV_DI['example'] else '')
    for ZV_DI in PI_STREAMLIT.session_state.get(
        ZV_ST_KEY_TYPECAST_WARNINGS, [])
]
if ZV_LI_DATA_WARN:
    PI_STREAMLIT.warning(
        'Data quality warnings (the analysis still runs):\n\n'
        + '\n\n'.join(f'- {ZV_W}' for ZV_W in ZV_LI_DATA_WARN)
    )

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
    PI_STREAMLIT.session_state[ZV_ST_KEY_CHART_RESET] = 0
    PI_STREAMLIT.rerun()

if ZV_LI_OB_UPLOADS and not ZV_BO_DATA_COMPLETE:
    PI_STREAMLIT.error('Cannot go forward — ' + '  '.join(ZV_LI_PROBLEMS))
elif ZV_LI_OB_UPLOADS:
    PI_STREAMLIT.success('All required tables and fields are present.')

if ZV_BO_RUN_PROCESSING and ZV_BO_DATA_COMPLETE:
    PI_STREAMLIT.session_state[ZV_ST_KEY_RESULTS] = FC_RUN_ANALYSIS(ZV_DI_TABLES)
    PI_STREAMLIT.session_state[ZV_ST_KEY_STATUS] = 'analysis_run'
    PI_STREAMLIT.session_state[ZV_ST_KEY_RUN_META] = {
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'hashes': dict(PI_STREAMLIT.session_state.get(ZV_ST_KEY_HASHES, {})),
        'encrypted': FC_SNAPSHOT_IS_ENCRYPTED(),
    }
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
    'The maps show every supplier; the tables below show the exceptions '
    'only — the vendors for which the three countries all differ.',
)

ZV_DF_ALL_VENDORS_FULL = ZV_DI_RESULTS['ALL_VENDORS']
ZV_DF_ALL_VENDORS = ZV_DF_ALL_VENDORS_FULL
ZV_DF_EXCEPTIONS = ZV_DI_RESULTS['EXCEPTIONS']
ZV_DF_TRANSACTIONS = ZV_DI_RESULTS['TRANSACTIONS']
ZV_DF_SETTLEMENTS = ZV_DI_RESULTS['SETTLEMENTS']

# The filter widgets themselves render further down (next to the detail
# tables they visually belong to), but their values must be known now, so
# KPI1-3 and the maps can react to them too. Same trick as the map-click
# selections just below: a widget's session_state value from the previous
# run is already there under its key before that widget is drawn again
# later this same run.
ZV_LI_SEL_BUKRS = PI_STREAMLIT.session_state.get('flt_bukrs', [])
ZV_LI_SEL_VENDOR_LAND1 = PI_STREAMLIT.session_state.get('flt_vendor_country', [])
ZV_LI_SEL_BANKS = PI_STREAMLIT.session_state.get('flt_bank_country', [])
ZV_LI_SEL_LIFNR = PI_STREAMLIT.session_state.get('flt_vendor', [])

# Read each map's current click from session_state (Streamlit updates a
# keyed widget's state *before* the script reruns, so whichever map was
# just clicked already has its new value here — before any of the four
# maps is drawn again below). Reading this before the KPI section, not just
# before the maps, is what lets a map click move the KPIs too — same as the
# filter boxes above.
#
# The widget keys carry a reset counter: clearing the map filters bumps the
# counter so every chart gets a brand-new key and Streamlit rebuilds the
# component — which also drops the browser-side Vega-Lite selection (the
# highlighted bubble). Popping session_state alone cannot do that.
ZV_NU_CHART_RESET = PI_STREAMLIT.session_state.get(ZV_ST_KEY_CHART_RESET, 0)
ZV_ST_CHART_SUFFIX = f'_{ZV_NU_CHART_RESET}'
ZV_OB_SEL_SONY = FC_GET_SELECTION_VALUE(
    PI_STREAMLIT.session_state.get(
        f'chart_ZV_SONY_SELECTION{ZV_ST_CHART_SUFFIX}'),
    'ZV_SONY_SELECTION',
)
ZV_OB_SEL_VENDOR = FC_GET_SELECTION_VALUE(
    PI_STREAMLIT.session_state.get(
        f'chart_ZV_VENDOR_SELECTION{ZV_ST_CHART_SUFFIX}'),
    'ZV_VENDOR_SELECTION',
)
ZV_OB_SEL_BANK = FC_GET_SELECTION_VALUE(
    PI_STREAMLIT.session_state.get(
        f'chart_ZV_BANK_SELECTION{ZV_ST_CHART_SUFFIX}'),
    'ZV_BANK_SELECTION',
)
ZV_LI_ST_SEL_ROLE = FC_GET_SELECTION_VALUE(
    PI_STREAMLIT.session_state.get(
        f'chart_role_overlap{ZV_ST_CHART_SUFFIX}'),
    'ZV_ROLE_SELECTION',
)

# -------- combine every filter dimension --------
# Different dimensions combine with AND (each one narrows the set). Values
# within the SAME dimension — the multiselect box and a map click on the
# same column — combine with OR (their union), so e.g. Vendor country box
# = PA plus a Vendor map click on CN means "PA or CN", never an empty
# intersection.
ZV_DI_FILTER_DIMENSIONS = [
    ('BUKRS', ZV_LI_SEL_BUKRS, []),
    ('VENDOR_LAND1', ZV_LI_SEL_VENDOR_LAND1, ZV_OB_SEL_VENDOR),
    ('BANKS', ZV_LI_SEL_BANKS, ZV_OB_SEL_BANK),
    ('SONY_LAND1', [], ZV_OB_SEL_SONY),
    ('LIFNR', ZV_LI_SEL_LIFNR, []),
]
for ZV_ST_COLUMN, ZV_LI_MS_VALUES, ZV_LI_MAP_VALUES in ZV_DI_FILTER_DIMENSIONS:
    ZV_LI_VALUES = list(dict.fromkeys([*ZV_LI_MS_VALUES, *ZV_LI_MAP_VALUES]))
    if ZV_LI_VALUES:
        ZV_DF_ALL_VENDORS = ZV_DF_ALL_VENDORS.filter(
            PI_POLARS.col(ZV_ST_COLUMN).is_in(ZV_LI_VALUES))
        ZV_DF_EXCEPTIONS = ZV_DF_EXCEPTIONS.filter(
            PI_POLARS.col(ZV_ST_COLUMN).is_in(ZV_LI_VALUES))

# A click on the role-overlap map behaves like the other three maps: the
# clicked country becomes a filter that narrows everything — KPI1, KPI2, the
# three bubble maps, the role-overlap map itself, and the tables below — down
# to vendors touching that country in any of its three roles (Sony, vendor
# or bank). Same OR-within-dimension semantics as the other maps: the role
# selection joins the SONY/VENDOR/BANK/LIFNR filter dimensions, not a new
# one, so it combines with them by AND across dimensions.
if ZV_LI_ST_SEL_ROLE:
    ZV_LI_ST_ROLE_CODES = ZV_LI_ST_SEL_ROLE  # already country codes
    ZV_DF_ALL_VENDORS = ZV_DF_ALL_VENDORS.filter(
        PI_POLARS.col('SONY_LAND1').is_in(ZV_LI_ST_ROLE_CODES)
        | PI_POLARS.col('VENDOR_LAND1').is_in(ZV_LI_ST_ROLE_CODES)
        | PI_POLARS.col('BANKS').is_in(ZV_LI_ST_ROLE_CODES)
    )
    ZV_DF_EXCEPTIONS = ZV_DF_EXCEPTIONS.filter(
        PI_POLARS.col('SONY_LAND1').is_in(ZV_LI_ST_ROLE_CODES)
        | PI_POLARS.col('VENDOR_LAND1').is_in(ZV_LI_ST_ROLE_CODES)
        | PI_POLARS.col('BANKS').is_in(ZV_LI_ST_ROLE_CODES)
    )

with PI_STREAMLIT.container(border=True):
    FC_SECTION_HEADER(
        '2.1', 'Overview Results',
        'Reacts to filters and map clicks.'
    )
    ZV_NU_KPI1 = ZV_DF_ALL_VENDORS.select('LIFNR').n_unique()
    ZV_NU_KPI2 = ZV_DF_EXCEPTIONS.select('LIFNR').n_unique()
    ZV_NU_KPI3 = (ZV_NU_KPI2 / ZV_NU_KPI1 * 100) if ZV_NU_KPI1 else 0.0
    ZV_OB_KPI1, ZV_OB_KPI2, ZV_OB_KPI3 = PI_STREAMLIT.columns(3)
    ZV_OB_KPI1.metric('Vendors', f'{ZV_NU_KPI1:,}',
                      help='KPI 1 — total vendors in scope')
    ZV_OB_KPI2.metric('Vendors flagged', f'{ZV_NU_KPI2:,}',
                      help='KPI 2 — vendors with three different countries')
    ZV_OB_KPI3.metric('Flagged share', f'{ZV_NU_KPI3:.1f}%',
                      help='KPI 3 — KPI 2 as a share of KPI 1')

with PI_STREAMLIT.container(border=True):
    FC_SECTION_HEADER(
        '2.2', 'Map graphs',
        'Click a bubble or a country to filter everything below.'
    )
    if ZV_OB_SEL_SONY or ZV_OB_SEL_VENDOR or ZV_OB_SEL_BANK or ZV_LI_ST_SEL_ROLE:
        _, ZV_OB_FILTER_BUTTON = PI_STREAMLIT.columns([5, 1])
        with ZV_OB_FILTER_BUTTON:
            if PI_STREAMLIT.button('Clear map filters',
                                   key='btn_clear_map_filters'):
                # Bump the chart-reset counter: every map gets a fresh widget
                # key next run, so Streamlit rebuilds each chart component and
                # the browser-side Vega-Lite selection (highlighted bubble /
                # dimmed countries) is dropped too — not just the Python-side
                # selection value.
                PI_STREAMLIT.session_state[ZV_ST_KEY_CHART_RESET] = (
                    ZV_NU_CHART_RESET + 1
                )
                PI_STREAMLIT.rerun()

    ZV_OB_MAP_ROW1_COL1, ZV_OB_MAP_ROW1_COL2 = PI_STREAMLIT.columns(2)
    ZV_OB_MAP_ROW2_COL1, ZV_OB_MAP_ROW2_COL2 = PI_STREAMLIT.columns(2)
    with ZV_OB_MAP_ROW1_COL1:
        FC_MAP_GRAPH(
            ZV_DF_ALL_VENDORS, 'SONY_LAND1', 'SONY_COUNTRY',
            'Sony country (T001_LAND1)', 'ZV_SONY_SELECTION',
            ZVFCI_ST_WIDGET_KEY=f'chart_ZV_SONY_SELECTION{ZV_ST_CHART_SUFFIX}',
        )
    with ZV_OB_MAP_ROW1_COL2:
        FC_MAP_GRAPH(
            ZV_DF_ALL_VENDORS, 'VENDOR_LAND1', 'VENDOR_COUNTRY',
            'Vendor country (LFA1_LAND1)', 'ZV_VENDOR_SELECTION',
            ZVFCI_ST_WIDGET_KEY=(
                f'chart_ZV_VENDOR_SELECTION{ZV_ST_CHART_SUFFIX}'),
        )
    with ZV_OB_MAP_ROW2_COL1:
        FC_MAP_GRAPH(
            ZV_DF_ALL_VENDORS, 'BANKS', 'BANK_COUNTRY',
            'Vendor bank (LFBK_BANKS)', 'ZV_BANK_SELECTION',
            ZVFCI_ST_WIDGET_KEY=f'chart_ZV_BANK_SELECTION{ZV_ST_CHART_SUFFIX}',
        )
    with ZV_OB_MAP_ROW2_COL2:
        FC_MAP_ROLE_OVERLAP(
            ZV_DF_ALL_VENDORS,
            ZVFCI_ST_WIDGET_KEY=f'chart_role_overlap{ZV_ST_CHART_SUFFIX}',
        )

ZV_DF_SELECTED_KEYS = ZV_DF_EXCEPTIONS.select(['LIFNR', 'BUKRS']).unique()
ZV_DF_TRANSACTIONS = ZV_DF_TRANSACTIONS.join(
    ZV_DF_SELECTED_KEYS, on=['LIFNR', 'BUKRS'], how='inner',
)
ZV_DF_SETTLEMENTS = ZV_DF_SETTLEMENTS.join(
    ZV_DF_SELECTED_KEYS, on=['LIFNR', 'BUKRS'], how='inner',
)

FC_SECTION_HEADER(
    '2.3', 'Detail tables',
    'Download each table to Excel, or browse it here.'
)

PI_STREAMLIT.markdown(
    '**Filters** — *:grey[leave a box empty to include everything.]*'
)
ZV_OB_FILTER1, ZV_OB_FILTER2, ZV_OB_FILTER3, ZV_OB_FILTER4 = (
    PI_STREAMLIT.columns(4)
)
with ZV_OB_FILTER1:
    FC_CATEGORY_MULTISELECT(
        ZV_DF_ALL_VENDORS_FULL, 'BUKRS', 'BUTXT',
        'Company code', 'flt_bukrs'
    )
with ZV_OB_FILTER2:
    FC_CATEGORY_MULTISELECT(
        ZV_DF_ALL_VENDORS_FULL, 'VENDOR_LAND1', 'VENDOR_COUNTRY',
        'Vendor country', 'flt_vendor_country'
    )
with ZV_OB_FILTER3:
    FC_CATEGORY_MULTISELECT(
        ZV_DF_ALL_VENDORS_FULL, 'BANKS', 'BANK_COUNTRY',
        'Bank country', 'flt_bank_country'
    )
with ZV_OB_FILTER4:
    FC_CATEGORY_MULTISELECT(
        ZV_DF_ALL_VENDORS_FULL, 'LIFNR', 'NAME1',
        'Vendor', 'flt_vendor'
    )

ZV_OB_TAB_VENDORS, ZV_OB_TAB_DOCS, ZV_OB_TAB_PAY = PI_STREAMLIT.tabs(
    ['Vendors', 'Transactions', 'Payment settlements']
)

# 300Framework SAP field naming: a code field carries its description in the
# same field (ZF_<Table>_<CodeField>_<DescField>, joined with a bare '-'),
# not two separate columns.
ZV_DF_VENDORS_DISPLAY = ZV_DF_EXCEPTIONS.select([
    'BUKRS', 'BUTXT', 'SONY_LAND1', 'SONY_COUNTRY',
    'LIFNR', 'NAME1', 'VENDOR_LAND1', 'VENDOR_COUNTRY', 'ORT01', 'STRAS',
    'BANKS', 'BANK_COUNTRY', 'BANKL', 'BANKN', 'KOINH', 'BVTYP',
    'LOEVM', 'SPERR',
])
for ZV_ST_CODE, ZV_ST_DESC, ZV_ST_TARGET in (
        ('BUKRS', 'BUTXT', 'ZF_LFB1_BUKRS_BUTXT'),
        ('SONY_LAND1', 'SONY_COUNTRY', 'ZF_T001_LAND1_LANDX'),
        ('LIFNR', 'NAME1', 'ZF_LFA1_LIFNR_NAME1'),
        ('VENDOR_LAND1', 'VENDOR_COUNTRY', 'ZF_LFA1_LAND1_LANDX'),
        ('BANKS', 'BANK_COUNTRY', 'ZF_LFBK_BANKS_LANDX')):
    ZV_DF_VENDORS_DISPLAY = FC_MERGE_CODE_DESCRIPTION(
        ZV_DF_VENDORS_DISPLAY, ZV_ST_CODE, ZV_ST_DESC, ZV_ST_TARGET
    )
ZV_DF_VENDORS_DISPLAY = ZV_DF_VENDORS_DISPLAY.select([
    'ZF_LFB1_BUKRS_BUTXT', 'ZF_T001_LAND1_LANDX',
    'ZF_LFA1_LIFNR_NAME1', 'ZF_LFA1_LAND1_LANDX', 'ORT01', 'STRAS',
    'ZF_LFBK_BANKS_LANDX', 'BANKL', 'BANKN', 'KOINH', 'BVTYP',
    'LOEVM', 'SPERR',
])

ZV_DF_TRANSACTIONS_DISPLAY = ZV_DF_TRANSACTIONS.select([
    'BUKRS', 'BUTXT', 'LIFNR', 'NAME1', 'BELNR', 'GJAHR', 'BUDAT',
    'BLART', 'DOCUMENT_TYPE', 'WRBTR', 'WAERS', 'SHKZG',
    'BVTYP', 'AUGBL', 'SOURCE',
])
for ZV_ST_CODE, ZV_ST_DESC, ZV_ST_TARGET in (
        ('BUKRS', 'BUTXT', 'ZF_T001_BUKRS_BUTXT'),
        ('LIFNR', 'NAME1', 'ZF_LFA1_LIFNR_NAME1'),
        ('BLART', 'DOCUMENT_TYPE', 'ZF_T003T_BLART_LTEXT')):
    ZV_DF_TRANSACTIONS_DISPLAY = FC_MERGE_CODE_DESCRIPTION(
        ZV_DF_TRANSACTIONS_DISPLAY, ZV_ST_CODE, ZV_ST_DESC, ZV_ST_TARGET
    )
ZV_DF_TRANSACTIONS_DISPLAY = ZV_DF_TRANSACTIONS_DISPLAY.select([
    'ZF_T001_BUKRS_BUTXT', 'ZF_LFA1_LIFNR_NAME1', 'BELNR', 'GJAHR', 'BUDAT',
    'ZF_T003T_BLART_LTEXT', 'WRBTR', 'WAERS', 'SHKZG',
    'BVTYP', 'AUGBL', 'SOURCE',
])

ZV_DF_SETTLEMENTS_DISPLAY = ZV_DF_SETTLEMENTS.select([
    'BUKRS', 'BUTXT', 'LIFNR', 'NAME1', 'VBLNR', 'VALUT', 'VALUT_YEAR',
    'ZBNKS', 'PAID_BANK_COUNTRY', 'ZBNKL', 'ZBNKN',
    'ACCOUNT_ON_MASTER', 'RZAWE',
])
for ZV_ST_CODE, ZV_ST_DESC, ZV_ST_TARGET in (
        ('BUKRS', 'BUTXT', 'ZF_T001_BUKRS_BUTXT'),
        ('LIFNR', 'NAME1', 'ZF_LFA1_LIFNR_NAME1'),
        ('ZBNKS', 'PAID_BANK_COUNTRY', 'ZF_T005T_ZBNKS_LANDX')):
    ZV_DF_SETTLEMENTS_DISPLAY = FC_MERGE_CODE_DESCRIPTION(
        ZV_DF_SETTLEMENTS_DISPLAY, ZV_ST_CODE, ZV_ST_DESC, ZV_ST_TARGET
    )
ZV_DF_SETTLEMENTS_DISPLAY = ZV_DF_SETTLEMENTS_DISPLAY.select([
    'ZF_T001_BUKRS_BUTXT', 'ZF_LFA1_LIFNR_NAME1', 'VBLNR', 'VALUT', 'VALUT_YEAR',
    'ZF_T005T_ZBNKS_LANDX', 'ZBNKL', 'ZBNKN',
    'ACCOUNT_ON_MASTER', 'RZAWE',
])

with ZV_OB_TAB_VENDORS:
    FC_SHOW_TABLE(
        'Table 1 — List of vendors',
        ZV_DF_VENDORS_DISPLAY,
        'VENDOR_BANK_VENDORS.xlsx', 'download_button_1'
    )

with ZV_OB_TAB_DOCS:
    FC_SHOW_TABLE(
        'Table 2 — List of vendor transactions (BSAK / BSIK)',
        ZV_DF_TRANSACTIONS_DISPLAY,
        'VENDOR_BANK_TRANSACTIONS.xlsx', 'download_button_2'
    )

with ZV_OB_TAB_PAY:
    FC_SHOW_TABLE(
        'Table 3 — List of payment settlements (REGUH)',
        ZV_DF_SETTLEMENTS_DISPLAY,
        'VENDOR_BANK_SETTLEMENTS.xlsx', 'download_button_3'
    )
    PI_STREAMLIT.markdown(
        "*:grey[**Note:** ACCOUNT_ON_MASTER = N means the payment went to an "
        "account that is not on the vendor master (LFBK).]*"
    )
