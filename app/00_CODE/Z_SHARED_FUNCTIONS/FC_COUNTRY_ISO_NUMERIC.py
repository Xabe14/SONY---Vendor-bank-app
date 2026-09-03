"""ISO 3166-1 numeric code lookup for the country-fill (choropleth) map.

NOTE: SAP holds only the two-character country key (LAND1). The numeric id is
needed only to join a country onto the vega-datasets world-atlas topojson,
which keys each country polygon by its ISO 3166-1 numeric code. Same scope
caveat as FC_COUNTRY_COORDINATES: covers the sandbox country set only, and
must be extended (or replaced by a full ISO table) for production data.
"""

ZV_DI_COUNTRY_ISO_NUMERIC = {
    'AE': 784, 'CH': 756, 'CN': 156,
    'DE': 276, 'FR': 250, 'GB': 826,
    'HK': 344, 'IN': 356, 'IT': 380,
    'JP': 392, 'KR': 410, 'KY': 136,
    'LU': 442, 'MY': 458, 'NL': 528,
    'PA': 591, 'SG': 702, 'TH': 764,
    'US': 840, 'VN': 704,
}


def FC_COUNTRY_ISO_NUMERIC(ZVFCI_ST_LAND1: str):
    return ZV_DI_COUNTRY_ISO_NUMERIC.get(ZVFCI_ST_LAND1)
