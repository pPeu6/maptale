"""Leitura da porta serial (Arduino) em uma thread separada, atualizando um
estado global de iluminação ("ON"/"OFF") consultado pelo loop do jogo."""

from __future__ import annotations

import logging
import threading

import pygame
import serial

from . import configuracoes as cfg

logger = logging.getLogger(__name__)


class EstadoIluminacao:
    """Estado thread-safe: `True` = luz ligada (sem overlay), `False` =
    luz apagada (overlay escuro semi-transparente)."""

    def __init__(self, ligado_inicial: bool = True):
        self._lock = threading.Lock()
        self._ligado = ligado_inicial

    @property
    def ligado(self) -> bool:
        with self._lock:
            return self._ligado

    @ligado.setter
    def ligado(self, valor: bool) -> None:
        with self._lock:
            self._ligado = valor


class ThreadLeituraSerial(threading.Thread):
    """Thread daemon que fica lendo linhas "ON"/"OFF" da porta serial e
    atualizando `EstadoIluminacao`. Reconecta automaticamente se o Arduino
    não estiver presente (útil também para desenvolver fora do Pi)."""

    def __init__(
        self,
        estado: EstadoIluminacao,
        porta: str = cfg.PORTA_SERIAL,
        baudrate: int = cfg.BAUDRATE_SERIAL,
    ):
        super().__init__(daemon=True, name="ThreadLeituraSerial")
        self._estado = estado
        self._porta = porta
        self._baudrate = baudrate
        self._parar = threading.Event()

    def parar(self) -> None:
        self._parar.set()

    def run(self) -> None:
        while not self._parar.is_set():
            try:
                with serial.Serial(self._porta, self._baudrate, timeout=1) as conexao:
                    logger.info("Conectado à porta serial %s (%d baud)", self._porta, self._baudrate)
                    while not self._parar.is_set():
                        bruta = conexao.readline()
                        if not bruta:
                            continue
                        linha = bruta.decode("utf-8", errors="ignore").strip().upper()
                        if linha == "ON":
                            self._estado.ligado = True
                        elif linha == "OFF":
                            self._estado.ligado = False
            except serial.SerialException as erro:
                logger.warning(
                    "Porta serial '%s' indisponível (%s). Tentando novamente em %.0fs...",
                    self._porta,
                    erro,
                    cfg.INTERVALO_RECONEXAO_SERIAL_SEG,
                )
                self._parar.wait(cfg.INTERVALO_RECONEXAO_SERIAL_SEG)


def criar_overlay_escuro(tamanho: tuple[int, int]) -> pygame.Surface:
    overlay = pygame.Surface(tamanho, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, cfg.ALPHA_OVERLAY_ESCURO))
    return overlay
