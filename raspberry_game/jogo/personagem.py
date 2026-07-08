"""Personagem controlável: 4 direções x 2 quadros (parado/passo) e
movimento com colisão contra a grade (bloqueia em PAREDE/JANELA/OBJETO_*)."""

from __future__ import annotations

import math

import pygame

from mapa.grade import GradeMapa
from . import configuracoes as cfg

DIRECOES = ("baixo", "cima", "esquerda", "direita")
QUADROS = ("parado", "passo")
_INTERVALO_ANIMACAO_SEG = 0.18

# Dimensões lógicas do personagem, espelhando `assets/gerador_tiles.py`
# (LARGURA_PERSONAGEM/ALTURA_PERSONAGEM). Mantidas aqui para o motor não
# depender do módulo de geração de assets em tempo de execução.
_LARGURA_LOGICA = 16
_ALTURA_LOGICA = 21


def _frame_placeholder(direcao: str, andando: bool, largura: int, altura: int) -> pygame.Surface:
    """Gera um retângulo com um pequeno triângulo indicando a direção,
    usado enquanto os PNGs finais (`assets/personagem/<direcao>_<quadro>.png`)
    não foram gerados."""
    superficie = pygame.Surface((largura, altura), pygame.SRCALPHA)
    cor_corpo = cfg.COR_PLACEHOLDER_PERSONAGEM
    raio = min(largura, altura) // 2 - (2 if andando else 4)
    centro = (largura // 2, altura // 2)
    pygame.draw.circle(superficie, cor_corpo, centro, max(raio, 2))

    pontas = {
        "baixo": [(centro[0] - 5, centro[1]), (centro[0] + 5, centro[1]), (centro[0], centro[1] + raio)],
        "cima": [(centro[0] - 5, centro[1]), (centro[0] + 5, centro[1]), (centro[0], centro[1] - raio)],
        "esquerda": [(centro[0], centro[1] - 5), (centro[0], centro[1] + 5), (centro[0] - raio, centro[1])],
        "direita": [(centro[0], centro[1] - 5), (centro[0], centro[1] + 5), (centro[0] + raio, centro[1])],
    }
    pygame.draw.polygon(superficie, (60, 60, 60), pontas[direcao])
    return superficie


def carregar_frames(tamanho_tile_px: int = cfg.TILE_SIZE_PX) -> dict[str, dict[str, pygame.Surface]]:
    """Carrega um arquivo por direção/quadro
    (`assets/personagem/<direcao>_<quadro>.png`, gerados por
    `assets/gerador_tiles.py`). Se algum arquivo não existir, usa um
    placeholder procedural no lugar.

    A escala aplicada preserva a proporção original 16x21 do personagem
    (diferente dos tiles, que são quadrados): o fator de ampliação é o
    mesmo usado para os tiles (`tamanho_tile_px / TAMANHO_TILE_LOGICO_PX`).
    """
    fator_escala = tamanho_tile_px / cfg.TAMANHO_TILE_LOGICO_PX
    tamanho_alvo = (round(_LARGURA_LOGICA * fator_escala), round(_ALTURA_LOGICA * fator_escala))

    frames: dict[str, dict[str, pygame.Surface]] = {d: {} for d in DIRECOES}

    for direcao in DIRECOES:
        for quadro in QUADROS:
            caminho = cfg.PASTA_PERSONAGEM / f"{direcao}_{quadro}.png"
            if caminho.exists():
                frame = pygame.image.load(str(caminho)).convert_alpha()
                if frame.get_size() != tamanho_alvo:
                    frame = pygame.transform.scale(frame, tamanho_alvo)
            else:
                frame = _frame_placeholder(direcao, quadro == "passo", *tamanho_alvo)
            frames[direcao][quadro] = frame

    return frames


class Personagem:
    def __init__(self, posicao_tiles: tuple[float, float], tamanho_tile_px: int = cfg.TILE_SIZE_PX):
        self.x, self.y = posicao_tiles  # posição em unidades de tile (float)
        self.tamanho_tile_px = tamanho_tile_px
        self.direcao = "baixo"
        self.andando = False
        self._tempo_animacao = 0.0
        self._frame_passo_visivel = False
        self.frames = carregar_frames(tamanho_tile_px)

    def _colide(self, grade: GradeMapa, x_tiles: float, y_tiles: float) -> bool:
        meia_bbox = cfg.TAMANHO_COLISAO_TILES / 2
        cantos = [
            (x_tiles - meia_bbox, y_tiles - meia_bbox),
            (x_tiles + meia_bbox, y_tiles - meia_bbox),
            (x_tiles - meia_bbox, y_tiles + meia_bbox),
            (x_tiles + meia_bbox, y_tiles + meia_bbox),
        ]
        for cx, cy in cantos:
            if grade.bloqueia_movimento(int(math.floor(cx)), int(math.floor(cy))):
                return True
        return False

    def mover(self, vetor_x: float, vetor_y: float, dt: float, grade: GradeMapa) -> None:
        """`vetor_x`/`vetor_y` já vêm normalizados (-1..1) de `entrada.py`."""
        self.andando = vetor_x != 0 or vetor_y != 0

        if vetor_x > 0:
            self.direcao = "direita"
        elif vetor_x < 0:
            self.direcao = "esquerda"
        elif vetor_y > 0:
            self.direcao = "baixo"
        elif vetor_y < 0:
            self.direcao = "cima"

        deslocamento = cfg.VELOCIDADE_TILES_POR_SEGUNDO * dt

        # Colisão separada por eixo, para permitir "deslizar" ao longo de paredes.
        novo_x = self.x + vetor_x * deslocamento
        if not self._colide(grade, novo_x, self.y):
            self.x = novo_x

        novo_y = self.y + vetor_y * deslocamento
        if not self._colide(grade, self.x, novo_y):
            self.y = novo_y

        self._atualizar_animacao(dt)

    def _atualizar_animacao(self, dt: float) -> None:
        if not self.andando:
            self._tempo_animacao = 0.0
            self._frame_passo_visivel = False
            return

        self._tempo_animacao += dt
        if self._tempo_animacao >= _INTERVALO_ANIMACAO_SEG:
            self._tempo_animacao = 0.0
            self._frame_passo_visivel = not self._frame_passo_visivel

    def desenhar(self, tela: pygame.Surface, camera_offset_px: tuple[int, int]) -> None:
        quadro = "passo" if (self.andando and self._frame_passo_visivel) else "parado"
        frame = self.frames[self.direcao][quadro]
        px = self.x * self.tamanho_tile_px - camera_offset_px[0]
        py = self.y * self.tamanho_tile_px - camera_offset_px[1]
        # O sprite (16x21 lógico) é mais alto que largo, então ancoramos
        # pelos "pés" (base do tile atual) em vez do centro geométrico -
        # caso contrário a cabeça pareceria flutuar acima da posição real.
        pes_y = py + self.tamanho_tile_px / 2
        rect = frame.get_rect(midbottom=(px, pes_y))
        tela.blit(frame, rect)
