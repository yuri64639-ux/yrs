import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="EM Pato Donald - Rio Preto",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🔗 Link do Portal Principal (mundo.py) já preenchido
LINK_PORTAL = "https://streamlit.app"

st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
        iframe { width: 100vw !important; height: 100vh !important; border: none !important; display: block !important; }
    </style>
""", unsafe_allow_html=True)

jogo_escola = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        body, html {{
            margin: 0; padding: 0; width: 100%; height: 100vh;
            font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
            overflow: hidden; user-select: none; touch-action: none;
        }}
        #cenario {{
            width: 100%; height: 100%;
            background: linear-gradient(to bottom, #87CEFA 55%, #F4A460 55%, #2E8B57 85%);
            display: flex; flex-direction: column; justify-content: space-between;
            align-items: center; padding: 10px; position: relative;
        }}

        /* Arco-íris e Chuva Realista */
        #arco-iris {{
            position: absolute; top: 10%; left: 50%; transform: translateX(-50%);
            width: 120vw; max-width: 850px; height: 60vw; max-height: 420px;
            border-radius: 50% 50% 0 0 / 100% 100% 0 0;
            background: radial-gradient(circle at 50% 100%,
                transparent 48%, rgba(148,0,211,0.35) 52%, rgba(0,119,255,0.4) 56%,
                rgba(0,200,80,0.4) 60%, rgba(255,230,0,0.45) 64%, rgba(255,20,20,0.4) 68%, transparent 72%);
            filter: blur(6px); pointer-events: none; opacity: 0; transition: opacity 0.8s; z-index: 1;
        }}
        #arco-iris.ativo {{ opacity: 1; }}

        #chuva-container {{
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; overflow: hidden; z-index: 2;
        }}
        .gota {{
            position: absolute; width: 2px; height: 20px;
            background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0.85));
            animation: cair linear infinite;
        }}
        @keyframes cair {{
            0% {{ transform: translate(0, -20px) rotate(12deg); }}
            100% {{ transform: translate(-35px, 105vh) rotate(12deg); }}
        }}

        /* Topo */
        #topo {{
            width: 100%; max-width: 800px; display: flex; justify-content: space-between;
            align-items: center; z-index: 10; gap: 8px;
        }}
        .btn-voltar {{
            background: #FF6B6B; color: white; border: 2px solid white; border-radius: 14px;
            padding: 6px 12px; font-size: 14px; font-weight: bold; text-decoration: none;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2); white-space: nowrap;
        }}
        .placa {{
            background: #FFD700; color: #003366; border: 3px solid #003366;
            padding: 5px 14px; border-radius: 14px; font-size: clamp(12px, 2.8vw, 17px);
            font-weight: bold; text-align: center; flex-grow: 1;
        }}

        /* Itens Arrastáveis da Escola */
        .bicho {{
            position: absolute; font-size: 56px; cursor: grab; z-index: 6;
            touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3));
            transition: transform 0.1s;
        }}
        .bicho:active {{ cursor: grabbing; transform: scale(1.2); }}

        /* Barra Inferior */
        #barra {{
            background: rgba(255, 255, 255, 0.94); padding: 8px 12px; border-radius: 22px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 10;
            display: flex; justify-content: center; align-items: center; gap: 6px;
            flex-wrap: wrap; max-width: 96%;
        }}
        .btn-item {{
            font-size: 24px; border: 2px solid #FFD700; background: #FFF8DC;
            border-radius: 14px; padding: 4px 8px; cursor: pointer;
        }}
        .btn-item:active {{ transform: scale(1.15); }}
        .btn-acao {{
            font-size: 14px; font-weight: bold; border: none; border-radius: 14px;
            padding: 8px 11px; cursor: pointer;
        }}
    </style>
</head>
<body>
<div id="cenario">
    <div id="arco-iris"></div>
    <div id="chuva-container"></div>

    <div id="topo">
        <a href="{LINK_PORTAL}" target="_top" class="btn-voltar">⬅️ Mundos</a>
        <div class="placa">🏫 EM Pato Donald - São José do Rio Preto</div>
    </div>

    <div id="palco"></div>

    <div id="barra">
        <button class="btn-item" onclick="criar('🦆')" title="Pato Donald">🦆</button>
        <button class="btn-item" onclick="criar('🏫')" title="Escola">🏫</button>
        <button class="btn-item" onclick="criar('🛝')" title="Parquinho">🛝</button>
        <button class="btn-item" onclick="criar('📚')" title="Livros">📚</button>
        <button class="btn-item" onclick="criar('🎨')" title="Pintura">🎨</button>
        <button class="btn-item" onclick="criar('⚽')" title="Bola">⚽</button>
        <button class="btn-acao" style="background:#FFD700; color:#333;" onclick="alternarClima()">🌦️ Clima</button>
        <button class="btn-acao" style="background:#FF6B6B; color:white;" onclick="limpar()">🗑️</button>
    </div>
</div>

<script>
    let clima = 0;

    function alternarClima() {{
        clima = (clima + 1) % 3;
        const chuvaDiv = document.getElementById('chuva-container');
        const arcoDiv = document.getElementById('arco-iris');
        chuvaDiv.innerHTML = '';
        arcoDiv.classList.remove('ativo');

        if (clima === 1) {{
            for (let i = 0; i < 50; i++) {{
                const g = document.createElement('div');
                g.className = 'gota';
                g.style.left = Math.random() * 100 + 'vw';
                g.style.animationDuration = (Math.random() * 0.4 + 0.5) + 's';
                g.style.animationDelay = Math.random() + 's';
                chuvaDiv.appendChild(g);
            }}
        }} else if (clima === 2) {{
            arcoDiv.classList.add('ativo');
        }}
    }}

    function criar(emoji) {{
        const palco = document.getElementById('palco');
        const el = document.createElement('div');
        el.className = 'bicho';
        el.innerText = emoji;
        el.style.left = (25 + Math.random() * 45) + 'vw';
        el.style.top = (25 + Math.random() * 30) + 'vh';

        let drag = false, ox = 0, oy = 0;

        el.onpointerdown = e => {{
            drag = true;
            const r = el.getBoundingClientRect();
            ox = e.clientX - r.left;
            oy = e.clientY - r.top;
            el.setPointerCapture(e.pointerId);
        }};

        el.onpointermove = e => {{
            if (!drag) return;
            el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 60)) + 'px';
            el.style.top = Math.max(45, Math.min(e.clientY - oy, window.innerHeight - 120)) + 'px';
        }};

        el.onpointerup = e => {{
            drag = false;
            el.releasePointerCapture(e.pointerId);
        }};

        palco.appendChild(el);
    }}

    function limpar() {{
        document.getElementById('palco').innerHTML = '';
    }}

    criar('🦆');
    criar('🏫');
</script>
</body>
</html>
"""

components.html(jogo_escola, height=800, scrolling=False)
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="EM Pato Donald - Rio Preto",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🔗 Cole aqui o link do seu Portal Principal (mundo.py) para o botão de voltar funcionar
LINK_PORTAL = "https://streamlit.app"

st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
        iframe { width: 100vw !important; height: 100vh !important; border: none !important; display: block !important; }
    </style>
""", unsafe_allow_html=True)

jogo_escola = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        body, html {{
            margin: 0; padding: 0; width: 100%; height: 100vh;
            font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
            overflow: hidden; user-select: none; touch-action: none;
        }}
        #cenario {{
            width: 100%; height: 100%;
            background: linear-gradient(to bottom, #87CEFA 55%, #F4A460 55%, #2E8B57 85%);
            display: flex; flex-direction: column; justify-content: space-between;
            align-items: center; padding: 10px; position: relative;
        }}

        /* Arco-íris e Chuva Realista */
        #arco-iris {{
            position: absolute; top: 10%; left: 50%; transform: translateX(-50%);
            width: 120vw; max-width: 850px; height: 60vw; max-height: 420px;
            border-radius: 50% 50% 0 0 / 100% 100% 0 0;
            background: radial-gradient(circle at 50% 100%,
                transparent 48%, rgba(148,0,211,0.35) 52%, rgba(0,119,255,0.4) 56%,
                rgba(0,200,80,0.4) 60%, rgba(255,230,0,0.45) 64%, rgba(255,20,20,0.4) 68%, transparent 72%);
            filter: blur(6px); pointer-events: none; opacity: 0; transition: opacity 0.8s; z-index: 1;
        }}
        #arco-iris.ativo {{ opacity: 1; }}

        #chuva-container {{
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none; overflow: hidden; z-index: 2;
        }}
        .gota {{
            position: absolute; width: 2px; height: 20px;
            background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0.85));
            animation: cair linear infinite;
        }}
        @keyframes cair {{
            0% {{ transform: translate(0, -20px) rotate(12deg); }}
            100% {{ transform: translate(-35px, 105vh) rotate(12deg); }}
        }}

        /* Topo */
        #topo {{
            width: 100%; max-width: 800px; display: flex; justify-content: space-between;
            align-items: center; z-index: 10; gap: 8px;
        }}
        .btn-voltar {{
            background: #FF6B6B; color: white; border: 2px solid white; border-radius: 14px;
            padding: 6px 12px; font-size: 14px; font-weight: bold; text-decoration: none;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2); white-space: nowrap;
        }}
        .placa {{
            background: #FFD700; color: #003366; border: 3px solid #003366;
            padding: 5px 14px; border-radius: 14px; font-size: clamp(12px, 2.8vw, 17px);
            font-weight: bold; text-align: center; flex-grow: 1;
        }}

        /* Itens Arrastáveis da Escola */
        .bicho {{
            position: absolute; font-size: 56px; cursor: grab; z-index: 6;
            touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3));
            transition: transform 0.1s;
        }}
        .bicho:active {{ cursor: grabbing; transform: scale(1.2); }}

        /* Barra Inferior */
        #barra {{
            background: rgba(255, 255, 255, 0.94); padding: 8px 12px; border-radius: 22px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 10;
            display: flex; justify-content: center; align-items: center; gap: 6px;
            flex-wrap: wrap; max-width: 96%;
        }}
        .btn-item {{
            font-size: 24px; border: 2px solid #FFD700; background: #FFF8DC;
            border-radius: 14px; padding: 4px 8px; cursor: pointer;
        }}
        .btn-item:active {{ transform: scale(1.15); }}
        .btn-acao {{
            font-size: 14px; font-weight: bold; border: none; border-radius: 14px;
            padding: 8px 11px; cursor: pointer;
        }}
    </style>
</head>
<body>
<div id="cenario">
    <div id="arco-iris"></div>
    <div id="chuva-container"></div>

    <div id="topo">
        <a href="{LINK_PORTAL}" target="_top" class="btn-voltar">⬅️ Mundos</a>
        <div class="placa">🏫 EM Pato Donald - São José do Rio Preto</div>
    </div>

    <div id="palco"></div>

    <div id="barra">
        <button class="btn-item" onclick="criar('🦆')" title="Pato Donald">🦆</button>
        <button class="btn-item" onclick="criar('🏫')" title="Escola">🏫</button>
        <button class="btn-item" onclick="criar('🛝')" title="Parquinho">🛝</button>
        <button class="btn-item" onclick="criar('📚')" title="Livros">📚</button>
        <button class="btn-item" onclick="criar('🎨')" title="Pintura">🎨</button>
        <button class="btn-item" onclick="criar('⚽')" title="Bola">⚽</button>
        <button class="btn-acao" style="background:#FFD700; color:#333;" onclick="alternarClima()">🌦️ Clima</button>
        <button class="btn-acao" style="background:#FF6B6B; color:white;" onclick="limpar()">🗑️</button>
    </div>
</div>

<script>
    let clima = 0; // 0 = Sol, 1 = Chuva, 2 = Arco-íris

    function alternarClima() {{
        clima = (clima + 1) % 3;
        const chuvaDiv = document.getElementById('chuva-container');
        const arcoDiv = document.getElementById('arco-iris');
        chuvaDiv.innerHTML = '';
        arcoDiv.classList.remove('ativo');

        if (clima === 1) {{
            for (let i = 0; i < 50; i++) {{
                const g = document.createElement('div');
                g.className = 'gota';
                g.style.left = Math.random() * 100 + 'vw';
                g.style.animationDuration = (Math.random() * 0.4 + 0.5) + 's';
                g.style.animationDelay = Math.random() + 's';
                chuvaDiv.appendChild(g);
            }}
        }} else if (clima === 2) {{
            arcoDiv.classList.add('ativo');
        }}
    }}

    function criar(emoji) {{
        const palco = document.getElementById('palco');
        const el = document.createElement('div');
        el.className = 'bicho';
        el.innerText = emoji;
        el.style.left = (25 + Math.random() * 45) + 'vw';
        el.style.top = (25 + Math.random() * 30) + 'vh';

        let drag = false, ox = 0, oy = 0;

        el.onpointerdown = e => {{
            drag = true;
            const r = el.getBoundingClientRect();
            ox = e.clientX - r.left;
            oy = e.clientY - r.top;
            el.setPointerCapture(e.pointerId);
        }};

        el.onpointermove = e => {{
            if (!drag) return;
            el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 60)) + 'px';
            el.style.top = Math.max(45, Math.min(e.clientY - oy, window.innerHeight - 120)) + 'px';
        }};

        el.onpointerup = e => {{
            drag = false;
            el.releasePointerCapture(e.pointerId);
        }};

        palco.appendChild(el);
    }}

    function limpar() {{
        document.getElementById('palco').innerHTML = '';
    }}

    // Inicia com o Pato e a Escola na tela
    criar('🦆');
    criar('🏫');
</script>
</body>
</html>
"""

components.html(jogo_escola, height=800, scrolling=False)
