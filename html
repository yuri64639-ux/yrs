import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Mundo dos Controles - EM Pato Donald",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Esconde o menu superior e margens do Streamlit para o jogo ocupar a tela toda
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        iframe {
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
            display: block !important;
        }
    </style>
""", unsafe_allow_html=True)

codigo_jogo = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * { box-sizing: border-box; }
        body, html {
            margin: 0; padding: 0; width: 100%; height: 100vh;
            font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
            overflow: hidden; user-select: none; transition: background 1s ease;
        }
        #cenario {
            width: 100%; height: 100%; display: flex; flex-direction: column;
            justify-content: space-between; align-items: center; padding: 10px 10px 15px 10px;
        }
        .escola { background: linear-gradient(to bottom, #87CEFA 55%, #F4A460 55%, #2E8B57 85%); }
        .floresta { background: linear-gradient(to bottom, #87CEEB 60%, #228B22 40%); }
        .espaco { background: radial-gradient(circle, #1B2735 0%, #090A0F 100%); color: white; }
        .oceano { background: linear-gradient(to bottom, #00BFFF 20%, #000080 80%); color: white; }
        .doces { background: linear-gradient(to bottom, #FFB6C1 60%, #FF69B4 40%); }

        #topo { display: flex; flex-direction: column; align-items: center; width: 100%; }
        #placa-escola {
            display: block; background: #FFD700; color: #003366; border: 3px solid #003366;
            padding: 6px 15px; border-radius: 12px; font-size: clamp(14px, 3vw, 20px);
            font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2); text-align: center; max-width: 95%;
        }
        #ceu { font-size: clamp(40px, 8vh, 65px); margin-top: 5px; cursor: pointer; transition: transform 0.3s; }
        #ceu:hover { transform: scale(1.15); }
        #personagem { font-size: clamp(60px, 14vh, 95px); cursor: pointer; transition: all 0.4s ease; z-index: 2; line-height: 1; }
        #chao { font-size: clamp(35px, 7vh, 55px); display: flex; justify-content: center; gap: clamp(15px, 4vw, 35px); width: 100%; }
        #painel {
            background: rgba(255, 255, 255, 0.95); padding: 10px 15px; border-radius: 25px;
            box-shadow: 0 6px 15px rgba(0,0,0,0.3); display: flex; flex-wrap: wrap;
            justify-content: center; gap: 8px; z-index: 10; width: 95%; max-width: 750px;
        }
        button {
            font-size: clamp(13px, 2.2vw, 17px); padding: 8px 12px; border: none; border-radius: 15px;
            cursor: pointer; font-weight: bold; transition: transform 0.2s; box-shadow: 0 3px 5px rgba(0,0,0,0.1);
        }
        button:hover { transform: scale(1.05); }
        .btn-escola { background: #1E90FF; color: #FFF; border: 2px solid #FFD700; }
        .btn-floresta { background: #90EE90; color: #006400; }
        .btn-espaco { background: #4B0082; color: #FFF; }
        .btn-oceano { background: #00CED1; color: #00008B; }
        .btn-doces { background: #FF1493; color: #FFF; }
        .btn-clima { background: #FFD700; color: #333; }
    </style>
</head>
<body>
<div id="cenario" class="escola">
    <div id="topo">
        <div id="placa-escola">🏫 EM Pato Donald - São José do Rio Preto</div>
        <div id="ceu" onclick="mudarClima()">☀️</div>
    </div>
    <div id="personagem" onclick="pular()">🦆</div>
    <div id="chao">
        <span>🏫</span><span>🛝</span><span>📚</span><span>🎨</span>
    </div>
    <div id="painel">
        <button class="btn-escola" onclick="mudarCenario('escola')">🦆 EM Pato Donald</button>
        <button class="btn-floresta" onclick="mudarCenario('floresta')">🌲 Floresta</button>
        <button class="btn-espaco" onclick="mudarCenario('espaco')">🚀 Espaço</button>
        <button class="btn-oceano" onclick="mudarCenario('oceano')">🌊 Oceano</button>
        <button class="btn-doces" onclick="mudarCenario('doces')">🍭 Doces</button>
        <button class="btn-clima" onclick="mudarClima()">🌦️ Clima</button>
    </div>
</div>
<script>
    let climaAtual = 0;
    const climas = ['☀️', '🌧️', '❄️', '🌈', '🌙'];
    const dadosCenarios = {
        escola: { classe: 'escola', personagem: '🦆', chao: ['🏫', '🛝', '📚', '🎨'], mostrarPlaca: true },
        floresta: { classe: 'floresta', personagem: '🦊', chao: ['🌲', '🍄', '🌻', '🌲'], mostrarPlaca: false },
        espaco: { classe: 'espaco', personagem: '👨‍🚀', chao: ['🪐', '☄️', '🛸', '⭐'], mostrarPlaca: false },
        oceano: { classe: 'oceano', personagem: '🐳', chao: ['🪸', '🐙', '🐚', '🐠'], mostrarPlaca: false },
        doces: { classe: 'doces', personagem: '🦄', chao: ['🧁', '🍩', '🍦', '🍭'], mostrarPlaca: false }
    };
    function mudarCenario(tipo) {
        document.getElementById('cenario').className = dadosCenarios[tipo].classe;
        document.getElementById('personagem').innerText = dadosCenarios[tipo].personagem;
        document.getElementById('placa-escola').style.display = dadosCenarios[tipo].mostrarPlaca ? 'block' : 'none';
        const chaoDiv = document.getElementById('chao');
        chaoDiv.innerHTML = '';
        dadosCenarios[tipo].chao.forEach(item => {
            const span = document.createElement('span');
            span.innerText = item;
            chaoDiv.appendChild(span);
        });
    }
    function mudarClima() {
        climaAtual = (climaAtual + 1) % climas.length;
        document.getElementById('ceu').innerText = climas[climaAtual];
    }
    function pular() {
        const p = document.getElementById('personagem');
        p.style.transform = 'translateY(-35px) scale(1.15)';
        setTimeout(() => { p.style.transform = 'translateY(0) scale(1)'; }, 400);
    }
</script>
</body>
</html>
"""

components.html(codigo_jogo, height=800, scrolling=False)
