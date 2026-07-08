"""Conversão do JSON do mapa (coordenadas em metros) em uma grade 2D de
tiles usada pelo motor Pygame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CHAO = "CHAO"
PAREDE = "PAREDE"
PORTA = "PORTA"
JANELA = "JANELA"
PREFIXO_OBJETO = "OBJETO_"

# Quantos tiles de margem sobram ao redor do desenho, para o personagem não
# nascer colado na borda da grade.
MARGEM_TILES = 2


def nome_tile_objeto(tipo: str) -> str:
    return f"{PREFIXO_OBJETO}{tipo}"


def eh_objeto(tile: str) -> bool:
    return tile.startswith(PREFIXO_OBJETO)


@dataclass
class GradeMapa:
    tiles: list[list[str]]
    largura_tiles: int
    altura_tiles: int
    tamanho_tile_px: int
    escala_metros_por_tile: float
    nome_ambiente: str
    offset_tiles: tuple[int, int] = field(default=(0, 0))

    def tile_em(self, coluna: int, linha: int) -> str | None:
        if 0 <= linha < self.altura_tiles and 0 <= coluna < self.largura_tiles:
            return self.tiles[linha][coluna]
        return None

    def bloqueia_movimento(self, coluna: int, linha: int) -> bool:
        tile = self.tile_em(coluna, linha)
        if tile is None:
            return True  # fora da grade é tratado como parede
        return tile == PAREDE or tile == JANELA or eh_objeto(tile)


def linha_bresenham(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """Rasteriza o segmento (x0,y0)-(x1,y1) em tiles inteiros usando o
    algoritmo de Bresenham (funciona para qualquer inclinação/octante)."""
    pontos: list[tuple[int, int]] = []

    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    erro = dx + dy

    x, y = x0, y0
    while True:
        pontos.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * erro
        if e2 >= dy:
            erro += dy
            x += sx
        if e2 <= dx:
            erro += dx
            y += sy

    return pontos


def _pontos_em_metros(dados_mapa: dict[str, Any]) -> list[tuple[float, float]]:
    pontos: list[tuple[float, float]] = []
    for parede in dados_mapa["paredes"]:
        pontos.append(tuple(parede["inicio"]))
        pontos.append(tuple(parede["fim"]))
    for porta in dados_mapa["portas"]:
        pontos.append(tuple(porta["posicao"]))
    for janela in dados_mapa["janelas"]:
        pontos.append(tuple(janela["posicao"]))
    for objeto in dados_mapa["objetos"]:
        pontos.append(tuple(objeto["posicao"]))
    return pontos


def _detectar_orientacao_parede(
    tiles: list[list[str]], coluna: int, linha: int
) -> str:
    """Olha os tiles vizinhos já rasterizados como PAREDE para decidir se a
    abertura (porta/janela) deve se estender na horizontal ou na vertical."""
    altura = len(tiles)
    largura = tiles[0]

    def eh_parede(c: int, r: int) -> bool:
        if r < 0 or r >= altura or c < 0 or c >= len(largura):
            return False
        return tiles[r][c] == PAREDE

    paredes_horizontais = eh_parede(coluna - 1, linha) or eh_parede(coluna + 1, linha)
    paredes_verticais = eh_parede(coluna, linha - 1) or eh_parede(coluna, linha + 1)

    if paredes_verticais and not paredes_horizontais:
        return "vertical"
    return "horizontal"  # padrão quando ambíguo/sem paredes próximas


def converter_json_em_grade(
    dados_mapa: dict[str, Any], tamanho_tile_px: int = 32
) -> GradeMapa:
    """Converte o JSON compartilhado (coordenadas em metros) em uma
    `GradeMapa` de tiles (`PAREDE`, `CHAO`, `PORTA`, `JANELA`,
    `OBJETO_<tipo>`).

    `tamanho_tile_px` não afeta os cálculos de posição (que dependem apenas
    de `escala_metros_por_tile`); ele é apenas propagado para a `GradeMapa`
    para que o motor Pygame saiba em qual resolução desenhar cada tile.
    """
    escala = float(dados_mapa["escala_metros_por_tile"])
    pontos_m = _pontos_em_metros(dados_mapa)

    if pontos_m:
        xs = [p[0] for p in pontos_m]
        ys = [p[1] for p in pontos_m]
        min_x_tile = min(round(x / escala) for x in xs)
        max_x_tile = max(round(x / escala) for x in xs)
        min_y_tile = min(round(y / escala) for y in ys)
        max_y_tile = max(round(y / escala) for y in ys)
    else:
        min_x_tile = max_x_tile = min_y_tile = max_y_tile = 0

    offset_x = MARGEM_TILES - min_x_tile
    offset_y = MARGEM_TILES - min_y_tile

    largura_tiles = (max_x_tile - min_x_tile) + 2 * MARGEM_TILES + 1
    altura_tiles = (max_y_tile - min_y_tile) + 2 * MARGEM_TILES + 1

    tiles = [[CHAO for _ in range(largura_tiles)] for _ in range(altura_tiles)]

    def para_grade(ponto_m: tuple[float, float]) -> tuple[int, int]:
        x_m, y_m = ponto_m
        coluna = round(x_m / escala) + offset_x
        linha = round(y_m / escala) + offset_y
        return coluna, linha

    def marcar(coluna: int, linha: int, tile: str) -> None:
        if 0 <= linha < altura_tiles and 0 <= coluna < largura_tiles:
            tiles[linha][coluna] = tile

    for parede in dados_mapa["paredes"]:
        c0, l0 = para_grade(tuple(parede["inicio"]))
        c1, l1 = para_grade(tuple(parede["fim"]))
        for coluna, linha in linha_bresenham(c0, l0, c1, l1):
            marcar(coluna, linha, PAREDE)

    def marcar_abertura(posicao_m: tuple[float, float], largura_m: float, tile: str) -> None:
        coluna, linha = para_grade(posicao_m)
        orientacao = _detectar_orientacao_parede(tiles, coluna, linha)
        quantidade_tiles = max(1, round(largura_m / escala))
        inicio = -(quantidade_tiles // 2)
        for i in range(inicio, inicio + quantidade_tiles):
            if orientacao == "horizontal":
                marcar(coluna + i, linha, tile)
            else:
                marcar(coluna, linha + i, tile)

    for porta in dados_mapa["portas"]:
        marcar_abertura(tuple(porta["posicao"]), float(porta["largura"]), PORTA)

    for janela in dados_mapa["janelas"]:
        marcar_abertura(tuple(janela["posicao"]), float(janela["largura"]), JANELA)

    for objeto in dados_mapa["objetos"]:
        coluna, linha = para_grade(tuple(objeto["posicao"]))
        marcar(coluna, linha, nome_tile_objeto(objeto["tipo"]))

    return GradeMapa(
        tiles=tiles,
        largura_tiles=largura_tiles,
        altura_tiles=altura_tiles,
        tamanho_tile_px=tamanho_tile_px,
        escala_metros_por_tile=escala,
        nome_ambiente=dados_mapa["nome_ambiente"],
        offset_tiles=(offset_x, offset_y),
    )
