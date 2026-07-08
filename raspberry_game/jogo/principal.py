"""Ponto de entrada do jogo.

Sobe o servidor Flask (`servidor.py`) em uma thread daemon e roda o loop
principal do Pygame na thread principal (obrigatório para o display).
Pode ser executado tanto como script direto (`python3 jogo/principal.py`,
usado pelo systemd) quanto como módulo (`python3 -m jogo.principal`).
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from pathlib import Path
from typing import Optional

# Garante que a raiz do projeto (raspberry_game/) esteja no sys.path,
# independentemente de como o script foi invocado.
_RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(_RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(_RAIZ_PROJETO))

import pygame  # noqa: E402

from jogo import configuracoes as cfg  # noqa: E402
from jogo import entrada, tiles  # noqa: E402
from jogo.iluminacao import EstadoIluminacao, ThreadLeituraSerial, criar_overlay_escuro  # noqa: E402
from jogo.personagem import Personagem  # noqa: E402
from mapa.grade import GradeMapa, converter_json_em_grade  # noqa: E402
from servidor import criar_app  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class EstadoMapaCompartilhado:
    """Guarda a grade atual do jogo de forma thread-safe: o servidor Flask
    escreve (quando um novo mapa chega), o loop do jogo lê a cada frame."""

    def __init__(self, grade_inicial: GradeMapa):
        self._lock = threading.Lock()
        self._grade = grade_inicial

    @property
    def grade(self) -> GradeMapa:
        with self._lock:
            return self._grade

    def substituir(self, nova_grade: GradeMapa) -> None:
        with self._lock:
            self._grade = nova_grade


def _grade_vazia_padrao() -> GradeMapa:
    """Grade mínima usada enquanto nenhum mapa foi enviado ainda."""
    dados_minimos = {
        "nome_ambiente": "aguardando_mapa",
        "escala_metros_por_tile": 0.1,
        "paredes": [],
        "portas": [],
        "janelas": [],
        "objetos": [],
    }
    return converter_json_em_grade(dados_minimos, cfg.TILE_SIZE_PX)


def _carregar_ultimo_mapa_salvo() -> Optional[GradeMapa]:
    if not cfg.PASTA_MAPAS.exists():
        return None
    arquivos = sorted(
        cfg.PASTA_MAPAS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not arquivos:
        return None
    try:
        dados = json.loads(arquivos[0].read_text(encoding="utf-8"))
        return converter_json_em_grade(dados, cfg.TILE_SIZE_PX)
    except Exception:
        logger.exception("Falha ao carregar mapa salvo '%s'", arquivos[0])
        return None


def _iniciar_servidor_em_thread(estado_mapa: EstadoMapaCompartilhado) -> None:
    def ao_receber_mapa(dados: dict) -> None:
        try:
            nova_grade = converter_json_em_grade(dados, cfg.TILE_SIZE_PX)
        except Exception:
            logger.exception("Falha ao converter o novo mapa recebido")
            return
        estado_mapa.substituir(nova_grade)
        logger.info("Mapa recarregado sem reiniciar: %s", nova_grade.nome_ambiente)

    app = criar_app(cfg.PASTA_MAPAS, ao_receber_mapa=ao_receber_mapa)

    thread = threading.Thread(
        target=lambda: app.run(
            host=cfg.HOST_SERVIDOR,
            port=cfg.PORTA_SERVIDOR,
            use_reloader=False,
            threaded=True,
        ),
        name="ThreadServidorFlask",
        daemon=True,
    )
    thread.start()
    logger.info(
        "Servidor Flask escutando em http://%s:%s/upload_map",
        cfg.HOST_SERVIDOR,
        cfg.PORTA_SERVIDOR,
    )


def _calcular_camera(personagem: Personagem, grade: GradeMapa) -> tuple[int, int]:
    """Centraliza a câmera no personagem, sem deixar a tela mostrar área
    fora dos limites da grade."""
    tamanho = grade.tamanho_tile_px
    alvo_x = personagem.x * tamanho - cfg.LARGURA_TELA / 2
    alvo_y = personagem.y * tamanho - cfg.ALTURA_TELA / 2

    limite_x = max(0, grade.largura_tiles * tamanho - cfg.LARGURA_TELA)
    limite_y = max(0, grade.altura_tiles * tamanho - cfg.ALTURA_TELA)

    offset_x = min(max(0, alvo_x), limite_x)
    offset_y = min(max(0, alvo_y), limite_y)
    return int(offset_x), int(offset_y)


def main() -> None:
    grade_inicial = _carregar_ultimo_mapa_salvo() or _grade_vazia_padrao()
    estado_mapa = EstadoMapaCompartilhado(grade_inicial)
    _iniciar_servidor_em_thread(estado_mapa)

    pygame.init()
    tela = pygame.display.set_mode((cfg.LARGURA_TELA, cfg.ALTURA_TELA))
    pygame.display.set_caption("Maptale")
    relogio = pygame.time.Clock()

    joystick = entrada.inicializar_joystick()
    tileset = tiles.carregar_tileset(cfg.TILE_SIZE_PX)
    overlay_escuro = criar_overlay_escuro((cfg.LARGURA_TELA, cfg.ALTURA_TELA))

    estado_iluminacao = EstadoIluminacao()
    thread_serial = ThreadLeituraSerial(estado_iluminacao)
    thread_serial.start()

    grade_atual = estado_mapa.grade
    personagem = Personagem(
        posicao_tiles=(grade_atual.largura_tiles / 2, grade_atual.altura_tiles / 2),
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

            grade_atual = estado_mapa.grade

            vetor_x, vetor_y = entrada.ler_vetor_movimento(joystick)
            personagem.mover(vetor_x, vetor_y, dt, grade_atual)

            camera_offset = _calcular_camera(personagem, grade_atual)

            tela.fill((0, 0, 0))
            tiles.desenhar_grade(tela, grade_atual, tileset, camera_offset)
            personagem.desenhar(tela, camera_offset)

            if not estado_iluminacao.ligado:
                tela.blit(overlay_escuro, (0, 0))

            pygame.display.flip()
    finally:
        thread_serial.parar()
        pygame.quit()


if __name__ == "__main__":
    main()
