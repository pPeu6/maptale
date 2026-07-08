"""Personagem controlável: spritesheet de 4 direções (parado/andando) e
movimento com colisão contra a grade (bloqueia em PAREDE/JANELA/OBJETO_*)."""

from __future__ import annotations

import math

import pygame

from mapa.grade import GradeMapa
from . import configuracoes as cfg

DIRECOES = ("baixo", "cima", "esquerda", "direita")
_LINHA_DIRECAO = {"baixo": 0, "cima": 1, "esquerda": 2, "direita": 3}
_INTERVALO_ANIMACAO_SEG = 0.18


def _frame_placeholder(direcao: str, andando: bool, tamanho: int) -> pygame.Surface:
    """Gera um quadrado com um pequeno triângulo indicando a direção,
    usado enquanto o spritesheet final não é fornecido."""
    superficie = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    cor_corpo = cfg.COR_PLACEHOLDER_PERSONAGEM
    raio = tamanho // 2 - (2 if andando else 4)
    centro = (tamanho // 2, tamanho // 2)
    pygame.draw.circle(superficie, cor_corpo, centro, raio)

    pontas = {
        "baixo": [(centro[0] - 5, centro[1]), (centro[0] + 5, centro[1]), (centro[0], centro[1] + raio)],
        "cima": [(centro[0] - 5, centro[1]), (centro[0] + 5, centro[1]), (centro[0], centro[1] - raio)],
        "esquerda": [(centro[0], centro[1] - 5), (centro[0], centro[1] + 5), (centro[0] - raio, centro[1])],
        "direita": [(centro[0], centro[1] - 5), (centro[0], centro[1] + 5), (centro[0] + raio, centro[1])],
    }
    pygame.draw.polygon(superficie, (60, 60, 60), pontas[direcao])
    return superficie


def carregar_frames(tamanho_tile_px: int = cfg.TILE_SIZE_PX) -> dict[str, dict[str, pygame.Surface]]:
    """Carrega `assets/personagem/spritesheet.png` (grade 2 colunas x 4
    linhas: parado/andando por direção baixo/cima/esquerda/direita). Se o
    arquivo não existir, gera placeholders procedurais."""
    caminho = cfg.PASTA_PERSONAGEM / "spritesheet.png"
    frames: dict[str, dict[str, pygame.Surface]] = {d: {} for d in DIRECOES}

    if caminho.exists():
        folha = pygame.image.load(str(caminho)).convert_alpha()
        largura_frame = folha.get_width() // 2
        altura_frame = folha.get_height() // len(DIRECOES)
        for direcao, linha in _LINHA_DIRECAO.items():
            for coluna, estado in enumerate(("parado", "andando")):
                retangulo = pygame.Rect(
                    coluna * largura_frame, linha * altura_frame, largura_frame, altura_frame
                )
                frame = folha.subsurface(retangulo).copy()
                if frame.get_size() != (tamanho_tile_px, tamanho_tile_px):
                    frame = pygame.transform.scale(frame, (tamanho_tile_px, tamanho_tile_px))
                frames[direcao][estado] = frame
    else:
        for direcao in DIRECOES:
            frames[direcao]["parado"] = _frame_placeholder(direcao, False, tamanho_tile_px)
            frames[direcao]["andando"] = _frame_placeholder(direcao, True, tamanho_tile_px)

    return frames


class Personagem:
    def __init__(self, posicao_tiles: tuple[float, float], tamanho_tile_px: int = cfg.TILE_SIZE_PX):
        self.x, self.y = posicao_tiles  # posição em unidades de tile (float)
        self.tamanho_tile_px = tamanho_tile_px
        self.direcao = "baixo"
        self.andando = False
        self._tempo_animacao = 0.0
        self._frame_andando_visivel = False
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
            self._frame_andando_visivel = False
            return

        self._tempo_animacao += dt
        if self._tempo_animacao >= _INTERVALO_ANIMACAO_SEG:
            self._tempo_animacao = 0.0
            self._frame_andando_visivel = not self._frame_andando_visivel

    def desenhar(self, tela: pygame.Surface, camera_offset_px: tuple[int, int]) -> None:
        estado = "andando" if (self.andando and self._frame_andando_visivel) else "parado"
        frame = self.frames[self.direcao][estado]
        px = self.x * self.tamanho_tile_px - camera_offset_px[0]
        py = self.y * self.tamanho_tile_px - camera_offset_px[1]
        rect = frame.get_rect(center=(px, py))
        tela.blit(frame, rect)
