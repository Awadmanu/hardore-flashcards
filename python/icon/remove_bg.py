#!/usr/bin/env python3
"""
remove_bg.py — Quita el fondo cuadrado de una imagen y lo vuelve transparente.

Uso:
    python remove_bg.py icon.png
    python remove_bg.py icon.png -o icon_transparente.png
    python remove_bg.py icon.png --tolerance 35
"""

from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image


def color_distance(c1, c2) -> int:
    """Distancia simple entre dos colores RGB."""
    return sum(abs(a - b) for a, b in zip(c1[:3], c2[:3]))


def get_corner_background_color(img: Image.Image) -> tuple[int, int, int]:
    """
    Estima el color de fondo usando las cuatro esquinas.
    Si el fondo es uniforme, esto funciona bastante bien.
    """
    width, height = img.size

    corners = []
    for pos in [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]:
        pixel = img.getpixel(pos)
        if isinstance(pixel, tuple):
            r, g, b = pixel[:3]
        else:
            # Handle non-tuple cases (e.g., grayscale or float)
            r = g = b = int(pixel) if pixel is not None else 0
        corners.append((r, g, b))

    r = sum(c[0] for c in corners) // 4
    g = sum(c[1] for c in corners) // 4
    b = sum(c[2] for c in corners) // 4

    return r, g, b


def remove_background(
    input_path: Path,
    output_path: Path,
    tolerance: int = 30,
    feather: bool = True,
) -> None:
    img = Image.open(input_path).convert("RGBA")
    bg_color = get_corner_background_color(img)

    width, height = img.size

    for y in range(height):
        for x in range(width):
            pixel = img.getpixel((x, y))
            r, g, b, a = pixel if isinstance(pixel, tuple) else (pixel, pixel, pixel, 255)
            r, g, b = int(r) if r is not None else 0, int(g) if g is not None else 0, int(b) if b is not None else 0
            dist = color_distance((r, g, b), bg_color)

            if dist <= tolerance:
                # Fondo claro: transparente total
                img.putpixel((x, y), (r, g, b, 0))

            elif feather and dist <= tolerance * 2:
                # Borde suavizado para evitar dientes de sierra
                alpha = int(255 * (dist - tolerance) / tolerance)
                img.putpixel((x, y), (r, g, b, alpha))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Quita el fondo cuadrado de una imagen y lo vuelve transparente."
    )

    parser.add_argument(
        "image",
        help="Imagen de entrada, por ejemplo icon.png",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Imagen PNG de salida. Por defecto añade _transparent al nombre.",
    )

    parser.add_argument(
        "--tolerance",
        type=int,
        default=30,
        help="Tolerancia para detectar el fondo. Prueba valores entre 20 y 80.",
    )

    parser.add_argument(
        "--no-feather",
        action="store_true",
        help="Desactiva suavizado de bordes.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.image)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(f"{input_path.stem}_transparent.png")

    if not input_path.exists():
        print(f"[ERROR] No existe: {input_path}")
        return 1

    try:
        remove_background(
            input_path=input_path,
            output_path=output_path,
            tolerance=args.tolerance,
            feather=not args.no_feather,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print("[OK] Fondo eliminado")
    print(f"     Entrada: {input_path}")
    print(f"     Salida:  {output_path}")
    print()
    print("Ahora puedes generar el .ico con:")
    print(f"     python make_icon.py {output_path} -o icon.ico")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())