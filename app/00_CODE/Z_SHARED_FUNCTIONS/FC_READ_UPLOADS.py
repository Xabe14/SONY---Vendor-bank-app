"""Streamlit: match uploads to required tables, per the shared-function standard.

Hardening: a failed file is reported loudly instead of being swallowed into a
None table. Returns (tables_dict, errors, hashes) so the caller can show which
file failed, and can print a sha256 fingerprint of every accepted file for
audit / re-runs.
"""

import hashlib

import streamlit as PI_STREAMLIT

from Z_SHARED_FUNCTIONS.FC_IMPORT_TEXT import FC_IMPORT_TEXT, FC_READ_BYTES


def FC_READ_UPLOADS(ZVFCI_LI_OB_FILES, ZVFCI_DI_REQUIRED_TABLES: dict) -> tuple:
    """Match each uploaded file to a table by its file stem: LFA1.txt -> LFA1.

    Returns (ZV_DI_TABLES, ZV_LI_ERRORS, ZV_DI_HASHES) where:
      - ZV_LI_ERRORS is a list of (filename, reason) for failed/skipped files
      - ZV_DI_HASHES maps table stem -> first 12 hex chars of sha256
    """
    ZV_DI_TABLES = {}
    ZV_LI_ERRORS = []
    ZV_DI_HASHES = {}
    ZV_LI_OB_FILES = list(ZVFCI_LI_OB_FILES or [])
    ZV_OB_BAR = PI_STREAMLIT.progress(0)
    for ZV_NU_INDEX, ZV_OB_FILE in enumerate(ZV_LI_OB_FILES):
        ZV_ST_STEM = ZV_OB_FILE.name.rsplit('.', 1)[0].strip().upper()
        if ZV_ST_STEM in ZVFCI_DI_REQUIRED_TABLES:
            try:
                ZV_BY_DATA = FC_READ_BYTES(ZV_OB_FILE)
                ZV_ST_HASH = hashlib.sha256(ZV_BY_DATA).hexdigest()[:12]
                ZV_DF = FC_IMPORT_TEXT(ZV_BY_DATA)
                if ZV_DF is None or ZV_DF.height == 0:
                    ZV_LI_ERRORS.append(
                        (ZV_OB_FILE.name, 'file is empty or unreadable')
                    )
                else:
                    ZV_DI_TABLES[ZV_ST_STEM] = ZV_DF
                    ZV_DI_HASHES[ZV_ST_STEM] = ZV_ST_HASH
            except Exception as ZV_EXC:
                ZV_LI_ERRORS.append((ZV_OB_FILE.name, str(ZV_EXC)))
        else:
            ZV_LI_ERRORS.append(
                (ZV_OB_FILE.name,
                 'file name does not match any required table')
            )
        ZV_OB_BAR.progress((ZV_NU_INDEX + 1) / max(len(ZV_LI_OB_FILES), 1))
    ZV_OB_BAR.empty()
    return ZV_DI_TABLES, ZV_LI_ERRORS, ZV_DI_HASHES
