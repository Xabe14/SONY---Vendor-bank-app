"""Wrapper around the Streamlit download_button()."""

import streamlit as PI_STREAMLIT

from FC_APP_CONFIG import ZV_BO_USE_WIDTH


def FC_DOWNLOAD_BUTTON(ZVFCI_BY_DATA: bytes,
                       ZVFCI_ST_FILENAME: str,
                       ZVFCI_ST_LABEL: str = 'Download Excel',
                       ZVFCI_ST_KEY: str = None):
    ZV_DI_KWARGS = {'width': 'stretch'} if ZV_BO_USE_WIDTH else {}
    return PI_STREAMLIT.download_button(
        label=ZVFCI_ST_LABEL,
        data=ZVFCI_BY_DATA,
        file_name=ZVFCI_ST_FILENAME,
        key=ZVFCI_ST_KEY,
        **ZV_DI_KWARGS,
    )
