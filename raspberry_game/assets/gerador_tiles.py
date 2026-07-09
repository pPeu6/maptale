"""Gera os sprites de móveis e do personagem (Pillow), em pixel art.

As paredes, portas, janelas e piso NÃO são mais tiles PNG: são desenhados
proceduralmente pelo motor (`jogo/tiles.py`) como linhas finas / preenchimentos.
Aqui geramos apenas os móveis (vista top-down, madeira/cerâmica) e o
personagem (humano detalhado, pele clara, cabelo e barba loiros).

Rodar: `python assets/gerador_tiles.py`
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

# --- Paleta -------------------------------------------------------------------

PALETA_HEX = {
    "VOID": "#0c0c0d",
    "INK": "#20160c",
    "ASH": "#8c8c90",
    "BONE": "#f4f4f2",
    # Madeira (móveis)
    "WOOD_DARK": "#5a3413",
    "WOOD_SHADOW": "#3f220d",
    "WOOD": "#8a5222",
    "WOOD_MID": "#9e642e",
    "WOOD_LIGHT": "#b57a3c",
    "WOOD_GOLD": "#d09a57",
    # Cerâmica / metal (banheiro, monitor)
    "STEEL": "#8b9199",
    "STEEL_DARK": "#4a4f57",
    "STEEL_LIGHT": "#c5cbd0",
    "CERAMIC": "#f2f0ea",
    "CERAMIC_SH": "#d3d1c8",
    "CERAMIC_HI": "#fffefa",
    "CERAMIC_DARK": "#aaa9a2",
    "GLASS": "#bfe6f2",
    "WATER": "#73c8e6",
    # Mesa branca + monitor
    "DESK": "#eef1f4",
    "DESK_SH": "#c8ccd2",
    "SCREEN": "#2f6fb0",
    # Roupa de cama
    "LINEN": "#efe7d6",
    "QUILT": "#5aa0a0",
    "QUILT_DARK": "#3f7d7d",
    # Personagem
    "SKIN": "#f2c49a",
    "SKIN_SH": "#d7a276",
    "HAIR": "#e6bf5a",
    "HAIR_SH": "#c39a3c",
    "BEARD": "#d9b24e",
    "EYE": "#2f5aa8",
    "MOUTH": "#a85742",
    "SHIRT": "#4a86c5",
    "SHIRT_SH": "#2f5f92",
    "PANTS": "#3b4a63",
    "PANTS_SH": "#2a3548",
    "SHOE": "#2a1c12",
}


def _hex_para_rgba(hex_cor: str, alpha: int = 255) -> tuple[int, int, int, int]:
    hex_cor = hex_cor.lstrip("#")
    r, g, b = (int(hex_cor[i : i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, alpha)


PALETA: dict[str, tuple[int, int, int, int]] = {
    nome: _hex_para_rgba(valor) for nome, valor in PALETA_HEX.items()
}

TILE = 16
LARGURA_PERSONAGEM = 16
ALTURA_PERSONAGEM = 21

PASTA_ASSETS = Path(__file__).resolve().parent
PASTA_OBJETOS = PASTA_ASSETS / "tiles" / "objetos"
PASTA_PERSONAGEM = PASTA_ASSETS / "personagem"


# --- Helpers ------------------------------------------------------------------


def _img(largura: int, altura: int) -> Image.Image:
    return Image.new("RGBA", (largura, altura), (0, 0, 0, 0))


def _rect(d, caixa, cor, contorno="INK") -> None:
    d.rectangle(
        caixa,
        fill=PALETA[cor] if cor else None,
        outline=PALETA[contorno] if contorno else None,
        width=1,
    )


def _linha(d, pontos, cor) -> None:
    d.line(pontos, fill=PALETA[cor], width=1)


def _ponto(d, pontos, cor) -> None:
    d.point(pontos, fill=PALETA[cor])


def _madeira(d, x0, y0, x1, y1, contorno=True) -> None:
    """Madeira em várias camadas: base, ripas, veios e brilho de borda."""
    d.rectangle((x0, y0, x1, y1), fill=PALETA["WOOD_MID"])
    for y in range(y0 + 2, y1, 4):
        _linha(d, [(x0 + 1, y), (x1 - 1, y)], "WOOD_DARK")
        if y + 1 < y1:
            _linha(d, [(x0 + 2, y + 1), (x1 - 2, y + 1)], "WOOD")
    # Veios curtos e deslocados para não parecer uma grade uniforme.
    largura = max(1, x1 - x0 - 3)
    for i, y in enumerate(range(y0 + 3, y1, 7)):
        inicio = x0 + 2 + (i * 7) % max(1, largura // 2)
        fim = min(x1 - 2, inicio + max(3, largura // 3))
        _linha(d, [(inicio, y), (fim, y)], "WOOD_GOLD")
    if y1 - y0 > 2:
        _linha(d, [(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], "WOOD_LIGHT")
        _linha(d, [(x1 - 1, y0 + 1), (x1 - 1, y1 - 1)], "WOOD_SHADOW")
    if contorno:
        d.rectangle((x0, y0, x1, y1), outline=PALETA["INK"], width=1)


# --- Móveis do quarto ---------------------------------------------------------


def gerar_guarda_roupa(lt: int = 2, at: int = 8) -> Image.Image:
    """Encostado na parede esquerda; vista de cima (topo do armário, sem
    portas - elas ficam na frente)."""
    w, h = lt * TILE, at * TILE
    img = _img(w, h)
    d = ImageDraw.Draw(img)
    _madeira(d, 0, 0, w - 1, h - 1)
    # Tampo visto de cima: moldura, junções e borda frontal chanfrada.
    _linha(d, [(3, 2), (w - 5, 2)], "WOOD_GOLD")
    _linha(d, [(3, h - 3), (w - 5, h - 3)], "WOOD_SHADOW")
    for y in range(TILE, h, TILE):
        _linha(d, [(2, y), (w - 5, y)], "WOOD_DARK")
    d.rectangle((w - 5, 1, w - 2, h - 2), fill=PALETA["WOOD_DARK"])
    _linha(d, [(w - 4, 2), (w - 4, h - 3)], "WOOD_LIGHT")
    return img


def gerar_cama(lt: int = 5, at: int = 5) -> Image.Image:
    """Cabeceira de madeira mais larga que a cama, com dois criados-mudos
    integrados nas laterais; colchão com travesseiro e edredom."""
    w, h = lt * TILE, at * TILE
    img = _img(w, h)
    d = ImageDraw.Draw(img)

    cab = 12  # altura da cabeceira
    ns = 17   # largura de cada criado-mudo

    # Cabeceira (largura total, passa da cama)
    _madeira(d, 0, 0, w - 1, cab - 1)

    # Colchão (centro, entre os criados-mudos)
    mx0, mx1 = ns, w - 1 - ns
    _rect(d, (mx0, cab, mx1, h - 1), "LINEN")
    # Travesseiro
    _rect(d, (mx0 + 4, cab + 3, mx1 - 4, cab + 15), "CERAMIC")
    # Edredom
    _rect(d, (mx0, cab + 20, mx1, h - 2), "QUILT")
    _linha(d, [(mx0 + 1, cab + 20), (mx1 - 1, cab + 20)], "QUILT_DARK")
    # Costuras acolchoadas e dobras dão volume ao tecido.
    for y in range(cab + 28, h - 3, 10):
        _linha(d, [(mx0 + 2, y), (mx1 - 2, y)], "QUILT_DARK")
    for x in range(mx0 + 10, mx1, 12):
        _linha(d, [(x, cab + 21), (x, h - 3)], "GLASS")
    _linha(d, [(mx0 + 2, cab + 1), (mx1 - 2, cab + 1)], "CERAMIC_HI")

    # Criados-mudos (laterais, abaixo da cabeceira)
    for x0 in (0, w - ns):
        _madeira(d, x0, cab, x0 + ns - 1, cab + ns - 1)
        cx = x0 + ns // 2
        d.rectangle((cx - 1, cab + ns // 2, cx + 1, cab + ns // 2 + 1), fill=PALETA["BONE"])
    return img


def gerar_mesa_pc(lt: int = 6, at: int = 2) -> Image.Image:
    """Mesa BRANCA encostada na parede de baixo, centralizada. Monitor
    encostado na parede (borda inferior), gabinete do PC no lado esquerdo,
    teclado à frente."""
    w, h = lt * TILE, at * TILE
    img = _img(w, h)
    d = ImageDraw.Draw(img)

    _rect(d, (0, 2, w - 1, h - 1), "DESK")
    _linha(d, [(1, 3), (w - 2, 3)], "CERAMIC_HI")
    _linha(d, [(1, h - 3), (w - 2, h - 3)], "DESK_SH")
    for x in range(16, w, 16):
        _linha(d, [(x, 4), (x, h - 4)], "DESK_SH")

    mx = w // 2

    _rect(d, (mx - 13, h - 12, mx + 13, h - 2), "STEEL_DARK")
    _rect(d, (mx - 11, h - 10, mx + 11, h - 4), "SCREEN")
    _linha(d, [(mx - 9, h - 9), (mx + 8, h - 9)], "GLASS")
    _ponto(d, [(mx + 10, h - 3)], "WATER")

    _rect(d, (3, 4, 15, h - 3), "STEEL_DARK")
    _linha(d, [(6, 6), (12, 6)], "STEEL")
    _linha(d, [(5, h - 6), (13, h - 6)], "STEEL")
    _ponto(d, [(9, 9)], "SCREEN")

    _rect(d, (mx - 12, 4, mx + 12, 9), "DESK_SH")
    for x in range(mx - 9, mx + 10, 4):
        _ponto(d, [(x, 6), (x, 8)], "STEEL_DARK")
    return img


# --- Banheiro -----------------------------------------------------------------


def gerar_chuveiro(lt: int = 2, at: int = 2) -> Image.Image:
    """Chuveiro elétrico branco preso à parede esquerda, como na referência."""
    w, h = lt * TILE, at * TILE
    img = _img(w, h)
    d = ImageDraw.Draw(img)

    # Cano horizontal saindo da parede e corpo cilíndrico branco.
    _rect(d, (0, 5, 13, 8), "CERAMIC")
    _linha(d, [(1, 5), (12, 5)], "CERAMIC_HI")
    _rect(d, (12, 2, 23, 12), "CERAMIC")
    d.ellipse((13, 8, 22, 15), fill=PALETA["CERAMIC_SH"], outline=PALETA["INK"])
    d.ellipse((15, 10, 20, 14), fill=PALETA["STEEL_DARK"])
    # Fiação azul e gotas d'água.
    _linha(d, [(5, 3), (10, 1), (15, 2)], "SCREEN")
    for x, y in ((15, 16), (18, 18), (21, 16), (16, 21), (20, 22)):
        _ponto(d, [(x, y)], "WATER")
    # Ralo separado no piso, canto oposto do box, com grelha.
    d.ellipse((w - 9, h - 9, w - 2, h - 2), fill=PALETA["STEEL"], outline=PALETA["INK"])
    _linha(d, [(w - 7, h - 7), (w - 4, h - 4)], "STEEL_DARK")
    _linha(d, [(w - 4, h - 7), (w - 7, h - 4)], "STEEL_DARK")
    return img


def gerar_vaso(lt: int = 1, at: int = 1) -> Image.Image:
    """Vaso muito compacto, encostado à esquerda e voltado para a direita."""
    w, h = lt * TILE, at * TILE
    img = _img(w, h)
    d = ImageDraw.Draw(img)

    # Caixa à esquerda (parede) e bacia apontando para a direita.
    _rect(d, (0, 3, 5, h - 4), "CERAMIC")
    _linha(d, [(1, 4), (4, 4)], "CERAMIC_HI")
    d.ellipse((4, 2, w - 2, h - 3), fill=PALETA["CERAMIC_HI"], outline=PALETA["INK"])
    d.ellipse((7, 5, w - 4, h - 6), fill=PALETA["CERAMIC_SH"], outline=PALETA["STEEL"])
    _ponto(d, [(3, h // 2)], "STEEL")
    return img


def gerar_pia_banheiro(lt: int = 1, at: int = 1) -> Image.Image:
    """Gabinete marrom compacto, com frente à direita e cuba sobreposta."""
    w, h = lt * TILE, at * TILE
    img = _img(w, h)
    d = ImageDraw.Draw(img)

    # Madeira continua predominante, usando a textura original de ripas/veios.
    _madeira(d, 0, 0, w - 1, h - 1)
    # Cuba quadrada menor, deixando a madeira visível em toda a volta.
    _rect(d, (3, 2, 11, 10), "CERAMIC")
    _rect(d, (5, 4, 9, 8), "CERAMIC_SH", None)
    _ponto(d, [(7, 7)], "STEEL_DARK")
    # Torneira e borda frontal (lado direito).
    _linha(d, [(7, 1), (10, 1), (10, 4)], "STEEL_LIGHT")
    _linha(d, [(w - 3, 1), (w - 3, h - 2)], "WOOD_GOLD")
    _linha(d, [(w - 2, 1), (w - 2, h - 2)], "WOOD_SHADOW")
    return img


# --- Personagem ---------------------------------------------------------------

QUADROS = ("parado", "passo")
DIRECOES = ("baixo", "cima", "esquerda", "direita")

_PERNAS = {
    "parado": ((5, 15, 7, 20), (9, 15, 11, 20)),
    "passo": ((5, 15, 7, 20), (9, 16, 11, 20)),
}


def _corpo_e_pernas(d, quadro: str) -> None:
    # Tronco (camisa)
    _rect(d, (3, 8, 12, 15), "SHIRT")
    _linha(d, [(3, 15), (12, 15)], "SHIRT_SH")
    # Mãos (pele) nas laterais
    d.rectangle((3, 12, 4, 14), fill=PALETA["SKIN"])
    d.rectangle((11, 12, 12, 14), fill=PALETA["SKIN"])
    # Pernas (calça) + sapatos
    esq, dir_ = _PERNAS[quadro]
    for perna in (esq, dir_):
        d.rectangle(perna, fill=PALETA["PANTS"])
        x0, y0, x1, y1 = perna
        d.rectangle((x0, y1 - 1, x1, y1), fill=PALETA["SHOE"])


def gerar_personagem(quadro: str, direcao: str = "baixo") -> Image.Image:
    if quadro not in QUADROS:
        raise ValueError(f"quadro inválido: {quadro!r}")
    if direcao not in DIRECOES:
        raise ValueError(f"direcao inválida: {direcao!r}")

    if direcao == "esquerda":
        return gerar_personagem(quadro, "direita").transpose(Image.FLIP_LEFT_RIGHT)

    img = _img(LARGURA_PERSONAGEM, ALTURA_PERSONAGEM)
    d = ImageDraw.Draw(img)

    _corpo_e_pernas(d, quadro)

    if direcao == "baixo":
        # Cabelo (loiro, médio) cobrindo topo e laterais
        _rect(d, (4, 0, 11, 3), "HAIR", None)
        d.rectangle((4, 3, 5, 6), fill=PALETA["HAIR"])
        d.rectangle((10, 3, 11, 6), fill=PALETA["HAIR"])
        # Rosto
        _rect(d, (5, 2, 10, 8), "SKIN", None)
        d.rectangle((5, 2, 10, 2), fill=PALETA["HAIR"])  # franja
        # Olhos azuis
        _ponto(d, [(6, 4), (9, 4)], "EYE")
        # Barba loira + boca
        d.rectangle((5, 6, 10, 8), fill=PALETA["BEARD"])
        _ponto(d, [(7, 7), (8, 7)], "MOUTH")
        d.rectangle((4, 0, 11, 8), outline=PALETA["INK"], width=0)
    elif direcao == "cima":
        # De costas: só cabelo
        _rect(d, (4, 0, 11, 8), "HAIR", None)
        _linha(d, [(4, 8), (11, 8)], "HAIR_SH")
    else:  # direita (perfil)
        # Nuca (cabelo) à esquerda, rosto à direita
        _rect(d, (4, 0, 8, 7), "HAIR", None)
        _rect(d, (8, 2, 11, 8), "SKIN", None)
        d.rectangle((8, 0, 11, 1), fill=PALETA["HAIR"])  # topo
        _ponto(d, [(10, 4)], "EYE")
        d.rectangle((8, 6, 11, 8), fill=PALETA["BEARD"])  # barba
        _ponto(d, [(11, 7)], "MOUTH")

    return img


# --- Geração ------------------------------------------------------------------

_DIMENSOES_OBJETOS = {
    "guarda_roupa": (2, 6),
    "cama": (6, 5),
    "mesa_pc": (6, 2),
    "chuveiro": (2, 2),
    "vaso": (1, 1),
    "pia_banheiro": (1, 1),
}

_GERADORES_OBJETOS = {
    "guarda_roupa": gerar_guarda_roupa,
    "cama": gerar_cama,
    "mesa_pc": gerar_mesa_pc,
    "chuveiro": gerar_chuveiro,
    "vaso": gerar_vaso,
    "pia_banheiro": gerar_pia_banheiro,
}


def gerar_e_salvar_tudo() -> None:
    PASTA_OBJETOS.mkdir(parents=True, exist_ok=True)
    PASTA_PERSONAGEM.mkdir(parents=True, exist_ok=True)

    total_objetos = 0
    for tipo, gerador in _GERADORES_OBJETOS.items():
        w, h = _DIMENSOES_OBJETOS[tipo]
        gerador(w, h).save(PASTA_OBJETOS / f"{tipo}.png")
        total_objetos += 1

    total_personagem = 0
    for direcao in DIRECOES:
        for quadro in QUADROS:
            gerar_personagem(quadro, direcao).save(
                PASTA_PERSONAGEM / f"{direcao}_{quadro}.png"
            )
            total_personagem += 1

    print(f"Gerados {total_objetos} objetos em: {PASTA_OBJETOS}")
    print(f"Gerados {total_personagem} quadros de personagem em: {PASTA_PERSONAGEM}")


if __name__ == "__main__":
    gerar_e_salvar_tudo()
