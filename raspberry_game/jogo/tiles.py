"""Carregamento do tileset e renderização da grade.

Prioriza simplicidade/performance (Raspberry Pi 3): sem parallax, sem
iluminação por tile, apenas blits diretos e cull dos tiles fora da tela.
"""

from __future__ import annotations

import pygame

from mapa.grade import CHAO, GradeMapa, JANELA, PAREDE, PORTA, eh_objeto
from . import configuracoes as cfg

_ARQUIVOS_TILE = {
    CHAO: "chao.png",
    PAREDE: "parede.png",
    PORTA: "porta.png",
    JANELA: "janela.png",
}

_fonte_objeto: pygame.font.Font | None = None


def _superficie_placeholder(cor: tuple[int, int, int], tamanho: int) -> pygame.Surface:
    superficie = pygame.Surface((tamanho, tamanho))
    superficie.fill(cor)
    pygame.draw.rect(superficie, (0, 0, 0), superficie.get_rect(), width=1)
    return superficie


def carregar_tileset(tamanho_tile_px: int = cfg.TILE_SIZE_PX) -> dict[str, pygame.Surface]:
    """Carrega os PNGs do tileset (chao/parede/porta/janela). Se algum
    arquivo não existir ainda, usa um retângulo colorido como placeholder,
    para o jogo continuar funcionável antes dos assets finais chegarem."""
    tileset: dict[str, pygame.Surface] = {}

    for tipo_tile, nome_arquivo in _ARQUIVOS_TILE.items():
        caminho = cfg.PASTA_TILES / nome_arquivo
        if caminho.exists():
            imagem = pygame.image.load(str(caminho)).convert()
            if imagem.get_size() != (tamanho_tile_px, tamanho_tile_px):
                imagem = pygame.transform.scale(imagem, (tamanho_tile_px, tamanho_tile_px))
            tileset[tipo_tile] = imagem
        else:
            cor = cfg.CORES_PLACEHOLDER_TILES[tipo_tile]
            tileset[tipo_tile] = _superficie_placeholder(cor, tamanho_tile_px)

    return tileset


def _obter_fonte() -> pygame.font.Font:
    global _fonte_objeto
    if _fonte_objeto is None:
        _fonte_objeto = pygame.font.SysFont(None, 16)
    return _fonte_objeto


def _superficie_objeto(tipo: str, tamanho_tile_px: int) -> pygame.Surface:
    superficie = _superficie_placeholder(cfg.COR_PLACEHOLDER_OBJETO, tamanho_tile_px)
    letra = tipo[len("OBJETO_"):][:1].upper() if tipo.startswith("OBJETO_") else "?"
    texto = _obter_fonte().render(letra, True, (30, 30, 30))
    retangulo_texto = texto.get_rect(center=(tamanho_tile_px // 2, tamanho_tile_px // 2))
    superficie.blit(texto, retangulo_texto)
    return superficie


def desenhar_grade(
    tela: pygame.Surface,
    grade: GradeMapa,
    tileset: dict[str, pygame.Surface],
    camera_offset_px: tuple[int, int],
) -> None:
    """Desenha apenas os tiles visíveis na tela (viewport culling)."""
    tamanho = grade.tamanho_tile_px
    offset_x, offset_y = camera_offset_px
    largura_tela, altura_tela = tela.get_size()

    coluna_inicial = max(0, offset_x // tamanho)
    linha_inicial = max(0, offset_y // tamanho)
    coluna_final = min(grade.largura_tiles, (offset_x + largura_tela) // tamanho + 2)
    linha_final = min(grade.altura_tiles, (offset_y + altura_tela) // tamanho + 2)

    cache_objetos: dict[str, pygame.Surface] = {}

    for linha in range(linha_inicial, linha_final):
        for coluna in range(coluna_inicial, coluna_final):
            tile = grade.tiles[linha][coluna]
            if eh_objeto(tile):
                superficie = cache_objetos.get(tile)
                if superficie is None:
                    superficie = _superficie_objeto(tile, tamanho)
                    cache_objetos[tile] = superficie
                # Desenha o chão embaixo do objeto para não deixar buraco.
                tela.blit(tileset[CHAO], (coluna * tamanho - offset_x, linha * tamanho - offset_y))
            else:
                superficie = tileset[tile]

            tela.blit(superficie, (coluna * tamanho - offset_x, linha * tamanho - offset_y))
