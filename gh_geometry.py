"""
GREENHOUSE DIGITAL TWIN - geometry and section profiles  (v4)
=============================================================
Curved-eave gable greenhouse, 20'-6 1/4" x 51'-3 1/4", 10'-2 7/8" to ridge.
Built from the supplied 10-sheet vector CAD set (10 sheets, 3/8" = 1'-0").

Everything below was measured programmatically off the CAD linework rather
than estimated by eye.  Scale is exactly 2.25 pt/inch; dimension lines carry
a constant 8.96 pt arrowhead inset, confirmed across three independent spans.
Geometry linework (not dimension lines) measures true at 2.25 pt/inch.

Datum:  x = 0 building centreline (width),  +x toward one side wall
        y = 0 top of foundation / floor slab,  +y up
        z = 0 at one gable end,  +z along the length
Units:  source dimensions in INCHES; the STEP export carries MILLIMETRES.

--------------------------------------------------------------------------
v4 corrections (see gh_verify.py for the checks that back these up)
--------------------------------------------------------------------------
1. Removed three fabricated "purlin support" members per half-truss.  They
   were digitised from stray linework and floated up to 16" clear of any
   member they were supposed to connect to.  The drawings punch the purlins
   straight through the top chord ("PUNCH FOR PURLIN (3/8")"), so no such
   member exists: 24 solids deleted.
2. Added the 13 13/16" short web, 2 per truss, which was missing entirely.
   Each truss half is top chord + bottom chord + long web + short web, with
   one centre web on the centreline: 5 webs per truss, not 3.
3. Split the lower gable horizontal brace.  It was one full-width member
   running straight through the doorway.  The drawings show TWO braces of
   104 13/16" each, stopping either side of the door opening.
4. Added the 8 truss plates per truss with their true 3/16" thickness,
   outlines and positions (see gh_plates.py).
5. Added the gable purlin support, 107 3/8" of 2x2x3/16 angle up each rake,
   which the gable bracing sheets call for and the model omitted.
6. Corrected the upper gable brace section: 1x2x1/8 channel, not 2x2 angle.
7. Purlin positions left UNCHANGED.  The truss sheet's "PUNCH FOR PURLIN"
   stations (42 3/4" / 86 1/4") are measured from a different origin than
   the top-chord apex; the side-wall elevation independently puts the purlin
   bands at 98.09-101.42" and 80.97-84.33", which the existing centres
   reproduce to 0.035".  Anchored to the elevation, not the punch dimension.
"""
import math
import cadquery as cq

IN = 25.4

# ======================================================================
# 1. PRIMARY DIMENSIONS   (src = sheet the value was read from)
# ======================================================================
OVERALL_W   = 246.25    # 20'-6 1/4"  overall width          [s1,s10 dim]
EXT_TRUSS_W = 242.25    # 20'-2 1/4"  exterior truss width   [s10 dim]
INT_TRUSS_W = 236.25    # 19'-8 1/4"  interior truss width   [s10 dim]
LENGTH      = 615.25    # 615 1/4"    side base / overall    [s7,s8 dim]
RIDGE_TOP   = 122.875   # 10'-2 7/8"  top of ridge           [s1,s7 dim]
PITCH       = 23.1      # degrees                            [s3,s10 dim]
BEND_H      = 52.00     # eave bend point                    [s7 geom 52.09]
POST_H      = 52.4375   # 52 7/16" truss post                [s10 dim]
ROOF_STRUCT = 119.80    # roof outer bar top @ x=0           [s1,s7,s10 geom]

HW  = OVERALL_W / 2     # 123.125  glazing outer face
HWT = EXT_TRUSS_W / 2   # 121.125  truss outer face
HWI = INT_TRUSS_W / 2   # 118.125  truss inner face
TAN = math.tan(math.radians(PITCH))
COS = math.cos(math.radians(PITCH))
SIN = math.sin(math.radians(PITCH))

# --- eave arc, solved by tangency (vertical @ HW, rafter through ridge) ---
EAVE_R = (RIDGE_TOP - BEND_H - TAN * HW) / (math.hypot(TAN, 1) - TAN)
ARC_C  = (HW - EAVE_R, BEND_H)
_n     = (TAN / math.hypot(TAN, 1), 1 / math.hypot(TAN, 1))
EAVE_T = (ARC_C[0] + EAVE_R * _n[0], ARC_C[1] + EAVE_R * _n[1])   # rafter tangent

# ======================================================================
# 2. TRUSS INTERNAL GEOMETRY          [sheet 10, measured off linework]
# ======================================================================
# Right half; the left half is mirrored in x.  Points are on the member
# lines as drawn (top chord point pair is its OUTER face).
TC_A   = (0.013, 115.200)      # top chord, peak end        127 5/16" SQ-LP
TC_B   = (117.053,  65.147)    # top chord, knee end
BC_A   = (0.413,  85.307)      # bottom chord, centre end   120 3/8" SQ-SQ
BC_B   = (118.280,  60.800)    # bottom chord, knee end
WEB_C  = ((0.0, 85.307), (0.0, 111.493))          # centre web  26 3/16"
WEB_L  = ((1.107, 109.520), (49.960, 75.200))     # long web    59 11/16"
WEB_S  = ((57.720, 87.253), (52.333, 74.507))     # short web   13 13/16"

TC_LEN   = 127.3125    # 127 5/16"   [s10 dim]
BC_LEN   = 120.375     # 120 3/8"    [s10 dim]
WEBC_LEN =  26.1875    # 26 3/16"    [s10 dim]
WEBL_LEN =  59.6875    # 59 11/16"   [s10 dim]
WEBS_LEN =  13.8125    # 13 13/16"   [s10 dim]
STRINGER_S = 70.125    # 70 1/8" along the bottom chord, DRILLED FOR STRINGER

# ======================================================================
# 3. GABLE ENDS                       [sheets 3 & 6, identical bracing]
# ======================================================================
GABLE_X    = [24.5, 49.0, 73.5, 98.0, 121.125]   # vertical stations [s2 chain]
GABLE_POST_X = 49.0        # gable posts at +/-49" (98" centre to centre)
GABLE_POST_TOP = 94.374    # 94 3/8" top of gable post (SQ-LP)   [s3 dim]
DOOR_HW    = 17.1875       # 34 3/8" door frame, jamb outer face [s1,s2 dim]
DOOR_HEAD  = 76.187        # clear opening head                  [s2 geom]
DOOR_TOP   = 77.200        # frame top / jamb top                [s2 geom]

# --- door leaf, measured off the sheet-2 frame elevation ---------------
# The leaf is a single glazed door: 2" stiles and top/bottom rails, a solid
# kick panel at the foot (hatched on the drawing -- diagonals, which is the
# solid-material hatch, not the dots-and-triangles concrete hatch used on
# the foundation), then two equal glazed lights split by a thin mid rail.
DL_HW      = 16.187       # leaf half width = clear opening      [s2 geom]
DL_TOP     = 76.187       # leaf height                          [s2 geom]
DL_STILE   = 2.0          # stile width, 17.187 -> 14.187         [s2 geom]
DL_T       = 1.50         # leaf thickness
DL_GLASS_T = 0.40         # light thickness
DL_KICK    = (2.000, 14.827)       # solid panel                 [s2 geom]
DL_RAILS   = [(0.000,  2.000),     # bottom rail
              (14.827, 18.827),    # rail over the kick panel
              (46.000, 47.013),    # mid rail
              (74.187, 76.187)]    # top rail
DL_LIGHTS  = [(18.827, 46.000),    # lower light, 27.173" tall
              (47.013, 74.187)]    # upper light, 27.174" tall
GLAZE_T    = 0.40         # glazing thickness, as the roof/side skin
BASE_CLEAR = 1.00         # gable glazing stops clear of the front base

# gable vertical tops lie on this line (least squares of the four s2 heights
# 108 1/8 / 97 5/8 / 87 3/16 / 76 11/16 at x = 24.5 / 49 / 73.5 / 98)
GT_A, GT_B = 118.604, 0.427721
def gable_top(x): return GT_A - GT_B * abs(x)

# --- horizontal braces, both 1" x 2" x 1/8" channel  [s3 "Bracing Materials"]
# Upper brace: ONE member, 148 1/2" (3/4 + 6 x 24 1/2 + 3/4), spans +/-74.25".
HB_HI_Y   = 80.007        # centreline height   [s3 dim 80", faces 79.5-80.5]
HB_HI_X   = 74.253        # half span           [s3 geom]
HB_HI_LEN = 148.5         # 148 1/2"            [s3 dim]
# Lower braces: TWO members, 104 13/16" each, stopping clear of the doorway.
# Outer end 121.133", inner end 16.320" -- the door frame is at 17.1875", so
# the braces bolt to the door jambs and do NOT cross the opening.
HB_LO_Y     = 38.007      # centreline height   [s3 dim 38", faces 37.5-38.5]
HB_LO_XOUT  = 121.133     # outer end           [s3 geom]
HB_LO_XIN   = 16.320      # inner end           [s3 geom, mean of +/-16.307/16.333]
HB_LO_LEN   = 104.8125    # 104 13/16"          [s3 dim]

# --- gable purlin support: 107 3/8" of 2x2x3/16 angle up each rake  [s3]
PSUP_A_PT = (0.013, 115.200)     # peak end (on the rake line)
PSUP_B_PT = (98.760,  72.987)    # lower end
PSUP_LEN  = 107.375              # 107 3/8"   [s3 dim]

# --- intake shutters (4 per gable end) ---
SHUT_X = [36.76, 85.75]
SHUT_W, SHUT_Y0, SHUT_Y1 = 22.0, 0.622, 24.489

# --- exhaust fan holes (one gable end)  20 7/8" sq, sill 54"   [s5 dim] ---
FAN_SZ, FAN_SILL, FAN_X = 20.875, 54.0, 61.25

# ======================================================================
# 4. LONGITUDINAL MEMBERS
# ======================================================================
# Purlin centres.  Slope distance from the ridge; cross-checked against the
# side-wall elevation bands 98.09-101.42" and 80.97-84.33" (agreement 0.035").
PURLIN_S = [43.9375, 87.4375]
PURLIN_D = 5.874                  # centreline drop below the glazing line
def purlin_pt(s):
    x = s * COS
    return (x, RIDGE_TOP - TAN * x - PURLIN_D)

SIDE_RUN_H = [73.845, 59.330]     # side-wall brace centre heights  [s7 geom]

TRUSS_Z = [125.375, 244.875, 370.375, 489.875]   # [s7 dim 125 3/8 + 119 1/2]
RIB_Z   = [1.375 + 24.5 * k for k in range(26)]  # 1 3/8 + 25 x 24 1/2 = 615 1/4
VENT_Z  = [74.9, 172.9, 270.9, 344.35, 442.35, 540.35]
VENT_L, VENT_RUN = 47.5, 19.75
SIDEVENT_Z = [185.15, 430.10]
SV_W, SV_Y0, SV_Y1 = 24.18, 6.55, 29.16

# ======================================================================
# 5. SECTION PROFILES  (true shapes from the Materials tables)
# ======================================================================
def L_angle(a, b, t):
    """L: leg a along +u, leg b along +v, thickness t."""
    return [(0, 0), (a, 0), (a, t), (t, t), (t, b), (0, b)]

def C_chan(d, f, t):
    """C: web depth d along +v, flanges f along +u, thickness t."""
    return [(0, 0), (f, 0), (f, t), (t, t), (t, d-t), (f, d-t), (f, d), (0, d)]

def rect(a, b): return [(0, 0), (a, 0), (a, b), (0, b)]

P_TOPCHORD = L_angle(2, 3, 3/16)      # 2x3x3/16 angle
P_BOTCHORD = L_angle(2, 2, 3/16)      # 2x2x3/16 angle
P_WEB      = L_angle(2, 2, 3/16)      # 2x2x3/16 angle
P_POST     = C_chan(3, 1.5, 3/16)     # 1 1/2x3x3/16 channel
P_PURLIN   = C_chan(3, 1.5, 3/16)     # 1 1/2x3x3/16 channel
P_PSUP     = L_angle(2, 2, 3/16)      # 2x2x3/16 angle  (gable purlin support)
P_HBRACE   = C_chan(2, 1.0, 1/8)      # 1x2x1/8 channel (both gable braces)
P_SBRACE   = L_angle(1, 0.75, 1/8)    # 1x3/4 angle     (side wall)
P_STRINGER = L_angle(2, 2, 3/16)      # 2x2 angle
P_CLEAT    = L_angle(2, 3, 3/16)      # 2x3x3/16 angle  (post cleats)
P_BASE     = L_angle(2, 1, 1/8)       # 1x2 angle (longitudinal: 2" horiz leg)
P_BASE_T   = L_angle(1, 2, 1/8)       # 1x2 angle (transverse: 1" vert leg)
P_GBAR     = rect(0.64, 1.40)         # glazing bar (measured 0.64 x ~1.4)
P_VENT     = rect(1.5, 1.6)

PLATE_T = 3/16                        # all truss plates: 3/16" aluminium

# ======================================================================
# 6. SOLID CONSTRUCTORS
# ======================================================================
def _wire(pts, plane, off=0.0):
    """Closed profile wire. `pts` are in INCHES and are scaled to mm here."""
    q = [(u*IN, v*IN) for u, v in pts]
    wp = cq.Workplane(plane).workplane(offset=off).moveTo(*q[0])
    for p in q[1:]:
        wp = wp.lineTo(*p)
    return wp.close()

def longitudinal(pts, x, y, z0, z1, rot=0):
    """Member running along Z. Profile in XY, origin placed at (x,y)."""
    s = _wire(pts, "XY").extrude((z1-z0)*IN)
    if rot:
        s = s.rotate((0, 0, 0), (0, 0, 1), rot)
    return s.translate((x*IN, y*IN, z0*IN))

def _prof(pts, rot=0, flip=False):
    """Orient a 2D profile: optional mirror about v, then rotation (degrees)."""
    if flip:
        pts = [(-u, v) for u, v in pts]
    if rot:
        c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        pts = [(u*c - v*sn, u*sn + v*c) for u, v in pts]
    return pts

def transverse(pts, p1, p2, z, rot=0, flip=False, zdir=0):
    """Member lying in the X-Y cross-section plane at station z.
       The profile is CENTRED on the member axis (in-plane), and in z is
       centred (zdir=0) or pushed fully to +z / -z of the station (zdir=+/-1).
    """
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return None
    q  = _prof(pts, rot, flip)
    us = [p[0] for p in q]; vs = [p[1] for p in q]
    uc = (min(us)+max(us))/2
    vc = (min(vs)+max(vs))/2; vd = max(vs)-min(vs)
    sol = _wire(q, "YZ").extrude(L*IN)
    sol = sol.translate((0, -uc*IN, (-vc + zdir*vd/2)*IN))
    sol = sol.rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(dy, dx)))
    return sol.translate((p1[0]*IN, p1[1]*IN, z*IN))

def long_face(pts, xface, sx, y, z0, z1):
    """Longitudinal member whose OUTER face sits at x=xface on side sx."""
    umax = max(p[0] for p in pts)
    x0 = xface - umax if sx > 0 else xface
    return longitudinal(pts, x0, y, z0, z1)

def plate(poly, x, y, z, rot_deg=0.0, mirror=False, t=PLATE_T, zdir=0):
    """A flat truss plate of thickness t, lying in the X-Y plane at station z.
       `poly` is a closed outline in inches about the plate's own centroid.
    """
    q = [(-u, v) for u, v in poly] if mirror else list(poly)
    if rot_deg:
        c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
        q = [(u*c - v*s, u*s + v*c) for u, v in q]
    sol = _wire(q, "XY").extrude(t*IN)
    return sol.translate((x*IN, y*IN, (z - t/2 + zdir*t/2)*IN))

# ======================================================================
# 7. ENVELOPE PROFILE (glazing outer surface)
# ======================================================================
def env_profile(off=0.0):
    """Closed cross-section wire, offset `off` inches inboard (>0 shrinks)."""
    hw = HW - off
    r  = EAVE_R - off
    cx, cy = ARC_C
    tx, ty = cx + r*_n[0], cy + r*_n[1]
    ridge_y = RIDGE_TOP - off/COS
    a0 = math.atan2(BEND_H-cy, hw-cx); a1 = math.atan2(ty-cy, tx-cx)
    am = (a0+a1)/2
    mx, my = cx + r*math.cos(am), cy + r*math.sin(am)
    wp = (cq.Workplane("XY").moveTo(0, ridge_y*IN)
          .lineTo(tx*IN, ty*IN)
          .threePointArc((mx*IN, my*IN), (hw*IN, BEND_H*IN))
          .lineTo(hw*IN, 0)
          .lineTo(-hw*IN, 0)
          .lineTo(-hw*IN, BEND_H*IN)
          .threePointArc((-mx*IN, my*IN), (-tx*IN, ty*IN))
          .close())
    return wp

def slab(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from inch bounds, in any order."""
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return (cq.Workplane("XY")
            .box((x1-x0)*IN, (y1-y0)*IN, (z1-z0)*IN)
            .translate(((x0+x1)/2*IN, (y0+y1)/2*IN, (z0+z1)/2*IN)))


def gable_pane(z, zdir):
    """Flat glazing pane filling one end wall, openings cut out.

    The end walls carry the same envelope cross-section as the roof and side
    walls, so the pane is env_profile extruded through the glazing thickness.
    Cut out: the door frame opening, the four intake shutters, and (far end
    only) the exhaust fan holes.
    """
    zo = z if zdir > 0 else z - GLAZE_T          # outward face at the end
    pane = env_profile(0.0).extrude(GLAZE_T*IN).translate((0, 0, zo*IN))
    T = 4*GLAZE_T                                 # cutter depth, generous
    zc0 = zo - GLAZE_T
    zc1 = zo + 2*GLAZE_T

    def cut(x0, x1, y0, y1):
        nonlocal pane
        pane = pane.cut(slab(x0, x1, y0, y1, zc0, zc1))

    cut(-HW*1.1, HW*1.1, -1.0, BASE_CLEAR)                   # clear the base
    cut(-DOOR_HW, DOOR_HW, -1.0, DOOR_TOP)                   # door opening
    for cx in SHUT_X:                                        # intake shutters
        for sx in (1, -1):
            cut(sx*cx - SHUT_W/2, sx*cx + SHUT_W/2, SHUT_Y0, SHUT_Y1)
    return pane


def fan_cut(pane, z, zdir):
    """Exhaust fan holes, one gable end only."""
    zo = z if zdir > 0 else z - GLAZE_T
    for sx in (1, -1):
        pane = pane.cut(slab(sx*FAN_X - FAN_SZ/2, sx*FAN_X + FAN_SZ/2,
                             FAN_SILL, FAN_SILL + FAN_SZ,
                             zo - GLAZE_T, zo + 2*GLAZE_T))
    return pane


def door_leaf(z, zdir):
    """One glazed door leaf.  Returns (frame_solids, glass_solids)."""
    z0 = z if zdir > 0 else z - DL_T
    z1 = z0 + DL_T
    gz0 = z0 + (DL_T - DL_GLASS_T)/2                 # lights centred in the leaf
    gz1 = gz0 + DL_GLASS_T
    fr, gl = [], []
    xi = DL_HW - DL_STILE                            # inner edge of the stiles
    for sx in (1, -1):                               # stiles, full height
        fr.append((slab(sx*xi, sx*DL_HW, 0.0, DL_TOP, z0, z1), "door stile"))
    for (ry0, ry1) in DL_RAILS:
        fr.append((slab(-xi, xi, ry0, ry1, z0, z1), "door rail"))
    fr.append((slab(-xi, xi, DL_KICK[0], DL_KICK[1],
                    z0 + 0.5, z0 + 1.0), "door kick panel"))
    for (ly0, ly1) in DL_LIGHTS:
        gl.append((slab(-xi, xi, ly0, ly1, gz0, gz1), "door light (glazed)"))
    return fr, gl


def rib(depth, z, zdir=0):
    """Transverse rib following the envelope, `depth` in from outer face."""
    o = env_profile(0.0).extrude(P_GBAR[1][0]*IN)
    i = env_profile(depth).extrude(P_GBAR[1][0]*IN)
    r = o.cut(i)
    r = r.cut(cq.Workplane("XY").box(OVERALL_W*1.2*IN, 2*IN, 4*IN)
              .translate((0, 0, P_GBAR[1][0]/2*IN)))     # trim at floor
    return r.translate((0, 0, (z - P_GBAR[1][0]/2*(1-zdir))*IN))


if __name__ == "__main__":
    print(f"eave arc  R={EAVE_R:.3f}in  centre={ARC_C[0]:.3f},{ARC_C[1]:.3f}  "
          f"rafter tangent=({EAVE_T[0]:.3f},{EAVE_T[1]:.3f})")
    print(f"purlin centres: "
          f"{[tuple(round(v,3) for v in purlin_pt(s)) for s in PURLIN_S]}")
    for tag, (a, b), n in (("centre web", WEB_C, WEBC_LEN),
                           ("long web",   WEB_L, WEBL_LEN),
                           ("short web",  WEB_S, WEBS_LEN)):
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        print(f"{tag:12s} modelled {L:8.4f}\"  drawing {n:8.4f}\"  "
              f"delta {L-n:+.4f}\"")
