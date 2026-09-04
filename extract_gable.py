"""Measure the gable end wall: glazing outline, door leaf rails, openings.

Sheet 2 carries two elevations of the same wall -- "Front Wall Frame" (upper
left) and "Front Wall Glazing" (lower right).  We work from the frame
elevation, establish its datum from the 246.25" overall width and the base
line, then read the door leaf's rail heights off the linework.
"""
import pymupdf, math, collections
from extract_plates import item_edges

PDF, PT = "drawings_source.pdf", 2.25
FRAME_BOX = (30, 45, 670, 400)          # the upper-left frame elevation, pts


def segs(pno, box):
    d = pymupdf.open(PDF); p = d[pno]; R = p.rotation_matrix
    out = []
    for dr in p.get_drawings():
        for it in dr["items"]:
            for e in item_edges(it, R):
                x0, y0, x1, y1 = (v / PT for v in e)
                if all(box[0]/PT <= x <= box[2]/PT for x in (x0, x1)) and \
                   all(box[1]/PT <= y <= box[3]/PT for y in (y0, y1)):
                    out.append((x0, y0, x1, y1))
    d.close()
    return out


if __name__ == "__main__":
    S = segs(1, FRAME_BOX)
    print(f"{len(S)} segments in the frame elevation")

    # --- datum ---------------------------------------------------------
    # base: the longest horizontal line; overall width should be 246.25"
    hor = [s for s in S if abs(s[3]-s[1]) < 0.06]
    hor.sort(key=lambda s: -abs(s[2]-s[0]))
    print("\nlongest horizontals (span, y):")
    for s in hor[:6]:
        print(f"   span {abs(s[2]-s[0]):8.3f}\"  y={(s[1]+s[3])/2:8.3f}"
              f"  x {min(s[0],s[2]):8.3f}..{max(s[0],s[2]):8.3f}")
    base = hor[0]
    Y_BASE = (base[1] + base[3]) / 2
    X_C = (min(base[0], base[2]) + max(base[0], base[2])) / 2
    print(f"\ndatum: X_C={X_C:.3f}  Y_BASE={Y_BASE:.3f}  "
          f"base span={abs(base[2]-base[0]):.3f}\" (expect 246.25)")

    def M(x, y): return (round(x - X_C, 3), round(Y_BASE - y, 3))

    # --- door leaf: horizontals inside the door width -------------------
    DW = 18.0     # search a little wider than the 34 3/8" frame
    rails = []
    for s in S:
        if abs(s[3]-s[1]) > 0.06:
            continue
        xa, xb = sorted((s[0], s[2]))
        if xa > X_C - DW and xb < X_C + DW and abs(xb-xa) > 8:
            rails.append((round(Y_BASE - (s[1]+s[3])/2, 3), round(xb-xa, 3),
                          round(xa - X_C, 3), round(xb - X_C, 3)))
    rails.sort()
    print(f"\ndoor-width horizontals ({len(rails)}), model height / span / x0 / x1:")
    for h, w, x0, x1 in rails:
        print(f"   y={h:8.3f}  span={w:7.3f}  x {x0:7.3f}..{x1:7.3f}")

    # --- door leaf: verticals inside the door width ---------------------
    vert = []
    for s in S:
        if abs(s[2]-s[0]) > 0.06:
            continue
        x = (s[0]+s[2])/2
        if abs(x - X_C) < DW:
            ya, yb = sorted((Y_BASE - s[1], Y_BASE - s[3]))
            if yb - ya > 8:
                vert.append((round(x - X_C, 3), round(ya, 3), round(yb, 3)))
    vert.sort()
    print(f"\ndoor-width verticals ({len(vert)}), model x / y0 / y1:")
    for x, y0, y1 in vert:
        print(f"   x={x:8.3f}  y {y0:8.3f}..{y1:8.3f}  (len {y1-y0:7.3f})")
