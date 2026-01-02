#!/usr/bin/env python3
"""
Generate extension icons using PIL/Pillow.
Run: python generate_icons.py
"""

import os
from pathlib import Path

def create_icons():
    """Create extension icons using Pillow."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not installed. Installing...")
        os.system("pip install Pillow --quiet")
        from PIL import Image, ImageDraw
    
    # Icon sizes
    sizes = [16, 32, 48, 128]
    
    # Colors
    bg_color = (37, 99, 235)  # #2563eb (primary blue)
    fg_color = (255, 255, 255)  # White
    accent_color = (96, 165, 250)  # #60a5fa (light blue)
    
    icons_dir = Path(__file__).parent
    
    for size in sizes:
        # Create image with rounded rectangle background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw rounded rectangle background
        radius = max(2, size // 8)
        draw.rounded_rectangle(
            [(0, 0), (size - 1, size - 1)],
            radius=radius,
            fill=bg_color
        )
        
        # Draw a simple document icon
        margin = size // 4
        doc_width = size - (margin * 2)
        doc_height = size - (margin * 2)
        
        # Document outline
        doc_points = [
            (margin, margin),
            (margin + doc_width * 0.7, margin),
            (margin + doc_width, margin + doc_height * 0.2),
            (margin + doc_width, margin + doc_height),
            (margin, margin + doc_height),
        ]
        draw.polygon(doc_points, fill=fg_color)
        
        # Fold corner
        fold_points = [
            (margin + doc_width * 0.7, margin),
            (margin + doc_width * 0.7, margin + doc_height * 0.2),
            (margin + doc_width, margin + doc_height * 0.2),
        ]
        draw.polygon(fold_points, fill=accent_color)
        
        # Lines on document
        if size >= 32:
            line_y_start = margin + doc_height * 0.35
            line_spacing = max(2, doc_height * 0.15)
            line_margin = margin + doc_width * 0.15
            line_width = doc_width * 0.6
            
            for i in range(3):
                y = line_y_start + (i * line_spacing)
                if y < margin + doc_height - line_spacing:
                    draw.rectangle(
                        [(line_margin, y), (line_margin + line_width, y + max(1, size // 16))],
                        fill=bg_color
                    )
        
        # Save icon
        icon_path = icons_dir / f'icon{size}.png'
        img.save(icon_path, 'PNG')
        print(f"Created: {icon_path}")
    
    print("\nIcons generated successfully!")

if __name__ == '__main__':
    create_icons()
