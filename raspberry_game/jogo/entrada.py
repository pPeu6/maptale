"""Entrada do jogador: teclado (útil para testar fora do Raspberry Pi) e
controle Xbox via `pygame.joystick` (eixo analógico esquerdo)."""

from __future__ import annotations

import logging
import math

import pygame

from . import configuracoes as cfg

logger = logging.getLogger(__name__)


def inicializar_joystick() -> pygame.joystick.Joystick | None:
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        logger.info("Nenhum controle detectado - use as setas/WASD do teclado.")
        return None

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    logger.info("Controle detectado: %s", joystick.get_name())
    return joystick


def ler_vetor_movimento(joystick: pygame.joystick.Joystick | None) -> tuple[float, float]:
    """Retorna um vetor (x, y) normalizado no intervalo [-1, 1] combinando
    teclado e o analógico esquerdo do controle Xbox."""
    teclas = pygame.key.get_pressed()
    x = 0.0
    y = 0.0

    if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
        x -= 1.0
    if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
        x += 1.0
    if teclas[pygame.K_UP] or teclas[pygame.K_w]:
        y -= 1.0
    if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
        y += 1.0

    if joystick is not None and joystick.get_numaxes() >= 2:
        eixo_x = joystick.get_axis(0)
        eixo_y = joystick.get_axis(1)
        if abs(eixo_x) > cfg.DEADZONE_JOYSTICK:
            x = eixo_x
        if abs(eixo_y) > cfg.DEADZONE_JOYSTICK:
            y = eixo_y

    magnitude = math.hypot(x, y)
    if magnitude > 1.0:
        x /= magnitude
        y /= magnitude

    return x, y
