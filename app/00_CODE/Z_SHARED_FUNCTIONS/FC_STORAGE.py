"""Snapshot storage abstraction for the vendor bank app.

Persists raw uploads + parsed tables + analysis results so the app can restore
state after a page reload, a server restart, or a container replacement.

Backends, in priority order:
  1. S3  — enabled only when the env var VB_S3_BUCKET is set (AWS deploy).
          boto3 is imported lazily so local runs never need it installed.
  2. Local disk under <repo_root>/.cache/vb/ — always available as fallback.

Any S3 failure degrades silently to local disk, so the app keeps working even
when the bucket is unreachable. The snapshot carries an app-version tag so a
cache written by an older UI version is never loaded back.
"""

import os
import pickle
from pathlib import Path

ZV_ST_SNAPSHOT_VERSION = '2026-08-31'  # bump when the snapshot format changes
ZV_ST_SNAPSHOT_FILENAME = 'snapshot.pkl'

ZV_ST_ROOT = Path(__file__).resolve().parent.parent.parent  # <repo_root>
ZV_OB_CACHE_DIR = ZV_ST_ROOT / '.cache' / 'vb'
ZV_OB_LOCAL_SNAPSHOT = ZV_OB_CACHE_DIR / ZV_ST_SNAPSHOT_FILENAME

ZV_ST_S3_BUCKET = os.environ.get('VB_S3_BUCKET', '').strip()
ZV_ST_S3_PREFIX = 'vendor-bank-app'


def _get_boto3():
    """Lazily import boto3; returns None when not installed/configured."""
    try:
        import boto3  # noqa: PLC0415
        return boto3
    except Exception:
        return None


def _s3_key():
    return f'{ZV_ST_S3_PREFIX}/{ZV_ST_SNAPSHOT_VERSION}/{ZV_ST_SNAPSHOT_FILENAME}'


def FC_SNAPSHOT_EXISTS() -> bool:
    """True when a usable snapshot is present on any backend."""
    if ZV_ST_S3_BUCKET:
        try:
            ZV_OB_BOTO = _get_boto3()
            if ZV_OB_BOTO is not None:
                ZV_OB_S3 = ZV_OB_BOTO.client('s3')
                ZV_OB_S3.head_object(Bucket=ZV_ST_S3_BUCKET, Key=_s3_key())
                return True
        except Exception:
            pass  # S3 unavailable -> fall through to local disk
    return ZV_OB_LOCAL_SNAPSHOT.exists()


def FC_SNAPSHOT_LOAD():
    """Return (tables_dict, results_dict, status_str) or (None, None, None)."""
    ZV_OB_PAYLOAD = None
    if ZV_ST_S3_BUCKET:
        try:
            ZV_OB_BOTO = _get_boto3()
            if ZV_OB_BOTO is not None:
                ZV_OB_S3 = ZV_OB_BOTO.client('s3')
                ZV_OB_RESPONSE = ZV_OB_S3.get_object(
                    Bucket=ZV_ST_S3_BUCKET, Key=_s3_key()
                )
                ZV_OB_PAYLOAD = pickle.loads(
                    ZV_OB_RESPONSE['Body'].read()
                )
        except Exception:
            ZV_OB_PAYLOAD = None  # fall back to local disk
    if ZV_OB_PAYLOAD is None and ZV_OB_LOCAL_SNAPSHOT.exists():
        try:
            with ZV_OB_LOCAL_SNAPSHOT.open('rb') as ZV_OB_FILE:
                ZV_OB_PAYLOAD = pickle.load(ZV_OB_FILE)
        except Exception:
            ZV_OB_PAYLOAD = None
    if not isinstance(ZV_OB_PAYLOAD, dict):
        return None, None, None
    if ZV_OB_PAYLOAD.get('VERSION') != ZV_ST_SNAPSHOT_VERSION:
        return None, None, None
    return (ZV_OB_PAYLOAD.get('TABLES'),
            ZV_OB_PAYLOAD.get('RESULTS'),
            ZV_OB_PAYLOAD.get('STATUS', 'not_started'))


def FC_SNAPSHOT_SAVE(ZVFCI_DI_TABLES, ZVFCI_DI_RESULTS,
                     ZVFCI_ST_STATUS: str) -> None:
    """Persist current state. Failures are logged to stderr, never raised."""
    ZV_OB_PAYLOAD = {
        'VERSION': ZV_ST_SNAPSHOT_VERSION,
        'TABLES': ZVFCI_DI_TABLES,
        'RESULTS': ZVFCI_DI_RESULTS,
        'STATUS': ZVFCI_ST_STATUS,
    }
    ZV_BY_PICKLE = pickle.dumps(ZV_OB_PAYLOAD)

    if ZV_ST_S3_BUCKET:
        try:
            ZV_OB_BOTO = _get_boto3()
            if ZV_OB_BOTO is not None:
                ZV_OB_S3 = ZV_OB_BOTO.client('s3')
                ZV_OB_S3.put_object(
                    Bucket=ZV_ST_S3_BUCKET, Key=_s3_key(),
                    Body=ZV_BY_PICKLE,
                )
                return
        except Exception as ZV_EXC:
            print(f'[FC_STORAGE] S3 save failed, using local disk: {ZV_EXC}')

    try:
        ZV_OB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with ZV_OB_LOCAL_SNAPSHOT.open('wb') as ZV_OB_FILE:
            ZV_OB_FILE.write(ZV_BY_PICKLE)
    except Exception as ZV_EXC:
        print(f'[FC_STORAGE] local snapshot save failed: {ZV_EXC}')


def FC_SNAPSHOT_CLEAR() -> None:
    """Delete the snapshot from every backend. Failures are ignored."""
    if ZV_ST_S3_BUCKET:
        try:
            ZV_OB_BOTO = _get_boto3()
            if ZV_OB_BOTO is not None:
                ZV_OB_S3 = ZV_OB_BOTO.client('s3')
                ZV_OB_S3.delete_object(Bucket=ZV_ST_S3_BUCKET, Key=_s3_key())
        except Exception as ZV_EXC:
            print(f'[FC_STORAGE] S3 snapshot clear failed: {ZV_EXC}')
    try:
        if ZV_OB_LOCAL_SNAPSHOT.exists():
            ZV_OB_LOCAL_SNAPSHOT.unlink()
    except Exception as ZV_EXC:
        print(f'[FC_STORAGE] local snapshot clear failed: {ZV_EXC}')


def FC_STORAGE_BACKEND_LABEL() -> str:
    """Human label of the active backend, for the restore notice."""
    if ZV_ST_S3_BUCKET:
        return f'S3 ({ZV_ST_S3_BUCKET})'
    return 'local disk'
