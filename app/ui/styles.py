import streamlit as st

def apply_custom_css():
    st.markdown('''
    <style>
        :root {
            --primary: #7b1fa2;
            --primary-dark: #4a148c;
            --secondary: #9c27b0;
            --background: #f8f9fa;
            --surface: #ffffff;
            --text: #2c3e50;
            --border: #e2e8f0;
        }
        .stApp {
            background-color: var(--background);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        /* Top Navigation Header Styling */
        div[data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }
        /* Cards de Métricas */
        div[data-testid="metric-container"] {
            background-color: var(--surface);
            border: 1px solid var(--border);
            padding: 1.25rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
            border-top: 4px solid var(--primary);
        }
        /* Botões */
        .stButton>button {
            background: linear-gradient(135deg, #7b1fa2 0%, #6a1b9a 100%) !important;
            color: white !important;
            border-radius: 6px;
            border: none;
            padding: 0.55rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            box-shadow: 0 4px 12px rgba(123, 31, 162, 0.35) !important;
            transform: translateY(-1px);
        }
        /* Tabs corporativas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 16px;
            border-bottom: 2px solid #ede7f6;
        }
        .stTabs [data-baseweb="tab"] {
            height: 48px;
            font-weight: 600;
            color: #64748b;
        }
        .stTabs [aria-selected="true"] {
            color: var(--primary) !important;
            border-bottom: 3px solid var(--primary) !important;
        }
        h1, h2, h3 {
            color: var(--primary-dark) !important;
            font-weight: 700;
        }
        /* Tabelas */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 8px;
            background: #fff;
        }
    </style>
    ''', unsafe_allow_html=True)
