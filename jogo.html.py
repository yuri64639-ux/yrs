import math
import random
import struct
import pygame

# ==============================================================================
# CONFIGURAÇÕES INICIAIS E CONSTANTES
# ==============================================================================
LARGURA, ALTURA = 1000, 660
FPS = 60
TITULO = "TOP GEAR: HORIZONTE TURBO - GARAGEM & TUNING"

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption(TITULO)
relogio = pygame.time.Clock()

fonte_grande = pygame.font.SysFont("arial", 42, bold=True)
fonte_media = pygame.font.SysFont("arial", 24, bold=True)
fonte_hud = pygame.font.SysFont("consolas", 21, bold=True)
fonte_pequena = pygame.font.SysFont("arial", 17, bold=True)

# ==============================================================================
# SINTETIZADOR DE ÁUDIO PROCEDURAL
# ==============================================================================
def gerar_som(frequencias, duracao_nota, volume=0.25, onda="square"):
    taxa = 22050
    amostras = bytearray()
    for freq in frequencias:
        num_amostras = int(taxa * duracao_nota)
        for i in range(num_amostras):
            if freq == 0:
                val = 0
            else:
                t = i / taxa
                envelope = max(0.0, 1.0 - (i / num_amostras) * 0.4)
                if onda == "square":
                    s = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                elif onda == "saw":
                    s = 2.0 * (t * freq - math.floor(0.5 + t * freq))
                elif onda == "noise":
                    s = random.uniform(-1.0, 1.0)
                else:
                    s = math.sin(2 * math.pi * freq * t)
                val = int(s * volume * envelope * 32767)
            amostras.extend(struct.pack("<h", max(-32768, min(32767, val))))
    return pygame.mixer.Sound(buffer=bytes(amostras))

som_nitro = gerar_som([220, 330, 440, 660, 880], 0.07, 0.25, "saw")
som_marcha = gerar_som([180, 260], 0.04, 0.20, "square")
som_batida = gerar_som([110, 75, 50], 0.07, 0.35, "noise")
som_combustivel = gerar_som([523, 659, 784, 1046], 0.06, 0.25, "square")
som_menu = gerar_som([440, 550], 0.03, 0.15, "square")
som_largada_baixo = gerar_som([440], 0.25, 0.25, "square")
som_largada_alto = gerar_som([880], 0.45, 0.30, "square")

notas_tema = [
    330, 330, 392, 440, 330, 0, 294, 330,
    392, 392, 440, 494, 392, 0, 330, 294,
    262, 262, 330, 392, 330, 294, 262, 247,
    220, 262, 330, 294, 247, 0, 220, 0
]
trilha_sonora = gerar_som(notas_tema, 0.14, 0.11, "square")

# ==============================================================================
# OPÇÕES DE TUNING, CARROS E PISTAS
# ==============================================================================
MOTORES = [
    {"nome": "V6 ASPIRADO 3.0", "vel_max": 265, "acel": 0.95, "consumo": 0.85},
    {"nome": "V8 TURBO 4.2", "vel_max": 290, "acel": 1.12, "consumo": 1.00},
    {"nome": "V10 BITURBO 5.5", "vel_max": 315, "acel": 1.28, "consumo": 1.18},
    {"nome": "V12 HÍBRIDO PRO", "vel_max": 340, "acel": 1.42, "consumo": 1.32},
]

FREIOS = [
    {"nome": "DISCO VENTILADO", "forca": 150.0},
    {"nome": "ESPORTIVO PERFURADO", "forca": 205.0},
    {"nome": "CERÂMICA DE CORRIDA", "forca": 265.0},
]

CORES_PINTURA = [
    {"nome": "VERMELHO CORSA", "rgb": (220, 25, 40), "faixa": (255, 255, 255)},
    {"nome": "AMARELO MODENA", "rgb": (245, 195, 15), "faixa": (20, 20, 25)},
    {"nome": "AZUL SAFIRA", "rgb": (25, 100, 235), "faixa": (140, 215, 255)},
    {"nome": "VERDE ESMERALDA", "rgb": (20, 175, 85), "faixa": (255, 230, 60)},
    {"nome": "PRETO CARBONO", "rgb": (32, 34, 40), "faixa": (235, 45, 45)},
    {"nome": "BRANCO PÉROLA", "rgb": (235, 240, 245), "faixa": (25, 95, 220)},
    {"nome": "LARANJA MCLAREN", "rgb": (245, 105, 20), "faixa": (25, 25, 30)},
]

RODAS = [
    {"nome": "LIGA LEVE PRATA", "cor_aro": (200, 205, 215), "aderencia": 0.96, "largura": 22},
    {"nome": "FORJADA DOURADA", "cor_aro": (235, 190, 50), "aderencia": 1.10, "largura": 25},
    {"nome": "SLICK FIBRA CARBONO", "cor_aro": (45, 48, 55), "aderencia": 1.24, "largura": 28},
]

PISTAS = [
    {
        "nome": "COSTA DO SOL",
        "ceu_topo": (25, 110, 210), "ceu_base": (135, 205, 250),
        "grama1": (34, 145, 55), "grama2": (28, 125, 45),
        "asfalto1": (65, 68, 75), "asfalto2": (55, 58, 65),
        "zebra1": (235, 45, 45), "zebra2": (245, 245, 245),
        "montanha": (45, 95, 135), "clima": "limpo", "aderencia": 1.0, "comprimento": 4200
    },
    {
        "nome": "DESERTO ESCARLATE",
        "ceu_topo": (180, 65, 30), "ceu_base": (250, 175, 85),
        "grama1": (210, 130, 60), "grama2": (190, 110, 48),
        "asfalto1": (75, 65, 62), "asfalto2": (65, 56, 54),
        "zebra1": (245, 195, 40), "zebra2": (40, 40, 40),
        "montanha": (140, 55, 35), "clima": "poeira", "aderencia": 0.93, "comprimento": 4800
    },
    {
        "nome": "AUTOESTRADA NOTURNA",
        "ceu_topo": (8, 10, 25), "ceu_base": (25, 35, 65),
        "grama1": (15, 30, 22), "grama2": (12, 24, 18),
        "asfalto1": (35, 38, 45), "asfalto2": (28, 30, 38),
        "zebra1": (0, 210, 255), "zebra2": (255, 255, 255),
        "montanha": (15, 20, 40), "clima": "chuva", "aderencia": 0.85, "comprimento": 5200
    },
    {
        "nome": "ALPES CONGELADOS",
        "ceu_topo": (90, 135, 175), "ceu_base": (210, 230, 245),
        "grama1": (225, 238, 248), "grama2": (200, 218, 235),
        "asfalto1": (85, 95, 110), "asfalto2": (72, 82, 98),
        "zebra1": (220, 40, 60), "zebra2": (255, 255, 255),
        "montanha": (150, 175, 200), "clima": "neve", "aderencia": 0.78, "comprimento": 5500
    }
]

# ==============================================================================
# FUNÇÕES DE DESENHO REALISTA (CARRO DO JOGADOR, RIVAIS, CENÁRIO E HUD)
# ==============================================================================
def desenhar_gradiente(superficie, cor_topo, cor_base, rect):
    x, y, w, h = rect
    for i in range(h):
        fator = i / max(1, h)
        r = int(cor_topo[0] + (cor_base[0] - cor_topo[0]) * fator)
        g = int(cor_topo[1] + (cor_base[1] - cor_topo[1]) * fator)
        b = int(cor_topo[2] + (cor_base[2] - cor_topo[2]) * fator)
        pygame.draw.line(superficie, (r, g, b), (x, y + i), (x + w, y + i))

def ajustar_cor(cor, delta):
    return tuple(max(0, min(255, c + delta)) for c in cor)

def desenhar_carro_realista(surf, cx, cy, escala, cor, faixa, cor_aro, larg_pneu, direcao, nitro_ativo, freando, noturno):
    if escala < 0.05:
        return
    inc = int(direcao * 9 * escala)
    pw = max(3, int(larg_pneu * escala))
    ph = max(4, int(34 * escala))

    # 1. Sombra realista projetada no asfalto
    sw = int(152 * escala)
    sh = max(3, int(24 * escala))
    pygame.draw.ellipse(surf, (12, 14, 18), (cx - sw // 2, cy + int(24 * escala), sw, sh))

    # 2. Pneus traseiros largos + detalhe da roda/aro customizado
    rx_esq = cx - int(68 * escala) + inc // 2
    rx_dir = cx + int(68 * escala) - pw + inc // 2
    ry_pneu = cy + int(4 * escala)
    pygame.draw.rect(surf, (16, 16, 18), (rx_esq, ry_pneu, pw, ph), border_radius=max(1, int(4 * escala)))
    pygame.draw.rect(surf, (16, 16, 18), (rx_dir, ry_pneu, pw, ph), border_radius=max(1, int(4 * escala)))
    # Detalhe metálico do aro na borda do pneu
    if pw >= 6:
        pygame.draw.line(surf, cor_aro, (rx_esq + 2, ry_pneu + 3), (rx_esq + 2, ry_pneu + ph - 3), max(1, int(2 * escala)))
        pygame.draw.line(surf, cor_aro, (rx_dir + pw - 3, ry_pneu + 3), (rx_dir + pw - 3, ry_pneu + ph - 3), max(1, int(2 * escala)))

    # 3. Difusor traseiro inferior (fibra de carbono)
    difusor = [
        (cx - int(58 * escala) + inc // 2, cy + int(16 * escala)),
        (cx + int(58 * escala) + inc // 2, cy + int(16 * escala)),
        (cx + int(52 * escala) + inc // 2, cy + int(28 * escala)),
        (cx - int(52 * escala) + inc // 2, cy + int(28 * escala)),
    ]
    pygame.draw.polygon(surf, (22, 24, 28), difusor)

    # 4. Carroceria inferior (saia e para-choque esculpido)
    cor_sombra = ajustar_cor(cor, -45)
    cor_brilho = ajustar_cor(cor, 45)
    base_corpo = [
        (cx - int(62 * escala) + inc, cy - int(6 * escala)),
        (cx + int(62 * escala) + inc, cy - int(6 * escala)),
        (cx + int(66 * escala) + inc // 2, cy + int(20 * escala)),
        (cx - int(66 * escala) + inc // 2, cy + int(20 * escala)),
    ]
    pygame.draw.polygon(surf, cor, base_corpo)
    pygame.draw.polygon(surf, cor_sombra, base_corpo, max(1, int(2 * escala)))

    # 5. Para-lamas musculosos (arcos das rodas)
    pygame.draw.ellipse(surf, cor_brilho, (cx - int(64 * escala) + inc, cy - int(11 * escala), int(34 * escala), int(14 * escala)))
    pygame.draw.ellipse(surf, cor_brilho, (cx + int(30 * escala) + inc, cy - int(11 * escala), int(34 * escala), int(14 * escala)))

    # 6. Cabine e vidro traseiro inclinado (com reflexo)
    cabine = [
        (cx - int(36 * escala) + int(inc * 1.3), cy - int(32 * escala)),
        (cx + int(36 * escala) + int(inc * 1.3), cy - int(32 * escala)),
        (cx + int(50 * escala) + inc, cy - int(6 * escala)),
        (cx - int(50 * escala) + inc, cy - int(6 * escala)),
    ]
    pygame.draw.polygon(surf, cor, cabine)

    vidro = [
        (cx - int(31 * escala) + int(inc * 1.25), cy - int(29 * escala)),
        (cx + int(31 * escala) + int(inc * 1.25), cy - int(29 * escala)),
        (cx + int(42 * escala) + inc, cy - int(9 * escala)),
        (cx - int(42 * escala) + inc, cy - int(9 * escala)),
    ]
    pygame.draw.polygon(surf, (22, 32, 46), vidro)
    # Reflexo diagonal no vidro traseiro
    if escala > 0.35:
        pygame.draw.line(
            surf, (95, 130, 165),
            (cx - int(18 * escala) + int(inc * 1.2), cy - int(27 * escala)),
            (cx - int(28 * escala) + inc, cy - int(11 * escala)),
            max(1, int(3 * escala))
        )

Use o código com cuidado.
# 7. Faixas de corrida duplas
if escala > 0.25:
fw = max(1, int(4 * escala))
pygame.draw.line(surf, faixa, (cx - int(6 * escala) + int(inc * 1.3), cy - int(32 * escala)), (cx - int(7 * escala) + inc // 2, cy + int(19 * escala)), fw)
pygame.draw.line(surf, faixa, (cx + int(6 * escala) + int(inc * 1.3), cy - int(32 * escala)), (cx + int(7 * escala) + inc // 2, cy + int(19 * escala)), fw)
# 8. Retrovisores laterais aerodinâmicos
if escala > 0.35:
pygame.draw.ellipse(surf, cor, (cx - int(54 * escala) + int(inc * 1.15), cy - int(18 * escala), int(12 * escala), int(6 * escala)))
pygame.draw.ellipse(surf, cor, (cx + int(42 * escala) + int(inc * 1.15), cy - int(18 * escala), int(12 * escala), int(6 * escala)))
# 9. Aerofólio traseiro em fibra de carbono
asa_y = cy - int(15 * escala)
pygame.draw.rect(surf, (25, 27, 32), (cx - int(44 * escala) + inc, asa_y + int(4 * escala), int(6 * escala), int(7 * escala)))
pygame.draw.rect(surf, (25, 27, 32), (cx + int(38 * escala) + inc, asa_y + int(4 * escala), int(6 * escala), int(7 * escala)))
pygame.draw.rect(surf, (30, 32, 38), (cx - int(66 * escala) + inc, asa_y, int(132 * escala), max(2, int(6 * escala))), border_radius=2)
pygame.draw.line(surf, cor_brilho, (cx - int(65 * escala) + inc, asa_y), (cx + int(65 * escala) + inc, asa_y), max(1, int(2 * escala)))
# 10. Conjunto óptico traseiro (lanternas LED)
cor_lanterna = (255, 35, 35) if (freando or noturno) else (165, 15, 20)
lw = max(3, int(34 * escala))
lh = max(2, int(8 * escala))
ly = cy + int(1 * escala)
pygame.draw.rect(surf, (20, 10, 10), (cx - int(58 * escala) + inc // 2, ly - 1, lw + 2, lh + 2), border_radius=2)
pygame.draw.rect(surf, (20, 10, 10), (cx + int(58 * escala) - lw + inc // 2, ly - 1, lw + 2, lh + 2), border_radius=2)
pygame.draw.rect(surf, cor_lanterna, (cx - int(57 * escala) + inc // 2, ly, lw, lh), border_radius=2)
pygame.draw.rect(surf, cor_lanterna, (cx + int(59 * escala) - lw + inc // 2, ly, lw, lh), border_radius=2)
if freando and escala > 0.35:
halo = pygame.Surface((int(56 * escala), int(26 * escala)), pygame.SRCALPHA)
pygame.draw.ellipse(halo, (255, 50, 50, 110), (0, 0, halo.get_width(), halo.get_height()))
surf.blit(halo, (cx - int(66 * escala) + inc // 2, ly - int(8 * escala)))
surf.blit(halo, (cx + int(10 * escala) + inc // 2, ly - int(8 * escala)))
# 11. Escapamento quádruplo esportivo e chamas do Nitro
if escala > 0.25:
raio_esc = max(2, int(4.5 * escala))
for ex in (-38, -27, 27, 38):
bx = cx + int(ex * escala) + inc // 2
by = cy + int(21 * escala)
pygame.draw.circle(surf, (15, 15, 18), (bx, by), raio_esc + 1)
pygame.draw.circle(surf, (150, 155, 165), (bx, by), raio_esc, 1)
if nitro_ativo:
tam_chama = int(random.randint(24, 46) * escala)
pygame.draw.polygon(surf, (0, 185, 255), [(bx - raio_esc, by), (bx + raio_esc, by), (bx, by + tam_chama)])
pygame.draw.polygon(surf, (255, 255, 255), [(bx - raio_esc // 2, by), (bx + raio_esc // 2, by), (bx, by + tam_chama // 2)])
def desenhar_galao(surf, cx, cy, escala):
w = max(6, int(36 * escala))
h = max(8, int(46 * escala))
x = int(cx - w // 2)
y = int(cy - h)
pygame.draw.rect(surf, (230, 35, 35), (x, y, w, h), border_radius=max(2, int(5 * escala)))
pygame.draw.rect(surf, (255, 220, 40), (x + w // 4, y - max(2, int(6 * escala)), w // 2, max(2, int(6 * escala))))
if w > 14:
pygame.draw.line(surf, (255, 255, 255), (x + 4, y + 6), (x + w - 4, y + h - 6), 2)
pygame.draw.line(surf, (255, 255, 255), (x + w - 4, y + 6), (x + 4, y + h - 6), 2)
def desenhar_tacometro(surf, cx, cy, raio, rpm, marcha):
pygame.draw.circle(surf, (15, 18, 25), (cx, cy), raio)
pygame.draw.circle(surf, (200, 205, 215), (cx, cy), raio, 3)
rect_arco = (cx - raio + 8, cy - raio + 8, (raio - 8) * 2, (raio - 8) * 2)
pygame.draw.arc(surf, (235, 45, 45), rect_arco, -0.3, 0.7, 6)
for i in range(9):
ang = math.radians(225 - i * 33.75)
x1 = cx + math.cos(ang) * (raio - 14)
y1 = cy - math.sin(ang) * (raio - 14)
x2 = cx + math.cos(ang) * (raio - 5)
y2 = cy - math.sin(ang) * (raio - 5)
cor_m = (255, 60, 60) if i >= 6 else (240, 240, 240)
pygame.draw.line(surf, cor_m, (x1, y1), (x2, y2), 2)
ang_ponteiro = math.radians(225 - rpm * 270)
px = cx + math.cos(ang_ponteiro) * (raio - 12)
py = cy - math.sin(ang_ponteiro) * (raio - 12)
pygame.draw.line(surf, (255, 180, 0), (cx, cy), (px, py), 3)
pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 6)
txt_m = fonte_media.render(f"{marcha}ª", True, (0, 230, 140))
surf.blit(txt_m, (cx - txt_m.get_width() // 2, cy + 12))
def criar_segmentos_pista(comprimento):
segmentos = []
curva_atual = 0.0
inclinacao_atual = 0.0
for i in range(comprimento):
if i % 120 == 0 and 100 < i < comprimento - 200:
curva_atual = random.choice([-2.8, -1.8, -1.0, 0.0, 1.0, 1.8, 2.8])
inclinacao_atual = random.choice([-1.2, -0.6, 0.0, 0.6, 1.2])
elif i >= comprimento - 200:
curva_atual = 0.0
inclinacao_atual = 0.0
segmentos.append({
"curva": curva_atual,
"inclinacao": inclinacao_atual,
"objeto": random.choice(["arvore", "poste", None, None]) if i % 6 == 0 else None,
"lado_obj": random.choice([-1, 1])
})
return segmentos

==============================================================================


CLASSE PRINCIPAL DO JOGO


==============================================================================

class JogoTopGear:
def init(self):
self.estado = "MENU"
# Índices da Garagem / Tuning
self.motor_idx = 1
self.freio_idx = 1
self.cor_idx = 0
self.roda_idx = 1
self.pista_idx = 0
self.categoria_menu = 0  # 0: Motor, 1: Freios, 2: Pintura, 3: Rodas, 4: Pista
self.mudo = False
self.recordes = {}
def iniciar_corrida(self):
self.motor = MOTORES[self.motor_idx]
self.freio = FREIOS[self.freio_idx]
self.pintura = CORES_PINTURA[self.cor_idx]
self.roda = RODAS[self.roda_idx]
self.pista = PISTAS[self.pista_idx]
self.segmentos = criar_segmentos_pista(self.pista["comprimento"])
self.pos_pista = 0.0
self.jogador_x = 0.0
self.velocidade = 0.0
self.marcha = 1
self.rpm = 0.1
self.combustivel = 100.0
self.nitros = 3
self.tempo_nitro = 0.0
self.tempo_corrida = 0.0
self.contagem_largada = 3.5
self.ultimo_bip = 4
self.tremor = 0
self.motivo_fim = ""
self.particulas = []
self.clima_particulas = [
[random.randint(0, LARGURA), random.randint(0, ALTURA), random.uniform(8, 16)]
for _ in range(95)
]
# Grid expandido com 29 rivais (30 carros no total na corrida!)
self.rivais = []
for i in range(1, 30):
estilo = random.choice(CORES_PINTURA)
self.rivais.append({
"z": i * 135.0 + random.uniform(-25, 25),
"x": random.uniform(-0.72, 0.72),
"alvo_x": random.uniform(-0.72, 0.72),
"timer_faixa": random.uniform(1.5, 4.5),
"vel": random.uniform(165, 265),
"cor": estilo["rgb"],
"faixa": estilo["faixa"],
"aro": random.choice(RODAS)["cor_aro"]
})
self.galoes = []
for z in range(750, self.pista["comprimento"] - 300, 620):
self.galoes.append({"z": float(z), "x": random.uniform(-0.6, 0.6), "coletado": False})
self.estado = "CORRIDA"
if not self.mudo:
trilha_sonora.play(loops=-1)
def encerrar_corrida(self, motivo):
self.motivo_fim = motivo
self.estado = "FIM"
trilha_sonora.stop()
if motivo == "CHEGADA":
chave = self.pista["nome"]
if chave not in self.recordes or self.tempo_corrida < self.recordes[chave]:
self.recordes[chave] = self.tempo_corrida
def atualizar_corrida(self, dt, teclas):
if self.contagem_largada > 0:
self.contagem_largada -= dt
segundo_atual = math.ceil(self.contagem_largada)
if segundo_atual < self.ultimo_bip and segundo_atual > 0:
self.ultimo_bip = segundo_atual
if not self.mudo:
som_largada_baixo.play()
elif self.contagem_largada <= 0 and self.ultimo_bip != 0:
self.ultimo_bip = 0
if not self.mudo:
som_largada_alto.play()
return
self.tempo_corrida += dt
acelerando = teclas[pygame.K_UP] or teclas[pygame.K_w]
freando = teclas[pygame.K_DOWN] or teclas[pygame.K_s]
dir_x = (-1.0 if (teclas[pygame.K_LEFT] or teclas[pygame.K_a]) else 0.0) + (1.0 if (teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) else 0.0)
if self.tempo_nitro > 0:
self.tempo_nitro -= dt
nitro_ativo = self.tempo_nitro > 0
vel_max_atual = self.motor["vel_max"] * (1.26 if nitro_ativo else 1.0)
# Escalonamento dinâmico das 5 marchas conforme o motor instalado
limites_marcha = [
0,
vel_max_atual * 0.28,
vel_max_atual * 0.50,
vel_max_atual * 0.70,
vel_max_atual * 0.86,
vel_max_atual
]
teto_marcha = limites_marcha[self.marcha]
if self.combustivel > 0:
if acelerando or nitro_ativo:
fator_marcha = 1.38 - (self.marcha * 0.14)
ganho = 96.0 * self.motor["acel"] * fator_marcha * (1.55 if nitro_ativo else 1.0)
if self.velocidade < teto_marcha:
self.velocidade += ganho * dt
else:
self.velocidade -= 25.0 * dt
else:
self.velocidade -= 40.0 * dt
else:
self.velocidade -= 65.0 * dt
if freando:
self.velocidade -= self.freio["forca"] * dt
fora_pista = abs(self.jogador_x) > 1.05
if fora_pista:
self.velocidade -= 110.0 * dt
if self.velocidade > 40:
self.tremor = 4
self.particulas.append([LARGURA // 2 + random.randint(-55, 55), ALTURA - 85, random.uniform(-2, 2), random.uniform(-4, -1), self.pista["grama1"], 12])
self.velocidade = max(0.0, min(vel_max_atual, self.velocidade))
piso_marcha = limites_marcha[self.marcha - 1] * 0.72
self.rpm = max(0.12, min(1.0, (self.velocidade - piso_marcha) / max(1.0, (teto_marcha - piso_marcha))))
idx_seg = int(self.pos_pista) % len(self.segmentos)
seg_atual = self.segmentos[idx_seg]
self.pos_pista += (self.velocidade / 60.0) * dt * 28.0
forca_centrifuga = seg_atual["curva"] * (self.velocidade / 265.0) * 0.58 * dt
aderencia = self.roda["aderencia"] * self.pista["aderencia"]
self.jogador_x += (dir_x * 1.62 * aderencia * (min(1.0, self.velocidade / 70.0)) * dt) - forca_centrifuga
self.jogador_x = max(-1.85, min(1.85, self.jogador_x))
if abs(dir_x) > 0 and self.velocidade > 150 and (aderencia < 0.95 or abs(seg_atual["curva"]) > 1.5):
self.particulas.append([LARGURA // 2 + random.randint(-45, 45), ALTURA - 80, random.uniform(-1, 1), random.uniform(-2, 0), (220, 220, 220), 10])
if self.velocidade > 5:
gasto = (0.82 + (self.velocidade / 185.0)) * self.motor["consumo"] * (1.45 if nitro_ativo else 1.0)
self.combustivel = max(0.0, self.combustivel - gasto * dt)
if self.combustivel <= 0 and self.velocidade <= 2:
self.encerrar_corrida("SEM_COMBUSTIVEL")
return
# Inteligência e movimentação dos 29 rivais
for r in self.rivais:
r["z"] += (r["vel"] / 60.0) * dt * 28.0
r["timer_faixa"] -= dt
if r["timer_faixa"] <= 0:
r["alvo_x"] = random.uniform(-0.75, 0.75)
r["timer_faixa"] = random.uniform(2.0, 5.0)
r["x"] += (r["alvo_x"] - r["x"]) * 0.8 * dt
dist_z = r["z"] - self.pos_pista
if 0 < dist_z < 2.2 and abs(r["x"] - self.jogador_x) < 0.34:
self.velocidade *= 0.48
self.tremor = 12
r["z"] += 4.5
if not self.mudo:
som_batida.play()
for _ in range(14):
self.particulas.append([LARGURA // 2, ALTURA - 100, random.uniform(-6, 6), random.uniform(-6, 2), (255, 210, 50), 15])
for g in self.galoes:
if not g["coletado"]:
dist_z = g["z"] - self.pos_pista
if -1.5 < dist_z < 2.5 and abs(g["x"] - self.jogador_x) < 0.36:
g["coletado"] = True
self.combustivel = min(100.0, self.combustivel + 35.0)
if not self.mudo:
som_combustivel.play()
for p in self.particulas[:]:
p[0] += p[2]
p[1] += p[3]
p[5] -= 1
if p[5] <= 0:
self.particulas.remove(p)
if self.tremor > 0:
self.tremor -= 1
if self.pos_pista >= self.pista["comprimento"] - 50:
self.encerrar_corrida("CHEGADA")
def desenhar_corrida(self):
offset_x = random.randint(-self.tremor, self.tremor) if self.tremor > 0 else 0
offset_y = random.randint(-self.tremor, self.tremor) if self.tremor > 0 else 0
idx_base = int(self.pos_pista)
seg_base = self.segmentos[idx_base % len(self.segmentos)]
horizonte = ALTURA // 2 - int(seg_base["inclinacao"] * 28) + offset_y
desenhar_gradiente(tela, self.pista["ceu_topo"], self.pista["ceu_base"], (0, 0, LARGURA, max(1, horizonte)))
if self.pista["clima"] == "chuva":
for sx in range(40, LARGURA, 95):
sy = (sx * 37) % max(40, horizonte - 30)
pygame.draw.circle(tela, (230, 240, 255), (sx, sy), 1)
desloc_montanha = int((self.pos_pista * 0.4 + seg_base["curva"] * 40) % LARGURA)
for m in range(-1, 3):
mx = m * 500 - desloc_montanha
pts = [(mx, horizonte), (mx + 165, horizonte - 85), (mx + 320, horizonte - 45), (mx + 500, horizonte)]
pygame.draw.polygon(tela, self.pista["montanha"], pts)
linhas_visiveis = ALTURA - horizonte
curva_acumulada = 0.0
desloc_curva = 0.0
objetos_para_desenhar = []
for y in range(ALTURA - 1, horizonte, -1):
dist_tela = y - horizonte
z = (linhas_visiveis / max(1, dist_tela)) * 12.0
seg_idx = int(self.pos_pista + z)
seg = self.segmentos[seg_idx % len(self.segmentos)]
curva_acumulada += seg["curva"] * 0.0045
desloc_curva += curva_acumulada
escala = dist_tela / max(1.0, linhas_visiveis)
centro_pista = (LARGURA // 2) - (self.jogador_x * 370 * escala) + desloc_curva + offset_x
largura_pista = 40 + 480 * escala
largura_zebra = largura_pista * 0.11
faixa_alternada = (seg_idx // 3) % 2 == 0
cor_grama = self.pista["grama1"] if faixa_alternada else self.pista["grama2"]
cor_asfalto = self.pista["asfalto1"] if faixa_alternada else self.pista["asfalto2"]
cor_zebra = self.pista["zebra1"] if faixa_alternada else self.pista["zebra2"]
if self.pista["comprimento"] - 55 <= seg_idx <= self.pista["comprimento"] - 48:
cor_asfalto = (245, 245, 245) if (seg_idx % 2 == 0) else (20, 20, 20)
pygame.draw.line(tela, cor_grama, (0, y), (LARGURA, y))
pygame.draw.line(tela, cor_zebra, (centro_pista - largura_pista - largura_zebra, y), (centro_pista + largura_pista + largura_zebra, y))
pygame.draw.line(tela, cor_asfalto, (centro_pista - largura_pista, y), (centro_pista + largura_pista, y))
if faixa_alternada:
fw = max(1, int(5 * escala))
pygame.draw.line(tela, (240, 240, 240), (centro_pista - largura_pista * 0.33 - fw, y), (centro_pista - largura_pista * 0.33 + fw, y))
pygame.draw.line(tela, (240, 240, 240), (centro_pista + largura_pista * 0.33 - fw, y), (centro_pista + largura_pista * 0.33 + fw, y))
if seg["objeto"] and int(z) != int((linhas_visiveis / max(1, dist_tela + 1)) * 12.0):
ox = centro_pista + seg["lado_obj"] * (largura_pista + largura_zebra + 45 * escala)
objetos_para_desenhar.append(("cenario", seg["objeto"], ox, y, escala))
for r in self.rivais:
dz = r["z"] - self.pos_pista
if 1.0 < dz < 145.0:
escala = min(1.15, 12.0 / dz)
ry = horizonte + int(linhas_visiveis * escala)
if horizonte < ry < ALTURA:
rx = (LARGURA // 2) + (r["x"] - self.jogador_x) * 370 * escala + offset_x
objetos_para_desenhar.append(("rival", r, rx, ry, escala))
