"""Constantes de configuração do jogo. Ajuste aqui em vez de espalhar
valores mágicos pelo resto do código."""

from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# --- Janela / performance (Raspberry Pi 3: 1GB RAM, quad-core 1.2GHz) ---
TILE_SIZE_PX = 32
FPS = 30
LARGURA_TELA = 800
ALTURA_TELA = 480

# --- Caminhos ---
PASTA_ASSETS = RAIZ_PROJETO / "assets"
PASTA_TILES = PASTA_ASSETS / "tiles"
PASTA_PERSONAGEM = PASTA_ASSETS / "personagem"
PASTA_MAPAS = RAIZ_PROJETO / "mapas"

# --- Servidor Flask embutido ---
HOST_SERVIDOR = "0.0.0.0"
PORTA_SERVIDOR = 5000

# --- Personagem ---
VELOCIDADE_TILES_POR_SEGUNDO = 4.0
TAMANHO_COLISAO_TILES = 0.6  # bounding box do personagem, em tiles

# --- Controle Xbox ---
DEADZONE_JOYSTICK = 0.2

# --- Serial (Arduino) ---
PORTA_SERIAL = "/dev/ttyACM0"
BAUDRATE_SERIAL = 9600
INTERVALO_RECONEXAO_SERIAL_SEG = 3.0

# --- Overlay de iluminação apagada ---
ALPHA_OVERLAY_ESCURO = 180  # 0 (transparente) a 255 (opaco)

# Cores placeholder usadas quando os PNGs finais (chao.png, parede.png,
# porta.png, janela.png, spritesheet do personagem) ainda não existem.
# Mesmo esquema de cores do preview do app mobile, para consistência visual.
CORES_PLACEHOLDER_TILES = {
    "CHAO": (58, 53, 63),
    "PAREDE": (74, 74, 74),
    "PORTA": (181, 101, 29),
    "JANELA": (110, 198, 255),
}
COR_PLACEHOLDER_OBJETO = (230, 168, 23)
COR_PLACEHOLDER_PERSONAGEM = (240, 240, 240)
