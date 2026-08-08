"""Shared visual theme for every Streamlit page in the application."""

import streamlit as st


def apply_dashboard_theme() -> None:
    """Inject the dashboard's shared CSS design system into the active page.

    The global colors are defined in ``.streamlit/config.toml``. This function
    adds component-level styling that Streamlit's theme configuration does not
    expose, including metric cards, navigation, buttons, chat, tables, tabs,
    focus states, and responsive spacing. It must be called after
    ``st.set_page_config`` on each page.
    """
    st.markdown(
        """
        <style>
        :root {
            --brand: #2dd4bf;
            --brand-strong: #14b8a6;
            --accent: #60a5fa;
            --surface: #111c2e;
            --surface-raised: #17243a;
            --border: #263650;
            --text: #e5eef8;
            --muted: #9fb0c5;
        }

        .stApp {
            background:
                radial-gradient(circle at 85% 0%, rgba(45, 212, 191, 0.07), transparent 26rem),
                #0b1220;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1280px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: -0.025em;
        }

        h1 {
            font-weight: 750;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stMarkdownContainer"] p {
            color: var(--muted);
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 0.55rem;
            margin: 0.12rem 0.65rem;
            transition: background-color 140ms ease, color 140ms ease;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: rgba(45, 212, 191, 0.10);
            color: var(--brand);
        }

        [data-testid="stMetric"] {
            min-height: 7.2rem;
            padding: 1rem 1.1rem;
            background: linear-gradient(145deg, var(--surface-raised), var(--surface));
            border: 1px solid var(--border);
            border-radius: 0.8rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted);
        }

        [data-testid="stMetricValue"] {
            color: var(--text);
            font-weight: 700;
        }

        .stButton > button, .stDownloadButton > button {
            border: 1px solid #34506b;
            border-radius: 0.6rem;
            font-weight: 600;
            transition: border-color 140ms ease, background-color 140ms ease,
                        transform 140ms ease;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: var(--brand);
            color: var(--brand);
            background: rgba(45, 212, 191, 0.08);
            transform: translateY(-1px);
        }

        .stButton > button[kind="primary"] {
            color: #06201c;
            background: var(--brand);
            border-color: var(--brand);
        }

        /* Streamlit renders button labels inside nested Markdown elements.
           Override the general muted paragraph color to preserve contrast. */
        .stButton > button[kind="primary"] *,
        .stButton > button[kind="primary"] p {
            color: #06201c !important;
        }

        .stButton > button:not([kind="primary"]) *,
        .stDownloadButton > button * {
            color: var(--text) !important;
        }

        .stButton > button:not([kind="primary"]):hover *,
        .stDownloadButton > button:hover * {
            color: var(--brand) !important;
        }

        .stButton > button:disabled,
        .stDownloadButton > button:disabled {
            opacity: 0.62;
            cursor: not-allowed;
            transform: none;
        }

        .stButton > button[kind="primary"]:disabled * {
            color: #173d38 !important;
        }

        div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stChatInput"] {
            background: var(--surface-raised);
            border-color: var(--border);
            border-radius: 0.65rem;
        }

        [data-testid="stChatMessage"] {
            background: rgba(17, 28, 46, 0.78);
            border: 1px solid var(--border);
            border-radius: 0.85rem;
            padding: 0.45rem 0.7rem;
            margin-bottom: 0.65rem;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            border-left: 3px solid var(--accent);
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            border-left: 3px solid var(--brand);
        }

        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            overflow: hidden;
        }

        [data-testid="stExpander"] {
            background: rgba(17, 28, 46, 0.65);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            border-bottom: 1px solid var(--border);
        }

        .stTabs [aria-selected="true"] {
            color: var(--brand);
        }

        hr {
            border-color: var(--border);
        }

        *:focus-visible {
            outline: 2px solid var(--brand) !important;
            outline-offset: 2px;
        }

        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                padding-top: 1.25rem;
            }
            [data-testid="stMetric"] {
                min-height: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
