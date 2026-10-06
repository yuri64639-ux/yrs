import streamlit as st
import time
import random

# Configuração da página
st.set_page_config(page_title="Custom Custom Racing", page_icon="🏎️", layout="centered")

st.title("🏎️ Oficina & Simulador de Corrida")
st.markdown("Monte seu carro na oficina, escolha as melhores peças e teste o desempenho nas pistas!")

# Inicializar estados do jogo
if "corrida_iniciada" not in st.session_state:
    st.session_state.corrida_iniciada = False

# --- FASE 1: A OFICINA ---
st.header("🛠️ 1. Monte seu Carro")

col1, col2 = st.columns(2)

with col1:
    # Escolha da Cor (Visual)
    cor = st.color_picker("Escolha a cor da pintura:", "#FF0000")
    
    # Escolha do Motor (Afeta Velocidade Máxima)
    motor = st.selectbox(
        "Escolha o Motor:",
        ["1.0 Econômico (Confiável, mas lento)", "2.0 Turbo (Equilibrado)", "V8 Nitro (Muito rápido, mas instável)"]
    )

with col2:
    # Escolha dos Pneus (Afeta Tração/Estabilidade)
    pneus = st.selectbox(
        "Tipo de Pneu:",
        ["Pneus de Rua (Padrão)", "Pneus Slick (Ótimos para asfalto seco)", "Pneus de Chuva (Muita aderência)"]
    )
    
    # Escolha da Pista
    pista = st.radio(
        "Escolha o circuito:",
        ["☀️ Reta de Interlagos (Asfalto Seco)", "🌧️ Circuito de Mônaco (Chuva e Curvas)"]
    )

# --- LÓGICA DE ATRIBUTOS ---
# Definindo velocidade e estabilidade com base nas escolhas
if "1.0" in motor:
    vel_base = 5
    quebra_chance = 0.02
elif "2.0" in motor:
    vel_base = 10
    quebra_chance = 0.05
else:  # V8 Nitro
    vel_base = 18
    quebra_chance = 0.15  # Mais chance de dar problema

# Modificadores de pneu baseados na pista
modificador_pneu = 1.0
if "Interlagos" in pista:
    if "Slick" in pneus:
        modificador_pneu = 1.3  # Bônus excelente
    elif "Chuva" in pneus:
        modificador_pneu = 0.8  # Pneu de chuva no seco perde rendimento
else:  # Mônaco com Chuva
    if "Chuva" in pneus:
        modificador_pneu = 1.4  # Bônus essencial para chuva
    elif "Slick" in pneus:
        modificador_pneu = 0.4  # Desastre na chuva
        quebra_chance += 0.10   # Chance de rodar na pista

# --- FASE 2: A CORRIDA ---
st.markdown("---")
st.header("🏁 2. Hora de Correr!")

# Mostrar o "Preview" do carro customizado usando HTML simples
st.markdown(
    f"""
    <div style="text-align: center; padding: 10px; border-radius: 10px; background-color: #262730;">
        <span style="font-size: 50px; color: {cor};">🏎️</span>
        <p style="margin: 0; font-weight: bold;">Seu Bólido Customizado pronto para o grid!</p>
    </div>
    """,
    unsafe_allow_html=True
)

if st.button("🔥 LARGADA!", type="primary"):
    st.session_state.corrida_iniciada = True
    
    distancia = 0
    meta = 100
    tempo_decorrido = 0.0
    
    progresso_barra = st.progress(0)
    status_texto = st.empty()
    logs_corrida = st.empty()
    
    historico_logs = ["🟢 Luzes verdes! Dada a largada!"]
    
    while distancia < meta:
        time.sleep(0.3)  # Delay para animação
        tempo_decorrido += 0.3
        
        # Calcular avanço da rodada
        sorte_rodada = random.uniform(0.7, 1.3)
        passo = vel_base * modificador_pneu * sorte_rodada
        
        # Evento aleatório de quebra ou rodada
        if random.random() < quebra_chance:
            if "V8" in motor and random.random() > 0.5:
                historico_logs.append("⚠️ O motor V8 superaqueceu! Você teve que desacelerar!")
                passo = passo * 0.2
            elif "Slick" in pneus and "Chuva" in pista:
                historico_logs.append("↪️ Seu pneu Slick derrapou na pista molhada! Perda de controle!")
                passo = 0
            else:
                historico_logs.append("🔧 Problemas mecânicos leves box-to-box!")
                passo = passo * 0.5
        
        distancia += passo
        if distancia > meta:
            distancia = meta
            
        # Atualizar interface dinamicamente
        progresso_barra.progress(int((distancia / meta) * 100))
        status_texto.markdown(f"**Distância percorrida:** {distancia:.1f}m / {meta}m")
        
        # Exibir os últimos acontecimentos
        if len(historico_logs) > 3:
            exibir_logs = historico_logs[-3:]
        else:
            exibir_logs = historico_logs
            
        logs_corrida.info("\n".join(exibir_logs))
        
    st.success(f"🏁 **Linha de Chegada!** Você completou o circuito em **{tempo_decorrido:.1f} segundos**!")
    st.balloons()
