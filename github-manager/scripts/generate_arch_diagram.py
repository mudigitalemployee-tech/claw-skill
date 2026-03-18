#!/usr/bin/env python3
"""
Generate an architecture diagram image from a JSON specification.

Usage:
    python3 generate_arch_diagram.py <spec.json> <output.png>

The spec.json must have this structure:
{
  "title": "System Architecture",
  "boxes": [
    {"id": "input", "label": "Input Layer\n(images, configs)", "x": 0.5, "y": 0.85, "w": 0.4, "h": 0.1, "color": "#4E79A7"},
    {"id": "process", "label": "Processing\nPipeline", "x": 0.5, "y": 0.55, "w": 0.4, "h": 0.15, "color": "#59A14F"},
    ...
  ],
  "arrows": [
    {"from": "input", "to": "process", "label": "feeds into"},
    ...
  ]
}

Coordinates: x, y are CENTER of the box, normalized 0-1. w, h are box dimensions.
y=1.0 is top, y=0.0 is bottom.
"""

import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def generate_diagram(spec, output_path):
    fig, ax = plt.subplots(1, 1, figsize=(14, 10), facecolor='#FAFAFA')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('auto')
    ax.axis('off')

    # Title removed — the HTML report provides the section heading
    # Diagram is purely visual (boxes + arrows)

    # Draw boxes
    box_positions = {}  # id -> (cx, cy, w, h)
    for box in spec.get("boxes", []):
        bid = box["id"]
        cx, cy = box["x"], box["y"]
        w, h = box.get("w", 0.3), box.get("h", 0.1)
        color = box.get("color", "#4E79A7")
        text_color = box.get("text_color", "white")
        font_size = box.get("font_size", 11)

        x0 = cx - w / 2
        y0 = cy - h / 2

        # Rounded rectangle
        fancy = FancyBboxPatch(
            (x0, y0), w, h,
            boxstyle="round,pad=0.01",
            facecolor=color,
            edgecolor='#2C3E50',
            linewidth=1.5,
            alpha=0.92,
            zorder=2
        )
        ax.add_patch(fancy)

        # Label
        ax.text(cx, cy, box["label"], ha='center', va='center',
                fontsize=font_size, color=text_color, fontweight='bold',
                fontfamily='sans-serif', zorder=3,
                linespacing=1.4)

        box_positions[bid] = (cx, cy, w, h)

    # Draw arrows
    for arrow in spec.get("arrows", []):
        src = arrow["from"]
        dst = arrow["to"]
        label = arrow.get("label", "")

        if src not in box_positions or dst not in box_positions:
            continue

        sx, sy, sw, sh = box_positions[src]
        dx, dy, dw, dh = box_positions[dst]

        # Determine connection points (bottom of src -> top of dst by default)
        # If src is to the left/right, connect side-to-side
        if abs(sx - dx) > 0.3 and abs(sy - dy) < 0.15:
            # Horizontal: right side of src -> left side of dst
            if sx < dx:
                start = (sx + sw/2, sy)
                end = (dx - dw/2, dy)
            else:
                start = (sx - sw/2, sy)
                end = (dx + dw/2, dy)
        else:
            # Vertical: bottom of src -> top of dst
            if sy > dy:
                start = (sx, sy - sh/2)
                end = (dx, dy + dh/2)
            else:
                start = (sx, sy + sh/2)
                end = (dx, dy - dh/2)

        arrow_style = arrow.get("style", "->")
        color = arrow.get("color", "#555555")

        ax.annotate(
            "", xy=end, xytext=start,
            arrowprops=dict(
                arrowstyle=arrow_style,
                color=color,
                lw=2,
                connectionstyle="arc3,rad=0.0",
                shrinkA=2, shrinkB=2
            ),
            zorder=1
        )

        # Arrow label
        if label:
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2
            ax.text(mid_x + 0.02, mid_y, label, fontsize=8, color='#666666',
                    fontfamily='sans-serif', fontstyle='italic', zorder=4)

    plt.tight_layout(pad=1.0)
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close(fig)
    print(f"Diagram saved to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generate_arch_diagram.py <spec.json> <output.png>")
        sys.exit(1)

    spec_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(spec_path, 'r') as f:
        spec = json.load(f)

    generate_diagram(spec, output_path)
