import streamlit as st
import streamlit.components.v1 as components
import psycopg2

st.set_page_config(
    page_title="Portal dos Mundos - EM Pato Donald",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def registrar_visita_neon(mundo_nome):
    try:
        if "DATABASE_URL" in st.secrets:
            conn = psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS public.visitas_mundos (
                            id SERIAL PRIMARY KEY,
                            mundo TEXT NOT NULL,
                            data_hora TIMESTAMP DEFAULT NOW()
                        );
                    """)
                    cur.execute("INSERT INTO public.visitas_mundos (mundo) VALUES (%s);", (mundo_nome,))
            conn.close()
    except Exception:
        pass
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "portal"

def abrir_mundo(nome):
    st.session_state.tela_atual = nome
    registrar_visita_neon(nome)

if st.session_state.tela_atual == "portal":
    st.markdown("""
        <style>
            #MainMenu, header, footer {visibility: hidden;}
            .stApp {
                background: linear-gradient(135deg, #87CEFA 0%, #E0F7FA 50%, #FFD54F 100%);
                font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
            }
            .cabecalho {
                background: #FFD700;
                color: #003366;
                border: 4px solid #003366;
                border-radius: 25px;
                padding: 20px;
                text-align: center;
                margin-bottom: 25px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            }
            .cabecalho h1 { margin: 0 0 8px 0; font-size: clamp(24px, 5vw, 34px); }
            .cabecalho p { margin: 0; font-size: clamp(15px, 3vw, 19px); font-weight: bold; }
            div.stButton > button {
                width: 100%;
                height: 150px;
                border-radius: 25px !important;
                border: 4px solid white !important;
                font-size: clamp(20px, 4vw, 26px) !important;
                font-weight: bold !important;
                background: linear-gradient(to bottom, #1E90FF, #005BB5) !important;
                color: white !important;
                box-shadow: 0 8px 18px rgba(0,0,0,0.25) !important;
                transition: transform 0.2s !important;
            }
            div.stButton > button:hover {
                transform: scale(1.04) !important;
                background: linear-gradient(to bottom, #00BFFF, #1E90FF) !important;
            }
        </style>

        <div class="cabecalho">
            <h1>🌍 Portal dos Mundos Mágicos</h1>
            <p>🏫 EM Pato Donald - São José do Rio Preto</p>
            <p style="font-size: 15px; margin-top: 6px; color: #333;">Toque em um mundo abaixo para entrar!</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🦆\nMundo da Escola", key="btn_escola", use_container_width=True):
            abrir_mundo("escola")
            st.rerun()
        st.write("")
        if st.button("🐳\nMundo do Oceano", key="btn_oceano", use_container_width=True):
            abrir_mundo("oceano")
            st.rerun()

    with col2:
        if st.button("🦫\nMundo da Represa", key="btn_represa", use_container_width=True):
            abrir_mundo("represa")
            st.rerun()
        st.write("")
        if st.button("🚀\nMundo do Espaço", key="btn_espaco", use_container_width=True):
            abrir_mundo("espaco")
            st.rerun()

else:
    st.markdown("""
        <style>
            #MainMenu, header, footer {visibility: hidden;}
            .block-container { padding: 5px 10px 0 10px !important; max-width: 100% !important; }
            div.stButton > button {
                background-color: #FF6B6B !important;
                color: white !important;
                border-radius: 15px !important;
                font-weight: bold !important;
                border: 2px solid white !important;
                height: 44px !important;
                font-size: 16px !important;
            }
            iframe { width: 100% !important; height: 88vh !important; border: none !important; display: block !important; }
        </style>
    """, unsafe_allow_html=True)

    if st.button("⬅️ Voltar ao Portal dos Mundos"):
        st.session_state.tela_atual = "portal"
        st.rerun()
    mundos = {
        "escola": {
            "titulo": "🏫 EM Pato Donald - São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #87CEFA 55%, #F4A460 55%, #2E8B57 85%)",
            "placa_bg": "#FFD700", "placa_cor": "#003366",
            "itens": ["🦆", "🏫", "🛝", "📚", "🎨", "⚽"],
            "iniciais": ["🦆", "🏫"],
            "clima_extra": "chuva_arcoiris"
        },
        "represa": {
            "titulo": "🌊 Represa Municipal - São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #87CEEB 45%, #1E90FF 45%, #3CB371 78%)",
            "placa_bg": "#00CED1", "placa_cor": "#003366",
            "itens": ["🦫", "🦢", "⛵", "🌴", "🚲", "🦆"],
            "iniciais": ["🦫", "🦢"],
            "clima_extra": "chuva_arcoiris"
        },
        "oceano": {
            "titulo": "🐠 Mundo do Oceano Azul",
            "fundo": "linear-gradient(to bottom, #00CED1 20%, #000080 85%)",
            "placa_bg": "#00008B", "placa_cor": "#FFFFFF",
            "itens": ["🐳", "🐙", "🐠", "🦀", "🪸", "🐚"],
            "iniciais": ["🐳", "🐙"],
            "clima_extra": "bolhas"
        },
        "espaco": {
            "titulo": "🚀 Viagem pelo Espaço Sideral",
            "fundo": "radial-gradient(circle, #1B2735 0%, #090A0F 100%)",
            "placa_bg": "#4B0082", "placa_cor": "#FFFFFF",
            "itens": ["👨‍🚀", "🛸", "🪐", "👽", "☄️", "🦆"],
            "iniciais": ["👨‍🚀", "🛸"],
            "clima_extra": "estrelas"
        }
    }

    cfg = mundos[st.session_state.tela_atual]
    botoes_itens = "".join([f'<button class="btn-item" onclick="criar(\'{i}\')">{i}</button>' for i in cfg["itens"]])
    iniciais_js = "".join([f"criar('{i}');" for i in cfg["iniciais"]])
    html_cenario = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
            body, html {{
                margin: 0; padding: 0; width: 100%; height: 100%;
                font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
                overflow: hidden; user-select: none; touch-action: none;
            }}
            #cenario {{
                width: 100%; height: 100%; background: {cfg['fundo']};
                border-radius: 20px; display: flex; flex-direction: column;
                justify-content: space-between; align-items: center; padding: 12px; position: relative;
            }}
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
            #efeitos-container {{
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
            .bolha {{
                position: absolute; bottom: -20px; border-radius: 50%;
                border: 2px solid rgba(255,255,255,0.7); background: rgba(255,255,255,0.2);
                animation: subir linear infinite;
            }}
            @keyframes subir {{
                0% {{ transform: translateY(0) scale(0.8); opacity: 0.8; }}
                100% {{ transform: translateY(-105vh) scale(1.3); opacity: 0; }}
            }}
            .estrela {{
                position: absolute; background: white; border-radius: 50%;
                box-shadow: 0 0 8px #FFF; animation: piscar 1.5s infinite alternate;
            }}
            @keyframes piscar {{
                0% {{ opacity: 0.2; transform: scale(0.8); }}
                100% {{ opacity: 1; transform: scale(1.3); }}
            }}
            .placa {{
                background: {cfg['placa_bg']}; color: {cfg['placa_cor']}; border: 3px solid #003366;
                padding: 6px 16px; border-radius: 14px; font-size: clamp(13px, 3vw, 18px);
                font-weight: bold; text-align: center; z-index: 10;
            }}
            .bicho {{
                position: absolute; font-size: 56px; cursor: grab; z-index: 6;
                touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3));
            }}
            .bicho:active {{ cursor: grabbing; transform: scale(1.2); }}
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
            .btn-acao {{
                font-size: 14px; font-weight: bold; border: none; border-radius: 14px;
                padding: 8px 11px; cursor: pointer;
            }}
        </style>
    </head>
    <body>
    <div id="cenario">
        <div id="arco-iris"></div>
        <div id="efeitos-container"></div>
        <div class="placa">{cfg['titulo']}</div>
        <div id="palco"></div>
        <div id="barra">
            {botoes_itens}
            <button class="btn-acao" style="background:#FFD700; color:#333;" onclick="alternarClima()">🌦️ Clima</button>
            <button class="btn-acao" style="background:#FF6B6B; color:white;" onclick="limpar()">🗑️</button>
        </div>
    </div>
    <script>
        let estadoClima = 0;
        const tipoClima = "{cfg['clima_extra']}";

        function alternarClima() {{
            const div = document.getElementById('efeitos-container');
            const arco = document.getElementById('arco-iris');
            div.innerHTML = '';
            arco.classList.remove('ativo');

            if (tipoClima === 'chuva_arcoiris') {{
                estadoClima = (estadoClima + 1) % 3;
                if (estadoClima === 1) {{
                    for (let i = 0; i < 50; i++) {{
                        const g = document.createElement('div');
                        g.className = 'gota';
                        g.style.left = Math.random() * 100 + 'vw';
                        g.style.animationDuration = (Math.random() * 0.4 + 0.5) + 's';
                        g.style.animationDelay = Math.random() + 's';
                        div.appendChild(g);
                    }}
                }} else if (estadoClima === 2) {{
                    arco.classList.add('ativo');
                }}
            }} else if (tipoClima === 'bolhas') {{
                estadoClima = (estadoClima + 1) % 2;
                if (estadoClima === 1) {{
                    for (let i = 0; i < 35; i++) {{
                        const b = document.createElement('div');
                        b.className = 'bolha';
                        const tam = (Math.random() * 14 + 6) + 'px';
                        b.style.width = tam; b.style.height = tam;
                        b.style.left = Math.random() * 100 + 'vw';
                        b.style.animationDuration = (Math.random() * 2 + 2) + 's';
                        b.style.animationDelay = (Math.random() * 2) + 's';
                        div.appendChild(b);
                    }}
                }}
            }} else if (tipoClima === 'estrelas') {{
                estadoClima = (estadoClima + 1) % 2;
                if (estadoClima === 1) {{
                    for (let i = 0; i < 45; i++) {{
                        const e = document.createElement('div');
                        e.className = 'estrela';
                        const tam = (Math.random() * 4 + 2) + 'px';
                        e.style.width = tam; e.style.height = tam;
                        e.style.left = Math.random() * 100 + 'vw';
                        e.style.top = Math.random() * 85 + 'vh';
                        e.style.animationDelay = (Math.random() * 2) + 's';
                        div.appendChild(e);
                    }}
                }}
            }}
        }}

        function criar(emoji) {{
            const palco = document.getElementById('palco');
            const el = document.createElement('div');
            el.className = 'bicho'; el.innerText = emoji;
            el.style.left = (25 + Math.random() * 45) + 'vw';
            el.style.top = (25 + Math.random() * 30) + 'vh';
            let drag = false, ox = 0, oy = 0;
            el.onpointerdown = e => {{
                drag = true; const r = el.getBoundingClientRect();
                ox = e.clientX - r.left; oy = e.clientY - r.top; el.setPointerCapture(e.pointerId);
            }};
            el.onpointermove = e => {{
                if (!drag) return;
                el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 60)) + 'px';
                el.style.top = Math.max(45, Math.min(e.clientY - oy, window.innerHeight - 120)) + 'px';
            }};
            el.onpointerup = e => {{ drag = false; el.releasePointerCapture(e.pointerId); }};
            palco.appendChild(el);
        }}

        function limpar() {{ document.getElementById('palco').innerHTML = ''; }}
        {iniciais_js}
    </script>
    </body>
    </html>
    """

    components.html(html_cenario, height=700, scrolling=False)
