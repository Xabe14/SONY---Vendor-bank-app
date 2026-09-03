"""Streamlit: headings-only upload template, per the shared-function standard."""

import io as PI_IO


def FC_BUILD_TEMPLATE_BYTES(ZVFCI_DI_REQUIRED_TABLES: dict) -> bytes:
    """Headings only, tab-delimited, one block per required table."""
    ZV_OB_BUFFER = PI_IO.StringIO()
    for ZV_ST_TABLE, ZV_LI_FIELDS in ZVFCI_DI_REQUIRED_TABLES.items():
        ZV_OB_BUFFER.write(f'# {ZV_ST_TABLE}\n')
        ZV_OB_BUFFER.write('\t'.join(ZV_LI_FIELDS) + '\n\n')
    return ZV_OB_BUFFER.getvalue().encode('utf-8')
