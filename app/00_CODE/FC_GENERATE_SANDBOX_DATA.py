"""Generate tab-delimited sandbox extracts that mimic the SAP tables used by the
vendor bank app. Run once:  python FC_GENERATE_SANDBOX_DATA.py
"""

import os as PI_OS
import random as PI_RANDOM
from datetime import date as PI_DATE, timedelta as PI_TIMEDELTA

import polars as PI_POLARS

PI_RANDOM.seed(20260831)

ZV_ST_OUTPUT_DIR = PI_OS.path.join(
    PI_OS.path.dirname(PI_OS.path.dirname(PI_OS.path.abspath(__file__))),
    '01_SANDBOX_DATA'
)

ZV_LI_DI_COMPANY_CODES = [
    {'BUKRS': '1000', 'BUTXT': 'Sony Corporation Japan',    'LAND1': 'JP'},
    {'BUKRS': '2000', 'BUTXT': 'Sony Europe BV',            'LAND1': 'NL'},
    {'BUKRS': '3000', 'BUTXT': 'Sony Electronics Inc',      'LAND1': 'US'},
    {'BUKRS': '4000', 'BUTXT': 'Sony UK Ltd',               'LAND1': 'GB'},
    {'BUKRS': '5000', 'BUTXT': 'Sony Vietnam Co Ltd',       'LAND1': 'VN'},
]

ZV_LI_DI_COUNTRIES = [
    {'LAND1': 'JP', 'LANDX': 'Japan'},
    {'LAND1': 'NL', 'LANDX': 'Netherlands'},
    {'LAND1': 'US', 'LANDX': 'United States'},
    {'LAND1': 'GB', 'LANDX': 'United Kingdom'},
    {'LAND1': 'VN', 'LANDX': 'Vietnam'},
    {'LAND1': 'DE', 'LANDX': 'Germany'},
    {'LAND1': 'CN', 'LANDX': 'China'},
    {'LAND1': 'SG', 'LANDX': 'Singapore'},
    {'LAND1': 'KR', 'LANDX': 'Korea, Republic of'},
    {'LAND1': 'MY', 'LANDX': 'Malaysia'},
    {'LAND1': 'TH', 'LANDX': 'Thailand'},
    {'LAND1': 'IN', 'LANDX': 'India'},
    {'LAND1': 'FR', 'LANDX': 'France'},
    {'LAND1': 'IT', 'LANDX': 'Italy'},
    {'LAND1': 'CH', 'LANDX': 'Switzerland'},
    {'LAND1': 'KY', 'LANDX': 'Cayman Islands'},
    {'LAND1': 'PA', 'LANDX': 'Panama'},
    {'LAND1': 'AE', 'LANDX': 'United Arab Emirates'},
    {'LAND1': 'HK', 'LANDX': 'Hong Kong'},
    {'LAND1': 'LU', 'LANDX': 'Luxembourg'},
]

ZV_LI_DI_DOC_TYPES = [
    {'BLART': 'KR', 'LTEXT': 'Vendor invoice'},
    {'BLART': 'KG', 'LTEXT': 'Vendor credit memo'},
    {'BLART': 'KZ', 'LTEXT': 'Vendor payment'},
    {'BLART': 'RE', 'LTEXT': 'Invoice receipt'},
]

ZV_LI_ST_NAME_STEMS = [
    'Pacific', 'Meridian', 'Northgate', 'Blue Harbour', 'Silverline', 'Kestrel',
    'Orion', 'Vertex', 'Arcadia', 'Lumen', 'Granite', 'Beacon', 'Halcyon',
    'Ironwood', 'Solstice', 'Cobalt', 'Tamarind', 'Windward', 'Everest', 'Sable',
]
ZV_LI_ST_NAME_TAILS = [
    'Components Ltd', 'Trading BV', 'Logistics GmbH', 'Industries Inc',
    'Electronics Co', 'Supplies SA', 'Technologies Pte', 'Materials Corp',
    'Services SARL', 'Manufacturing Sdn Bhd',
]
ZV_LI_ST_STREETS = [
    'Harbour Road', 'Industriestrasse', 'Nguyen Hue', 'Market Street',
    'Keizersgracht', 'Chome-Ginza', 'Orchard Road', 'Rue de la Paix',
]
ZV_LI_ST_CITIES = [
    'Tokyo', 'Amsterdam', 'San Jose', 'London', 'Ho Chi Minh City', 'Munich',
    'Shenzhen', 'Singapore', 'Seoul', 'Kuala Lumpur', 'Bangkok', 'Mumbai',
    'Paris', 'Milan', 'Zurich', 'George Town', 'Panama City', 'Dubai',
    'Hong Kong', 'Luxembourg',
]

ZV_NU_VENDOR_COUNT = 420


def FC_RANDOM_COUNTRY(ZVFCI_LI_EXCLUDE: list = None) -> str:
    ZV_LI_POOL = [
        ZV_DI_ROW['LAND1']
        for ZV_DI_ROW in ZV_LI_DI_COUNTRIES
        if ZV_DI_ROW['LAND1'] not in (ZVFCI_LI_EXCLUDE or [])
    ]
    return PI_RANDOM.choice(ZV_LI_POOL)


def FC_BUILD_VENDOR_MASTER() -> tuple:
    """Return (LFA1 rows, LFB1 rows, LFBK rows)."""
    ZV_LI_DI_LFA1 = []
    ZV_LI_DI_LFB1 = []
    ZV_LI_DI_LFBK = []

    for ZV_NU_INDEX in range(ZV_NU_VENDOR_COUNT):
        ZV_ST_LIFNR = f'{100000 + ZV_NU_INDEX:010d}'
        ZV_DI_COMPANY = PI_RANDOM.choice(ZV_LI_DI_COMPANY_CODES)
        ZV_ST_SONY_COUNTRY = ZV_DI_COMPANY['LAND1']

        # 20% of vendors are deliberately built as three-country exceptions
        ZV_BO_EXCEPTION = PI_RANDOM.random() < 0.20

        if ZV_BO_EXCEPTION:
            ZV_ST_VENDOR_COUNTRY = FC_RANDOM_COUNTRY([ZV_ST_SONY_COUNTRY])
            ZV_ST_BANK_COUNTRY = FC_RANDOM_COUNTRY(
                [ZV_ST_SONY_COUNTRY, ZV_ST_VENDOR_COUNTRY]
            )
        else:
            ZV_ST_VENDOR_COUNTRY = (
                ZV_ST_SONY_COUNTRY if PI_RANDOM.random() < 0.55
                else FC_RANDOM_COUNTRY([ZV_ST_SONY_COUNTRY])
            )
            ZV_ST_BANK_COUNTRY = ZV_ST_VENDOR_COUNTRY

        ZV_LI_DI_LFA1.append({
            'LIFNR': ZV_ST_LIFNR,
            'NAME1': f'{PI_RANDOM.choice(ZV_LI_ST_NAME_STEMS)} '
                     f'{PI_RANDOM.choice(ZV_LI_ST_NAME_TAILS)}',
            'LAND1': ZV_ST_VENDOR_COUNTRY,
            'ORT01': PI_RANDOM.choice(ZV_LI_ST_CITIES),
            'STRAS': f'{PI_RANDOM.randint(1, 240)} '
                     f'{PI_RANDOM.choice(ZV_LI_ST_STREETS)}',
            'LOEVM': 'X' if PI_RANDOM.random() < 0.03 else '',
            'SPERR': 'X' if PI_RANDOM.random() < 0.04 else '',
        })

        ZV_LI_DI_LFB1.append({
            'LIFNR': ZV_ST_LIFNR,
            'BUKRS': ZV_DI_COMPANY['BUKRS'],
            'AKONT': '0000160000',
        })

        # most vendors hold one bank account, some hold two
        ZV_NU_BANK_COUNT = 1 if PI_RANDOM.random() < 0.82 else 2
        for ZV_NU_BANK in range(ZV_NU_BANK_COUNT):
            ZV_ST_THIS_BANK_COUNTRY = (
                ZV_ST_BANK_COUNTRY if ZV_NU_BANK == 0
                else FC_RANDOM_COUNTRY([ZV_ST_BANK_COUNTRY])
            )
            ZV_LI_DI_LFBK.append({
                'LIFNR': ZV_ST_LIFNR,
                'BANKS': ZV_ST_THIS_BANK_COUNTRY,
                'BANKL': f'{PI_RANDOM.randint(10000000, 99999999)}',
                'BANKN': f'{PI_RANDOM.randint(10 ** 11, 10 ** 12 - 1)}',
                'KOINH': ZV_LI_DI_LFA1[-1]['NAME1'],
                # BVTYP is deliberately left blank most of the time: this is why
                # the definition says it must not be used as a join key
                'BVTYP': '' if PI_RANDOM.random() < 0.72
                         else f'{ZV_NU_BANK + 1:04d}',
            })

    return ZV_LI_DI_LFA1, ZV_LI_DI_LFB1, ZV_LI_DI_LFBK


def FC_BUILD_DOCUMENTS(ZVFCI_LI_DI_LFA1: list, ZVFCI_LI_DI_LFB1: list,
                       ZVFCI_LI_DI_LFBK: list) -> tuple:
    """Return (BSIK rows, BSAK rows, REGUH rows)."""
    ZV_DI_COMPANY_BY_VENDOR = {
        ZV_DI_ROW['LIFNR']: ZV_DI_ROW['BUKRS'] for ZV_DI_ROW in ZVFCI_LI_DI_LFB1
    }
    ZV_DI_BANK_BY_VENDOR = {}
    for ZV_DI_ROW in ZVFCI_LI_DI_LFBK:
        ZV_DI_BANK_BY_VENDOR.setdefault(ZV_DI_ROW['LIFNR'], []).append(ZV_DI_ROW)

    ZV_LI_DI_BSIK = []
    ZV_LI_DI_BSAK = []
    ZV_LI_DI_REGUH = []
    ZV_NU_DOC_SEQ = 5100000000
    ZV_NU_PAY_SEQ = 2000000000
    ZV_DT_BASE = PI_DATE(2026, 1, 1)

    for ZV_DI_VENDOR in ZVFCI_LI_DI_LFA1:
        ZV_ST_LIFNR = ZV_DI_VENDOR['LIFNR']
        ZV_ST_BUKRS = ZV_DI_COMPANY_BY_VENDOR[ZV_ST_LIFNR]

        for ZV_NU_DOC in range(PI_RANDOM.randint(1, 6)):
            ZV_NU_DOC_SEQ += 1
            ZV_DT_POSTING = ZV_DT_BASE + PI_TIMEDELTA(
                days=PI_RANDOM.randint(0, 230)
            )
            ZV_DI_DOC_TYPE = PI_RANDOM.choice(ZV_LI_DI_DOC_TYPES)
            ZV_DI_BANK = PI_RANDOM.choice(ZV_DI_BANK_BY_VENDOR[ZV_ST_LIFNR])

            ZV_DI_LINE = {
                'BUKRS': ZV_ST_BUKRS,
                'LIFNR': ZV_ST_LIFNR,
                'BELNR': str(ZV_NU_DOC_SEQ),
                'GJAHR': str(ZV_DT_POSTING.year),
                'BUDAT': ZV_DT_POSTING.isoformat(),
                'WRBTR': round(PI_RANDOM.uniform(450, 480000), 2),
                'WAERS': PI_RANDOM.choice(['EUR', 'USD', 'JPY', 'GBP']),
                'SHKZG': 'H',
                'BLART': ZV_DI_DOC_TYPE['BLART'],
                'BVTYP': ZV_DI_BANK['BVTYP'],
            }

            ZV_BO_CLEARED = PI_RANDOM.random() < 0.62
            if not ZV_BO_CLEARED:
                ZV_LI_DI_BSIK.append(ZV_DI_LINE)
                continue

            ZV_NU_PAY_SEQ += 1
            ZV_DT_CLEARING = ZV_DT_POSTING + PI_TIMEDELTA(
                days=PI_RANDOM.randint(5, 75)
            )
            ZV_ST_VBLNR = str(ZV_NU_PAY_SEQ)

            ZV_DI_CLEARED_LINE = dict(ZV_DI_LINE)
            ZV_DI_CLEARED_LINE['AUGDT'] = ZV_DT_CLEARING.isoformat()
            ZV_DI_CLEARED_LINE['AUGBL'] = ZV_ST_VBLNR
            ZV_LI_DI_BSAK.append(ZV_DI_CLEARED_LINE)

            # 6% of settlements are paid to an account that is NOT on the vendor
            # master: this is what the REGUH comparison is meant to surface
            ZV_BO_OFF_MASTER = PI_RANDOM.random() < 0.06
            if ZV_BO_OFF_MASTER:
                ZV_ST_PAID_COUNTRY = FC_RANDOM_COUNTRY([ZV_DI_BANK['BANKS']])
                ZV_ST_PAID_ACCOUNT = f'{PI_RANDOM.randint(10 ** 11, 10 ** 12 - 1)}'
                ZV_ST_PAID_BANKL = f'{PI_RANDOM.randint(10000000, 99999999)}'
            else:
                ZV_ST_PAID_COUNTRY = ZV_DI_BANK['BANKS']
                ZV_ST_PAID_ACCOUNT = ZV_DI_BANK['BANKN']
                ZV_ST_PAID_BANKL = ZV_DI_BANK['BANKL']

            ZV_LI_DI_REGUH.append({
                'ZBUKR': ZV_ST_BUKRS,
                'LIFNR': ZV_ST_LIFNR,
                'VBLNR': ZV_ST_VBLNR,
                'VALUT': ZV_DT_CLEARING.isoformat(),
                'ZBNKS': ZV_ST_PAID_COUNTRY,
                'ZBNKL': ZV_ST_PAID_BANKL,
                'ZBNKN': ZV_ST_PAID_ACCOUNT,
                'RZAWE': PI_RANDOM.choice(['T', 'U', 'C']),
                'EMPFG': ZV_ST_LIFNR if PI_RANDOM.random() > 0.04 else 'THIRDPARTY',
            })

    return ZV_LI_DI_BSIK, ZV_LI_DI_BSAK, ZV_LI_DI_REGUH


def FC_WRITE_TABLE(ZVFCI_ST_NAME: str, ZVFCI_LI_DI_ROWS: list) -> None:
    ZV_DF = PI_POLARS.DataFrame(ZVFCI_LI_DI_ROWS)
    ZV_ST_PATH = PI_OS.path.join(ZV_ST_OUTPUT_DIR, f'{ZVFCI_ST_NAME}.txt')
    ZV_DF.write_csv(ZV_ST_PATH, separator='\t')
    print(f'{ZVFCI_ST_NAME:<8} {ZV_DF.height:>7,} rows  ->  {ZV_ST_PATH}')


def FC_MAIN() -> None:
    PI_OS.makedirs(ZV_ST_OUTPUT_DIR, exist_ok=True)

    ZV_LI_DI_LFA1, ZV_LI_DI_LFB1, ZV_LI_DI_LFBK = FC_BUILD_VENDOR_MASTER()
    ZV_LI_DI_BSIK, ZV_LI_DI_BSAK, ZV_LI_DI_REGUH = FC_BUILD_DOCUMENTS(
        ZV_LI_DI_LFA1, ZV_LI_DI_LFB1, ZV_LI_DI_LFBK
    )

    FC_WRITE_TABLE('LFA1', ZV_LI_DI_LFA1)
    FC_WRITE_TABLE('LFB1', ZV_LI_DI_LFB1)
    FC_WRITE_TABLE('T001', ZV_LI_DI_COMPANY_CODES)
    FC_WRITE_TABLE('LFBK', ZV_LI_DI_LFBK)
    FC_WRITE_TABLE('BSIK', ZV_LI_DI_BSIK)
    FC_WRITE_TABLE('BSAK', ZV_LI_DI_BSAK)
    FC_WRITE_TABLE('REGUH', ZV_LI_DI_REGUH)
    FC_WRITE_TABLE('T005T', ZV_LI_DI_COUNTRIES)
    FC_WRITE_TABLE('T003T', ZV_LI_DI_DOC_TYPES)


if __name__ == '__main__':
    FC_MAIN()
