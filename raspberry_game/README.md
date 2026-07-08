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
  tiles/                 # chao.png, parede.png, porta.png, janela.png (a fornecer)
  personagem/             # spritesheet.png (a fornecer)
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

## Assets

Os PNGs finais (`chao.png`, `parede.png`, `porta.png`, `janela.png` em
`assets/tiles/`, e `spritesheet.png` em `assets/personagem/`, grade 2
colunas [parado, andando] x 4 linhas [baixo, cima, esquerda, direita], cada
frame do tamanho de um tile) ainda não foram fornecidos. Enquanto isso, o
jogo desenha retângulos coloridos e um personagem placeholder (círculo com
indicador de direção) - basta soltar os arquivos nas pastas acima que o
carregamento automático (`jogo/tiles.py`, `jogo/personagem.py`) passa a
usá-los.

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
