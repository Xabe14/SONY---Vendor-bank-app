# Vendor bank app

Audit question: does Sony have vendors where the Sony company country, the vendor
country and the bank country are all three different?

Layout follows page 4 of the vendor bank app definition; tables, fields and join
path follow page 5. Streamlit patterns follow the 300Framework Streamlit chapter.

## Run

    pip install -r 00_CODE/requirements.txt
    cd 00_CODE
    streamlit run FC_VENDOR_BANK_APP.py

Then upload the nine files from `01_SANDBOX_DATA/` (drag them all in at once).
The app matches a file to a table by its file name, so `LFA1.txt` is read as LFA1.

## Or run it from GitHub Pages, with no server

`index.html` at the root of the project mounts the app with stlite, exactly as
described in the Streamlit chapter. Push the project, then open
Settings -> Pages -> Visit site. `FC_APP_CONFIG.ZV_BO_USE_WIDTH` is set to False
by index.html, because the browser build does not accept `width='stretch'`.

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
- On load, the app offers **Use saved data / Discard saved data** when a
  snapshot exists; **Start Over** clears it too.
- The snapshot is tagged with an app-version so old caches are never loaded.
- The stlite browser build (GitHub Pages) has no disk; it degrades gracefully —
  it simply has no snapshot and uploads fresh each time.

For AWS, install with `requirements-aws.txt` (adds `boto3`) and give the task
an IAM role allowing `s3:GetObject/PutObject/DeleteObject/HeadObject` on the
bucket. No hardcoded credentials — use the role / `AWS_PROFILE`.

## Not real data

The extracts in `01_SANDBOX_DATA` are generated, not from any SAP system. The
country coordinate lookup is also not from SAP and must be replaced by the lookup
already used by the existing supplier location chart.

## Still open

- Field list is DRAFT, pending 300Framework P01 (L03).
- REGUH-LAND1 to be verified in the system.
- Counting grain where a vendor holds several bank accounts: KPI 2 counts
  distinct vendors, not vendor-bank combinations.
- Treatment of blocked (SPERR) and deletion-flagged (LOEVM) vendors: both are
  currently carried into the population and shown as columns, not excluded.
