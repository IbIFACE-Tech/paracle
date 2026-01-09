#!/usr/bin/env python3
"""Create square icon from Paracle logo."""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("âŒ Pillow not installed. Install with: pip install Pillow")
    exit(1)


def create_icon(size: int = 128):
    """Create a square Paracle icon.

    Args:
        size: Icon size (width and height)
    """
    # Create white background
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)

    # Try to load existing logo
    assets_dir = Path(__file__).parent.parent / "assets"
    logo_path = assets_dir / "paracle_vis.png"

    if logo_path.exists():
        # Load and resize existing logo
        logo = Image.open(logo_path)

        # Resize maintaining aspect ratio
        logo.thumbnail((int(size * 0.8), int(size * 0.8)), Image.Resampling.LANCZOS)

        # Center the logo
        x = (size - logo.width) // 2
        y = (size - logo.height) // 2

        # Paste logo (handle transparency)
        if logo.mode == "RGBA":
            img.paste(logo, (x, y), logo)
        else:
            img.paste(logo, (x, y))
    else:
        # Fallback: Draw simple "P" text if logo not found
        try:
            # Try to use a system font
            font_size = int(size * 0.6)
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        text = "P"
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center text
        x = (size - text_width) // 2
        y = (size - text_height) // 2

        # Draw black text
        draw.text((x, y), text, fill="black", font=font)

    # Save icon
    output_path = assets_dir / "paracle_icon.png"
    img.save(output_path, "PNG")
    print(f"âœ… Icon created: {output_path}")
    print(f"   Size: {size}x{size} pixels")

    # Also create a 64x64 version
    if size == 128:
        img_small = img.resize((64, 64), Image.Resampling.LANCZOS)
        output_small = assets_dir / "paracle_icon_64.png"
        img_small.save(output_small, "PNG")
        print(f"âœ… Small icon created: {output_small}")
        print("   Size: 64x64 pixels")


if __name__ == "__main__":
    import sys

    size = 128
    if len(sys.argv) > 1:
        size = int(sys.argv[1])

    create_icon(size)
