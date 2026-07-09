"""Gera programaticamente os assets pixel art do jogo (Pillow).

Direção de arte:
- Grade de tile: 16x16 pixels lógicos.
- Personagem: 16x21, 2 quadros de caminhada por direção.
- Contorno: 1 pixel lógico INK.
- Paredes lisas (sem tijolos); móveis com textura de madeira.
- Sem anti-aliasing / gradientes suaves.

Rodar: `python assets/gerador_tiles.py`
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

# --- Paleta -------------------------------------------------------------------

PALETA_HEX = {
    "VOID": "#0c0c0d",
    "INK": "#1c1c1e",
    "SLATE": "#48484c",
    "MID": "#5c5c60",
    "ASH": "#8c8c90",
    "FOG": "#cccccf",
    "BONE": "#f4f4f2",
    # Madeira (móveis)
    "WOOD_DARK": "#3d2415",
    "WOOD": "#6b3f22",
    "WOOD_LIGHT": "#a06a3c",
    # Banheiro / metal
    "STEEL": "#6e7278",
    "STEEL_DARK": "#3a3d42",
    "CERAMIC": "#e8e6e0",
}


def _hex_para_rgba(hex_cor: str, alpha: int = 255) -> tuple[int, int, int, int]:
    hex_cor = hex_cor.lstrip("#")
    r, g, b = (int(hex_cor[i : i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, alpha)


PALETA: dict[str, tuple[int, int, int, int]] = {
    nome: _hex_para_rgba(valor) for nome, valor in PALETA_HEX.items()
}

TAMANHO_TILE = 16
LARGURA_PERSONAGEM = 16
ALTURA_PERSONAGEM = 21

PASTA_ASSETS = Path(__file__).resolve().parent
PASTA_TILES = PASTA_ASSETS / "tiles"
PASTA_OBJETOS = PASTA_TILES / "objetos"
PASTA_PERSONAGEM = PASTA_ASSETS / "personagem"


# ==============================================================================
# Helpers
# ==============================================================================


def nova_tile(cor_base: str) -> Image.Image:
    return Image.new("RGBA", (TAMANHO_TILE, TAMANHO_TILE), PALETA[cor_base])


def nova_imagem(largura: int, altura: int, cor: str | None = None) -> Image.Image:
    fill = PALETA[cor] if cor else (0, 0, 0, 0)
    return Image.new("RGBA", (largura, altura), fill)


def desenhar_retangulo(
    desenho: ImageDraw.ImageDraw,
    caixa: tuple[int, int, int, int],
    cor_preenchimento: str | None,
    cor_contorno: str | None = "INK",
) -> None:
    desenho.rectangle(
        caixa,
        fill=PALETA[cor_preenchimento] if cor_preenchimento else None,
        outline=PALETA[cor_contorno] if cor_contorno else None,
        width=1,
    )


def desenhar_contorno_tile(desenho: ImageDraw.ImageDraw, tamanho: int = TAMANHO_TILE) -> None:
    desenho.rectangle((0, 0, tamanho - 1, tamanho - 1), outline=PALETA["INK"], width=1)


def linha(desenho: ImageDraw.ImageDraw, pontos: list[tuple[int, int]], cor: str) -> None:
    desenho.line(pontos, fill=PALETA[cor], width=1)


def ponto(desenho: ImageDraw.ImageDraw, pontos: list[tuple[int, int]], cor: str) -> None:
    desenho.point(pontos, fill=PALETA[cor])


def _rotacionar_se_vertical(imagem: Image.Image, orientacao: str) -> Image.Image:
    if orientacao not in ("horizontal", "vertical"):
        raise ValueError(f"orientacao inválida: {orientacao!r}")
    return imagem.rotate(90, expand=False) if orientacao == "vertical" else imagem


def _textura_madeira(desenho: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    """Preenche retângulo com madeira + veios horizontais (máx. 3 tons)."""
    desenho.rectangle((x0, y0, x1, y1), fill=PALETA["WOOD"])
    for y in range(y0 + 2, y1, 3):
        linha(desenho, [(x0 + 1, y), (x1 - 1, y)], "WOOD_DARK")
    # bisel claro no topo
    if y1 - y0 > 2:
        linha(desenho, [(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], "WOOD_LIGHT")


# ==============================================================================
# Tiles base
# ==============================================================================


def gerar_tile_chao() -> Image.Image:
    imagem = nova_tile("FOG")
    desenho = ImageDraw.Draw(imagem)
    for posicao in (0, 8):
        linha(desenho, [(posicao, 0), (posicao, TAMANHO_TILE - 1)], "ASH")
        linha(desenho, [(0, posicao), (TAMANHO_TILE - 1, posicao)], "ASH")
    return imagem


def gerar_tile_parede() -> Image.Image:
    """Parede lisa: SLATE + bisel ASH + contorno INK (sem tijolos)."""
    imagem = nova_tile("SLATE")
    desenho = ImageDraw.Draw(imagem)
    linha(desenho, [(1, 1), (TAMANHO_TILE - 2, 1)], "ASH")
    linha(desenho, [(1, TAMANHO_TILE - 2), (TAMANHO_TILE - 2, TAMANHO_TILE - 2)], "MID")
    desenhar_contorno_tile(desenho)
    return imagem


def gerar_tile_porta(orientacao: str = "horizontal") -> Image.Image:
    imagem = gerar_tile_parede()
    desenho = ImageDraw.Draw(imagem)
    _textura_madeira(desenho, 3, 2, 12, 15)
    desenho.rectangle((3, 2, 12, 15), outline=PALETA["INK"], width=1)
    desenho.rectangle((9, 8, 10, 9), fill=PALETA["BONE"])
    return _rotacionar_se_vertical(imagem, orientacao)


def gerar_tile_janela(orientacao: str = "horizontal") -> Image.Image:
    imagem = gerar_tile_parede()
    desenho = ImageDraw.Draw(imagem)
    caixa_vidro = (3, 3, 12, 12)
    desenhar_retangulo(desenho, caixa_vidro, cor_preenchimento="BONE", cor_contorno="INK")
    centro_x = (caixa_vidro[0] + caixa_vidro[2]) // 2
    centro_y = (caixa_vidro[1] + caixa_vidro[3]) // 2
    linha(desenho, [(centro_x, caixa_vidro[1] + 1), (centro_x, caixa_vidro[3] - 1)], "INK")
    linha(desenho, [(caixa_vidro[0] + 1, centro_y), (caixa_vidro[2] - 1, centro_y)], "INK")
    linha(desenho, [(4, 6), (6, 4)], "FOG")
    return _rotacionar_se_vertical(imagem, orientacao)


# ==============================================================================
# Móveis / banheiro (sprites multi-tile em px lógicos = tiles * 16)
# ==============================================================================


def gerar_guarda_roupa(largura_tiles: int = 2, altura_tiles: int = 5) -> Image.Image:
    """Guarda-roupa de 6 portas: esq / meio (vidro) / dir, empilhadas em 2 colunas."""
    w, h = largura_tiles * TAMANHO_TILE, altura_tiles * TAMANHO_TILE
    imagem = nova_imagem(w, h)
    desenho = ImageDraw.Draw(imagem)
    _textura_madeira(desenho, 0, 0, w - 1, h - 1)
    desenho.rectangle((0, 0, w - 1, h - 1), outline=PALETA["INK"], width=1)

    # 3 faixas verticais de portas (cada uma com 2 portas empilhadas)
    faixa = w // 3
    for i in range(1, 3):
        x = i * faixa
        linha(desenho, [(x, 1), (x, h - 2)], "WOOD_DARK")

    meio = h // 2
    linha(desenho, [(1, meio), (w - 2, meio)], "WOOD_DARK")

    # Portas do meio = vidro (faixa central)
    x0, x1 = faixa + 1, 2 * faixa - 1
    for y0, y1 in ((1, meio - 1), (meio + 1, h - 2)):
        desenhar_retangulo(desenho, (x0, y0, x1, y1), "BONE", "INK")
        # cruzeta leve no vidro
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        linha(desenho, [(cx, y0 + 1), (cx, y1 - 1)], "ASH")
        linha(desenho, [(x0 + 1, cy), (x1 - 1, cy)], "ASH")

    # Puxadores nas portas de madeira
    for i in (0, 2):
        px = i * faixa + faixa // 2
        for py in (meio // 2, meio + meio // 2):
            desenho.rectangle((px, py, px + 1, py + 1), fill=PALETA["BONE"])

    return imagem


def gerar_cama(largura_tiles: int = 3, altura_tiles: int = 5) -> Image.Image:
    """Cama com cabeceira mais larga que o colchão."""
    w, h = largura_tiles * TAMANHO_TILE, altura_tiles * TAMANHO_TILE
    imagem = nova_imagem(w, h)
    desenho = ImageDraw.Draw(imagem)

    # Cabeceira (mais larga: ocupa toda a largura, 4px de altura)
    altura_cab = 5
    _textura_madeira(desenho, 0, 0, w - 1, altura_cab - 1)
    desenho.rectangle((0, 0, w - 1, altura_cab - 1), outline=PALETA["INK"], width=1)

    # Colchão um pouco mais estreito (inset 2px cada lado)
    inset = 2
    _textura_madeira(desenho, inset, altura_cab, w - 1 - inset, h - 1)
    desenho.rectangle((inset, altura_cab, w - 1 - inset, h - 1), outline=PALETA["INK"], width=1)

    # Travesseiro
    desenhar_retangulo(
        desenho,
        (inset + 3, altura_cab + 2, w - inset - 4, altura_cab + 7),
        "CERAMIC",
        "INK",
    )
    # Dobra do lençol
    linha(desenho, [(inset + 1, h - 6), (w - inset - 2, h - 6)], "WOOD_LIGHT")
    return imagem


def gerar_mesa_cabeceira(largura_tiles: int = 2, altura_tiles: int = 2) -> Image.Image:
    w, h = largura_tiles * TAMANHO_TILE, altura_tiles * TAMANHO_TILE
    imagem = nova_imagem(w, h)
    desenho = ImageDraw.Draw(imagem)
    _textura_madeira(desenho, 1, 1, w - 2, h - 2)
    desenho.rectangle((1, 1, w - 2, h - 2), outline=PALETA["INK"], width=1)
    # gaveta
    linha(desenho, [(3, h // 2), (w - 4, h // 2)], "WOOD_DARK")
    desenho.rectangle((w // 2 - 1, h // 2 + 1, w // 2 + 1, h // 2 + 2), fill=PALETA["BONE"])
    return imagem


def gerar_mesa_pc(largura_tiles: int = 5, altura_tiles: int = 2) -> Image.Image:
    """Mesa com monitor no centro e gabinete no lado do guarda-roupa (esq.)."""
    w, h = largura_tiles * TAMANHO_TILE, altura_tiles * TAMANHO_TILE
    imagem = nova_imagem(w, h)
    desenho = ImageDraw.Draw(imagem)

    # Tampo
    _textura_madeira(desenho, 0, h // 2 - 2, w - 1, h - 1)
    desenho.rectangle((0, h // 2 - 2, w - 1, h - 1), outline=PALETA["INK"], width=1)

    # Monitor (centro)
    mx0 = w // 2 - 8
    mx1 = w // 2 + 7
    desenhar_retangulo(desenho, (mx0, 1, mx1, h // 2 - 3), "STEEL_DARK", "INK")
    desenhar_retangulo(desenho, (mx0 + 2, 3, mx1 - 2, h // 2 - 5), "STEEL", "INK")
    # base do monitor
    linha(desenho, [(w // 2, h // 2 - 3), (w // 2, h // 2 - 2)], "INK")

    # Gabinete no lado do guarda-roupa (esquerda no top-down da planta)
    gx0 = 2
    desenhar_retangulo(desenho, (gx0, h // 2 - 1, gx0 + 10, h - 2), "STEEL_DARK", "INK")
    ponto(desenho, [(gx0 + 3, h // 2 + 2), (gx0 + 5, h // 2 + 2)], "BONE")
    return imagem


def gerar_pia_banheiro(largura_tiles: int = 2, altura_tiles: int = 2) -> Image.Image:
    w, h = largura_tiles * TAMANHO_TILE, altura_tiles * TAMANHO_TILE
    imagem = nova_imagem(w, h)
    desenho = ImageDraw.Draw(imagem)
    _textura_madeira(desenho, 1, 1, w - 2, h - 2)
    desenho.rectangle((1, 1, w - 2, h - 2), outline=PALETA["INK"], width=1)
    # Pia (círculo branco)
    cx, cy = w // 2, h // 2
    r = min(w, h) // 3
    desenho.ellipse((cx - r, cy - r, cx + r, cy + r), fill=PALETA["CERAMIC"], outline=PALETA["INK"])
    ponto(desenho, [(cx, cy)], "ASH")  # ralo da pia
    return imagem


def gerar_vaso(largura_tiles: int = 2, altura_tiles: int = 2) -> Image.Image:
    w, h = largura_tiles * TAMANHO_TILE, altura_tiles * TAMANHO_TILE
    imagem = nova_imagem(w, h)
    desenho = ImageDraw.Draw(imagem)
    # caixa
    desenhar_retangulo(desenho, (w // 2 - 4, 1, w // 2 + 4, 6), "CERAMIC", "INK")
    # assento
    desenho.ellipse((2, 5, w - 3, h - 2), fill=PALETA["STEEL"], outline=PALETA["INK"])
    desenho.ellipse((5, 8, w - 6, h - 5), fill=PALETA["STEEL_DARK"], outline=PALETA["INK"])
    return imagem


def gerar_chuveiro(largura_tiles: int = 2, altura_tiles: int = 2) -> Image.Image:
    w, h = largura_tiles * TAMANHO_TILE, altura_tiles * TAMANHO_TILE
    imagem = nova_imagem(w, h)
    desenho = ImageDraw.Draw(imagem)
    # haste da parede (esquerda) até o centro
    linha(desenho, [(1, h // 2), (w // 2 - 4, h // 2)], "STEEL")
    # cabeça do chuveiro
    cx, cy = w // 2, h // 2
    desenho.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=PALETA["STEEL"], outline=PALETA["INK"])
    ponto(desenho, [(cx - 2, cy), (cx + 2, cy), (cx, cy - 2), (cx, cy + 2)], "STEEL_DARK")
    return imagem


def gerar_ralo(largura_tiles: int = 1, altura_tiles: int = 1) -> Image.Image:
    w, h = largura_tiles * TAMANHO_TILE, altura_tiles * TAMANHO_TILE
    imagem = nova_imagem(w, h)
    desenho = ImageDraw.Draw(imagem)
    cx, cy = w // 2, h // 2
    desenho.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=PALETA["INK"], outline=PALETA["STEEL_DARK"])
    ponto(desenho, [(cx, cy)], "STEEL")
    return imagem


# ==============================================================================
# Personagem
# ==============================================================================

QUADROS = ("parado", "passo")
DIRECOES = ("baixo", "cima", "esquerda", "direita")

_PERNAS_POR_QUADRO = {
    "parado": {"esquerda": (4, 16, 6, 20), "direita": (9, 16, 11, 20)},
    "passo": {"esquerda": (4, 15, 6, 19), "direita": (9, 17, 11, 20)},
}

_CAIXA_CORPO = (3, 7, 12, 15)
_CAIXA_CABECA = (4, 0, 11, 7)


def gerar_personagem(quadro: str, direcao: str = "baixo") -> Image.Image:
    if quadro not in QUADROS:
        raise ValueError(f"quadro inválido: {quadro!r}")
    if direcao not in DIRECOES:
        raise ValueError(f"direcao inválida: {direcao!r}")

    if direcao == "esquerda":
        return gerar_personagem(quadro, "direita").transpose(Image.FLIP_LEFT_RIGHT)

    imagem = nova_imagem(LARGURA_PERSONAGEM, ALTURA_PERSONAGEM)
    desenho = ImageDraw.Draw(imagem)

    pernas = _PERNAS_POR_QUADRO[quadro]
    desenho.rectangle(pernas["esquerda"], fill=PALETA["INK"])
    desenho.rectangle(pernas["direita"], fill=PALETA["INK"])

    desenhar_retangulo(desenho, _CAIXA_CORPO, cor_preenchimento="SLATE", cor_contorno="INK")
    desenho.ellipse(_CAIXA_CABECA, fill=PALETA["SLATE"], outline=PALETA["INK"], width=1)

    if direcao == "baixo":
        ponto(desenho, [(6, 3), (9, 3)], "INK")
    elif direcao == "direita":
        ponto(desenho, [(9, 3)], "INK")

    return imagem


# ==============================================================================
# Geração
# ==============================================================================

# Dimensões padrão dos sprites (tiles) — alinhadas ao quarto.json (escala 0.5)
_DIMENSOES_OBJETOS = {
    "guarda_roupa": (2, 5),
    "cama": (3, 5),
    "mesa_cabeceira": (2, 2),
    "mesa_pc": (5, 2),
    "pia_banheiro": (2, 2),
    "vaso": (2, 2),
    "chuveiro": (2, 2),
    "ralo": (1, 1),
}

_GERADORES_OBJETOS = {
    "guarda_roupa": gerar_guarda_roupa,
    "cama": gerar_cama,
    "mesa_cabeceira": gerar_mesa_cabeceira,
    "mesa_pc": gerar_mesa_pc,
    "pia_banheiro": gerar_pia_banheiro,
    "vaso": gerar_vaso,
    "chuveiro": gerar_chuveiro,
    "ralo": gerar_ralo,
}


def gerar_e_salvar_tudo() -> None:
    PASTA_TILES.mkdir(parents=True, exist_ok=True)
    PASTA_OBJETOS.mkdir(parents=True, exist_ok=True)
    PASTA_PERSONAGEM.mkdir(parents=True, exist_ok=True)

    gerar_tile_chao().save(PASTA_TILES / "chao.png")
    gerar_tile_parede().save(PASTA_TILES / "parede.png")
    gerar_tile_porta("horizontal").save(PASTA_TILES / "porta_horizontal.png")
    gerar_tile_porta("vertical").save(PASTA_TILES / "porta_vertical.png")
    gerar_tile_janela("horizontal").save(PASTA_TILES / "janela_horizontal.png")
    gerar_tile_janela("vertical").save(PASTA_TILES / "janela_vertical.png")
    total_tiles = 6

    total_objetos = 0
    for tipo, gerador in _GERADORES_OBJETOS.items():
        w, h = _DIMENSOES_OBJETOS[tipo]
        gerador(w, h).save(PASTA_OBJETOS / f"{tipo}.png")
        total_objetos += 1

    total_personagem = 0
    for direcao in DIRECOES:
        for quadro in QUADROS:
            caminho = PASTA_PERSONAGEM / f"{direcao}_{quadro}.png"
            gerar_personagem(quadro, direcao).save(caminho)
            total_personagem += 1

    print(f"Gerados {total_tiles} tiles em: {PASTA_TILES}")
    print(f"Gerados {total_objetos} objetos em: {PASTA_OBJETOS}")
    print(f"Gerados {total_personagem} quadros de personagem em: {PASTA_PERSONAGEM}")


if __name__ == "__main__":
    gerar_e_salvar_tudo()
