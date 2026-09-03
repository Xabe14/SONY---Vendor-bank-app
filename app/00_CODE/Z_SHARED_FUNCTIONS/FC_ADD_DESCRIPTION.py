"""Streamlit: code-description join, per the shared-function standard."""

import polars as PI_POLARS


def FC_ADD_DESCRIPTION(ZVFCI_DF, ZVFCI_ST_CODE_COLUMN: str, ZVFCI_DF_TEXT,
                       ZVFCI_ST_TEXT_KEY: str, ZVFCI_ST_TEXT_COLUMN: str,
                       ZVFCI_ST_TARGET: str):
    """Code-description rule: every code is shown next to its description."""
    ZV_DF_LOOKUP = (
        ZVFCI_DF_TEXT
        .select([ZVFCI_ST_TEXT_KEY, ZVFCI_ST_TEXT_COLUMN])
        .unique(subset=[ZVFCI_ST_TEXT_KEY])
        .rename({ZVFCI_ST_TEXT_KEY: ZVFCI_ST_CODE_COLUMN,
                 ZVFCI_ST_TEXT_COLUMN: ZVFCI_ST_TARGET})
    )
    return ZVFCI_DF.join(ZV_DF_LOOKUP, on=ZVFCI_ST_CODE_COLUMN, how='left')


def FC_MERGE_CODE_DESCRIPTION(ZVFCI_DF, ZVFCI_ST_CODE_COLUMN: str,
                              ZVFCI_ST_DESC_COLUMN: str,
                              ZVFCI_ST_TARGET_COLUMN: str):
    """Mandatory field order, 300Framework SAP field naming: a code field
    carries its description in the same field, named ZF_<Table>_<CodeField>
    _<DescField> and joined with a bare '-' (see FC_CONCATENATE_FIELDS /
    FC_LFA1LFB1_CONCAT in 300F_PYTHON_BACKEND), not two separate columns."""
    return ZVFCI_DF.with_columns(
        PI_POLARS.concat_str(
            [PI_POLARS.col(ZVFCI_ST_CODE_COLUMN),
             PI_POLARS.col(ZVFCI_ST_DESC_COLUMN)],
            separator='-', ignore_nulls=True,
        ).alias(ZVFCI_ST_TARGET_COLUMN)
    ).drop([ZVFCI_ST_CODE_COLUMN, ZVFCI_ST_DESC_COLUMN])
