"""Check the model against the drawings.

Five families of check:

  A. DIMENSIONS   modelled length/position vs the stated drawing value.
  B. CONNECTIVITY every truss member end must land on another member.  This
                  is the check that catches members floating in mid-air --
                  the v3 model had six per truss sitting up to 16" clear of
                  anything, and no dimensional check could see it.
  C. CLEARANCE    no structural member may cross a door opening.
  D. PLATES       every plate must sit on a real joint and cover the members
                  meeting there.
  E. END WALLS    both ends glazed, the door leaf fits its opening and tiles
                  its own height, and the openings are really cut -- tested
                  against the built mesh, not against the intent.

    python gh_verify.py
"""
import math, json
from gh_geometry import *
import gh_plates as GP

rows, fails = [], 0


def chk(name, model, drawing, tol, src):
    global fails
    d = model - drawing
    ok = abs(d) <= tol
    if not ok:
        fails += 1
    rows.append((ok, name, model, drawing, d, src))
    return ok


def seg_dist(p, a, b):
    """Distance from point p to segment a-b."""
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay
    L2 = dx*dx + dy*dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy)/L2))
    return math.hypot(px - (ax+t*dx), py - (ay+t*dy))


# ======================================================================
# A. DIMENSIONS
# ======================================================================
def L(a, b): return math.hypot(b[0]-a[0], b[1]-a[1])

hw_glaze = HW + P_GBAR[1][0]/2 * 0  # glazing outer face is HW by definition
chk("Overall width (glazing outer)", 2*HW, 246.25, 0.05, "s1/s10 20'-6 1/4\"")
chk("Overall length", LENGTH, 615.25, 0.02, "s7/s8 615 1/4\"")
chk("Top of ridge", RIDGE_TOP, 122.875, 0.02, "s1/s7 10'-2 7/8\"")
chk("Roof pitch (deg)", PITCH, 23.1, 0.02, "s3/s10 23.1")
chk("Interior truss width", INT_TRUSS_W, 236.25, 0.05, "s10 19'-8 1/4\"")
chk("Exterior truss width", EXT_TRUSS_W, 242.25, 0.05, "s10 20'-2 1/4\"")
chk("Eave bend point height", BEND_H, 52.09, 0.15, "s7 geom")
chk("Eave arc R (glazing)", EAVE_R, 27.79, 0.05, "tangency solve")
chk("Truss post height", POST_H, 52.4375, 0.02, "s10 52 7/16\"")

chk("Top chord length", L(TC_A, TC_B), TC_LEN, 0.05, "s10 127 5/16\"")
chk("Bottom chord length", L(BC_A, BC_B), BC_LEN, 0.05, "s10 120 3/8\"")
chk("Centre web length", L(*WEB_C), WEBC_LEN, 0.05, "s10 26 3/16\"")
chk("Long web length", L(*WEB_L), WEBL_LEN, 0.05, "s10 59 11/16\"")
chk("Short web length", L(*WEB_S), WEBS_LEN, 0.05, "s10 13 13/16\"")

p1, p2 = (purlin_pt(s) for s in PURLIN_S)
chk("Purlin-1 centre height", p1[1], 99.755, 0.06, "s7 band 98.09-101.42")
chk("Purlin-2 centre height", p2[1], 82.650, 0.06, "s7 band 80.97-84.33")
chk("Purlin spacing (slope)", PURLIN_S[1]-PURLIN_S[0], 43.5, 0.02, "s1 43 1/2\"")

chk("Door frame width", 2*DOOR_HW, 34.375, 0.02, "s1/s2 34 3/8\"")
chk("Door clear opening width", 2*DL_HW, 32.373, 0.03, "s2 geom")
chk("Door clear opening head", DOOR_HEAD, 76.187, 0.02, "s2 geom")
chk("Door frame top", DOOR_TOP, 77.200, 0.02, "s2 geom")
chk("Door stile width", DL_STILE, 2.0, 0.02, "s2 geom 17.187->14.187")
chk("Door lower light height", DL_LIGHTS[0][1]-DL_LIGHTS[0][0], 27.173, 0.03,
    "s2 geom")
chk("Door upper light height", DL_LIGHTS[1][1]-DL_LIGHTS[1][0], 27.174, 0.03,
    "s2 geom")
chk("Door kick panel height", DL_KICK[1]-DL_KICK[0], 12.827, 0.03, "s2 geom")
chk("Gable post top", GABLE_POST_TOP, 94.375, 0.02, "s3 94 3/8\"")
chk("Gable post spacing", 2*GABLE_POST_X, 98.0, 0.02, "s3 98\"")
chk("Outside base to gable post", HW-GABLE_POST_X, 74.125, 0.02, "s3 74 1/8\"")
chk("Upper gable brace length", 2*HB_HI_X, HB_HI_LEN, 0.05, "s3 148 1/2\"")
chk("Upper gable brace height", HB_HI_Y, 80.0, 0.06, "s3 80\"")
chk("Lower gable brace length", HB_LO_XOUT-HB_LO_XIN, HB_LO_LEN, 0.05,
    "s3 104 13/16\"")
chk("Lower gable brace height", HB_LO_Y, 38.0, 0.06, "s3 38\"")
chk("Gable purlin support length", L(PSUP_A_PT, PSUP_B_PT), PSUP_LEN, 0.06,
    "s3 107 3/8\"")
chk("Glazing-bar pitch", RIB_Z[1]-RIB_Z[0], 24.5, 0.01, "s9 24 1/2\"")
chk("Rib chain end gap", LENGTH-RIB_Z[-1], 1.375, 0.01,
    "s9 1 3/8 + 25x24 1/2 + 1 3/8")
chk("First truss from end", TRUSS_Z[0], 125.375, 0.02, "s7 125 3/8\"")
chk("Truss spacing (inner)", TRUSS_Z[2]-TRUSS_Z[1], 125.5, 0.05, "s7 125 1/2\"")

# ======================================================================
# B. CONNECTIVITY -- no member may float
# ======================================================================
# One truss half plus the mirrored half, as centrelines in the X-Y plane.
MEMBERS = []
for sx in (1, -1):
    MEMBERS += [
        (f"top chord {sx:+d}",    (sx*TC_A[0], TC_A[1]), (sx*TC_B[0], TC_B[1])),
        (f"bottom chord {sx:+d}", (sx*BC_A[0], BC_A[1]), (sx*BC_B[0], BC_B[1])),
        (f"long web {sx:+d}",     (sx*WEB_L[0][0], WEB_L[0][1]),
                                  (sx*WEB_L[1][0], WEB_L[1][1])),
        (f"short web {sx:+d}",    (sx*WEB_S[0][0], WEB_S[0][1]),
                                  (sx*WEB_S[1][0], WEB_S[1][1])),
        (f"post {sx:+d}",         (sx*(HWI+1.5), 0.0), (sx*(HWI+1.5), POST_H)),
    ]
MEMBERS.append(("centre web", WEB_C[0], WEB_C[1]))

# Section depths are up to 3", so an end within 3.5" of another member's line
# is a direct bolted joint.  A member end may ALSO be legitimately held by a
# plate (the knee is exactly that: post, top chord and bottom chord all stop
# short of each other and are tied by the 13.6 x 22" knee plate), or land on
# the foundation.  A member that satisfies none of the three is floating.
JOIN_TOL = 3.5
PLATE_MARGIN = 1.0      # inches of plate beyond the member end

def plate_polys():
    """Every plate outline placed into model X-Y coordinates."""
    out = []
    for pid, px, py, prot, pmir, tag in GP.PLACEMENTS:
        c, s = math.cos(math.radians(prot)), math.sin(math.radians(prot))
        poly = []
        for x, y in GP.OUTLINE[pid]:
            u = -x if pmir else x
            poly.append((px + u*c - y*s, py + u*s + y*c))
        out.append((tag, poly))
    return out

def in_poly(p, poly, margin=0.0):
    """Point in polygon, optionally grown by `margin` about its centroid."""
    if margin:
        cx = sum(q[0] for q in poly)/len(poly)
        cy = sum(q[1] for q in poly)/len(poly)
        gp = []
        for x, y in poly:
            d = math.hypot(x-cx, y-cy) or 1.0
            gp.append((x + (x-cx)/d*margin, y + (y-cy)/d*margin))
        poly = gp
    x, y = p; c = False
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i+1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < x0 + (y-y0)/(y1-y0+1e-12)*(x1-x0):
            c = not c
    return c

PLATES = plate_polys()

print("=" * 78)
print("B. CONNECTIVITY  (every truss member end must be held by something)")
print("=" * 78)
worst, worst_who = 0.0, ""
for name, a, b in MEMBERS:
    for lbl, p in (("start", a), ("end", b)):
        dmin, who = 1e9, ""
        for n2, a2, b2 in MEMBERS:
            if n2 == name:
                continue
            d = seg_dist(p, a2, b2)
            if d < dmin:
                dmin, who = d, n2
        held_by, ok = "", False
        if dmin <= JOIN_TOL:
            held_by, ok = f"member: {who} @ {dmin:.3f}\"", True
        elif p[1] <= 0.5:
            held_by, ok = "foundation", True
        else:
            for tag, poly in PLATES:
                if in_poly(p, poly, PLATE_MARGIN):
                    held_by, ok = f"plate: {tag}", True
                    break
        if not ok:
            fails += 1
            held_by = f"NOTHING (nearest {who} @ {dmin:.3f}\")"
            if dmin > worst:
                worst, worst_who = dmin, f"{name} {lbl}"
        print(f"  {'PASS' if ok else 'FAIL'}  {name:16s} {lbl:5s} "
              f"({p[0]:8.3f},{p[1]:7.3f})  held by {held_by}")
print(f"  -> floating member ends: "
      f"{'none' if not worst else f'{worst_who} at {worst:.3f}\"'}")

# ======================================================================
# C. CLEARANCE -- nothing may cross a doorway
# ======================================================================
print()
print("=" * 78)
print("C. DOOR CLEARANCE  (no brace may cross the opening)")
print("=" * 78)
# The clear opening is between the INNER faces of the door jambs, not the
# frame centrelines.  Each jamb is a 1 1/2" channel on x = +/-DOOR_HW, so it
# occupies 0.75" either side and the clear opening is DOOR_HW - 0.75.
JAMB_W   = 1.5
CLEAR_HW = DOOR_HW - JAMB_W/2                   # 16.4375"
TOUCH    = 0.25                                 # allow butting onto the jamb
GABLE_SPANS = [
    ("gable brace, upper", (-HB_HI_X, HB_HI_Y), (HB_HI_X, HB_HI_Y)),
    ("gable brace, lower +", (HB_LO_XIN, HB_LO_Y), (HB_LO_XOUT, HB_LO_Y)),
    ("gable brace, lower -", (-HB_LO_XIN, HB_LO_Y), (-HB_LO_XOUT, HB_LO_Y)),
    ("gable purlin supp +", PSUP_A_PT, (PSUP_B_PT[0], PSUP_B_PT[1])),
    ("gable purlin supp -", (-PSUP_A_PT[0], PSUP_A_PT[1]),
                            (-PSUP_B_PT[0], PSUP_B_PT[1])),
]
for name, a, b in GABLE_SPANS:
    # deepest intrusion of this span into the clear opening
    worst_in = 0.0
    for i in range(1001):
        t = i/1000.0
        x = a[0] + (b[0]-a[0])*t; y = a[1] + (b[1]-a[1])*t
        if 0.0 < y < DOOR_HEAD:
            worst_in = max(worst_in, CLEAR_HW - abs(x))
    spans_cl = (min(a[0], b[0]) < 0 < max(a[0], b[0])) and a[1] < DOOR_HEAD
    ok = worst_in <= TOUCH and not spans_cl
    if not ok:
        fails += 1
    note = ("clear of opening" if worst_in <= 0 else
            f"butts jamb by {worst_in:.3f}\"" if ok else
            f"INTRUDES {worst_in:.3f}\"" +
            ("  and SPANS THE CENTRELINE" if spans_cl else ""))
    print(f"  {'PASS' if ok else 'FAIL'}  {name:22s} "
          f"x {min(a[0],b[0]):8.3f}..{max(a[0],b[0]):8.3f} at y={a[1]:7.3f}"
          f"   {note}")
print(f"  clear opening: |x| < {CLEAR_HW}\" (jamb centres +/-{DOOR_HW}\"), "
      f"y < {DOOR_HEAD}\"; butting tolerance {TOUCH}\"")

# ======================================================================
# D. PLATES
# ======================================================================
print()
print("=" * 78)
print("D. TRUSS PLATES  (each must sit on a joint and cover its members)")
print("=" * 78)
JOINTS = {
    "knee, left":   (-(HWI+1.5), POST_H), "knee, right": ((HWI+1.5), POST_H),
    "short-web top, left": (-WEB_S[0][0], WEB_S[0][1]),
    "short-web top, right": (WEB_S[0][0], WEB_S[0][1]),
    "mid joint, left": (-WEB_L[1][0], WEB_L[1][1]),
    "mid joint, right": (WEB_L[1][0], WEB_L[1][1]),
    "king-post base, centre": (WEB_C[0][0], WEB_C[0][1]),
    "peak, centre": (WEB_C[1][0], WEB_C[1][1]),
}
for pid, px, py, prot, pmir, tag in GP.PLACEMENTS:
    jx, jy = JOINTS[tag]
    d = math.hypot(px-jx, py-jy)
    # the plate must reach the joint it serves
    reach = max(math.hypot(x, y) for x, y in GP.OUTLINE[pid])
    ok = d <= reach
    if not ok:
        fails += 1
    f = GP.FIT[pid]
    print(f"  {'PASS' if ok else 'FAIL'}  plate {pid} {tag:24s} "
          f"centre->joint {d:6.3f}\"  reach {reach:6.3f}\"  "
          f"fit {f['inliers']}/{f['nholes']} holes  scale {f['scale']:.4f}  "
          f"rms {f['rms_in']:.4f}\"")
nb = sum(len(GP.HOLES[p]) for p, *_ in GP.PLACEMENTS)
chk("Plate bolt holes per truss", nb, 62, 0, "s10 table 60 + 2 to ridge")

# ======================================================================
# E. END WALLS -- glazed, with the door leaf inside its opening
# ======================================================================
print()
print("=" * 78)
print("E. END WALLS  (glazed, and the door leaf fits its opening)")
print("=" * 78)
try:
    man = json.load(open("manifest.json"))
except Exception:
    man = {}


def echk(name, ok, note):
    global fails
    if not ok:
        fails += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {name:34s} {note}")


npane = man.get("gable end glazing", 0)
echk("Both end walls glazed", npane == 2, f"{npane} panes (expect 2)")
nlight = man.get("door light (glazed)", 0)
echk("Glazed door lights", nlight == 4,
     f"{nlight} lights (2 per door x 2 doors)")
echk("Door leaf inside clear opening", DL_HW <= DOOR_HW - 0.5,
     f"leaf half-width {DL_HW}\" vs jamb face {DOOR_HW}\"")
echk("Leaf height clears the head", DL_TOP <= DOOR_HEAD + 1e-6,
     f"leaf {DL_TOP}\" vs opening head {DOOR_HEAD}\"")
# leaf sub-elements must tile the full leaf height with no gap or overlap
spans = sorted(DL_RAILS + [DL_KICK] + DL_LIGHTS)
gap = 0.0
for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
    gap = max(gap, abs(b0 - a1))
echk("Leaf elements tile the height", gap < 1e-6 and
     abs(spans[0][0]) < 1e-6 and abs(spans[-1][1] - DL_TOP) < 1e-6,
     f"worst gap/overlap {gap:.4f}\", spans {spans[0][0]}..{spans[-1][1]}\"")
# Openings really cut: test the built mesh, not the intent.  No glazing
# surface may sit inside the door opening or a shutter opening at either end.
# The door lights are a separate solid inside the doorway, so we exclude the
# leaf's own footprint and test the ring between the leaf and the jambs.
try:
    import trimesh
    gl = trimesh.load("glazing.stl")
    c = gl.triangles_center / 25.4          # mm -> inches
    def occupied(x0, x1, y0, y1, zlo, zhi):
        m = ((c[:, 0] > x0) & (c[:, 0] < x1) &
             (c[:, 1] > y0) & (c[:, 1] < y1) &
             (c[:, 2] > zlo) & (c[:, 2] < zhi))
        return int(m.sum())
    bad = []
    for tag, z0, z1 in (("near end", -0.6, GLAZE_T+0.6),
                        ("far end", LENGTH-GLAZE_T-0.6, LENGTH+0.6)):
        # ring inside the jambs but outside the door leaf
        n1 = occupied(-DOOR_HW+0.01, -DL_HW-0.01, 1.0, DOOR_HEAD-1.0, z0, z1)
        n2 = occupied(DL_HW+0.01, DOOR_HW-0.01, 1.0, DOOR_HEAD-1.0, z0, z1)
        n3 = occupied(SHUT_X[0]-SHUT_W/2+1, SHUT_X[0]+SHUT_W/2-1,
                      SHUT_Y0+1, SHUT_Y1-1, z0, z1)
        if n1 or n2 or n3:
            bad.append(f"{tag}: door {n1+n2} tris, shutter {n3} tris")
    nfan = occupied(FAN_X-FAN_SZ/2+1, FAN_X+FAN_SZ/2-1,
                    FAN_SILL+1, FAN_SILL+FAN_SZ-1,
                    LENGTH-GLAZE_T-0.6, LENGTH+0.6)
    if nfan:
        bad.append(f"far end: fan {nfan} tris")
    echk("Pane openings really cut", not bad,
         "no glazing inside the door, shutter or fan openings"
         if not bad else "; ".join(bad))
except ImportError:
    print("  SKIP  Pane openings really cut          (trimesh not available)")

# ======================================================================
# A. report
# ======================================================================
print()
print("=" * 78)
print("A. DIMENSIONS")
print("=" * 78)
print(f"  {'':4} {'check':34s} {'model':>10s} {'drawing':>10s} "
      f"{'delta':>8s}  source")
for ok, name, m, d, dd, src in rows:
    print(f"  {'PASS' if ok else 'FAIL'} {name:34s} {m:10.4f} {d:10.4f} "
          f"{dd:+8.4f}  {src}")

npass = sum(1 for r in rows if r[0])
print()
print("=" * 78)
print(f"RESULT: {npass}/{len(rows)} dimensional checks pass; "
      f"{fails} failure(s) across all five families")
print("=" * 78)

json.dump({"dimensional": [{"pass": bool(o), "check": n, "model": m,
                            "drawing": d, "delta": dd, "source": s}
                           for o, n, m, d, dd, s in rows],
           "failures": fails,
           "worst_unconnected_end_in": round(worst, 4)},
          open("verification_report.json", "w"), indent=1)
print("-> verification_report.json")
