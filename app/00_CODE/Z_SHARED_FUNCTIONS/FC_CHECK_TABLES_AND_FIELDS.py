"""Streamlit: validate uploads against required tables/fields, per the
shared-function standard.

Hardening: in addition to missing tables/fields, this reports data-quality
warnings — NULL/blank values in key columns (LIFNR, BUKRS), empty tables, and
row counts over a performance threshold — so a wrong-looking analysis can be
traced to bad input instead of a silent join drop.
"""

ZV_NU_MAX_ROWS_WARN = 2_000_000  # warn above this many rows in a detail table


def FC_CHECK_TABLES_AND_FIELDS(ZVFCI_DI_TABLES: dict,
                               ZVFCI_DI_REQUIRED_TABLES: dict) -> list:
    """Return list of problems. Empty list means every required table/field ok."""
    ZV_LI_PROBLEMS = []
    for ZV_ST_TABLE, ZV_LI_FIELDS in ZVFCI_DI_REQUIRED_TABLES.items():
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


def FC_CHECK_TABLE_WARNINGS(ZVFCI_DI_TABLES: dict,
                            ZVFCI_DI_REQUIRED_TABLES: dict) -> list:
    """Return data-quality warnings (not blockers) for uploaded tables.

    Warnings cover: empty tables, blank key values (LIFNR/BUKRS), and row
    counts over ZV_NU_MAX_ROWS_WARN (a performance red flag, not an error).
    """
    ZV_LI_WARNINGS = []
    for ZV_ST_TABLE, ZV_LI_FIELDS in ZVFCI_DI_REQUIRED_TABLES.items():
        ZV_DF = ZVFCI_DI_TABLES.get(ZV_ST_TABLE)
        if ZV_DF is None:
            continue
        if ZV_DF.height == 0:
            ZV_LI_WARNINGS.append(f'Table {ZV_ST_TABLE} is empty (0 rows).')
            continue
        if ZV_DF.height > ZV_NU_MAX_ROWS_WARN:
            ZV_LI_WARNINGS.append(
                f'Table {ZV_ST_TABLE} has {ZV_DF.height:,} rows — '
                f'above {ZV_NU_MAX_ROWS_WARN:,}; the app may be slow.'
            )
        for ZV_ST_KEY in ('LIFNR', 'BUKRS'):
            if ZV_ST_KEY not in ZV_DF.columns:
                continue
            ZV_NU_BLANK = int(
                ZV_DF.filter(
                    ZV_DF[ZV_ST_KEY].is_null()
                    | (ZV_DF[ZV_ST_KEY] == '')
                ).height
            )
            if ZV_NU_BLANK:
                ZV_LI_WARNINGS.append(
                    f'Table {ZV_ST_TABLE}: {ZV_ST_KEY} has {ZV_NU_BLANK:,} '
                    'blank/empty value(s).'
                )
    return ZV_LI_WARNINGS
