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

from jogo import ambiente, configuracoes as cfg
from jogo import tiles
from mapa.grade import converter_json_em_grade

ESCALA_EXTRA = 2  # além do TILE_SIZE_PX, para o preview ficar legível
FATOR_DIA_PREVIEW = 0.9  # dia claro, para mostrar o feixe de sol
SAIDA = Path(__file__).resolve().parent / "preview_mapa.png"


def main() -> None:
    dados = json.loads(cfg.MAPA_PADRAO.read_text(encoding="utf-8"))
    # Preview em resolução lógica ampliada
    tamanho_tile = cfg.TAMANHO_TILE_LOGICO_PX * ESCALA_EXTRA
    grade = converter_json_em_grade(dados, tamanho_tile)

    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1))  # necessário para convert()

    sprites = tiles.carregar_sprites_objetos(tamanho_tile)

    superficie = pygame.Surface(
        (grade.largura_tiles * tamanho_tile, grade.altura_tiles * tamanho_tile)
    )
    superficie.fill(cfg.COR_FUNDO)
    tiles.desenhar_grade(superficie, grade, (0, 0), sprites)
    tiles.desenhar_feixes_sol(superficie, grade, (0, 0), FATOR_DIA_PREVIEW)

    estado = ambiente.EstadoAmbiente()
    thread = ambiente.ThreadClima(estado)
    temp, codigo = thread._buscar_clima()
    if temp is not None:
        estado.temperatura = temp
        estado.codigo_clima = codigo
    ambiente.desenhar_hud(superficie, estado)

    pygame.image.save(superficie, str(SAIDA))
    print(f"Preview do mapa salvo em: {SAIDA}")
    pygame.quit()


if __name__ == "__main__":
    main()
