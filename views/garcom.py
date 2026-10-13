# ==============================================================================
# VIEWS/GARCOM.PY - INTERFACE DO TERMINAL DE PEDIDOS
# ==============================================================================
import streamlit as st

def renderizar_terminal_garcom(empresa_id, senha_master):
    st.subheader("📱 Terminal Operacional (Garçom / Caixa)")
    st.write(f"Estabelecimento logado: **ID {empresa_id}**")
    
    # Adicione os recursos operacionais (Lançar pedidos, Carrinho, Mesas) aqui
    st.success("Terminal operacional pronto para uso.")
