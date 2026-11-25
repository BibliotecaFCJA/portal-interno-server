"""
Converte a imagem 'marca-dágua.jpeg' (fundo branco) em
'static/img/marca-dagua.png' com fundo transparente.

Técnica: preenchimento (flood fill) a partir das bordas — apenas os pixels
quase brancos CONECTADOS às bordas ficam transparentes. Assim, áreas brancas
internas da arte (olhos, detalhes, texto) são preservadas.
"""

from collections import deque
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent
ORIGEM = BASE / 'marca-dágua.jpeg'
DESTINO = BASE / 'static' / 'img' / 'marca-dagua.png'

# Tolerância para considerar um pixel como "fundo claro".
LIMIAR = 232


def eh_fundo(pixel):
    r, g, b = pixel[0], pixel[1], pixel[2]
    return r >= LIMIAR and g >= LIMIAR and b >= LIMIAR


def main():
    img = Image.open(ORIGEM).convert('RGBA')
    largura, altura = img.size
    pixels = img.load()

    visitados = bytearray(largura * altura)
    fila = deque()

    # Semeia a fila com todos os pixels de borda que sejam fundo.
    for x in range(largura):
        for y in (0, altura - 1):
            if eh_fundo(pixels[x, y]):
                fila.append((x, y))
    for y in range(altura):
        for x in (0, largura - 1):
            if eh_fundo(pixels[x, y]):
                fila.append((x, y))

    # BFS: espalha a transparência somente pelo fundo conectado às bordas.
    while fila:
        x, y = fila.popleft()
        indice = y * largura + x
        if visitados[indice]:
            continue
        visitados[indice] = 1
        if not eh_fundo(pixels[x, y]):
            continue
        r, g, b, _ = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)
        if x > 0:
            fila.append((x - 1, y))
        if x < largura - 1:
            fila.append((x + 1, y))
        if y > 0:
            fila.append((x, y - 1))
        if y < altura - 1:
            fila.append((x, y + 1))

    # Recorte automático do excesso de margem transparente.
    caixa = img.getbbox()
    if caixa:
        img = img.crop(caixa)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(DESTINO), 'PNG')
    print(f'OK: {DESTINO} ({img.size[0]}x{img.size[1]})')


if __name__ == '__main__':
    main()