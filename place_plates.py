"""Locate each 3/16" truss plate on the truss elevation.

The plates appear twice on the truss sheet: flat in the detail box
(extract_plates.py recovers those outlines) and in place on the elevation.
Both carry the same 3/8" bolt holes, so we match each detail plate to its
elevation position by 2-point RANSAC over the hole patterns -- robust to the
extra holes the elevation carries at each joint (purlin punches, stringer
holes, post-cleat bolts) which belong to no plate.

Scale is expected to solve to 1.00; that is the check that the detail box is
drawn at the same scale as the elevation, and hence that the recovered
outline sizes are true.

Output: plate_placements.json in MODEL inches
        (x = 0 building centreline, y = 0 top of foundation).
"""
import pymupdf, math, json
from extract_plates import item_pts

PDF, PT = "drawings_source.pdf", 2.25
ELEV = (280, 100, 960, 560)          # truss elevation region, page points
# Elevation datum from the extracted linework: post inner faces at
# 149.440 / 385.680 in (= 236.24", the interior truss width), bases at 223.680.
X_C, Y_BASE = 267.560, 223.680
TOL = 0.15                           # inch inlier tolerance


def elev_holes():
    d = pymupdf.open(PDF); p = d[9]; R = p.rotation_matrix
    out = []
    for dr in p.get_drawings():
        items = dr["items"]
        if not items or not all(it[0] == "c" for it in items):
            continue
        pts = []
        for it in items:
            pts += item_pts(it, R)
        xs = [q.x for q in pts]; ys = [q.y for q in pts]
        if not (0.2 < (max(xs)-min(xs))/PT < 0.7 and 0.2 < (max(ys)-min(ys))/PT < 0.7):
            continue
        cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
        if ELEV[0] <= cx <= ELEV[2] and ELEV[1] <= cy <= ELEV[3]:
            out.append((cx/PT - X_C, Y_BASE - cy/PT))     # model inches
    d.close()
    return out


def ransac(D, E):
    """Best similarity mapping detail holes D into elevation holes E.
    Returns (ninliers, rot_deg, scale, tx, ty, mirror, rms)."""
    best = (0, 0.0, 1.0, 0.0, 0.0, False, 9e9)
    for mir in (False, True):
        Dm = [(-x, y) if mir else (x, y) for x, y in D]
        for a in range(len(Dm)):
            for b in range(len(Dm)):
                if a == b: continue
                dax, day = Dm[b][0]-Dm[a][0], Dm[b][1]-Dm[a][1]
                dl = math.hypot(dax, day)
                if dl < 1.0: continue
                for c in range(len(E)):
                    for e in range(len(E)):
                        if c == e: continue
                        ex, ey = E[e][0]-E[c][0], E[e][1]-E[c][1]
                        el = math.hypot(ex, ey)
                        if el < 1.0: continue
                        sc = el/dl
                        if not (0.92 < sc < 1.08): continue
                        th = math.atan2(ey, ex) - math.atan2(day, dax)
                        cs, sn = math.cos(th)*sc, math.sin(th)*sc
                        tx = E[c][0] - (Dm[a][0]*cs - Dm[a][1]*sn)
                        ty = E[c][1] - (Dm[a][0]*sn + Dm[a][1]*cs)
                        n, ss = 0, 0.0
                        for (px, py) in Dm:
                            qx = px*cs - py*sn + tx
                            qy = px*sn + py*cs + ty
                            dmin = min((qx-fx)**2 + (qy-fy)**2 for fx, fy in E)
                            if dmin < TOL*TOL:
                                n += 1; ss += dmin
                        if n > best[0] or (n == best[0] and ss/max(n,1) < best[6]**2):
                            best = (n, math.degrees(th), sc, tx, ty, mir,
                                    math.sqrt(ss/n) if n else 9e9)
    return best


# Which joint each plate serves, from the truss topology: 8 joints, 8 plates.
JOINT = {0: "knee (left)", 1: "short-web top (right)", 2: "mid joint (?)",
         3: "centre bottom / king-post base", 4: "peak",
         5: "mid joint (?)", 6: "short-web top (left)", 7: "knee (right)"}

if __name__ == "__main__":
    plates = json.load(open("truss_plates.json"))
    E = elev_holes()
    print(f"{len(E)} bolt holes on the truss elevation\n")
    out = []
    for p in plates:
        D = [tuple(h) for h in p["holes"]]
        n, rot, sc, tx, ty, mir, rms = ransac(D, E)
        ok = "OK " if n == len(D) and rms < 0.05 else "?? "
        print(f"  {ok}plate {p['id']} ({len(D)} holes, {p['w']:5.2f}x{p['h']:5.2f}in): "
              f"{n}/{len(D)} inliers  at ({tx:8.3f},{ty:8.3f})  "
              f"rot={rot:8.2f}d  scale={sc:6.4f}  rms={rms:.4f}in"
              f"{'  MIRROR' if mir else ''}")
        out.append({"plate": p["id"], "nholes": len(D), "inliers": n,
                    "x": round(tx, 4), "y": round(ty, 4),
                    "rot_deg": round(rot, 3), "scale": round(sc, 4),
                    "mirror": bool(mir), "rms_in": round(rms, 4),
                    "w": p["w"], "h": p["h"], "joint": JOINT.get(p["id"], "")})
    json.dump(out, open("plate_placements.json", "w"), indent=1)
    print("\n-> plate_placements.json")
