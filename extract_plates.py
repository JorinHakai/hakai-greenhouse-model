"""Recover the eight 3/16" truss-plate outlines + bolt-hole patterns.

The plate detail box on the truss sheet draws each plate as loose line
segments (one path per segment) with 3/8" bolt holes as 4-bezier circles.
The eight plates are spatially separated in that box, so we cluster the
segments by proximity (one cluster per plate) and take each cluster's
convex hull as the outline.  The drawn plates are convex apart from a small
notch at the apex of the peak plate, which the hull closes -- noted in the
report rather than silently ignored.

Output: truss_plates.json, outlines and hole centres in INCHES, each
plate's coordinates relative to its own centroid.
"""
import pymupdf, math, json

PDF, PT = "drawings_source.pdf", 2.25
# Border of the "3/16" TRUSS PLATES" detail box, read off the sheet as the
# one 'qu' path enclosing the plate cluster.
BOX = (893, 587, 1158, 668)
LINK = 0.5                           # inches: cluster link distance


def item_pts(it, R):
    """Corner points of any drawing item, in rotated page space."""
    if it[0] == "l":
        return [pymupdf.Point(it[1]) * R, pymupdf.Point(it[2]) * R]
    if it[0] == "c":
        return [pymupdf.Point(q) * R for q in it[1:5]]
    if it[0] == "re":
        r = pymupdf.Rect(it[1]) * R
        return [pymupdf.Point(r.x0, r.y0), pymupdf.Point(r.x1, r.y0),
                pymupdf.Point(r.x1, r.y1), pymupdf.Point(r.x0, r.y1)]
    if it[0] == "qu":
        q = it[1]
        return [pymupdf.Point(p) * R for p in (q.ul, q.ur, q.lr, q.ll)]
    return []


def item_edges(it, R):
    """Closed-outline edges for area items; the single segment for a line."""
    p = item_pts(it, R)
    if it[0] == "l":
        return [(p[0].x, p[0].y, p[1].x, p[1].y)] if len(p) == 2 else []
    if it[0] in ("re", "qu"):
        return [(p[k].x, p[k].y, p[(k + 1) % 4].x, p[(k + 1) % 4].y)
                for k in range(4)]
    return []


def collect():
    d = pymupdf.open(PDF); p = d[9]; R = p.rotation_matrix
    segs, holes = [], []
    for dr in p.get_drawings():
        items = dr["items"]
        pts = []
        for it in items:
            pts += item_pts(it, R)
        if not pts:
            continue
        xs = [q.x for q in pts]; ys = [q.y for q in pts]
        if not (min(xs) >= BOX[0] and max(xs) <= BOX[2]
                and min(ys) >= BOX[1] and max(ys) <= BOX[3]):
            continue
        w, h = (max(xs) - min(xs)) / PT, (max(ys) - min(ys)) / PT
        if all(it[0] == "c" for it in items) and 0.2 < w < 0.7 and 0.2 < h < 0.7:
            holes.append(((min(xs) + max(xs)) / 2 / PT, (min(ys) + max(ys)) / 2 / PT))
            continue
        if w > 60 or h > 40:                     # the detail-box border itself
            continue
        for it in items:
            # Two of the eight plates are single 'qu' quad paths rather than
            # polylines, so area items contribute all four of their edges.
            for e in item_edges(it, R):
                L = math.hypot(e[2] - e[0], e[3] - e[1]) / PT
                if 0.02 < L < 25.0:
                    segs.append((e[0] / PT, e[1] / PT, e[2] / PT, e[3] / PT))
    d.close()
    return segs, holes


def cluster(segs):
    """Union-find segments whose endpoints come within LINK inches."""
    n = len(segs); par = list(range(n))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    def uni(a, b):
        a, b = find(a), find(b)
        if a != b: par[b] = a
    def ends(s): return ((s[0], s[1]), (s[2], s[3]))
    for i in range(n):
        for j in range(i + 1, n):
            if any(math.hypot(p[0] - q[0], p[1] - q[1]) < LINK
                   for p in ends(segs[i]) for q in ends(segs[j])):
                uni(i, j)
    groups = {}
    for i, s in enumerate(segs):
        groups.setdefault(find(i), []).append(s)
    return list(groups.values())


def hull(pts):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    if len(pts) < 3:
        return pts
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def inside(pt, poly):
    x, y = pt; c = False
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) / (y1 - y0 + 1e-12) * (x1 - x0):
            c = not c
    return c


def area(poly):
    return 0.5 * abs(sum(poly[i][0]*poly[(i+1) % len(poly)][1]
                         - poly[(i+1) % len(poly)][0]*poly[i][1]
                         for i in range(len(poly))))


if __name__ == "__main__":
    segs, holes = collect()
    groups = cluster(segs)
    groups = [g for g in groups if len(g) >= 3]
    recs = []
    for g in groups:
        pts = [(s[0], s[1]) for s in g] + [(s[2], s[3]) for s in g]
        h = hull(pts)
        if area(h) < 8.0:
            continue
        cx = sum(p[0] for p in h) / len(h); cy = sum(p[1] for p in h) / len(h)
        recs.append({"h": h, "cx": cx, "cy": cy})
    recs.sort(key=lambda r: r["cx"])

    print(f"{len(segs)} outline segments, {len(holes)} bolt holes, "
          f"{len(recs)} plate clusters")
    out = []
    for i, r in enumerate(recs):
        hl = [q for q in holes if inside(q, r["h"])]
        xs = [p[0] for p in r["h"]]; ys = [p[1] for p in r["h"]]
        rec = {"id": i,
               "w": round(max(xs) - min(xs), 3),
               "h": round(max(ys) - min(ys), 3),
               "area_in2": round(area(r["h"]), 2),
               "nholes": len(hl),
               # y flipped: PDF y grows downward, model y grows up
               "poly": [[round(x - r["cx"], 4), round(-(y - r["cy"]), 4)] for x, y in r["h"]],
               "holes": [[round(qx - r["cx"], 4), round(-(qy - r["cy"]), 4)] for qx, qy in hl]}
        out.append(rec)
        print(f"  plate {i}: {rec['w']:6.2f} x {rec['h']:6.2f} in, "
              f"area {rec['area_in2']:7.2f} in2, {rec['nholes']:2d} holes, "
              f"{len(rec['poly'])} hull verts")
    print(f"  total holes assigned: {sum(r['nholes'] for r in out)}")
    json.dump(out, open("truss_plates.json", "w"), indent=1)
    print(f"-> truss_plates.json ({len(out)} plates)")
