# Maptale - Jogo Raspberry Pi (Python)

Recebe o mapa gerado pelo app mobile (ver
[`../schema/mapa.schema.json`](../schema/mapa.schema.json)), converte para
uma grade de tiles e roda um jogo top-down simples em Pygame, com suporte a
controle Xbox e iluminação controlada por um Arduino via serial.

## Estrutura

```
servidor.py            # Flask: POST /upload_map, salva o JSON em mapas/
mapa/
  esquema.py            # validação manual do JSON recebido
  grade.py              # converter_json_em_grade() + rasterização Bresenham
jogo/
  principal.py          # entry point: sobe o Flask (thread) + loop Pygame
  configuracoes.py       # constantes (tamanho de tile, FPS, portas, etc.)
  tiles.py               # tileset + fallback de retângulos coloridos
  personagem.py          # spritesheet 4 direções + colisão
  entrada.py              # teclado + Xbox (pygame.joystick)
  iluminacao.py           # thread serial ON/OFF + overlay escuro
assets/
  gerador_tiles.py        # gera a pixel art (Pillow) a partir da paleta/especificação
  preview_tiles.py        # janela Pygame com todos os tiles/quadros lado a lado
  requirements-assets.txt # Pillow (só para gerar/pré-visualizar os assets)
  tiles/                  # chao.png, parede.png, porta_*.png, janela_*.png (gerados)
  personagem/              # <direcao>_<quadro>.png (gerados)
mapas/                    # JSONs recebidos (gerado em runtime, gitignored)
systemd/maptale-jogo.service
```

## Instalação

```bash
cd raspberry_game
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Raspberry Pi OS, `pygame` pode exigir bibliotecas do sistema
(`sudo apt install python3-pygame libsdl2-dev` costuma resolver a maioria
dos casos caso o `pip install` falhe ao compilar).

## Rodando manualmente

```bash
python3 jogo/principal.py
```

Isso sobe o servidor Flask em `http://0.0.0.0:5000/upload_map` **e** abre a
janela do jogo. Assim que o app mobile envia um mapa, ele é salvo em
`mapas/<nome_ambiente>.json` e recarregado automaticamente no jogo, sem
precisar reiniciar o processo.

Também é possível rodar só o servidor (útil para testar o upload sem abrir
o Pygame):

```bash
python3 servidor.py
```

## Assets (pixel art gerada programaticamente)

Os PNGs em `assets/tiles/` e `assets/personagem/` são gerados por
`assets/gerador_tiles.py` (usa Pillow), seguindo a direção de arte pixel
art grayscale (paleta de 7 tons, grade de 16x16, contorno INK de 1px,
máximo 3 tons de cinza por elemento):

```bash
pip install -r assets/requirements-assets.txt   # só Pillow, não é preciso no Pi
python assets/gerador_tiles.py
```

Isso (re)gera:
- `assets/tiles/chao.png`, `parede.png`, `porta_horizontal.png`,
  `porta_vertical.png`, `janela_horizontal.png`, `janela_vertical.png`.
- `assets/personagem/<direcao>_<quadro>.png` para as 4 direções
  (`baixo`, `cima`, `esquerda`, `direita`) x 2 quadros (`parado`, `passo`).

Para conferir visualmente sem abrir cada PNG:

```bash
python assets/preview_tiles.py
```

`jogo/tiles.py` e `jogo/personagem.py` carregam esses arquivos
automaticamente (e ampliam de 16px lógico para `TILE_SIZE_PX`, 32px por
padrão, preservando a proporção do personagem). Se algum PNG estiver
ausente, o jogo continua funcionando com um placeholder procedural no
lugar (retângulo colorido / boneco simples).

## Controle Xbox

Conecte o controle antes de iniciar o jogo (USB ou Bluetooth pareado). O
eixo analógico esquerdo controla o movimento; sem controle conectado, use
as setas ou WASD.

## Arduino (iluminação)

`jogo/iluminacao.py` espera receber as strings `ON`/`OFF` (uma por linha)
na porta serial configurada em `jogo/configuracoes.py`
(`PORTA_SERIAL = "/dev/ttyACM0"`, `BAUDRATE_SERIAL = 9600`). Ajuste a porta
conforme o seu Arduino (`ls /dev/tty*` para descobrir). Se a porta não
existir, o jogo continua rodando normalmente (assume luz ligada) e tenta
reconectar periodicamente.

## Autostart no boot (systemd)

```bash
sudo cp systemd/maptale-jogo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable maptale-jogo.service
sudo systemctl start maptale-jogo.service

# Ver logs:
journalctl -u maptale-jogo.service -f
```

Ajuste `WorkingDirectory` e `User` no arquivo `.service` conforme o local
onde o repositório foi clonado no seu Pi. Se o Pi rodar sem ambiente
gráfico (Raspberry Pi OS Lite), descomente as variáveis `SDL_VIDEODRIVER`/
`SDL_FBDEV` no `.service` para o Pygame desenhar direto no framebuffer.
