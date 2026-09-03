"""Country centroid lookup for the bubble maps.

NOTE: SAP holds only the two-character country key. These coordinates are NOT
from SAP. In the production app this lookup must be replaced by the one already
used by the existing supplier location chart.
"""

ZV_DI_COUNTRY_COORDINATES = {
    'AE': (23.42, 53.85),   'CH': (46.82, 8.23),    'CN': (35.86, 104.20),
    'DE': (51.17, 10.45),   'FR': (46.23, 2.21),    'GB': (55.38, -3.44),
    'HK': (22.32, 114.17),  'IN': (20.59, 78.96),   'IT': (41.87, 12.57),
    'JP': (36.20, 138.25),  'KR': (35.91, 127.77),  'KY': (19.31, -81.25),
    'LU': (49.82, 6.13),    'MY': (4.21, 101.98),   'NL': (52.13, 5.29),
    'PA': (8.54, -80.78),   'SG': (1.35, 103.82),   'TH': (15.87, 100.99),
    'US': (37.09, -95.71),  'VN': (14.06, 108.28),
}


def FC_COUNTRY_COORDINATES(ZVFCI_ST_LAND1: str):
    return ZV_DI_COUNTRY_COORDINATES.get(ZVFCI_ST_LAND1)
