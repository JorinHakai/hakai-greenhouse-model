"""Draw the model truss on top of the original CAD linework.

This is the visual counterpart to gh_verify.py: if a member is the wrong
length, in the wrong place or missing, it shows up immediately against the
grey drawing lines.  Needs the source drawings, so it is a dev tool rather
than part of the build.

    python gh_overlay.py    ->  verification_overlay.png
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
import pymupdf

from gh_geometry import *
import gh_plates as GP
from extract_plates import item_edges

PDF, PT = "drawings_source.pdf", 2.25
X_C, Y_BASE = 267.560, 223.680        # sheet-10 elevation datum, inches


def drawing_segments():
    d = pymupdf.open(PDF); p = d[9]; R = p.rotation_matrix
    segs = []
    for dr in p.get_drawings():
        for it in dr["items"]:
            for e in item_edges(it, R):
                x0, y0, x1, y1 = (v/PT for v in e)
                # keep only the elevation region, drop tables + title block
                if not (124 <= x0 <= 427 and 44 <= y0 <= 249):
                    continue
                if not (124 <= x1 <= 427 and 44 <= y1 <= 249):
                    continue
                segs.append((x0-X_C, Y_BASE-y0, x1-X_C, Y_BASE-y1))
    d.close()
    return segs


fig, axes = plt.subplots(1, 2, figsize=(22, 9))

for ax, (title, xlim, ylim) in zip(axes, [
        ("Full truss on drawing linework", (-130, 130), (-6, 130)),
        ("Right half, joints and plates", (30, 128), (48, 122))]):

    for x0, y0, x1, y1 in drawing_segments():
        ax.plot([x0, x1], [y0, y1], color="0.35", lw=0.8, zorder=5)

    # model members
    def mem(a, b, col, lab=None, lw=5.0):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=col, lw=lw,
                solid_capstyle="round", label=lab, zorder=3, alpha=0.55)

    first = True
    for sx in (1, -1):
        mem((sx*TC_A[0], TC_A[1]), (sx*TC_B[0], TC_B[1]), "#0b6fa4",
            "top chord 127 5/16 (2x3x3/16 L)" if first else None)
        mem((sx*BC_A[0], BC_A[1]), (sx*BC_B[0], BC_B[1]), "#128a5f",
            "bottom chord 120 3/8 (2x2x3/16 L)" if first else None)
        a, b = WEB_L
        mem((sx*a[0], a[1]), (sx*b[0], b[1]), "#c0392b",
            "long web 59 11/16" if first else None)
        a, b = WEB_S
        mem((sx*a[0], a[1]), (sx*b[0], b[1]), "#e07b00",
            "short web 13 13/16  (WAS MISSING)" if first else None)
        mem((sx*(HWI+1.5), 0.0), (sx*(HWI+1.5), POST_H), "#5b3fa8",
            "post 52 7/16 (1.5x3x3/16 C)" if first else None)
        first = False
    mem(WEB_C[0], WEB_C[1], "#b8138a", "centre web 26 3/16")

    # plates
    lab = "3/16\" truss plate (8 per truss, NEW)"
    for pid, px, py, prot, pmir, tag in GP.PLACEMENTS:
        c, s = math.cos(math.radians(prot)), math.sin(math.radians(prot))
        poly = []
        for x, y in GP.OUTLINE[pid]:
            u = -x if pmir else x
            poly.append((px + u*c - y*s, py + u*s + y*c))
        ax.add_patch(MplPoly(poly, closed=True, facecolor="#f2c200",
                             edgecolor="#8a6d00", alpha=0.45, lw=1.2,
                             zorder=2, label=lab))
        lab = None
        for hx, hy in GP.HOLES[pid]:
            u = -hx if pmir else hx
            ax.plot(px + u*c - hy*s, py + u*s + hy*c, marker="o", ms=2.4,
                    color="#4a3c00", zorder=4)

    ax.set_title(title, fontsize=13)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal"); ax.grid(alpha=0.18, lw=0.5)
    ax.set_xlabel("x from centreline (in)"); ax.set_ylabel("height (in)")

axes[0].legend(loc="upper left", fontsize=8.5, framealpha=0.94)
fig.suptitle("Model truss (colour) over original CAD linework (grey)  -  "
             "3/8\" = 1'-0\" sheet, geometry measured at 2.25 pt/inch",
             fontsize=14)
fig.tight_layout()
fig.savefig("verification_overlay.png", dpi=115)
print("-> verification_overlay.png")
