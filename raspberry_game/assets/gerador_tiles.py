"""Gera programaticamente os assets pixel art (grayscale) do jogo, usando
Pillow para desenhar pixel a pixel via `ImageDraw`.

Direção de arte:
- Grade de tile: 16x16 pixels lógicos.
- Personagem: 16x21 pixels lógicos, com 2 quadros de caminhada por direção
  (parado e passo).
- Contorno: sempre 1 pixel lógico, na cor mais escura da paleta (INK).
- Sombreamento: no máximo 3 tons de cinza por elemento, sem gradiente, sem
  anti-aliasing (por isso desenhamos em RGBA "flat", sem usar `resize`
  com filtros suaves em nenhum momento).

Rodar `python assets/gerador_tiles.py` regenera todos os PNGs em
`assets/tiles/` e `assets/personagem/`, prontos para o motor (`jogo/tiles.py`
e `jogo/personagem.py`) carregar via `pygame.image.load`.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

# --- Paleta (grayscale puro) -------------------------------------------------

PALETA_HEX = {
    "VOID": "#0c0c0d",   # fundo/vazio
    "INK": "#1c1c1e",    # contornos, sombra mais escura
    "SLATE": "#48484c",  # parede - tom base
    "MID": "#5c5c60",    # tom intermediário (portas/detalhes)
    "ASH": "#8c8c90",    # tom claro (texturas/grout)
    "FOG": "#cccccf",    # chão - tom base
    "BONE": "#f4f4f2",   # branco quase puro (vidro/destaques)
}


def _hex_para_rgba(hex_cor: str, alpha: int = 255) -> tuple[int, int, int, int]:
    hex_cor = hex_cor.lstrip("#")
    r, g, b = (int(hex_cor[i : i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, alpha)


PALETA: dict[str, tuple[int, int, int, int]] = {
    nome: _hex_para_rgba(valor) for nome, valor in PALETA_HEX.items()
}

# --- Dimensões ---------------------------------------------------------------

TAMANHO_TILE = 16
LARGURA_PERSONAGEM = 16
ALTURA_PERSONAGEM = 21

# --- Caminhos de saída ---------------------------------------------------------

PASTA_ASSETS = Path(__file__).resolve().parent
PASTA_TILES = PASTA_ASSETS / "tiles"
PASTA_PERSONAGEM = PASTA_ASSETS / "personagem"


# ==============================================================================
# Helpers reutilizáveis de desenho
# ==============================================================================


def nova_tile(cor_base: str) -> Image.Image:
    """Cria uma imagem RGBA `TAMANHO_TILE`x`TAMANHO_TILE` preenchida com a
    cor base indicada (chave de `PALETA`)."""
    return Image.new("RGBA", (TAMANHO_TILE, TAMANHO_TILE), PALETA[cor_base])


def nova_imagem_transparente(largura: int, altura: int) -> Image.Image:
    """Cria uma imagem RGBA totalmente transparente (usada para sprites que
    não ocupam o retângulo inteiro, como o personagem)."""
    return Image.new("RGBA", (largura, altura), (0, 0, 0, 0))


def desenhar_retangulo(
    desenho: ImageDraw.ImageDraw,
    caixa: tuple[int, int, int, int],
    cor_preenchimento: str | None,
    cor_contorno: str | None = "INK",
) -> None:
    """Desenha um retângulo preenchido com uma cor da paleta e contorno de
    1 pixel lógico (por padrão INK, a cor mais escura), sem gradiente."""
    desenho.rectangle(
        caixa,
        fill=PALETA[cor_preenchimento] if cor_preenchimento else None,
        outline=PALETA[cor_contorno] if cor_contorno else None,
        width=1,
    )


def desenhar_contorno_tile(desenho: ImageDraw.ImageDraw, tamanho: int = TAMANHO_TILE) -> None:
    """Desenha a borda de 1 pixel lógico ao redor de todo o tile, em INK."""
    desenho.rectangle((0, 0, tamanho - 1, tamanho - 1), outline=PALETA["INK"], width=1)


def linha(desenho: ImageDraw.ImageDraw, pontos: list[tuple[int, int]], cor: str) -> None:
    desenho.line(pontos, fill=PALETA[cor], width=1)


def ponto(desenho: ImageDraw.ImageDraw, pontos: list[tuple[int, int]], cor: str) -> None:
    desenho.point(pontos, fill=PALETA[cor])


def _rotacionar_se_vertical(imagem: Image.Image, orientacao: str) -> Image.Image:
    """Gira 90° o tile canônico (desenhado em orientação horizontal) para
    encaixar em paredes verticais. Como é um múltiplo de 90°, não há
    interpolação/anti-aliasing envolvido - a paleta se mantém intacta."""
    if orientacao not in ("horizontal", "vertical"):
        raise ValueError(f"orientacao inválida: {orientacao!r} (use 'horizontal' ou 'vertical')")
    return imagem.rotate(90, expand=False) if orientacao == "vertical" else imagem


# ==============================================================================
# Tiles
# ==============================================================================


def gerar_tile_chao() -> Image.Image:
    """Piso em FOG com um leve padrão de grid/grout: linhas ASH a cada 8px."""
    imagem = nova_tile("FOG")
    desenho = ImageDraw.Draw(imagem)

    for posicao in (0, 8):
        linha(desenho, [(posicao, 0), (posicao, TAMANHO_TILE - 1)], "ASH")
        linha(desenho, [(0, posicao), (TAMANHO_TILE - 1, posicao)], "ASH")

    return imagem


def gerar_tile_parede() -> Image.Image:
    """Parede em SLATE com contorno INK, fiada de tijolos (linhas
    horizontais INK a cada 4px, com juntas verticais alternando de
    deslocamento) e um leve bisel ASH na linha do topo."""
    imagem = nova_tile("SLATE")
    desenho = ImageDraw.Draw(imagem)

    altura_fiada = 4
    linhas_argamassa = range(altura_fiada - 1, TAMANHO_TILE - 1, altura_fiada)  # y = 3, 7, 11

    for indice, y in enumerate(linhas_argamassa):
        linha(desenho, [(1, y), (TAMANHO_TILE - 2, y)], "INK")

        # Juntas verticais entre tijolos, alternando o deslocamento a cada
        # fiada para simular um assentamento "cambado" (staggered brick).
        deslocamento = 4 if indice % 2 == 0 else 0
        for x in range(deslocamento, TAMANHO_TILE, 8):
            if 0 < x < TAMANHO_TILE - 1:
                ponto(desenho, [(x, y + 1)], "INK")

    linha(desenho, [(1, 1), (TAMANHO_TILE - 2, 1)], "ASH")  # bisel superior
    desenhar_contorno_tile(desenho)
    return imagem


def gerar_tile_porta(orientacao: str = "horizontal") -> Image.Image:
    """Reaproveita a parede como moldura, com um painel central em MID e
    uma maçaneta em BONE. `orientacao` gira o tile para encaixar em
    paredes horizontais ou verticais."""
    imagem = gerar_tile_parede()
    desenho = ImageDraw.Draw(imagem)

    desenhar_retangulo(desenho, (3, 2, 12, 15), cor_preenchimento="MID", cor_contorno="INK")
    desenho.rectangle((9, 8, 10, 9), fill=PALETA["BONE"])  # maçaneta

    return _rotacionar_se_vertical(imagem, orientacao)


def gerar_tile_janela(orientacao: str = "horizontal") -> Image.Image:
    """Reaproveita a parede como moldura, com "vidro" em BONE, cruzeta
    central em INK e um brilho diagonal sutil em FOG."""
    imagem = gerar_tile_parede()
    desenho = ImageDraw.Draw(imagem)

    caixa_vidro = (3, 3, 12, 12)
    desenhar_retangulo(desenho, caixa_vidro, cor_preenchimento="BONE", cor_contorno="INK")

    centro_x = (caixa_vidro[0] + caixa_vidro[2]) // 2
    centro_y = (caixa_vidro[1] + caixa_vidro[3]) // 2
    linha(desenho, [(centro_x, caixa_vidro[1] + 1), (centro_x, caixa_vidro[3] - 1)], "INK")
    linha(desenho, [(caixa_vidro[0] + 1, centro_y), (caixa_vidro[2] - 1, centro_y)], "INK")

    linha(desenho, [(4, 6), (6, 4)], "FOG")  # brilho diagonal sutil no canto superior esquerdo

    return _rotacionar_se_vertical(imagem, orientacao)


# ==============================================================================
# Personagem
# ==============================================================================

QUADROS = ("parado", "passo")
DIRECOES = ("baixo", "cima", "esquerda", "direita")

# Retângulos das pernas por quadro: a perna "esquerda" fica um pouco mais
# curta/alta e a "direita" um pouco mais longa/baixa (e vice-versa) para
# simular a passada, sem precisar de gradiente ou interpolação.
_PERNAS_POR_QUADRO = {
    "parado": {"esquerda": (4, 16, 6, 20), "direita": (9, 16, 11, 20)},
    "passo": {"esquerda": (4, 15, 6, 19), "direita": (9, 17, 11, 20)},
}

_CAIXA_CORPO = (3, 7, 12, 15)
_CAIXA_CABECA = (4, 0, 11, 7)


def gerar_personagem(quadro: str, direcao: str = "baixo") -> Image.Image:
    """Gera um quadro do personagem: cabeça arredondada com olhos (pontos
    INK), corpo retangular em SLATE com contorno INK, e pernas que
    alternam de posição entre os quadros "parado" e "passo".

    `direcao` controla a posição dos olhos (perfil/frente/costas);
    "esquerda" é gerada espelhando horizontalmente o quadro "direita",
    já que são simétricos.
    """
    if quadro not in QUADROS:
        raise ValueError(f"quadro inválido: {quadro!r} (use {QUADROS!r})")
    if direcao not in DIRECOES:
        raise ValueError(f"direcao inválida: {direcao!r} (use {DIRECOES!r})")

    if direcao == "esquerda":
        return gerar_personagem(quadro, "direita").transpose(Image.FLIP_LEFT_RIGHT)

    imagem = nova_imagem_transparente(LARGURA_PERSONAGEM, ALTURA_PERSONAGEM)
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
    # "cima" (de costas): sem olhos visíveis.

    return imagem


# ==============================================================================
# Geração/gravação de todos os assets
# ==============================================================================


def gerar_e_salvar_tudo() -> None:
    PASTA_TILES.mkdir(parents=True, exist_ok=True)
    PASTA_PERSONAGEM.mkdir(parents=True, exist_ok=True)

    gerar_tile_chao().save(PASTA_TILES / "chao.png")
    gerar_tile_parede().save(PASTA_TILES / "parede.png")
    gerar_tile_porta("horizontal").save(PASTA_TILES / "porta_horizontal.png")
    gerar_tile_porta("vertical").save(PASTA_TILES / "porta_vertical.png")
    gerar_tile_janela("horizontal").save(PASTA_TILES / "janela_horizontal.png")
    gerar_tile_janela("vertical").save(PASTA_TILES / "janela_vertical.png")
    total_tiles = 6

    total_personagem = 0
    for direcao in DIRECOES:
        for quadro in QUADROS:
            caminho = PASTA_PERSONAGEM / f"{direcao}_{quadro}.png"
            gerar_personagem(quadro, direcao).save(caminho)
            total_personagem += 1

    print(f"Gerados {total_tiles} tiles em: {PASTA_TILES}")
    print(f"Gerados {total_personagem} quadros de personagem em: {PASTA_PERSONAGEM}")


if __name__ == "__main__":
    gerar_e_salvar_tudo()
