"""Streamlit: code-description multiselect filter, per the shared-function
standard.

Empty selection means "no filter" (show everything) — matches
FC_FILTER_BY_CATEGORY_SELECTION's semantics, so nothing needs to be
pre-selected even when the option list is long (e.g. one row per vendor).
"""

import streamlit as PI_STREAMLIT


def FC_CATEGORY_MULTISELECT(ZVFCI_DF, ZVFCI_ST_CODE_COLUMN: str,
                            ZVFCI_ST_DESC_COLUMN: str, ZVFCI_ST_LABEL: str,
                            ZVFCI_ST_KEY: str) -> list:
    """Multiselect over every distinct code, shown as 'code - description'."""
    ZV_LI_DI_OPTIONS = (
        ZVFCI_DF.select([ZVFCI_ST_CODE_COLUMN, ZVFCI_ST_DESC_COLUMN])
                .unique().sort(ZVFCI_ST_CODE_COLUMN).to_dicts()
    )
    ZV_LI_ST_CODES = [ZV_DI[ZVFCI_ST_CODE_COLUMN] for ZV_DI in ZV_LI_DI_OPTIONS]
    ZV_DI_LABELS = {
        ZV_DI[ZVFCI_ST_CODE_COLUMN]:
            f"{ZV_DI[ZVFCI_ST_CODE_COLUMN]} - {ZV_DI[ZVFCI_ST_DESC_COLUMN]}"
        for ZV_DI in ZV_LI_DI_OPTIONS
    }
    return PI_STREAMLIT.multiselect(
        ZVFCI_ST_LABEL, ZV_LI_ST_CODES,
        format_func=lambda ZV_ST_CODE: ZV_DI_LABELS.get(ZV_ST_CODE, ZV_ST_CODE),
        placeholder='All',
        key=ZVFCI_ST_KEY,
    )
