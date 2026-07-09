"""Gera um PNG de preview do mapa completo (quarto + banheiro).

Rodar (a partir de raspberry_game/):
  python assets/gerador_tiles.py
  python assets/preview_mapa.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pygame

from jogo import configuracoes as cfg
from jogo import tiles
from mapa.grade import converter_json_em_grade

ESCALA_EXTRA = 2  # além do TILE_SIZE_PX, para o preview ficar legível
SAIDA = Path(__file__).resolve().parent / "preview_mapa.png"


def main() -> None:
    dados = json.loads(cfg.MAPA_PADRAO.read_text(encoding="utf-8"))
    # Preview em resolução lógica ampliada
    tamanho_tile = cfg.TAMANHO_TILE_LOGICO_PX * ESCALA_EXTRA
    grade = converter_json_em_grade(dados, tamanho_tile)

    pygame.init()
    pygame.display.set_mode((1, 1))  # necessário para convert()

    tileset = tiles.carregar_tileset(tamanho_tile)
    sprites = tiles.carregar_sprites_objetos(tamanho_tile)

    superficie = pygame.Surface(
        (grade.largura_tiles * tamanho_tile, grade.altura_tiles * tamanho_tile)
    )
    superficie.fill((20, 20, 22))
    tiles.desenhar_grade(superficie, grade, tileset, (0, 0), sprites)

    pygame.image.save(superficie, str(SAIDA))
    print(f"Preview do mapa salvo em: {SAIDA}")
    pygame.quit()


if __name__ == "__main__":
    main()
