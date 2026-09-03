"""Serialise a polars DataFrame to xlsx bytes, for the download button."""

import io as PI_IO


def FC_GET_EXCEL_BYTES(ZVFCI_DF, ZVFCI_ST_SHEET_NAME: str = 'Data') -> bytes:
    ZV_OB_BUFFER = PI_IO.BytesIO()
    ZVFCI_DF.write_excel(ZV_OB_BUFFER, worksheet=ZVFCI_ST_SHEET_NAME)
    return ZV_OB_BUFFER.getvalue()
