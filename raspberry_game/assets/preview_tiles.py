"""Preview visual rápido (Pygame) de todos os tiles e quadros de personagem
gerados por `gerador_tiles.py`, para conferir a arte sem abrir cada PNG.

Rodar: `python assets/preview_tiles.py` (rode `gerador_tiles.py` antes, caso
ainda não exista nenhum PNG em `tiles/`/`personagem/`).

Controles: ESC ou fechar a janela para sair.
"""

from __future__ import annotations

from pathlib import Path

import pygame

PASTA_ASSETS = Path(__file__).resolve().parent
PASTA_TILES = PASTA_ASSETS / "tiles"
PASTA_PERSONAGEM = PASTA_ASSETS / "personagem"

ESCALA = 6  # amplia os sprites (nativamente pequenos, 16px) para caberem na tela
ESPACAMENTO = 14
COLUNAS = 7
COR_FUNDO = (30, 30, 32)
COR_TEXTO = (220, 220, 220)
COR_GRADE_CELULA = (55, 55, 58)

# Altura de referência: o personagem (21px) é o sprite mais alto do conjunto.
_ALTURA_SPRITE_REF_PX = 21


def _listar_imagens() -> list[Path]:
    return sorted(PASTA_TILES.glob("*.png")) + sorted(PASTA_PERSONAGEM.glob("*.png"))


def _carregar_ampliado(caminho: Path) -> pygame.Surface:
    original = pygame.image.load(str(caminho)).convert_alpha()
    tamanho_ampliado = (original.get_width() * ESCALA, original.get_height() * ESCALA)
    # scale (não smoothscale) preserva o look "pixel perfeito", sem
    # anti-aliasing/gradientes - consistente com a direção de arte.
    return pygame.transform.scale(original, tamanho_ampliado)


def main() -> None:
    arquivos = _listar_imagens()
    if not arquivos:
        print(
            "Nenhum PNG encontrado em 'tiles/' ou 'personagem/'.\n"
            "Rode antes: python assets/gerador_tiles.py"
        )
        return

    pygame.init()
    pygame.display.set_caption("Maptale - Preview dos tiles")
    fonte = pygame.font.SysFont(None, 18)

    altura_celula_sprite = _ALTURA_SPRITE_REF_PX * ESCALA
    largura_celula = 16 * ESCALA + ESPACAMENTO
    altura_celula = altura_celula_sprite + ESPACAMENTO + 18  # + espaço pro rótulo

    linhas = -(-len(arquivos) // COLUNAS)  # divisão com arredondamento pra cima
    largura_janela = COLUNAS * largura_celula + ESPACAMENTO
    altura_janela = linhas * altura_celula + ESPACAMENTO

    tela = pygame.display.set_mode((largura_janela, altura_janela))

    itens = [(caminho.stem, _carregar_ampliado(caminho)) for caminho in arquivos]

    relogio = pygame.time.Clock()
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                rodando = False

        tela.fill(COR_FUNDO)

        for indice, (nome, superficie) in enumerate(itens):
            coluna = indice % COLUNAS
            linha_idx = indice // COLUNAS
            x = ESPACAMENTO + coluna * largura_celula
            y = ESPACAMENTO + linha_idx * altura_celula

            celula = pygame.Rect(x, y, largura_celula - ESPACAMENTO // 2, altura_celula - ESPACAMENTO // 2)
            pygame.draw.rect(tela, COR_GRADE_CELULA, celula, border_radius=4)

            # Sprites mais baixos que a referência (tiles) ficam alinhados
            # pela base, como ficariam no jogo (personagem "de pé" no tile).
            pos_y = y + (altura_celula_sprite - superficie.get_height())
            tela.blit(superficie, (x, pos_y))

            rotulo = fonte.render(nome, True, COR_TEXTO)
            tela.blit(rotulo, (x, y + altura_celula_sprite + 2))

        pygame.display.flip()
        relogio.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
