<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Jogo de Corrida</title>
    <style>
        * { box-sizing: border-box; user-select: none; -webkit-user-select: none; }
        body {
            margin: 0; padding: 10px; display: flex; flex-direction: column;
            align-items: center; justify-content: center; min-height: 100vh;
            background: #e0f7fa;
            font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif; overflow: hidden;
        }
        #game-wrapper {
            position: relative; width: 100%; max-width: 520px;
            border: 5px solid #003366; border-radius: 25px; overflow: hidden;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3); background: #2E7D32;
        }
        canvas { display: block; width: 100%; height: 460px; }
        #hud {
            position: absolute; top: 12px; left: 12px; right: 12px;
            display: flex; justify-content: space-between; pointer-events: none;
        }
        .badge {
            background: #FFD700; color: #003366; border: 3px solid #003366;
            border-radius: 15px; padding: 5px 14px; font-size: 18px; font-weight: bold;
        }
        #overlay {
            position: absolute; inset: 0; background: rgba(0, 51, 102, 0.85);
            display: flex; flex-direction: column; justify-content: center;
            align-items: center; color: white; text-align: center; padding: 20px;
        }
        #overlay h2 { font-size: 30px; color: #FFD700; margin: 0 0 10px 0; }
        #overlay p { font-size: 18px; margin: 0 0 20px 0; }
        #start-btn {
            background: #4CAF50; color: white; border: 4px solid white;
            border-radius: 25px; padding: 15px 35px; font-size: 24px;
            font-weight: bold; cursor: pointer; font-family: inherit;
        }
        #start-btn:hover { background: #45a049; }
        #controls {
            display: flex; justify-content: space-between; width: 100%;
            max-width: 520px; margin-top: 12px; gap: 15px;
        }
        .ctrl-btn {
            flex: 1; height: 85px; background: #1E90FF; color: white;
            border: 4px solid white; border-radius: 25px; font-size: 38px;
            font-weight: bold; cursor: pointer; touch-action: manipulation;
        }
        .ctrl-btn:active { background: #005BB5; transform: scale(0.96); }
    </style>
</head>
<body>

<div id="game-wrapper">
    <canvas id="gameCanvas" width="500" height="460"></canvas>
    <div id="hud">
        <div class="badge">⭐ Pontos: <span id="score">0</span></div>
        <div class="badge">❤️ Vidas: <span id="lives">3</span></div>
    </div>
    <div id="overlay">
        <h2 id="overlay-title">🏁 Pronto para Correr?</h2>
        <p id="overlay-msg">Desvie dos cones e pegue as estrelas douradas!</p>
        <button id="start-btn" onclick="startGame()">🚀 ACELERAR!</button>
    </div>
</div>

<div id="controls">
    <button class="ctrl-btn" id="btn-left">⬅️</button>
    <button class="ctrl-btn" id="btn-right">➡️</button>
</div>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const overlay = document.getElementById('overlay');
const scoreEl = document.getElementById('score');
const livesEl = document.getElementById('lives');

const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSound(freq, type, duration) {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration);
    osc.connect(gain); 
    gain.connect(audioCtx.destination);
    osc.start(); 
    osc.stop(audioCtx.currentTime + duration);
}

let gameRunning = false, score = 0, lives = 3, speed = 5, roadOffset = 0, frameCount = 0;
let items = [], trees = [];

// Correção 1: Coordenadas X das 3 faixas da pista definidas
const lanes = [132, 250, 368]; 
let currentLane = 1;
let player = { x: lanes[1], y: 365, targetX: lanes[1] };

for (let i = 0; i < 8; i++) {
    trees.push({ x: i % 2 === 0 ? 35 : 465, y: i * 70, size: 26 });
}

function startGame() {
    score = 0; lives = 3; speed = 5; items = [];
    currentLane = 1; 
    player.x = lanes[1]; 
    player.targetX = lanes[1];
    scoreEl.innerText = score; 
    livesEl.innerText = lives;
    overlay.style.display = 'none'; 
    gameRunning = true;
    playSound(520, 'triangle', 0.2);
    requestAnimationFrame(gameLoop);
}

function moveLeft() {
    if (gameRunning && currentLane > 0) {
        currentLane--; 
        player.targetX = lanes[currentLane];
        playSound(300, 'sine', 0.08);
    }
}

function moveRight() {
    if (gameRunning && currentLane < 2) {
        currentLane++; 
        player.targetX = lanes[currentLane];
        playSound(350, 'sine', 0.08);
    }
}

window.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') moveLeft();
    if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') moveRight();
});
document.getElementById('btn-left').addEventListener('pointerdown', (e) => { e.preventDefault(); moveLeft(); });
document.getElementById('btn-right').addEventListener('pointerdown', (e) => { e.preventDefault(); moveRight(); });

function drawCar(x, y) {
    ctx.save(); 
    ctx.translate(x, y);
    // Pneus
    ctx.fillStyle = '#111';
    ctx.fillRect(-32, -30, 8, 20); ctx.fillRect(24, -30, 8, 20);
    ctx.fillRect(-32, 14, 8, 20); ctx.fillRect(24, 14, 8, 20);
    // Carroceria
    ctx.fillStyle = '#FF1744'; 
    ctx.beginPath(); 
    ctx.roundRect(-26, -42, 52, 84, 15); 
    ctx.fill();
    ctx.lineWidth = 3; 
    ctx.strokeStyle = '#FFF'; 
    ctx.stroke();
    // Faixa central
    ctx.fillStyle = '#FFD700'; 
    ctx.fillRect(-6, -40, 12, 80);
    // Para-brisa
    ctx.fillStyle = '#81D4FA'; 
    ctx.beginPath(); 
    ctx.roundRect(-19, -18, 38, 22, 6); 
    ctx.fill();
    ctx.restore();
}

function gameLoop() {
    if (!gameRunning) return;
    frameCount++;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Grama e Asfalto
    ctx.fillStyle = '#43A047'; ctx.fillRect(0, 0, 500, 460);
    ctx.fillStyle = '#37474F'; ctx.fillRect(75, 0, 350, 460);
    
    // Zebras laterais
    roadOffset = (roadOffset + speed) % 60;
    for (let y = -60; y < 520; y += 30) {
        ctx.fillStyle = (Math.floor((y + roadOffset) / 30) % 2 === 0) ? '#FF5252' : '#FFF';
        ctx.fillRect(65, y + roadOffset, 10, 30); 
        ctx.fillRect(425, y + roadOffset, 10, 30);
    }
    
    // Faixas tracejadas
    ctx.strokeStyle = '#FFD700'; ctx.lineWidth = 5; ctx.setLineDash([25, 35]);
    ctx.lineDashOffset = -roadOffset; ctx.beginPath();
    ctx.moveTo(188, 0); ctx.lineTo(188, 460); 
    ctx.moveTo(312, 0); ctx.lineTo(312, 460);
    ctx.stroke(); ctx.setLineDash([]);

    // Árvores
    trees.forEach(t => {
        t.y += speed; 
        if (t.y > 500) t.y = -40;
        ctx.fillStyle = '#1B5E20'; 
        ctx.beginPath(); 
        ctx.arc(t.x, t.y, t.size, 0, Math.PI * 2); 
        ctx.fill();
    });

    // Movimento suave do carro
    player.x += (player.targetX - player.x) * 0.22;
    drawCar(player.x, player.y);

    // Geração de estrelas e cones
    if (frameCount % Math.max(32, Math.floor(65 - speed * 2)) === 0) {
        items.push({ 
            x: lanes[Math.floor(Math.random() * 3)], 
            y: -50, 
            type: Math.random() > 0.45 ? 'star' : 'cone' 
        });
    }

    // Desenho e colisão dos itens
    ctx.font = '38px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (let i = items.length - 1; i >= 0; i--) {
        let item = items[i]; 
        item.y += speed;
        ctx.fillText(item.type === 'star' ? '⭐' : '🚧', item.x, item.y);

        if (Math.abs(player.x - item.x) < 42 && Math.abs(player.y - item.y) < 55) {
            if (item.type === 'star') {
                score += 10; 
                scoreEl.innerText = score; 
                playSound(660, 'sine', 0.15);
                if (score % 50 === 0 && speed < 12) speed += 0.6;
            } else {
                lives--; 
                livesEl.innerText = lives; 
                playSound(150, 'sawtooth', 0.3);
                if (lives <= 0) {
                    gameRunning = false;
                    document.getElementById('overlay-title').innerText = '🏆 Fim da Corrida!';
                    document.getElementById('overlay-msg').innerText = `Você fez ${score} pontos!`;
                    document.getElementById('start-btn').innerText = '🔄 JOGAR DE NOVO';
                    overlay.style.display = 'flex';
                    return;
                }
            }
            items.splice(i, 1); 
            continue;
        }
        if (item.y > 510) items.splice(i, 1);
    }
    requestAnimationFrame(gameLoop);
}
</script>
</body>
</html>
