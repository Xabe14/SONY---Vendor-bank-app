"""Streamlit: obtain data from chart selection.

Returns the value(s) a user selected on a Vega-Lite chart. A single selected
category is returned as a list of one; an empty selection returns an empty list.
"""


def FC_GET_SELECTION_VALUE(ZVFCI_OB_CHART_DATA, ZVFCI_ST_PARAM_NAME: str):
    if ZVFCI_OB_CHART_DATA is None:
        return []

    ZV_DI_SELECTION = getattr(ZVFCI_OB_CHART_DATA, 'selection', None)
    if ZV_DI_SELECTION is None and isinstance(ZVFCI_OB_CHART_DATA, dict):
        ZV_DI_SELECTION = ZVFCI_OB_CHART_DATA.get('selection')
    if not ZV_DI_SELECTION:
        return []

    ZV_OB_PARAM = ZV_DI_SELECTION.get(ZVFCI_ST_PARAM_NAME)
    if not ZV_OB_PARAM:
        return []

    # interval selections arrive as {field: [values]}
    if isinstance(ZV_OB_PARAM, dict):
        ZV_LI_OUT = []
        for ZV_LI_VALUES in ZV_OB_PARAM.values():
            if isinstance(ZV_LI_VALUES, list):
                ZV_LI_OUT.extend(ZV_LI_VALUES)
        return ZV_LI_OUT

    # point selections arrive as [{field: value}, ...]
    ZV_LI_OUT = []
    for ZV_DI_ROW in ZV_OB_PARAM:
        if isinstance(ZV_DI_ROW, dict):
            ZV_LI_OUT.extend(ZV_DI_ROW.values())
    return ZV_LI_OUT
