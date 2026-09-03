"""Read a tab-delimited file (path or in-memory upload) into a polars DataFrame."""

import polars as PI_POLARS


def FC_IMPORT_TEXT(ZVFCI_OB_SOURCE, ZVFCI_ST_SEPARATOR: str = '\t'):
    if ZVFCI_OB_SOURCE is None:
        return None
    if hasattr(ZVFCI_OB_SOURCE, 'seek'):
        ZVFCI_OB_SOURCE.seek(0)
    return PI_POLARS.read_csv(
        ZVFCI_OB_SOURCE,
        separator=ZVFCI_ST_SEPARATOR,
        infer_schema_length=0,
        encoding='utf8-lossy',
    )
