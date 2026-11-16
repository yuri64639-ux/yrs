import streamlit as st
import streamlit.components.v1 as components

def _renderizar_cenario(titulo, fundo, cor_placa, borda_placa, texto_placa, botoes_html, bicho_inicial):
    if st.button("⬅️ Voltar ao Portal dos Mundos"):
        st.switch_page("html.py")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 88vh; overflow: hidden; font-family: 'Comic Sans MS', sans-serif; }}
        #tela {{ width: 100%; height: 100%; background: {fundo}; position: relative; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 10px; box-sizing: border-box; }}
        .placa {{ background: {cor_placa}; color: {texto_placa}; border: 2px solid {borda_placa}; padding: 5px 15px; border-radius: 12px; font-weight: bold; text-align: center; }}
        .bicho {{ position: absolute; font-size: 55px; cursor: grab; touch-action: none; user-select: none; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.25)); }}
        .barra {{ background: rgba(255,255,255,0.92); padding: 8px; border-radius: 20px; display: flex; gap: 8px; z-index: 10; flex-wrap: wrap; justify-content: center; }}
        button {{ font-size: 22px; border: none; background: #FFF8DC; border-radius: 12px; padding: 5px 10px; cursor: pointer; }}
    </style>
    </head>
    <body>
    <div id="tela">
        <div class="placa">{titulo}</div>
        <div id="palco"></div>
        <div class="barra">
            {botoes_html}
            <button onclick="document.getElementById('palco').innerHTML=''" style="font-size:15px; background:#FF6B6B; color:white;">🗑️</button>
        </div>
    </div>
    <script>
        function add(emoji) {{
            const el = document.createElement('div');
            el.className = 'bicho'; el.innerText = emoji;
            el.style.left = (25 + Math.random()*45) + 'vw'; el.style.top = (25 + Math.random()*30) + 'vh';
            let drag = false, ox = 0, oy = 0;
            el.onpointerdown = e => {{ drag = true; ox = e.clientX - el.offsetLeft; oy = e.clientY - el.offsetTop; el.setPointerCapture(e.pointerId); }};
            el.onpointermove = e => {{ if(drag){{ el.style.left = (e.clientX - ox)+'px'; el.style.top = (e.clientY - oy)+'px'; }}}};
            el.onpointerup = e => {{ drag = false; el.releasePointerCapture(e.pointerId); }};
            document.getElementById('palco').appendChild(el);
        }}
        add('{bicho_inicial}');
    </script>
    </body>
    </html>
    """
    components.html(html, height=650)

def mundo_escola():
    botoes = """
        <button onclick="add('🦆')">🦆</button>
        <button onclick="add('🛝')">🛝</button>
        <button onclick="add('📚')">📚</button>
        <button onclick="add('🎨')">🎨</button>
    """
    _renderizar_cenario(
        titulo="🏫 EM Pato Donald - São José do Rio Preto",
        fundo="linear-gradient(to bottom, #87CEFA 60%, #90EE90 60%)",
        cor_placa="#FFD700", borda_placa="#003366", texto_placa="#003366",
        botoes_html=botoes, bicho_inicial="🦆"
    )

def mundo_represa():
    botoes = """
        <button onclick="add('🦫')">🦫</button>
        <button onclick="add('🦢')">🦢</button>
        <button onclick="add('⛵')">⛵</button>
        <button onclick="add('🌴')">🌴</button>
    """
    _renderizar_cenario(
        titulo="🌊 Represa Municipal - São José do Rio Preto",
        fundo="linear-gradient(to bottom, #87CEEB 50%, #1E90FF 50%, #3CB371 80%)",
        cor_placa="#00CED1", borda_placa="#003366", texto_placa="#003366",
        botoes_html=botoes, bicho_inicial="🦫"
    )

def mundo_oceano():
    botoes = """
        <button onclick="add('🐳')">🐳</button>
        <button onclick="add('🐙')">🐙</button>
        <button onclick="add('🐠')">🐠</button>
        <button onclick="add('🪸')">🪸</button>
    """
    _renderizar_cenario(
        titulo="🐠 Mundo do Oceano Azul",
        fundo="linear-gradient(to bottom, #00CED1 25%, #000080 85%)",
        cor_placa="#00008B", borda_placa="#00CED1", texto_placa="#FFFFFF",
        botoes_html=botoes, bicho_inicial="🐳"
    )

def mundo_espaco():
    botoes = """
        <button onclick="add('👨‍🚀')">👨‍🚀</button>
        <button onclick="add('🛸')">🛸</button>
        <button onclick="add('🪐')">🪐</button>
        <button onclick="add('⭐')">⭐</button>
    """
    _renderizar_cenario(
        titulo="🚀 Viagem pelo Espaço Sideral",
        fundo="radial-gradient(circle, #1B2735 0%, #090A0F 100%)",
        cor_placa="#4B0082", borda_placa="#FFD700", texto_placa="#FFFFFF",
        botoes_html=botoes, bicho_inicial="👨‍🚀"
    )
