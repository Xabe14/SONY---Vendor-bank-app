"""Wrapper around the Streamlit file_uploader(). Returns the file(s) in memory."""

import streamlit as PI_STREAMLIT


def FC_FILE_UPLOADER(ZVFCI_LI_ALLOWED_TYPES: list = None,
                     ZVFCI_BO_ACCEPT_MUL_FILES: bool = False,
                     ZVFCI_ST_LABEL: str = 'Upload file',
                     ZVFCI_ST_KEY: str = None):
    return PI_STREAMLIT.file_uploader(
        ZVFCI_ST_LABEL,
        type=ZVFCI_LI_ALLOWED_TYPES or ['csv'],
        accept_multiple_files=ZVFCI_BO_ACCEPT_MUL_FILES,
        key=ZVFCI_ST_KEY,
    )
