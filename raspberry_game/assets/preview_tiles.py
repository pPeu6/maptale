"""Preview visual rápido (Pygame) de tiles, móveis e personagem gerados
por `gerador_tiles.py`.

Rodar: `python assets/preview_tiles.py`

Controles: ESC ou fechar a janela para sair.
"""

from __future__ import annotations

from pathlib import Path

import pygame

PASTA_ASSETS = Path(__file__).resolve().parent
PASTA_TILES = PASTA_ASSETS / "tiles"
PASTA_OBJETOS = PASTA_TILES / "objetos"
PASTA_PERSONAGEM = PASTA_ASSETS / "personagem"

ESCALA = 4
ESPACAMENTO = 12
COLUNAS = 6
COR_FUNDO = (30, 30, 32)
COR_TEXTO = (220, 220, 220)
COR_GRADE_CELULA = (55, 55, 58)

# Célula larga o bastante para o guarda-roupa / cama (5 tiles * 16 * escala)
_LARGURA_CELULA_REF = 5 * 16
_ALTURA_SPRITE_REF_PX = 5 * 16


def _listar_imagens() -> list[Path]:
    tiles = sorted(PASTA_TILES.glob("*.png"))
    objetos = sorted(PASTA_OBJETOS.glob("*.png")) if PASTA_OBJETOS.exists() else []
    personagem = sorted(PASTA_PERSONAGEM.glob("*.png"))
    return tiles + objetos + personagem


def _carregar_ampliado(caminho: Path) -> pygame.Surface:
    original = pygame.image.load(str(caminho)).convert_alpha()
    tamanho_ampliado = (original.get_width() * ESCALA, original.get_height() * ESCALA)
    return pygame.transform.scale(original, tamanho_ampliado)


def main() -> None:
    arquivos = _listar_imagens()
    if not arquivos:
        print(
            "Nenhum PNG encontrado.\n"
            "Rode antes: python assets/gerador_tiles.py"
        )
        return

    pygame.init()
    pygame.display.set_caption("Maptale - Preview dos tiles")
    fonte = pygame.font.SysFont(None, 16)

    largura_celula = _LARGURA_CELULA_REF * ESCALA + ESPACAMENTO
    altura_celula = _ALTURA_SPRITE_REF_PX * ESCALA + ESPACAMENTO + 18

    linhas = -(-len(arquivos) // COLUNAS)
    largura_janela = min(COLUNAS * largura_celula + ESPACAMENTO, 1400)
    altura_janela = min(linhas * altura_celula + ESPACAMENTO, 900)

    tela = pygame.display.set_mode((largura_janela, altura_janela))
    itens = [(caminho.stem, _carregar_ampliado(caminho)) for caminho in arquivos]

    scroll_y = 0
    max_scroll = max(0, linhas * altura_celula + ESPACAMENTO - altura_janela)

    relogio = pygame.time.Clock()
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                rodando = False
            elif evento.type == pygame.MOUSEWHEEL:
                scroll_y = max(0, min(max_scroll, scroll_y - evento.y * 40))

        tela.fill(COR_FUNDO)

        for indice, (nome, superficie) in enumerate(itens):
            coluna = indice % COLUNAS
            linha_idx = indice // COLUNAS
            x = ESPACAMENTO + coluna * largura_celula
            y = ESPACAMENTO + linha_idx * altura_celula - scroll_y

            if y + altura_celula < 0 or y > altura_janela:
                continue

            celula = pygame.Rect(
                x, y, largura_celula - ESPACAMENTO // 2, altura_celula - ESPACAMENTO // 2
            )
            pygame.draw.rect(tela, COR_GRADE_CELULA, celula, border_radius=4)

            pos_y = y + (_ALTURA_SPRITE_REF_PX * ESCALA - superficie.get_height())
            tela.blit(superficie, (x, pos_y))

            rotulo = fonte.render(nome, True, COR_TEXTO)
            tela.blit(rotulo, (x, y + _ALTURA_SPRITE_REF_PX * ESCALA + 2))

        pygame.display.flip()
        relogio.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
