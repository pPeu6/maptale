"""Renderização top-down da planta (estilo rascunho): piso residencial,
paredes como retângulo perfeito (linhas finas amarelas por cima do piso),
portas e janelas detalhadas, móveis como sprites e feixes de luz do sol.
"""

from __future__ import annotations

import pygame

from mapa.grade import GradeMapa, JANELA, PAREDE, PORTA, SpriteObjeto
from . import configuracoes as cfg


def _superficie_placeholder(cor: tuple[int, int, int], tamanho: tuple[int, int]) -> pygame.Surface:
    superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
    superficie.fill((*cor, 255))
    pygame.draw.rect(superficie, (0, 0, 0), superficie.get_rect(), width=1)
    return superficie


def carregar_sprites_objetos(tamanho_tile_px: int = cfg.TILE_SIZE_PX) -> dict[str, pygame.Surface]:
    """Carrega PNGs de `assets/tiles/objetos/<tipo>.png` ampliados pelo mesmo
    fator dos tiles (16 -> tamanho_tile_px)."""
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
    info: SpriteObjeto,
    sprites: dict[str, pygame.Surface],
    tamanho_tile_px: int,
) -> pygame.Surface:
    existente = sprites.get(info.tipo)
    if existente is not None:
        return existente
    w = info.largura_tiles * tamanho_tile_px
    h = info.altura_tiles * tamanho_tile_px
    return _superficie_placeholder(cfg.COR_PLACEHOLDER_OBJETO, (w, h))


# --- Piso ---------------------------------------------------------------------


def _desenhar_piso(tela, grade, offx, offy, tamanho) -> None:
    externo = grade.retangulo_externo or grade.retangulo_interior
    if externo:
        c0, r0, c1, r1 = externo
        # Piso termina no centro dos tiles de parede, para o retângulo de
        # paredes ficar rente à borda do piso (nada de piso "sobrando" fora).
        meio = tamanho // 2
        x = c0 * tamanho - offx + meio
        y = r0 * tamanho - offy + meio
        w = (c1 - c0) * tamanho
        h = (r1 - r0) * tamanho
        pygame.draw.rect(tela, cfg.COR_PISO, (x, y, w, h))
        for yy in range(y, y + h + 1, tamanho):
            pygame.draw.line(tela, cfg.COR_PISO_LINHA, (x, yy), (x + w, yy), 1)
        # Emendas alternadas e veios curtos: tábuas de madeira, não faixas lisas.
        for linha_idx, yy in enumerate(range(y, y + h, tamanho)):
            deslocamento = tamanho // 2 if linha_idx % 2 else 0
            for xx in range(x + deslocamento, x + w, tamanho * 2):
                pygame.draw.line(
                    tela,
                    cfg.COR_PISO_LINHA,
                    (xx, yy),
                    (xx, min(yy + tamanho, y + h)),
                    1,
                )
            veio_y = yy + tamanho // 3
            for xx in range(x + 7 + deslocamento, x + w - 5, tamanho):
                pygame.draw.line(
                    tela,
                    cfg.COR_PISO_LINHA,
                    (xx, veio_y),
                    (min(xx + tamanho // 3, x + w), veio_y),
                    1,
                )

    for piso in grade.pisos:
        # Piso especial (banheiro): preenche o retângulo inteiro entre as
        # paredes (mesma lógica do piso principal — sem recuar).
        meio = tamanho // 2
        x = piso.coluna * tamanho - offx + meio
        y = piso.linha * tamanho - offy + meio
        w = piso.largura_tiles * tamanho
        h = piso.altura_tiles * tamanho
        if w <= 0 or h <= 0:
            continue
        pygame.draw.rect(tela, cfg.COR_PISO_BANHEIRO, (x, y, w, h))
        # Variação sutil entre placas, com borda iluminada e sombra no rejunte.
        for linha_idx, yy in enumerate(range(y, y + h, tamanho)):
            for coluna_idx, xx in enumerate(range(x, x + w, tamanho)):
                if (linha_idx + coluna_idx) % 2:
                    placa = pygame.Rect(
                        xx + 2,
                        yy + 2,
                        min(tamanho - 3, x + w - xx - 2),
                        min(tamanho - 3, y + h - yy - 2),
                    )
                    pygame.draw.rect(tela, cfg.COR_PISO_BANHEIRO_DETALHE, placa)
                pygame.draw.line(
                    tela,
                    cfg.COR_PISO_BANHEIRO_BRILHO,
                    (xx + 2, yy + 2),
                    (min(xx + tamanho - 3, x + w), yy + 2),
                    1,
                )
        for xx in range(x, x + w + 1, tamanho):
            pygame.draw.line(tela, cfg.COR_PISO_BANHEIRO_LINHA, (xx, y), (xx, y + h), 1)
        for yy in range(y, y + h + 1, tamanho):
            pygame.draw.line(tela, cfg.COR_PISO_BANHEIRO_LINHA, (x, yy), (x + w, yy), 1)


# --- Paredes (retângulo perfeito, sem "stubs" nos cantos) ---------------------


def _desenhar_paredes(tela, grade, offx, offy, tamanho, ci, ri, cf, rf) -> None:
    espessura = max(3, tamanho // 8)
    meia = espessura // 2
    cor = cfg.COR_PAREDE
    for r in range(ri, rf):
        for c in range(ci, cf):
            if grade.tiles[r][c] != PAREDE:
                continue
            x = c * tamanho - offx
            y = r * tamanho - offy
            xc = x + tamanho // 2
            yc = y + tamanho // 2
            # Bloco central + braços apenas na direção de vizinhos conectivos
            # (parede/porta/janela). Evita pontas sobrando nos cantos.
            pygame.draw.rect(tela, cor, (xc - meia, yc - meia, espessura, espessura))
            if grade.eh_conectivo(c - 1, r):
                pygame.draw.rect(tela, cor, (x, yc - meia, tamanho // 2 + meia, espessura))
            if grade.eh_conectivo(c + 1, r):
                pygame.draw.rect(tela, cor, (xc - meia, yc - meia, tamanho // 2 + meia, espessura))
            if grade.eh_conectivo(c, r - 1):
                pygame.draw.rect(tela, cor, (xc - meia, y, espessura, tamanho // 2 + meia))
            if grade.eh_conectivo(c, r + 1):
                pygame.draw.rect(tela, cor, (xc - meia, yc - meia, espessura, tamanho // 2 + meia))


# --- Portas e janelas (aberturas agrupadas e detalhadas) ----------------------


def _agrupar_aberturas(grade) -> list[tuple[str, str, int, int, int]]:
    """Agrupa PORTA/JANELA contíguas em runs.
    Retorna (tipo, orientacao, coluna0, linha0, comprimento)."""
    visitado = [[False] * grade.largura_tiles for _ in range(grade.altura_tiles)]
    runs: list[tuple[str, str, int, int, int]] = []
    for r in range(grade.altura_tiles):
        for c in range(grade.largura_tiles):
            tile = grade.tiles[r][c]
            if tile not in (PORTA, JANELA) or visitado[r][c]:
                continue
            horizontal = grade.eh_conectivo(c - 1, r) or grade.eh_conectivo(c + 1, r)
            comprimento = 1
            visitado[r][c] = True
            if horizontal:
                cc = c + 1
                while cc < grade.largura_tiles and grade.tiles[r][cc] == tile and not visitado[r][cc]:
                    visitado[r][cc] = True
                    comprimento += 1
                    cc += 1
                runs.append((tile, "horizontal", c, r, comprimento))
            else:
                rr = r + 1
                while rr < grade.altura_tiles and grade.tiles[rr][c] == tile and not visitado[rr][c]:
                    visitado[rr][c] = True
                    comprimento += 1
                    rr += 1
                runs.append((tile, "vertical", c, r, comprimento))
    return runs


def _dir_interior(grade, orientacao, c, r) -> tuple[int, int]:
    """Direção (dx, dy) apontando da parede para dentro do cômodo."""
    externo = grade.retangulo_externo
    if externo is None:
        return (0, 1)
    c0, r0, c1, r1 = externo
    if orientacao == "horizontal":
        return (0, -1) if r >= r1 else (0, 1)
    return (-1, 0) if c >= c1 else (1, 0)


def _desenhar_janela(tela, grade, run, offx, offy, tamanho) -> None:
    _, orientacao, c, r, comp = run
    profund = max(6, tamanho // 3)
    moldura = cfg.COR_JANELA_MOLDURA
    vidro = cfg.COR_JANELA_VIDRO

    if orientacao == "horizontal":
        yc = r * tamanho - offy + tamanho // 2
        x0 = c * tamanho - offx
        largura = comp * tamanho
        caixa = (x0, yc - profund // 2, largura, profund)
        pygame.draw.rect(tela, vidro, caixa)
        pygame.draw.rect(tela, moldura, caixa, width=2)
        for i in range(comp + 1):
            xx = x0 + i * tamanho
            pygame.draw.line(tela, moldura, (xx, yc - profund // 2), (xx, yc + profund // 2), 2)
    else:
        xc = c * tamanho - offx + tamanho // 2
        y0 = r * tamanho - offy
        altura = comp * tamanho
        caixa = (xc - profund // 2, y0, profund, altura)
        pygame.draw.rect(tela, vidro, caixa)
        pygame.draw.rect(tela, moldura, caixa, width=2)
        for i in range(comp + 1):
            yy = y0 + i * tamanho
            pygame.draw.line(tela, moldura, (xc - profund // 2, yy), (xc + profund // 2, yy), 2)


def _desenhar_porta(tela, grade, run, offx, offy, tamanho) -> None:
    tipo, orientacao, c, r, comp = run
    dx, dy = _dir_interior(grade, orientacao, c, r)
    vermelho = cfg.COR_PORTA
    madeira = cfg.COR_PORTA_FOLHA
    espessura = max(3, tamanho // 8)

    if orientacao == "horizontal":
        comprimento = comp * tamanho
        yc = r * tamanho - offy + tamanho // 2
        # Dobradiça no extremo esquerdo da abertura.
        hinge_x = c * tamanho - offx
        fim_x = hinge_x + comprimento
        # Batentes (montantes) nas pontas
        pygame.draw.rect(tela, vermelho, (hinge_x - 1, yc - tamanho // 3, 3, 2 * tamanho // 3))
        pygame.draw.rect(tela, vermelho, (fim_x - 2, yc - tamanho // 3, 3, 2 * tamanho // 3))
        # Folha da porta aberta (para dentro do cômodo)
        folha = pygame.Rect(0, 0, max(4, espessura + 1), comprimento)
        folha.topleft = (hinge_x, yc) if dy > 0 else (hinge_x, yc - comprimento)
        pygame.draw.rect(tela, madeira, folha)
        pygame.draw.rect(tela, vermelho, folha, width=1)
        # Arco de abertura
        raio = comprimento
        arco = pygame.Rect(hinge_x - raio, yc - raio, 2 * raio, 2 * raio)
        if dy > 0:
            pygame.draw.arc(tela, vermelho, arco, 4.712, 6.283, 1)
        else:
            pygame.draw.arc(tela, vermelho, arco, 0.0, 1.571, 1)
    else:
        comprimento = comp * tamanho
        xc = c * tamanho - offx + tamanho // 2
        hinge_y = r * tamanho - offy
        fim_y = hinge_y + comprimento
        pygame.draw.rect(tela, vermelho, (xc - tamanho // 3, hinge_y - 1, 2 * tamanho // 3, 3))
        pygame.draw.rect(tela, vermelho, (xc - tamanho // 3, fim_y - 2, 2 * tamanho // 3, 3))
        folha = pygame.Rect(0, 0, comprimento, max(4, espessura + 1))
        folha.topleft = (xc, hinge_y) if dx > 0 else (xc - comprimento, hinge_y)
        pygame.draw.rect(tela, madeira, folha)
        pygame.draw.rect(tela, vermelho, folha, width=1)
        raio = comprimento
        arco = pygame.Rect(xc - raio, hinge_y - raio, 2 * raio, 2 * raio)
        if dx > 0:
            pygame.draw.arc(tela, vermelho, arco, 0.0, 1.571, 1)
        else:
            pygame.draw.arc(tela, vermelho, arco, 1.571, 3.142, 1)


def _desenhar_aberturas(tela, grade, offx, offy, tamanho) -> None:
    for run in _agrupar_aberturas(grade):
        if run[0] == JANELA:
            _desenhar_janela(tela, grade, run, offx, offy, tamanho)
        else:
            _desenhar_porta(tela, grade, run, offx, offy, tamanho)


# --- Feixes de luz do sol -----------------------------------------------------

_superficie_feixe: pygame.Surface | None = None


def desenhar_feixes_sol(
    tela: pygame.Surface,
    grade: GradeMapa,
    camera_offset_px: tuple[int, int],
    fator_dia: float,
) -> None:
    """Feixes de luz solar saindo das janelas para dentro do cômodo.
    Intensidade proporcional a `fator_dia` (0 = noite, 1 = meio-dia).
    Cor e transparência idênticas nas duas janelas (overlay suave, não aditivo)."""
    global _superficie_feixe
    if fator_dia <= 0.03:
        return

    tamanho = grade.tamanho_tile_px
    offx, offy = camera_offset_px
    lw, lh = tela.get_size()

    if _superficie_feixe is None or _superficie_feixe.get_size() != (lw, lh):
        _superficie_feixe = pygame.Surface((lw, lh), pygame.SRCALPHA)

    _superficie_feixe.fill((0, 0, 0, 0))
    intensidade = min(1.0, max(0.0, fator_dia))
    alpha = max(1, int(cfg.ALPHA_FEIXE_MAX * intensidade))
    cor = (*cfg.COR_SOL, alpha)

    alcance = int(cfg.ALCANCE_FEIXE_TILES * tamanho)
    espalhamento = max(4, tamanho // 3)

    houve = False
    for tipo, orientacao, c, r, comp in _agrupar_aberturas(grade):
        if tipo != JANELA:
            continue
        dx, dy = _dir_interior(grade, orientacao, c, r)
        if orientacao == "horizontal":
            x0 = c * tamanho - offx
            x1 = x0 + comp * tamanho
            y = r * tamanho - offy + tamanho // 2
            ponta = y + dy * alcance
            pontos = [
                (x0, y),
                (x1, y),
                (x1 + espalhamento, ponta),
                (x0 - espalhamento, ponta),
            ]
        else:
            y0 = r * tamanho - offy
            y1 = y0 + comp * tamanho
            x = c * tamanho - offx + tamanho // 2
            ponta = x + dx * alcance
            pontos = [
                (x, y0),
                (x, y1),
                (ponta, y1 + espalhamento),
                (ponta, y0 - espalhamento),
            ]
        pygame.draw.polygon(_superficie_feixe, cor, pontos)
        houve = True

    if houve:
        tela.blit(_superficie_feixe, (0, 0))


# --- Orquestração -------------------------------------------------------------


def desenhar_grade(
    tela: pygame.Surface,
    grade: GradeMapa,
    camera_offset_px: tuple[int, int],
    sprites_objetos: dict[str, pygame.Surface] | None = None,
) -> None:
    tamanho = grade.tamanho_tile_px
    offx, offy = camera_offset_px
    lw, lh = tela.get_size()
    sprites_objetos = sprites_objetos or {}

    _desenhar_piso(tela, grade, offx, offy, tamanho)

    ci = max(0, offx // tamanho)
    ri = max(0, offy // tamanho)
    cf = min(grade.largura_tiles, (offx + lw) // tamanho + 2)
    rf = min(grade.altura_tiles, (offy + lh) // tamanho + 2)

    # Móveis primeiro; paredes e aberturas ficam por cima e nunca parecem
    # cortadas quando um objeto está encostado nelas.
    for info in grade.sprites_objetos:
        superficie = _sprite_para(info, sprites_objetos, tamanho)
        x = info.coluna * tamanho - offx
        y = info.linha * tamanho - offy
        # Ajustes apenas visuais: a colisão continua nos tiles interiores.
        # Itens do banheiro tocam a parede esquerda; cama e mesa encostam
        # exatamente nas paredes superior e inferior.
        if info.tipo in ("chuveiro", "pia_banheiro", "vaso"):
            x -= tamanho // 2
        if info.tipo == "cama":
            y -= tamanho // 2
        if info.tipo == "mesa_pc":
            y += tamanho // 2
        if x + superficie.get_width() < 0 or y + superficie.get_height() < 0:
            continue
        if x > lw or y > lh:
            continue
        tela.blit(superficie, (x, y))

    _desenhar_paredes(tela, grade, offx, offy, tamanho, ci, ri, cf, rf)
    _desenhar_aberturas(tela, grade, offx, offy, tamanho)
