"""Read a delimited text file (path or in-memory upload) into a polars DataFrame.

Hardening: the encoding and separator are auto-detected instead of assuming
utf-8 + tab, and decoding never silently replaces unknown bytes with U+FFFD.
Detection tries strict decoders in order (utf-8-sig, utf-8, cp1252, latin-1)
and picks the separator with the most occurrences on a sample line.
"""

import io as PI_IO
from pathlib import Path as PI_PATH

import polars as PI_POLARS

ZV_LI_ENCODING_CANDIDATES = ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1')
ZV_LI_SEPARATOR_CANDIDATES = ('\t', ',', ';', '|')


def FC_READ_BYTES(ZVFCI_OB_SOURCE) -> bytes:
    """Normalize a path, bytes, str or file-like upload into bytes."""
    if ZVFCI_OB_SOURCE is None:
        return b''
    if isinstance(ZVFCI_OB_SOURCE, bytes):
        return ZVFCI_OB_SOURCE
    if isinstance(ZVFCI_OB_SOURCE, str):
        return PI_PATH(ZVFCI_OB_SOURCE).read_bytes()
    if hasattr(ZVFCI_OB_SOURCE, 'read_bytes'):  # pathlib.Path
        return ZVFCI_OB_SOURCE.read_bytes()
    if hasattr(ZVFCI_OB_SOURCE, 'seek'):
        ZVFCI_OB_SOURCE.seek(0)
    if hasattr(ZVFCI_OB_SOURCE, 'getvalue'):
        ZV_OB_DATA = ZVFCI_OB_SOURCE.getvalue()
    else:
        ZV_OB_DATA = ZVFCI_OB_SOURCE.read()
    if isinstance(ZV_OB_DATA, str):
        ZV_OB_DATA = ZV_OB_DATA.encode('utf-8')
    return ZV_OB_DATA


def FC_DETECT_FORMAT(ZVFCI_OB_SOURCE) -> tuple:
    """Return (separator, encoding) detected from the file content."""
    ZV_BY_DATA = FC_READ_BYTES(ZVFCI_OB_SOURCE)
    ZV_ST_ENCODING = 'utf-8'
    for ZV_ST_ENC in ZV_LI_ENCODING_CANDIDATES:
        try:
            ZV_BY_DATA.decode(ZV_ST_ENC)
            ZV_ST_ENCODING = ZV_ST_ENC
            break
        except (UnicodeDecodeError, LookupError):
            continue

    ZV_ST_SAMPLE = ZV_BY_DATA[:16384].decode(ZV_ST_ENCODING, errors='replace')
    ZV_DI_COUNTS = {
        ZV_ST_SEP: ZV_ST_SAMPLE.count(ZV_ST_SEP)
        for ZV_ST_SEP in ZV_LI_SEPARATOR_CANDIDATES
    }
    ZV_ST_SEPARATOR = max(ZV_DI_COUNTS, key=ZV_DI_COUNTS.get)
    if ZV_DI_COUNTS[ZV_ST_SEPARATOR] == 0:
        ZV_ST_SEPARATOR = '\t'
    return ZV_ST_SEPARATOR, ZV_ST_ENCODING


def FC_IMPORT_TEXT(ZVFCI_OB_SOURCE,
                   ZVFCI_ST_SEPARATOR: str = None,
                   ZVFCI_ST_ENCODING: str = None):
    """Read a delimited file into a polars DataFrame (all columns as Utf8).

    Pass a separator/encoding to force them; otherwise both are auto-detected.
    """
    if ZVFCI_OB_SOURCE is None:
        return None
    ZV_BY_DATA = FC_READ_BYTES(ZVFCI_OB_SOURCE)
    if not ZV_BY_DATA.strip():
        return None
    if ZVFCI_ST_SEPARATOR is None or ZVFCI_ST_ENCODING is None:
        ZV_ST_SEP_DETECTED, ZV_ST_ENC_DETECTED = FC_DETECT_FORMAT(ZV_BY_DATA)
        ZVFCI_ST_SEPARATOR = ZVFCI_ST_SEPARATOR or ZV_ST_SEP_DETECTED
        ZVFCI_ST_ENCODING = ZVFCI_ST_ENCODING or ZV_ST_ENC_DETECTED
    ZV_ST_TEXT = ZV_BY_DATA.decode(ZVFCI_ST_ENCODING)
    return PI_POLARS.read_csv(
        PI_IO.StringIO(ZV_ST_TEXT),
        separator=ZVFCI_ST_SEPARATOR,
        infer_schema_length=0,
    )
