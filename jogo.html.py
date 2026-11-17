import pathlib
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Top Gear: Horizonte Turbo", layout="centered")
html_jogo = (pathlib.Path(__file__).parent / "jogo.html").read_text(encoding="utf-8")
components.html(html_jogo, height=600)
