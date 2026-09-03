"""Streamlit: filter a polars DataFrame on a chart selection."""

import polars as PI_POLARS


def FC_FILTER_BY_CATEGORY_SELECTION(ZVFCI_DF,
                                    ZVFCI_OB_SELECTION,
                                    ZVFCI_ST_CATEGORY_COLUMN: str):
    if ZVFCI_DF is None or not ZVFCI_OB_SELECTION:
        return ZVFCI_DF
    if ZVFCI_ST_CATEGORY_COLUMN not in ZVFCI_DF.columns:
        return ZVFCI_DF

    ZV_LI_VALUES = (
        ZVFCI_OB_SELECTION if isinstance(ZVFCI_OB_SELECTION, (list, tuple))
        else [ZVFCI_OB_SELECTION]
    )
    return ZVFCI_DF.filter(
        PI_POLARS.col(ZVFCI_ST_CATEGORY_COLUMN).is_in(ZV_LI_VALUES)
    )
