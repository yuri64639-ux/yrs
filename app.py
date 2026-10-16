import os
import sys
import pandas as pd
import streamlit as st
from datetime import datetime

# =====================================================================
# SISTEMA DE CAMINHOS ROBUSTO PARA RESOLVER O MODULENOTFOUNDERROR
# =====================================================================
# Captura o diretório onde o arquivo app.py está fisicamente localizado
raiz_projeto = os.path.dirname(os.path.abspath(__file__))

# Força o Python a priorizar a raiz do projeto na busca por módulos locais
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

# =====================================================================
# IMPORTS DO SEU SISTEMA (Agora o Python localizará os caminhos corretamente)
# =====================================================================
from core.database import inicializar_banco, ob_cx                      
from views.garcom_login import renderizar_terminal_garcom               
from views.caixa import renderizar_fechamento_caixa                     
from views.gerencia import renderizar_painel_gerencial                  

# ---------------------------------------------------------------------
# O restante do seu código (configurações da página, tabelas, etc.)
# continua idêntico abaixo, sem alterações...
# ---------------------------------------------------------------------
