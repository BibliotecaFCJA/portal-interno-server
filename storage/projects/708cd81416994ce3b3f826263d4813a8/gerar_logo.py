"""Gera a logo institucional simplificada da FCJA (PNG com transparência).

A logo oficial em alta resolução deve ser substituída pelo acervo da
Fundação quando disponível; este arquivo é um placeholder institucional
com as cores oficiais (vermelho institucional #B3252C e neutros).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
DESTINO = BASE / 'static' / 'img' / 'logo-fcja.png'
DESTINO.parent.mkdir(parents=True, exist_ok=True)

VERMELHO = (179, 37, 44, 255)      # vermelho institucional
VERMELHO_ESCURO = (140, 27, 33, 255)
BRANCO = (255, 255, 255, 255)
CINZA = (74, 74, 74, 255)

LARGURA, ALTURA = 900, 340
imagem = Image.new('RGBA', (LARGURA, ALTURA), (0, 0, 0, 0))
desenho = ImageDraw.Draw(imagem)

# Símbolo: monograma "CJ" dentro de um escudo/casa estilizado -------
# Casa (telhado triangular + corpo) — referência à "Casa".
desenho.polygon(
    [(70, 130), (210, 30), (350, 130)],
    fill=VERMELHO,
)
desenho.rounded_rectangle(
    [95, 125, 325, 300], radius=18, fill=VERMELHO,
)
desenho.rounded_rectangle(
    [115, 145, 305, 280], radius=12, fill=BRANCO,
)

# Letras "CJ" no corpo da casa
def _fonte(tamanho):
    caminhos = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    ]
    for caminho in caminhos:
        if Path(caminho).is_file():
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()

fonte_cj = _fonte(96)
desenho.text((210, 212), 'CJ', anchor='mm', font=fonte_cj, fill=VERMELHO)

# Texto institucional ------------------------------------------------
fonte_titulo = _fonte(72)
fonte_sub = _fonte(34)
desenho.text((390, 120), 'Casa de', anchor='lm', font=fonte_titulo, fill=CINZA)
desenho.text((390, 195), 'José Américo', anchor='lm', font=fonte_titulo,
             fill=VERMELHO)
desenho.text((392, 255), 'FUNDAÇÃO  ·  GOVERNO DA PARAÍBA', anchor='lm',
             font=fonte_sub, fill=CINZA)
desenho.rectangle([390, 285, 830, 291], fill=VERMELHO)

imagem.save(DESTINO, 'PNG', optimize=True)
print(f'Logo gerada em: {DESTINO}')