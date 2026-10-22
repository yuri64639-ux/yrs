    yuri64639-ux
    yrs

Repository navigation

    Code
    Issues
    Pull requests
    Agents
    Actions
    Projects
    Security and quality
    Insights
    Settings

    yrs

/
in
main

    Edit
    Preview

Indent mode
Indent size
Line wrap mode
Editing pedidos.py file contents
  1
  2
  3
  4
  5
  6
  7
  8
  9
 10
 11
 12
 13
 14
 15
 16
 17
 18
 19
 20
 21
 22
 23
 24
 25
 26
 27
 28
 29
 30
 31
 32
 33
 34
 35
 36
 37
 38
 39
 40
 41
 42
 43
 44
 45
 46
 47
 48
 49
 50
 51
 52
 53
 54
 55
 56
 57
 58
 59
 60
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time  

# Configuração de ambiente para dispositivos móveis e maquininhas
st.set_page_config(page_title="Frente de Caixa & Pedidos", layout="wide")

# INJEÇÃO DE CSS: Alvo direto no selo vermelho "Hosted with Streamlit" e barras nativas
st.markdown(
    """
    <style>
    /* 1. Oculta os botões superiores direito (share, star, 3 pontinhos) e cabeçalhos */
    div[data-testid="stToolbar"], [data-testid="stHeader"], header, #MainMenu {
        visibility: hidden !important;
        display: none !important;
        height: 0px !important;
    }
    
    /* 2. Oculta o botão/ícone de edição/deploy (Lápis) */
    .stAppDeployButton, button[title="View source code"], button[title="Edit this app"] {
        display: none !important;
    }
    
    /* 3. ALVO DEFINITIVO: REMOVE O RETÂNGULO VERMELHO DO "HOSTED WITH STREAMLIT" */
    .viewerBadge_container__1QSob, 
    .styles_viewerBadge__1yB5_, 
    .viewerBadge_link__1S137, 
    .viewerBadge_text__1JaDK,
    .viewerBadge_container__3664s,
    [data-testid="stStatusWidget"],
    div[class*="viewerBadge"],
    a[href*="streamlit.io"],
    .css-1jc7ptx, 
    .e1ewe7hr3 {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        width: 0px !important;
        pointer-events: none !important;
    }
    
    /* 4. Bloqueio genérico de rodapés estruturais */
    footer, .stAppViewFooter, .stFooter, [data-testid="stFooterBlock"], .stAppFooter, div[class^="st-emotion-cache"] footer {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        padding: 0px !important;
    }
    
    /* Ajusta o espaçamento do topo para compensar a remoção do cabeçalho */
    .main .block-container {
        padding-top: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
