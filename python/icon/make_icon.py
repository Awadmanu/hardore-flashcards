#!/usr/bin/env python3
"""
make_icon.py — Convierte una imagen a icon.ico multi-resolución para Windows.

Uso:
    python make_icon.py icon.png
    python make_icon.py icon.png -o icon.ico
    python make_icon.py icon.png --crop
    python make_icon.py icon.png --padding 0.12
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Falta Pillow. Instálalo con:")
    print("        pip install pillow")
    sys.exit(1)


ICO_SIZES = [
    (16, 16),
    (24, 24),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
]


def make_square_canvas(img: Image.Image, crop: bool = False, padding: float = 0.0) -> Image.Image:
    """
    Convierte la imagen en cuadrada.

    - Si crop=True, recorta centrado.
    - Si crop=False, añade fondo transparente.
    - padding añade margen interno transparente.
    """

    img = img.convert("RGBA")
    width, height = img.size

    if crop:
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        img = img.crop((left, top, left + side, top + side))
    else:
        side = max(width, height)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        x = (side - width) // 2
        y = (side - height) // 2
        canvas.paste(img, (x, y), img)
        img = canvas

    if padding > 0:
        if not 0 <= padding < 0.5:
            raise ValueError("El padding debe estar entre 0 y 0.5")

        side = img.size[0]
        inner_size = int(side * (1 - padding * 2))

        resized = img.resize((inner_size, inner_size), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        offset = (side - inner_size) // 2
        canvas.paste(resized, (offset, offset), resized)
        img = canvas

    return img


def create_icon(input_path: Path, output_path: Path, crop: bool, padding: float) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {input_path}")

    if not input_path.is_file():
        raise ValueError(f"No es un archivo válido: {input_path}")

    try:
        img = Image.open(input_path)
    except Exception as exc:
        raise ValueError(f"No se pudo abrir la imagen: {exc}") from exc

    img = make_square_canvas(img, crop=crop, padding=padding)

    # Usamos una base grande para que Pillow genere bien todos los tamaños.
    base = img.resize((256, 256), Image.Resampling.LANCZOS)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    base.save(
        output_path,
        format="ICO",
        sizes=ICO_SIZES,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convierte una imagen PNG/JPG/WEBP/etc. en un .ico multi-resolución para Windows."
    )

    parser.add_argument(
        "image",
        help="Imagen de entrada. Recomendado: PNG cuadrado de 512x512 o 1024x1024.",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Archivo .ico de salida. Por defecto usa el mismo nombre que la imagen.",
    )

    parser.add_argument(
        "--crop",
        action="store_true",
        help="Recorta la imagen a cuadrado en vez de añadir fondo transparente.",
    )

    parser.add_argument(
        "--padding",
        type=float,
        default=0.0,
        help="Margen interno transparente. Ejemplo: 0.08 o 0.12.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.image)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(".ico")

    try:
        create_icon(
            input_path=input_path,
            output_path=output_path,
            crop=args.crop,
            padding=args.padding,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print("[OK] Icono generado correctamente")
    print(f"     Entrada: {input_path}")
    print(f"     Salida:  {output_path}")
    print(f"     Tamaños: {', '.join(f'{w}x{h}' for w, h in ICO_SIZES)}")
    print()
    print("Ahora vuelve a ejecutar build_windows.bat.")
    print("Si Windows sigue mostrando el icono viejo, cambia el nombre del .exe o reinicia el Explorador.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())