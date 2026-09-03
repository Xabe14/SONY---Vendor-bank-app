# Vendor bank app

Audit question: does Sony have vendors where the Sony company country, the vendor
country and the bank country are all three different?

Layout follows page 4 of the vendor bank app definition; tables, fields and join
path follow page 5. Streamlit patterns follow the 300Framework Streamlit chapter.

## Run (local machine)

Requires **Python 3.10+** and **Git** (optional, for cloning). On Windows use
`python` from the Python.org installer; on macOS/Linux use your system python.

```bash
# 1. clone / open the project, then create a virtual environment
python -m venv .venv

# 2. activate it
#    Windows (Git Bash / CMD):
#      .venv\Scripts\activate
#    Windows (PowerShell):
#      .venv\Scripts\Activate.ps1
#    macOS / Linux:
#      source .venv/bin/activate

# 3. install dependencies
pip install -r app/00_CODE/requirements.txt

# 4. run the app (from the repo root)
streamlit run app/00_CODE/FC_VENDOR_BANK_APP.py
```

Then open http://localhost:8501 in your browser and drag the **nine `.txt`
files** from `01_SANDBOX_DATA/` into the uploader (drag them all in at once).
The app matches a file to a table by its file **stem**: `LFA1.txt` is read as
table LFA1, `BSAK.txt` as BSAK, and so on.

## Or run it from GitHub Pages, with no server

`app/index.html` mounts the app with stlite, exactly as described in the
Streamlit chapter; a redirect `index.html` at the repo root sends GitHub Pages
visitors there. Push the project, then open Settings -> Pages -> Visit site.
`FC_APP_CONFIG.ZV_BO_USE_WIDTH` is set to False by index.html, because the
browser build does not accept `width='stretch'`.

## Regenerate the sandbox data

    cd 00_CODE
    python FC_GENERATE_SANDBOX_DATA.py

420 vendors, of which roughly 20% are built as three-country exceptions. About 6%
of settlements are paid to an account that is not on the vendor master, and BVTYP
is blank on about 72% of bank records — which is why it must never be a join key.

## Join path

    LFA1.LIFNR                    = LFB1.LIFNR                  vendor to company code
    LFB1.BUKRS                    = T001.BUKRS                  company code to Sony country
    LFA1.LIFNR                    = LFBK.LIFNR                  vendor to bank country
    BSIK / BSAK .LIFNR + .BUKRS   = LFB1 .LIFNR + .BUKRS        transactions to vendor
    REGUH .LIFNR + .ZBUKR         = LFB1 .LIFNR + .BUKRS        settlements to vendor
    REGUH .LIFNR + .ZBNKN         = LFBK .LIFNR + .BANKN        payee account to registered account
    LFA1.LAND1, T001.LAND1, LFBK.BANKS = T005T.LAND1            country descriptions
    BSIK / BSAK .BLART            = T003T.BLART                 document type description

The payee account comparison is a left join on purpose: payments to an account
that is not on the vendor master are the exceptions, so they are kept, not
dropped. LFBK is stored at client level and carries no BUKRS.

## Shared functions

Every reusable object goes through `Z_SHARED_FUNCTIONS`, per the standard:

    FC_IMPORT_TEXT                    read a tab-delimited file or upload
    FC_FILE_UPLOADER                  file_uploader wrapper
    FC_GET_SELECTION_VALUE            read a Vega-Lite chart selection
    FC_FILTER_BY_CATEGORY_SELECTION   filter a DataFrame on that selection
    FC_GET_EXCEL_BYTES                DataFrame to xlsx bytes
    FC_DOWNLOAD_BUTTON                download_button wrapper
    FC_COUNTRY_COORDINATES            country centroids for the map graphs
    FC_UI_STYLE                       stylesheet + hero / section / status pills
    FC_STORAGE                        snapshot persistence (local disk / S3)
    FC_TYPECAST                       numeric column casting + data-quality warnings

## UI

The presentation layer is themeable and responsive:

- Local server: `.streamlit/config.toml` sets the light bank-blue theme.
- Browser build (stlite): no `config.toml`, so `FC_UI_STYLE` follows the OS
  theme and ships dark-mode overrides as well.
- All colours live in one place: the constants at the top of
  `Z_SHARED_FUNCTIONS/FC_UI_STYLE.py`. Change a colour there (and in
  `config.toml` if you want the local theme to match) and the whole app follows.
- Layout is responsive: Streamlit columns stack on narrow screens via the
  `@media (max-width: 768px)` rules in the same file.

Analysis logic, join path and export are untouched by the UI layer.

## Storage (persist across reload / restart)

`Z_SHARED_FUNCTIONS/FC_STORAGE.py` saves a snapshot of the uploaded tables and
analysis results so the app can restore state after a page reload, a server
restart or a container replacement.

- **Local runs** store to `.cache/vb/snapshot.pkl` under the repo root.
- **AWS deploys** set `VB_S3_BUCKET=<bucket>` and the snapshot goes to
  `s3://<bucket>/vendor-bank-app/<version>/snapshot.pkl` via `boto3`. Any S3
  failure degrades silently to the local-disk cache.
- On load, a saved snapshot is **restored automatically** so reloading the page
  keeps the data; **Start Over** clears it too.
- The snapshot is tagged with an app-version so old caches are never loaded.
- **Encryption (optional but recommended for real data):** set `VB_SNAPSHOT_KEY`
  to a Fernet key (`python -c "from cryptography.fernet import Fernet;
  print(Fernet.generate_key().decode())"`) and the snapshot is encrypted at
  rest on disk and in S3. Without it the app logs a loud warning that the
  snapshot is NOT encrypted. `cryptography` ships in `requirements-aws.txt`.
- The stlite browser build (GitHub Pages) has no disk; it degrades gracefully —
  it simply has no snapshot and uploads fresh each time.

For AWS, install with `requirements-aws.txt` (adds `boto3` and `cryptography`)
and give the task an IAM role allowing `s3:GetObject/PutObject/DeleteObject/
HeadObject` on the bucket. No hardcoded credentials — use the role / `AWS_PROFILE`.

## Data hardening (real SAP data)

The parser and validators are defensive by design:

- `FC_IMPORT_TEXT` auto-detects the **separator** (tab/comma/semicolon/pipe)
  and **encoding** (utf-8-sig/utf-8/cp1252/latin-1); decoding never silently
  replaces unknown bytes with U+FFFD.
- `FC_READ_UPLOADS` reports failed files loudly with the reason, and returns a
  **sha256 fingerprint** of every accepted file (shown in section 1.4 and in
  the run metadata under 2.3 for auditability).
- `FC_TYPECAST` casts `WRBTR` amounts to numeric and reports any unparsable
  value (count + example) as a data-quality warning before Run Analysis.
- `FC_CHECK_TABLE_WARNINGS` flags empty tables, blank `LIFNR`/`BUKRS` keys, and
  row counts above 2M (performance red flag).
- The KPI/map/join logic is untouched: hardening only adds warnings and clearer
  failures, never changes the numbers.

## Not real data

The extracts in `01_SANDBOX_DATA` are generated, not from any SAP system. The
country coordinate lookup is also not from SAP and must be replaced by the lookup
already used by the existing supplier location chart.

