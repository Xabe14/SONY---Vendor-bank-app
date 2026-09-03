"""Type-cast numeric/date columns after import, with loud warnings.

Hardening: SAP extracts come in as all-string (infer_schema_length=0). Columns
that feed arithmetic (WRBTR amounts) are cast to numeric so totals are computed
on real numbers. Any value that cannot be parsed is counted and reported so the
analyst sees exactly where data quality breaks, instead of a silently wrong
total.

Deliberately NOT cast: GJAHR, BUDAT, VALUT. The app already derives
VALUT_YEAR via string slicing (`.str.slice(0, 4)`), and changing those
columns to numbers would break that path. They stay Utf8; WRBTR becomes
Float64.

Rules per table:
    BSIK / BSAK : WRBTR -> Float64
    REGUH       : (none — VALUT stays Utf8 for VALUT_YEAR slicing)
    others      : no numeric casts (keys stay Utf8)
"""

import polars as PI_POLARS

ZV_DI_NUMERIC_COLUMNS = {
    'BSIK': ['WRBTR'],
    'BSAK': ['WRBTR'],
}


def _strip(ZVFCI_SERIES):
    """Whitespace-strip a Utf8 series, tolerant of old/new polars APIs."""
    try:
        return ZVFCI_SERIES.str.strip_chars()
    except AttributeError:
        return ZVFCI_SERIES.str.strip()


def FC_TYPECAST_ONE(ZVFCI_DF, ZVFCI_ST_TABLE: str) -> tuple:
    """Cast numeric columns of one table.

    Returns (ZVFCI_DF, ZV_LI_WARNINGS); ZV_LI_WARNINGS is a list of
    {table, column, failed, example} for values that did not parse.
    """
    ZV_LI_WARNINGS = []
    if ZVFCI_DF is None:
        return ZVFCI_DF, ZV_LI_WARNINGS
    ZV_DF = ZVFCI_DF
    for ZV_ST_COLUMN in ZV_DI_NUMERIC_COLUMNS.get(ZVFCI_ST_TABLE, []):
        if ZV_ST_COLUMN not in ZV_DF.columns:
            continue
        ZV_SERIES = _strip(ZV_DF[ZV_ST_COLUMN])
        ZV_MASK_EMPTY = (ZV_SERIES == '')
        ZV_SERIES_NUM = ZV_SERIES.cast(PI_POLARS.Float64, strict=False)
        ZV_MASK_FAILED = (~ZV_MASK_EMPTY) & ZV_SERIES_NUM.is_null()
        ZV_NU_FAILED = int(ZV_MASK_FAILED.sum())
        if ZV_NU_FAILED:
            ZV_OB_EXAMPLE = ZV_DF.filter(ZV_MASK_FAILED) \
                .select(ZV_ST_COLUMN).head(1).to_series().to_list()
            ZV_LI_WARNINGS.append({
                'table': ZVFCI_ST_TABLE,
                'column': ZV_ST_COLUMN,
                'failed': ZV_NU_FAILED,
                'example': (str(ZV_OB_EXAMPLE[0]) if ZV_OB_EXAMPLE else ''),
            })
        ZV_DF = ZV_DF.with_columns(
            ZV_SERIES_NUM.fill_null(0).alias(ZV_ST_COLUMN)
        )
    return ZV_DF, ZV_LI_WARNINGS


def FC_TYPECAST_TABLES(ZVFCI_DI_TABLES: dict) -> tuple:
    """Cast every known table; returns (tables, warnings)."""
    ZV_LI_WARNINGS = []
    for ZV_ST_TABLE, ZV_DF in (ZVFCI_DI_TABLES or {}).items():
        ZV_DF_NEW, ZV_LI_WARN = FC_TYPECAST_ONE(ZV_DF, ZV_ST_TABLE)
        if ZV_DF_NEW is not None:
            ZVFCI_DI_TABLES[ZV_ST_TABLE] = ZV_DF_NEW
        ZV_LI_WARNINGS.extend(ZV_LI_WARN)
    return ZVFCI_DI_TABLES, ZV_LI_WARNINGS
