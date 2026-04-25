#!/usr/bin/env python3
"""
make_icon.py — Convierte cualquier imagen a .ico para Windows
Uso: python make_icon.py mi_imagen.png
     python make_icon.py mi_imagen.png -o mi_icono.ico
"""

import sys
import os
import argparse

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Necesitas Pillow: pip install pillow")
    sys.exit(1)

# Tamaños estándar que Windows usa (explorador, taskbar, ALT+TAB, etc.)
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def make_ico(src: str, dst: str):
    img = Image.open(src).convert("RGBA")

    # Recortar a cuadrado centrado si no lo es
    w, h = img.size
    if w != h:
        side = min(w, h)
        left = (w - side) // 2
        top  = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        print(f"  Recortado a cuadrado {side}×{side}")

    frames = [img.resize((s, s), Image.Resampling.LANCZOS) for s in ICO_SIZES]
    frames[0].save(dst, format="ICO", sizes=[(s, s) for s in ICO_SIZES],
                   append_images=frames[1:])
    print(f"  Guardado: {dst}")
    print(f"  Tamaños incluidos: {ICO_SIZES}")


def main():
    parser = argparse.ArgumentParser(description="Convierte imagen a .ico para Windows")
    parser.add_argument("imagen", help="Imagen de entrada (PNG, JPG, WEBP...)")
    parser.add_argument("-o", "--output", help="Nombre del .ico de salida (por defecto: mismo nombre)")
    args = parser.parse_args()

    if not os.path.exists(args.imagen):
        print(f"[ERROR] No se encuentra: {args.imagen}")
        sys.exit(1)

    dst = args.output or os.path.splitext(args.imagen)[0] + ".ico"
    print(f"\nConvirtiendo {args.imagen} → {dst}")
    make_ico(args.imagen, dst)
    print("\n¡Listo! Ahora ejecuta build_windows.bat para compilar con el nuevo icono.")


if __name__ == "__main__":
    main()