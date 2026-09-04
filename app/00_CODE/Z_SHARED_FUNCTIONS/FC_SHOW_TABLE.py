"""Streamlit: table with a Download Excel button, per the shared-function standard."""

import streamlit as PI_STREAMLIT

from FC_APP_CONFIG import ZV_BO_USE_WIDTH
from Z_SHARED_FUNCTIONS.FC_DOWNLOAD_BUTTON import FC_DOWNLOAD_BUTTON
from Z_SHARED_FUNCTIONS.FC_GET_EXCEL_BYTES import FC_GET_EXCEL_BYTES


def FC_SHOW_TABLE(ZVFCI_ST_TITLE: str, ZVFCI_DF, ZVFCI_ST_FILENAME: str,
                  ZVFCI_ST_KEY: str) -> None:
    """Title, row count, a download button, then the DataFrame itself."""
    ZV_DI_WIDTH = {'width': 'stretch'} if ZV_BO_USE_WIDTH else {}
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
        # A dict, not the polars DataFrame itself: Streamlit's own dataframe
        # conversion calls polars' to_pandas(), whose Rust-side arrow/pandas
        # bridge panics with "capacity overflow" on the wasm32 build (stlite /
        # GitHub Pages) — a dict is built into a pandas DataFrame by pandas
        # itself, skipping that bridge entirely, on desktop too.
        PI_STREAMLIT.dataframe(ZVFCI_DF.to_dict(as_series=False),
                               hide_index=True, **ZV_DI_WIDTH)
