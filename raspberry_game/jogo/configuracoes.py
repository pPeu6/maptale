"""Constantes de configuração do jogo. Ajuste aqui em vez de espalhar
valores mágicos pelo resto do código."""

from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# --- Janela / performance (Raspberry Pi 3: 1GB RAM, quad-core 1.2GHz) ---
TILE_SIZE_PX = 40
FPS = 30
# Fallback se o modo fullscreen falhar (ex.: sem display).
LARGURA_TELA = 960
ALTURA_TELA = 640
TELA_CHEIA = True

# Resolução "lógica" em que os assets são desenhados por
# `assets/gerador_tiles.py` (pixel art 16x16). O motor amplia por
# TILE_SIZE_PX / TAMANHO_TILE_LOGICO_PX ao carregar.
TAMANHO_TILE_LOGICO_PX = 16

# --- Caminhos ---
PASTA_ASSETS = RAIZ_PROJETO / "assets"
PASTA_TILES = PASTA_ASSETS / "tiles"
PASTA_OBJETOS = PASTA_TILES / "objetos"
PASTA_PERSONAGEM = PASTA_ASSETS / "personagem"
PASTA_MAPAS = RAIZ_PROJETO / "mapas"
MAPA_PADRAO = PASTA_MAPAS / "quarto.json"

# --- Personagem ---
VELOCIDADE_TILES_POR_SEGUNDO = 4.0
TAMANHO_COLISAO_TILES = 0.6

# --- Controle Xbox ---
DEADZONE_JOYSTICK = 0.2

# --- Serial (Arduino) ---
PORTA_SERIAL = "/dev/ttyUSB0"
BAUDRATE_SERIAL = 9600
INTERVALO_RECONEXAO_SERIAL_SEG = 3.0

# --- Overlay de iluminação apagada (luz da serial ON/OFF) ---
ALPHA_OVERLAY_ESCURO = 170

# --- Luz natural (varia com o horário) e feixe de sol ---
# Escuridão máxima adicionada de madrugada/noite (mesmo com a luz acesa é
# amenizada; com a luz apagada soma-se ALPHA_OVERLAY_ESCURO).
ALPHA_NOITE_MAX = 140
# Redução da escuridão noturna quando a luz interna está acesa.
ALPHA_NOITE_COM_LUZ = 45
COR_NOITE = (10, 14, 40)              # tom azulado da escuridão noturna
COR_SOL = (255, 236, 170)            # feixe de sol (amarelo quente, igual nas duas janelas)
ALPHA_FEIXE_MAX = 28                 # transparência máxima do feixe (0-255; menor = mais sutil)
ALCANCE_FEIXE_TILES = 4              # comprimento do feixe em tiles
# Curva do dia: horas (Brasília) de amanhecer/anoitecer.
HORA_AMANHECER = 6.0
HORA_PICO = 13.0
HORA_ANOITECER = 19.0

# --- Cores da planta (renderização top-down procedural) ---
COR_FUNDO = (26, 24, 32)
COR_PISO = (239, 239, 234)            # piso branco do quarto
COR_PISO_LINHA = (210, 211, 207)      # juntas e textura suave
COR_PISO_BANHEIRO = (188, 224, 229)   # cerâmica clara
COR_PISO_BANHEIRO_LINHA = (156, 200, 208)
COR_PISO_BANHEIRO_DETALHE = (181, 218, 224)
COR_PISO_BANHEIRO_BRILHO = (218, 241, 243)
COR_PAREDE = (233, 186, 41)           # paredes: linhas finas amarelas
COR_PAREDE_SOMBRA = (176, 138, 22)
COR_PORTA = (211, 71, 48)             # portas: acento vermelho
COR_PORTA_FOLHA = (196, 150, 92)      # folha de madeira da porta
COR_JANELA_MOLDURA = (233, 186, 41)   # janelas: moldura amarela
COR_JANELA_VIDRO = (176, 221, 236)    # vidro

# Placeholder de objeto quando o PNG do sprite não existe.
COR_PLACEHOLDER_OBJETO = (150, 98, 52)
COR_PLACEHOLDER_PERSONAGEM = (240, 220, 200)

# --- HUD (temperatura + horário + clima) ---
COR_HUD_FUNDO = (18, 24, 42, 210)
COR_HUD_BORDA = (88, 168, 255)
COR_HUD_BRILHO = (120, 200, 255, 80)
COR_HUD_HORA = (255, 248, 220)
COR_HUD_TEMP = (255, 178, 92)
COR_HUD_TEMP_FRIO = (120, 210, 255)
COR_HUD_SEPARADOR = (70, 90, 130)
TAMANHO_FONTE_HUD = 22
TAMANHO_FONTE_HUD_PEQUENA = 16
TAMANHO_ICONE_CLIMA = 28

# --- APIs de ambiente ---
# Itaquaquecetuba / SP
LATITUDE = -23.4864
LONGITUDE = -46.3486
FUSO_HORARIO = "America/Sao_Paulo"
URL_CLIMA = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LATITUDE}&longitude={LONGITUDE}"
    "&current=temperature_2m,weather_code&timezone=America/Sao_Paulo"
)
INTERVALO_ATUALIZACAO_CLIMA_SEG = 600.0  # 10 min
TIMEOUT_CLIMA_SEG = 8.0
