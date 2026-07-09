"""Ponto de entrada do jogo.

Carrega o mapa local fixo (`mapas/quarto.json`) e roda o loop principal do
Pygame em tela cheia. Pode ser executado tanto como script direto
(`python3 jogo/principal.py`, usado pelo systemd) quanto como módulo
(`python3 -m jogo.principal`).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Garante que a raiz do projeto (raspberry_game/) esteja no sys.path,
# independentemente de como o script foi invocado.
_RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(_RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROJETO))

import pygame  # noqa: E402

from jogo import ambiente, configuracoes as cfg  # noqa: E402
from jogo import entrada, tiles  # noqa: E402
from jogo.iluminacao import (  # noqa: E402
    EstadoIluminacao,
    ThreadLeituraSerial,
    alpha_escuridao,
    criar_overlay_noite,
)
from jogo.personagem import Personagem  # noqa: E402
from mapa.grade import GradeMapa, converter_json_em_grade  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def _carregar_mapa_padrao() -> GradeMapa:
    caminho = cfg.MAPA_PADRAO
    if not caminho.exists():
        raise FileNotFoundError(
            f"Mapa padrão não encontrado: {caminho}. "
            "Esperado mapas/quarto.json no projeto."
        )
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return converter_json_em_grade(dados, cfg.TILE_SIZE_PX)


def _abrir_tela() -> pygame.Surface:
    if cfg.TELA_CHEIA:
        try:
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        except pygame.error:
            logger.warning("Fullscreen falhou; usando janela %sx%s", cfg.LARGURA_TELA, cfg.ALTURA_TELA)
    return pygame.display.set_mode((cfg.LARGURA_TELA, cfg.ALTURA_TELA))


def _calcular_camera(
    personagem: Personagem, grade: GradeMapa, largura_tela: int, altura_tela: int
) -> tuple[int, int]:
    """Se o mapa cabe na tela, centraliza. Caso contrário, segue o
    personagem com clamp nas bordas da grade."""
    tamanho = grade.tamanho_tile_px
    mapa_w = grade.largura_tiles * tamanho
    mapa_h = grade.altura_tiles * tamanho

    if mapa_w <= largura_tela and mapa_h <= altura_tela:
        # Offset negativo = mapa centralizado (bordas pretas ao redor).
        return -((largura_tela - mapa_w) // 2), -((altura_tela - mapa_h) // 2)

    alvo_x = personagem.x * tamanho - largura_tela / 2
    alvo_y = personagem.y * tamanho - altura_tela / 2
    limite_x = max(0, mapa_w - largura_tela)
    limite_y = max(0, mapa_h - altura_tela)
    return int(min(max(0, alvo_x), limite_x)), int(min(max(0, alvo_y), limite_y))


def _spawn_livre(grade: GradeMapa) -> tuple[float, float]:
    """Primeiro tile de chão livre perto do centro (evita nascer em móvel)."""
    cx, cy = grade.largura_tiles // 2, grade.altura_tiles // 2
    for raio in range(0, max(grade.largura_tiles, grade.altura_tiles)):
        for dy in range(-raio, raio + 1):
            for dx in range(-raio, raio + 1):
                c, l = cx + dx, cy + dy
                if grade.tile_em(c, l) == "CHAO":
                    return float(c) + 0.5, float(l) + 0.5
    return float(cx), float(cy)


def main() -> None:
    grade = _carregar_mapa_padrao()
    logger.info("Mapa carregado: %s (%sx%s tiles)", grade.nome_ambiente, grade.largura_tiles, grade.altura_tiles)

    pygame.init()
    tela = _abrir_tela()
    largura_tela, altura_tela = tela.get_size()
    pygame.display.set_caption("Maptale")
    relogio = pygame.time.Clock()

    joystick = entrada.inicializar_joystick()
    sprites_objetos = tiles.carregar_sprites_objetos(cfg.TILE_SIZE_PX)
    overlay_noite = criar_overlay_noite((largura_tela, altura_tela))
    fonte_hud = pygame.font.SysFont(None, cfg.TAMANHO_FONTE_HUD)

    estado_iluminacao = EstadoIluminacao()
    thread_serial = ThreadLeituraSerial(estado_iluminacao)
    thread_serial.start()

    estado_ambiente = ambiente.EstadoAmbiente()
    thread_clima = ambiente.ThreadClima(estado_ambiente)
    thread_clima.start()

    personagem = Personagem(
        posicao_tiles=_spawn_livre(grade),
        tamanho_tile_px=cfg.TILE_SIZE_PX,
    )

    rodando = True
    try:
        while rodando:
            dt = relogio.tick(cfg.FPS) / 1000.0

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    rodando = False
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    rodando = False

            vetor_x, vetor_y = entrada.ler_vetor_movimento(joystick)
            personagem.mover(vetor_x, vetor_y, dt, grade)

            camera_offset = _calcular_camera(personagem, grade, largura_tela, altura_tela)

            tela.fill(cfg.COR_FUNDO)
            tiles.desenhar_grade(tela, grade, camera_offset, sprites_objetos)
            personagem.desenhar(tela, camera_offset)

            # Luz natural: escuridão combinada (horário + luz interna) e, por
            # cima, o feixe de sol saindo das janelas (mais fraco à tardinha).
            luz_dia = ambiente.fator_dia()
            alpha = alpha_escuridao(luz_dia, estado_iluminacao.ligado)
            if alpha > 0:
                overlay_noite.set_alpha(alpha)
                tela.blit(overlay_noite, (0, 0))
            tiles.desenhar_feixes_sol(tela, grade, camera_offset, luz_dia)

            ambiente.desenhar_hud(tela, estado_ambiente, fonte_hud)

            pygame.display.flip()
    finally:
        thread_serial.parar()
        thread_clima.parar()
        pygame.quit()


if __name__ == "__main__":
    main()
