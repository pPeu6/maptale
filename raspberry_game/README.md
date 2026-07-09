# Maptale - Jogo Raspberry Pi (Python)

Carrega o mapa local [`mapas/quarto.json`](mapas/quarto.json) (ver
[`../schema/mapa.schema.json`](../schema/mapa.schema.json)), converte
para uma grade de tiles e roda um jogo top-down em Pygame (tela cheia),
com suporte a controle Xbox e iluminação controlada por Arduino via serial.

## Estrutura

```
mapa/
  grade.py              # converter_json_em_grade() + rasterização Bresenham
jogo/
  principal.py          # entry point: mapa local + loop Pygame fullscreen
  configuracoes.py       # constantes (tile, FPS, MAPA_PADRAO, etc.)
  tiles.py               # tileset + sprites de móveis
  personagem.py          # spritesheet 4 direções + colisão
  entrada.py              # teclado + Xbox (pygame.joystick)
  iluminacao.py           # thread serial ON/OFF + overlay escuro
assets/
  gerador_tiles.py        # gera a pixel art (Pillow)
  preview_tiles.py        # galeria Pygame dos tiles/móveis/personagem
  requirements-assets.txt # Pillow (só para gerar/pré-visualizar)
  tiles/                  # chao, parede, porta, janela + objetos/
  personagem/              # <direcao>_<quadro>.png
mapas/quarto.json         # mapa fixo do quarto + banheiro
systemd/maptale-jogo.service
```

## Instalação

```bash
cd raspberry_game
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r assets/requirements-assets.txt
python assets/gerador_tiles.py
```

No Raspberry Pi OS, `pygame` pode exigir bibliotecas do sistema
(`sudo apt install python3-pygame libsdl2-dev`).

## Rodando

```bash
python3 jogo/principal.py
```

Abre em **tela cheia**. ESC sai. Se o mapa for menor que a tela, fica
centralizado com bordas pretas.

## Assets (pixel art)

```bash
python assets/gerador_tiles.py
python assets/preview_tiles.py
```

Direção de arte: contorno INK 1px, sem anti-alias, paredes lisas, móveis
com textura de madeira (paleta marrom).

## Controle Xbox

Eixo analógico esquerdo; sem controle, use setas ou WASD.

## Arduino (iluminação)

`jogo/iluminacao.py` espera `ON`/`OFF` na porta serial de
`jogo/configuracoes.py`. Se a porta não existir, o jogo assume luz ligada.

## Autostart (systemd)

```bash
sudo cp systemd/maptale-jogo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now maptale-jogo.service
journalctl -u maptale-jogo.service -f
```
