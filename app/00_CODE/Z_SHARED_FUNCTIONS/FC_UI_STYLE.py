"""UI style and layout helpers shared by every Streamlit file in this app.

Presentation layer only: one injectable stylesheet plus small render helpers
(hero, section headers, status pills). This module never touches analysis
logic, data or export. It is safe to import from the stlite browser build: no
external resource is fetched (system font stack), and every rule rides on
stable Streamlit DOM selectors so the app looks the same on the local server
and on GitHub Pages.
"""

import streamlit as PI_STREAMLIT

# ------------------------------------------------------------------ brand
# Keep in sync with .streamlit/config.toml (local server theme).
ZV_ST_COLOR_PRIMARY = '#2563EB'
ZV_ST_COLOR_PRIMARY_DARK = '#1E40AF'
ZV_ST_COLOR_ACCENT = '#0EA5E9'
ZV_ST_COLOR_SURFACE = '#FFFFFF'
ZV_ST_COLOR_SURFACE_SOFT = '#F1F5F9'
ZV_ST_COLOR_TEXT = '#0F172A'
ZV_ST_COLOR_MUTED = '#64748B'
ZV_ST_COLOR_SUCCESS = '#16A34A'
ZV_ST_COLOR_WARNING = '#D97706'
ZV_ST_COLOR_DANGER = '#DC2626'

ZV_ST_CSS_TEMPLATE = """
<style>
/* ------------------------------------------------------------ base */
html, body, [data-testid="stAppViewContainer"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, "Noto Sans", sans-serif;
}
[data-testid="stAppViewContainer"] { color: __TEXT__; }
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    padding-left: 2.2rem;
    padding-right: 2.2rem;
    max-width: 1280px;
}

/* ------------------------------------------------------------ hero */
.zv-hero {
    background: linear-gradient(120deg, __PRIMARY_DARK__ 0%,
                                __PRIMARY__ 55%, __ACCENT__ 130%);
    color: #FFFFFF;
    border-radius: 18px;
    padding: 1.6rem 1.8rem 1.5rem;
    margin-bottom: 1.4rem;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.28);
}
.zv-hero-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: #FFFFFF;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-radius: 999px;
    padding: 0.22rem 0.7rem;
    margin-bottom: 0.6rem;
}
.zv-hero h1 {
    margin: 0;
    padding: 0;
    color: #FFFFFF;
    font-size: 1.7rem;
    line-height: 1.2;
    font-weight: 700;
}
.zv-hero-sub {
    margin: 0.4rem 0 0;
    color: rgba(255, 255, 255, 0.85);
    font-size: 0.95rem;
    line-height: 1.5;
}

/* ------------------------------------------------------- section head */
.zv-section { display: flex; align-items: center; gap: 0.6rem;
              flex-wrap: wrap; margin: 1.4rem 0 0.2rem; }
.zv-section-badge {
    background: linear-gradient(120deg, __PRIMARY__ 0%, __ACCENT__ 100%);
    color: #FFFFFF;
    font-size: 0.85rem;
    font-weight: 700;
    min-width: 1.7rem;
    text-align: center;
    border-radius: 9px;
    padding: 0.28rem 0.45rem;
    box-shadow: 0 3px 8px rgba(37, 99, 235, 0.3);
}
.zv-section-title {
    margin: 0; padding: 0;
    color: __TEXT__;
    font-size: 1.18rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}
.zv-section-sub {
    flex-basis: 100%;
    margin: 0.1rem 0 0 2.3rem;
    color: __MUTED__;
    font-size: 0.85rem;
}

/* ------------------------------------------------------------ sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, __PRIMARY_DARK__ 0%,
                                #123A8F 55%, #0E2F73 100%);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: rgba(255, 255, 255, 0.92);
}
.zv-sidebar-brand { padding-top: 0.2rem; }
.zv-sidebar-brand h3 {
    color: #FFFFFF; margin: 0; padding: 0;
    font-size: 1.1rem; font-weight: 700;
}
.zv-sidebar-brand p {
    color: rgba(255, 255, 255, 0.75);
    font-size: 0.82rem; margin: 0.15rem 0 0;
}
[data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, 0.22); }

/* sidebar controls on the dark panel */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 8px;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: rgba(255, 255, 255, 0.85);
}
.zv-pill {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 600;
    border-radius: 999px;
    padding: 0.22rem 0.75rem;
    margin: 0.2rem 0;
}
.zv-pill-neutral { background: rgba(255,255,255,0.16); color: #E2E8F0;
                   border: 1px solid rgba(255,255,255,0.3); }
.zv-pill-ok    { background: rgba(22,163,74,0.18); color: #86EFAC;
                 border: 1px solid rgba(74,222,128,0.5); }
.zv-pill-warn  { background: rgba(217,119,6,0.18);  color: #FCD34D;
                 border: 1px solid rgba(252,211,77,0.5); }
.zv-pill-err   { background: rgba(220,38,38,0.18);  color: #FCA5A5;
                 border: 1px solid rgba(252,165,165,0.5); }
.zv-sidebar-footer {
    margin-top: 1.2rem;
    padding-top: 0.8rem;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.65);
    font-size: 0.78rem;
}

/* ------------------------------------------------------- KPI metrics */
[data-testid="stMetric"] {
    background: __SURFACE__;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 0.9rem 1rem 0.7rem;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05);
    border-top: 4px solid __PRIMARY__;
}
[data-testid="stMetricLabel"] p {
    color: __MUTED__;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
[data-testid="stMetricValue"] {
    color: __TEXT__;
    font-size: 1.55rem;
    font-weight: 700;
}

/* ------------------------------------------------ bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: __SURFACE__;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    padding: 0.4rem 1rem 1rem;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] {
    color: __TEXT__;
}

/* equal-height cards: bordered containers inside a column row stretch to the
   tallest sibling (used by the 1.1 / 1.2 / 1.3 input cards). Only border
   wrappers are affected; metric rows, maps and buttons keep natural height. */
[data-testid="stHorizontalBlock"] > div {
    display: flex;
    flex-direction: column;
}
[data-testid="stHorizontalBlock"] > div > [data-testid="stVerticalBlockBorderWrapper"] {
    flex: 1 1 0%;
}

/* --------------------------------------------------------------- buttons */
.stButton > button,
[data-testid="stBaseButton-primary"] {
    border-radius: 10px;
    font-weight: 600;
    padding: 0.45rem 1.1rem;
    transition: transform 0.06s ease, box-shadow 0.15s ease;
}
.stButton > button:hover,
[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-1px);
}
[data-testid="stBaseButton-secondary"] {
    border-radius: 10px;
    font-weight: 600;
}

/* --------------------------------------------------------------- tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.35rem;
    background: __SURFACE_SOFT__;
    padding: 0.35rem;
    border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    padding: 0.4rem 1rem;
    font-weight: 600;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: __PRIMARY__;
    border-radius: 9px;
}
.stTabs [data-baseweb="tab"]:not([aria-selected="true"]) { color: __MUTED__; }

/* ------------------------------------------------------------ expander */
[data-testid="stExpander"] {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    background: __SURFACE__;
}
[data-testid="stExpander"] summary { font-weight: 600; color: __TEXT__; }

/* ------------------------------------------------------------ dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    overflow: hidden;
}

/* ------------------------------------------------------------- uploader */
[data-testid="stFileUploaderDropzone"] {
    border-radius: 12px;
    border: 1px dashed #C7D2FE !important;
    background: #EFF4FF;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: __PRIMARY__ !important;
    background: #E6EEFF;
}

/* ------------------------------------------------------------ messages */
[data-testid="stAlert"] { border-radius: 12px; border: none; }

/* ---------------------------------------------------- responsive */
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
    }
    .zv-hero { padding: 1.1rem 1.2rem 1rem; }
    .zv-hero h1 { font-size: 1.3rem; }
    .zv-hero-sub { font-size: 0.85rem; }
    .zv-section-title { font-size: 1.02rem; }
    .zv-section-sub { margin-left: 0; }
    /* stack Streamlit columns on small screens */
    [data-testid="stHorizontalBlock"] { flex-direction: column; }
    [data-testid="stHorizontalBlock"] > div {
        width: 100% !important;
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }
    [data-testid="stMetricValue"] { font-size: 1.3rem; }
}

/* ----------------------------------------------------- dark mode overrides
   The local server enforces a light theme via config.toml; the stlite
   browser build follows the OS, so keep surfaces readable there too. */
@media (prefers-color-scheme: dark) {
    [data-testid="stAppViewContainer"] { color: #E2E8F0; }
    [data-testid="stMetric"],
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"] {
        background: #1E293B;
        border-color: #334155;
    }
    [data-testid="stMetricLabel"] p { color: #94A3B8; }
    [data-testid="stMetricValue"] { color: #F1F5F9; }
    .zv-section-title { color: #F1F5F9; }
    .zv-section-sub { color: #94A3B8; }
    .stTabs [data-baseweb="tab-list"] { background: #1E293B; }
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]) { color: #94A3B8; }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] {
        color: #E2E8F0;
    }
}
</style>
"""

ZV_ST_CSS = (
    ZV_ST_CSS_TEMPLATE
    .replace('__PRIMARY__', ZV_ST_COLOR_PRIMARY)
    .replace('__PRIMARY_DARK__', ZV_ST_COLOR_PRIMARY_DARK)
    .replace('__ACCENT__', ZV_ST_COLOR_ACCENT)
    .replace('__SURFACE__', ZV_ST_COLOR_SURFACE)
    .replace('__SURFACE_SOFT__', ZV_ST_COLOR_SURFACE_SOFT)
    .replace('__TEXT__', ZV_ST_COLOR_TEXT)
    .replace('__MUTED__', ZV_ST_COLOR_MUTED)
    .replace('__SUCCESS__', ZV_ST_COLOR_SUCCESS)
    .replace('__WARNING__', ZV_ST_COLOR_WARNING)
    .replace('__DANGER__', ZV_ST_COLOR_DANGER)
)


def FC_INJECT_CSS() -> None:
    """Inject the shared stylesheet once. Call at the top of the app."""
    PI_STREAMLIT.markdown(ZV_ST_CSS, unsafe_allow_html=True)


def FC_HERO(ZVFCI_ST_TITLE: str,
            ZVFCI_ST_SUBTITLE: str = None,
            ZVFCI_ST_BADGE: str = None) -> None:
    """Page hero: gradient banner with title, subtitle and an optional badge."""
    ZV_ST_BADGE = (
        f'<span class="zv-hero-badge">{ZVFCI_ST_BADGE}</span>'
        if ZVFCI_ST_BADGE else ''
    )
    ZV_ST_SUB = (
        f'<p class="zv-hero-sub">{ZVFCI_ST_SUBTITLE}</p>'
        if ZVFCI_ST_SUBTITLE else ''
    )
    PI_STREAMLIT.markdown(
        f'<div class="zv-hero">{ZV_ST_BADGE}<h1>{ZVFCI_ST_TITLE}</h1>'
        f'{ZV_ST_SUB}</div>',
        unsafe_allow_html=True,
    )


def FC_SECTION_HEADER(ZVFCI_ST_NUMBER: str,
                      ZVFCI_ST_TITLE: str,
                      ZVFCI_ST_SUBTITLE: str = None) -> None:
    """Consistent section heading: numbered badge + title + optional note."""
    ZV_ST_SUB = (
        f'<p class="zv-section-sub">{ZVFCI_ST_SUBTITLE}</p>'
        if ZVFCI_ST_SUBTITLE else ''
    )
    PI_STREAMLIT.markdown(
        f'<div class="zv-section"><span class="zv-section-badge">'
        f'{ZVFCI_ST_NUMBER}</span>'
        f'<h2 class="zv-section-title">{ZVFCI_ST_TITLE}</h2>'
        f'{ZV_ST_SUB}</div>',
        unsafe_allow_html=True,
    )


def FC_STATUS_PILL(ZVFCI_ST_TEXT: str, ZVFCI_ST_TONE: str = 'neutral') -> None:
    """Small status pill for the sidebar. Tones: neutral / ok / warn / err."""
    ZV_ST_TONE = {
        'ok': 'zv-pill-ok',
        'warn': 'zv-pill-warn',
        'err': 'zv-pill-err',
    }.get(ZVFCI_ST_TONE, 'zv-pill-neutral')
    PI_STREAMLIT.markdown(
        f'<span class="zv-pill {ZV_ST_TONE}">{ZVFCI_ST_TEXT}</span>',
        unsafe_allow_html=True,
    )
