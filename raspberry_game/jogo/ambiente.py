"""Ambiente externo: temperatura, código de clima (Open-Meteo) e horário
(fuso de Brasília). A temperatura e o clima são buscados em uma thread
separada com fallback silencioso quando não há internet."""

from __future__ import annotations

import json
import logging
import math
import threading
from datetime import datetime
from urllib.request import urlopen

import pygame

from . import configuracoes as cfg

try:
    from zoneinfo import ZoneInfo

    _FUSO = ZoneInfo(cfg.FUSO_HORARIO)
except Exception:  # pragma: no cover - fallback se a timezone não existir
    _FUSO = None

logger = logging.getLogger(__name__)

# Tipos de ícone de clima (WMO weather_code -> ícone procedural).
CLIMA_SOL = "sol"
CLIMA_PARCIAL = "parcial"
CLIMA_NUBLADO = "nublado"
CLIMA_CHUVA = "chuva"
CLIMA_NEBLINA = "neblina"
CLIMA_NEVE = "neve"
CLIMA_TEMPESTADE = "tempestade"
CLIMA_DESCONHECIDO = "desconhecido"

# Paleta dos ícones do HUD (desenho vetorial em Pygame).
_COR_SOL = (255, 210, 60)
_COR_SOL_RAIOS = (255, 235, 120)
_COR_NUVEM = (210, 220, 235)
_COR_NUVEM_SOMBRA = (150, 165, 190)
_COR_CHUVA = (90, 170, 255)
_COR_NEBLINA = (180, 195, 210)
_COR_NEVE = (230, 245, 255)
_COR_RAIO = (255, 230, 80)

_fonte_hora: pygame.font.Font | None = None
_fonte_temp: pygame.font.Font | None = None


def hora_brasilia() -> datetime:
    """Horário atual no fuso de Brasília (ou relógio local como fallback)."""
    if _FUSO is not None:
        return datetime.now(_FUSO)
    return datetime.now()


def fator_dia(momento: datetime | None = None) -> float:
    """Fator de luz natural em [0, 1]: 0 de madrugada/noite, ~1 ao meio-dia."""
    agora = momento or hora_brasilia()
    hora = agora.hour + agora.minute / 60.0

    amanhecer = cfg.HORA_AMANHECER
    pico = cfg.HORA_PICO
    anoitecer = cfg.HORA_ANOITECER

    if hora <= amanhecer or hora >= anoitecer:
        return 0.0
    if hora <= pico:
        fator = (hora - amanhecer) / (pico - amanhecer)
    else:
        fator = (anoitecer - hora) / (anoitecer - pico)
    return max(0.0, min(1.0, fator))


def mapear_codigo_clima(codigo: int | None) -> str:
    """Converte o weather_code WMO do Open-Meteo em tipo de ícone."""
    if codigo is None:
        return CLIMA_DESCONHECIDO
    if codigo == 0:
        return CLIMA_SOL
    if codigo in (1, 2):
        return CLIMA_PARCIAL
    if codigo == 3:
        return CLIMA_NUBLADO
    if codigo in (45, 48):
        return CLIMA_NEBLINA
    if codigo in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return CLIMA_CHUVA
    if codigo in (71, 73, 75, 77, 85, 86):
        return CLIMA_NEVE
    if codigo in (95, 96, 99):
        return CLIMA_TEMPESTADE
    return CLIMA_DESCONHECIDO


class EstadoAmbiente:
    """Estado thread-safe: temperatura e código de clima mais recentes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._temperatura: float | None = None
        self._codigo_clima: int | None = None

    @property
    def temperatura(self) -> float | None:
        with self._lock:
            return self._temperatura

    @temperatura.setter
    def temperatura(self, valor: float | None) -> None:
        with self._lock:
            self._temperatura = valor

    @property
    def codigo_clima(self) -> int | None:
        with self._lock:
            return self._codigo_clima

    @codigo_clima.setter
    def codigo_clima(self, valor: int | None) -> None:
        with self._lock:
            self._codigo_clima = valor

    def tipo_clima(self) -> str:
        return mapear_codigo_clima(self.codigo_clima)

    def texto_temperatura(self) -> str:
        temp = self.temperatura
        return "--°C" if temp is None else f"{temp:.0f}°C"


class ThreadClima(threading.Thread):
    """Consulta a API de clima periodicamente e atualiza `EstadoAmbiente`."""

    def __init__(self, estado: EstadoAmbiente) -> None:
        super().__init__(daemon=True, name="ThreadClima")
        self._estado = estado
        self._parar = threading.Event()

    def parar(self) -> None:
        self._parar.set()

    def _buscar_clima(self) -> tuple[float | None, int | None]:
        try:
            with urlopen(cfg.URL_CLIMA, timeout=cfg.TIMEOUT_CLIMA_SEG) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
            atual = dados["current"]
            temp = float(atual["temperature_2m"])
            codigo = int(atual.get("weather_code", 0))
            return temp, codigo
        except Exception as erro:
            logger.warning("Falha ao obter clima (%s). Usando fallback.", erro)
            return None, None

    def run(self) -> None:
        while not self._parar.is_set():
            temperatura, codigo = self._buscar_clima()
            if temperatura is not None:
                self._estado.temperatura = temperatura
                self._estado.codigo_clima = codigo
                logger.info(
                    "Clima atualizado: %.1f°C, código WMO %s",
                    temperatura,
                    codigo,
                )
            self._parar.wait(cfg.INTERVALO_ATUALIZACAO_CLIMA_SEG)


def _garantir_fontes() -> tuple[pygame.font.Font, pygame.font.Font]:
    global _fonte_hora, _fonte_temp
    if _fonte_hora is None:
        _fonte_hora = pygame.font.SysFont("consolas,segoeui,arial", cfg.TAMANHO_FONTE_HUD, bold=True)
    if _fonte_temp is None:
        _fonte_temp = pygame.font.SysFont("consolas,segoeui,arial", cfg.TAMANHO_FONTE_HUD_PEQUENA, bold=True)
    return _fonte_hora, _fonte_temp


def _desenhar_sol(superficie: pygame.Surface, cx: int, cy: int, raio: int) -> None:
    pygame.draw.circle(superficie, _COR_SOL, (cx, cy), raio)
    for angulo in range(0, 360, 45):
        rad = math.radians(angulo)
        x0 = cx + int(math.cos(rad) * (raio + 2))
        y0 = cy + int(math.sin(rad) * (raio + 2))
        x1 = cx + int(math.cos(rad) * (raio + 6))
        y1 = cy + int(math.sin(rad) * (raio + 6))
        pygame.draw.line(superficie, _COR_SOL_RAIOS, (x0, y0), (x1, y1), 2)


def _desenhar_nuvem(superficie: pygame.Surface, x: int, y: int, escala: float = 1.0) -> None:
    r = int(5 * escala)
    pygame.draw.circle(superficie, _COR_NUVEM_SOMBRA, (x + 1, y + 1), r + 2)
    pygame.draw.circle(superficie, _COR_NUVEM, (x - r, y), r)
    pygame.draw.circle(superficie, _COR_NUVEM, (x, y - 2), r + 1)
    pygame.draw.circle(superficie, _COR_NUVEM, (x + r + 1, y), r)


def _desenhar_icone_clima(superficie: pygame.Surface, tipo: str, x: int, y: int, tamanho: int) -> None:
    """Ícones vetoriais coloridos do clima atual."""
    cx = x + tamanho // 2
    cy = y + tamanho // 2
    raio = tamanho // 4

    if tipo == CLIMA_SOL:
        _desenhar_sol(superficie, cx, cy, raio)
    elif tipo == CLIMA_PARCIAL:
        _desenhar_sol(superficie, cx - 4, cy - 2, raio - 2)
        _desenhar_nuvem(superficie, cx + 6, cy + 4, 0.9)
    elif tipo == CLIMA_NUBLADO:
        _desenhar_nuvem(superficie, cx - 5, cy, 1.0)
        _desenhar_nuvem(superficie, cx + 7, cy + 2, 0.85)
    elif tipo == CLIMA_CHUVA:
        _desenhar_nuvem(superficie, cx, cy - 4, 1.0)
        for dx in (-6, 0, 6):
            pygame.draw.line(
                superficie, _COR_CHUVA, (cx + dx, cy + 4), (cx + dx - 2, cy + 12), 2
            )
    elif tipo == CLIMA_NEBLINA:
        for dy in (0, 5, 10):
            pygame.draw.line(
                superficie,
                _COR_NEBLINA,
                (x + 3, y + 8 + dy),
                (x + tamanho - 3, y + 8 + dy),
                2,
            )
    elif tipo == CLIMA_NEVE:
        _desenhar_nuvem(superficie, cx, cy - 4, 0.95)
        for dx in (-5, 0, 5):
            pygame.draw.circle(superficie, _COR_NEVE, (cx + dx, cy + 10), 2)
    elif tipo == CLIMA_TEMPESTADE:
        _desenhar_nuvem(superficie, cx, cy - 5, 1.0)
        pontos = [(cx - 2, cy + 2), (cx + 4, cy + 2), (cx, cy + 12)]
        pygame.draw.polygon(superficie, _COR_RAIO, pontos)
    else:
        pygame.draw.circle(superficie, _COR_NUVEM, (cx, cy), raio, 2)
        pygame.draw.line(superficie, _COR_NUVEM_SOMBRA, (cx - 4, cy), (cx + 4, cy), 2)


def _cor_temperatura(temp: float | None) -> tuple[int, int, int]:
    if temp is None:
        return cfg.COR_HUD_TEMP
    if temp >= 28:
        return (255, 120, 80)
    if temp <= 15:
        return cfg.COR_HUD_TEMP_FRIO
    return cfg.COR_HUD_TEMP


def desenhar_hud(
    tela: pygame.Surface,
    estado: EstadoAmbiente,
    fonte: pygame.font.Font | None = None,
) -> None:
    """Painel colorido no canto superior direito: ícone de clima, horário e
    temperatura."""
    fonte_hora, fonte_temp = _garantir_fontes()
    if fonte is not None:
        fonte_hora = fonte

    agora = hora_brasilia()
    hora_txt = fonte_hora.render(f"{agora:%H:%M}", True, cfg.COR_HUD_HORA)
    temp_txt = fonte_temp.render(estado.texto_temperatura(), True, _cor_temperatura(estado.temperatura))

    icone = cfg.TAMANHO_ICONE_CLIMA
    padding = 10
    gap = 8
    largura = padding + icone + gap + max(hora_txt.get_width(), temp_txt.get_width()) + padding
    altura = padding + max(icone, hora_txt.get_height() + temp_txt.get_height() + 2) + padding
    margem = 12
    x = tela.get_width() - largura - margem
    y = margem

    painel = pygame.Surface((largura, altura), pygame.SRCALPHA)
    painel.fill(cfg.COR_HUD_FUNDO)
    pygame.draw.rect(painel, cfg.COR_HUD_BORDA, painel.get_rect(), width=2, border_radius=10)
    # Faixa de brilho no topo do painel.
    brilho = pygame.Surface((largura - 4, 6), pygame.SRCALPHA)
    brilho.fill(cfg.COR_HUD_BRILHO)
    painel.blit(brilho, (2, 2))

    icone_y = padding + (altura - 2 * padding - icone) // 2
    _desenhar_icone_clima(painel, estado.tipo_clima(), padding, icone_y, icone)

    texto_x = padding + icone + gap
    texto_y = padding + (altura - 2 * padding - hora_txt.get_height() - temp_txt.get_height()) // 2
    painel.blit(hora_txt, (texto_x, texto_y))
    painel.blit(temp_txt, (texto_x, texto_y + hora_txt.get_height() + 2))

    # Separador vertical sutil entre ícone e textos.
    sep_x = padding + icone + gap // 2
    pygame.draw.line(
        painel,
        cfg.COR_HUD_SEPARADOR,
        (sep_x, padding + 4),
        (sep_x, altura - padding - 4),
        1,
    )

    tela.blit(painel, (x, y))
