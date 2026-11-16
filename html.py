import streamlit as st
import streamlit.components.v1 as components

if st.button("⬅️ Voltar ao Portal dos Mundos"):
    st.switch_page("app.py")

html_escola = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
    body, html { margin: 0; padding: 0; width: 100%; height: 90vh; overflow: hidden; font-family: 'Comic Sans MS', sans-serif; }
    #tela { width: 100%; height: 100%; background: linear-gradient(to bottom, #87CEFA 60%, #90EE90 60%); position: relative; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 10px; box-sizing: border-box; }
    .placa { background: #FFD700; color: #003366; border: 2px solid #003366; padding: 5px 15px; border-radius: 12px; font-weight: bold; }
    .bicho { position: absolute; font-size: 55px; cursor: grab; touch-action: none; user-select: none; }
    .barra { background: rgba(255,255,255,0.9); padding: 8px; border-radius: 20px; display: flex; gap: 8px; z-index: 10; }
    button { font-size: 22px; border: none; background: #FFF8DC; border-radius: 12px; padding: 5px 10px; cursor: pointer; }
</style>
</head>
<body>
<div id="tela">
    <div class="placa">🏫 EM Pato Donald - São José do Rio Preto</div>
    <div id="palco"></div>
    <div class="barra">
        <button onclick="add('🦆')">🦆</button>
        <button onclick="add('🛝')">🛝</button>
        <button onclick="add('📚')">📚</button>
        <button onclick="add('🎨')">🎨</button>
        <button onclick="document.getElementById('palco').innerHTML=''" style="font-size:15px; background:#FF6B6B; color:white;">🗑️</button>
    </div>
</div>
<script>
    function add(emoji) {
        const el = document.createElement('div');
        el.className = 'bicho'; el.innerText = emoji;
        el.style.left = (25 + Math.random()*45) + 'vw'; el.style.top = (25 + Math.random()*30) + 'vh';
        let drag = false, ox = 0, oy = 0;
        el.onpointerdown = e => { drag = true; ox = e.clientX - el.offsetLeft; oy = e.clientY - el.offsetTop; el.setPointerCapture(e.pointerId); };
        el.onpointermove = e => { if(drag){ el.style.left = (e.clientX - ox)+'px'; el.style.top = (e.clientY - oy)+'px'; }};
        el.onpointerup = e => { drag = false; el.releasePointerCapture(e.pointerId); };
        document.getElementById('palco').appendChild(el);
    }
    add('🦆');
</script>
</body>
</html>
"""
components.html(html_escola, height=650)
