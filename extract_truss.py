"""Measure truss + gable-brace linework off the vector CAD sheets.

Scale is exactly 2.25 pt/inch (3/8" = 1'-0" at 72 dpi), established by
differencing three known dimension spans on one sheet.  We only measure
*geometry* linework here, never dimension lines, so no arrowhead inset applies.
"""
import pymupdf, math, collections, json

PDF   = "drawings_source.pdf"
PT_IN = 2.25                      # points per inch


def sheet_lines(pno):
    """All straight segments on a sheet, in points, page-rotated space."""
    doc = pymupdf.open(PDF)
    p   = doc[pno]
    R   = p.rotation_matrix
    segs = []
    for dr in p.get_drawings():
        for it in dr["items"]:
            if it[0] == "l":
                a = pymupdf.Point(it[1]) * R
                b = pymupdf.Point(it[2]) * R
                segs.append((a.x, a.y, b.x, b.y))
            elif it[0] == "re":
                r = pymupdf.Rect(it[1]) * R
                segs += [(r.x0, r.y0, r.x1, r.y0), (r.x1, r.y0, r.x1, r.y1),
                         (r.x1, r.y1, r.x0, r.y1), (r.x0, r.y1, r.x0, r.y0)]
            elif it[0] == "c":
                pts = [pymupdf.Point(q) * R for q in it[1:5]]
                for i in range(3):
                    segs.append((pts[i].x, pts[i].y, pts[i+1].x, pts[i+1].y))
    doc.close()
    return segs


def in_box(s, box):
    x0, y0, x1, y1 = box
    return all(x0 <= v <= x1 for v in (s[0], s[2])) and \
           all(y0 <= v <= y1 for v in (s[1], s[3]))


def report(pno, box, want, label):
    """Print segments whose length matches any wanted inch-length."""
    segs = [s for s in sheet_lines(pno) if in_box(s, box)]
    print(f"\n=== sheet {pno+1} : {label} : {len(segs)} segs in box ===")
    hits = collections.defaultdict(list)
    for s in segs:
        L = math.hypot(s[2]-s[0], s[3]-s[1]) / PT_IN
        for w in want:
            if abs(L - w) < 0.35:
                hits[w].append((L, s))
    for w in sorted(want):
        rows = sorted(hits[w], key=lambda r: -r[0])
        print(f"  target {w:9.4f}\"  -> {len(rows)} match(es)")
        for L, s in rows[:6]:
            print(f"      L={L:9.4f}  ({s[0]/PT_IN:8.3f},{s[1]/PT_IN:8.3f})"
                  f" -> ({s[2]/PT_IN:8.3f},{s[3]/PT_IN:8.3f})")
    return segs


if __name__ == "__main__":
    # Truss sheet: elevation occupies the middle of the sheet; exclude the
    # materials/fastener tables (top corners) and the plate box (bottom right).
    TRUSS_BOX = (280, 100, 960, 560)
    TRUSS_WANT = [127.3125,   # top chord
                  120.375,    # bottom chord
                  59.6875,    # long web
                  26.1875,    # centre web / king post
                  13.8125,    # short web
                  52.4375]    # truss post
    report(9, TRUSS_BOX, TRUSS_WANT, "truss members")

    # Gable bracing sheet: horizontal braces.
    GAB_BOX = (280, 100, 960, 620)
    GAB_WANT = [148.5, 104.8125, 107.375, 94.375]
    report(2, GAB_BOX, GAB_WANT, "gable braces")
