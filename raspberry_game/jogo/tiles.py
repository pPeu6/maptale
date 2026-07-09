"""Carregamento do tileset, sprites de móveis e renderização da grade.

Prioriza simplicidade/performance (Raspberry Pi 3): blits diretos e cull
dos tiles fora da tela.
"""

from __future__ import annotations

import pygame

from mapa.grade import CHAO, GradeMapa, JANELA, PAREDE, PORTA, SpriteObjeto, eh_objeto
from . import configuracoes as cfg

_ARQUIVOS_TILE = {
    CHAO: "chao.png",
    PAREDE: "parede.png",
    f"{PORTA}_horizontal": "porta_horizontal.png",
    f"{PORTA}_vertical": "porta_vertical.png",
    f"{JANELA}_horizontal": "janela_horizontal.png",
    f"{JANELA}_vertical": "janela_vertical.png",
}


def _superficie_placeholder(cor: tuple[int, int, int], tamanho: tuple[int, int]) -> pygame.Surface:
    superficie = pygame.Surface(tamanho)
    superficie.fill(cor)
    pygame.draw.rect(superficie, (0, 0, 0), superficie.get_rect(), width=1)
    return superficie


def carregar_tileset(tamanho_tile_px: int = cfg.TILE_SIZE_PX) -> dict[str, pygame.Surface]:
    tileset: dict[str, pygame.Surface] = {}
    alvo = (tamanho_tile_px, tamanho_tile_px)

    # Chão / parede
    for tipo in (CHAO, PAREDE):
        caminho = cfg.PASTA_TILES / f"{tipo.lower()}.png"
        if caminho.exists():
            imagem = pygame.image.load(str(caminho)).convert()
            if imagem.get_size() != alvo:
                imagem = pygame.transform.scale(imagem, alvo)
            tileset[tipo] = imagem
        else:
            tileset[tipo] = _superficie_placeholder(cfg.CORES_PLACEHOLDER_TILES[tipo], alvo)

    # Portas / janelas (horizontal + vertical)
    for tipo, nome_base in ((PORTA, "porta"), (JANELA, "janela")):
        for orientacao in ("horizontal", "vertical"):
            chave = f"{tipo}_{orientacao}"
            caminho = cfg.PASTA_TILES / f"{nome_base}_{orientacao}.png"
            if caminho.exists():
                imagem = pygame.image.load(str(caminho)).convert()
                if imagem.get_size() != alvo:
                    imagem = pygame.transform.scale(imagem, alvo)
                tileset[chave] = imagem
            else:
                tileset[chave] = _superficie_placeholder(cfg.CORES_PLACEHOLDER_TILES[tipo], alvo)

    return tileset


def carregar_sprites_objetos(tamanho_tile_px: int = cfg.TILE_SIZE_PX) -> dict[str, pygame.Surface]:
    """Carrega PNGs de `assets/tiles/objetos/<tipo>.png`."""
    sprites: dict[str, pygame.Surface] = {}
    pasta = cfg.PASTA_OBJETOS
    if not pasta.exists():
        return sprites

    fator = tamanho_tile_px / cfg.TAMANHO_TILE_LOGICO_PX
    for caminho in sorted(pasta.glob("*.png")):
        imagem = pygame.image.load(str(caminho)).convert_alpha()
        alvo = (round(imagem.get_width() * fator), round(imagem.get_height() * fator))
        if imagem.get_size() != alvo:
            imagem = pygame.transform.scale(imagem, alvo)
        sprites[caminho.stem] = imagem
    return sprites


def _sprite_para(
    sprite_info: SpriteObjeto,
    sprites: dict[str, pygame.Surface],
    tamanho_tile_px: int,
) -> pygame.Surface:
    existente = sprites.get(sprite_info.tipo)
    if existente is not None:
        return existente
    w = sprite_info.largura_tiles * tamanho_tile_px
    h = sprite_info.altura_tiles * tamanho_tile_px
    return _superficie_placeholder(cfg.COR_PLACEHOLDER_OBJETO, (w, h))


def _superficie_tile(
    tile: str,
    coluna: int,
    linha: int,
    grade: GradeMapa,
    tileset: dict[str, pygame.Surface],
) -> pygame.Surface:
    if tile in (PORTA, JANELA):
        orientacao = grade.orientacoes_abertura.get((coluna, linha), "horizontal")
        return tileset.get(f"{tile}_{orientacao}", tileset[f"{tile}_horizontal"])
    return tileset.get(tile, tileset[CHAO])


def desenhar_grade(
    tela: pygame.Surface,
    grade: GradeMapa,
    tileset: dict[str, pygame.Surface],
    camera_offset_px: tuple[int, int],
    sprites_objetos: dict[str, pygame.Surface] | None = None,
) -> None:
    """Desenha chão/paredes/aberturas e, por cima, sprites multi-tile."""
    tamanho = grade.tamanho_tile_px
    offset_x, offset_y = camera_offset_px
    largura_tela, altura_tela = tela.get_size()
    sprites_objetos = sprites_objetos or {}

    coluna_inicial = max(0, offset_x // tamanho)
    linha_inicial = max(0, offset_y // tamanho)
    coluna_final = min(grade.largura_tiles, (offset_x + largura_tela) // tamanho + 2)
    linha_final = min(grade.altura_tiles, (offset_y + altura_tela) // tamanho + 2)

    for linha in range(linha_inicial, linha_final):
        for coluna in range(coluna_inicial, coluna_final):
            tile = grade.tiles[linha][coluna]
            px = coluna * tamanho - offset_x
            py = linha * tamanho - offset_y
            if eh_objeto(tile):
                tela.blit(tileset[CHAO], (px, py))
            else:
                tela.blit(_superficie_tile(tile, coluna, linha, grade, tileset), (px, py))

    for info in grade.sprites_objetos:
        superficie = _sprite_para(info, sprites_objetos, tamanho)
        px = info.coluna * tamanho - offset_x
        py = info.linha * tamanho - offset_y
        if px + superficie.get_width() < 0 or py + superficie.get_height() < 0:
            continue
        if px > largura_tela or py > altura_tela:
            continue
        tela.blit(superficie, (px, py))
