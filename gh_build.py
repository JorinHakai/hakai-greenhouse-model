"""Greenhouse digital twin - assembly and export.

Writes greenhouse.step (millimetres, solid B-rep, the master model),
greenhouse.glb (metres, for web/Blender/Unity) and frame/glazing STLs.

    python gh_build.py            # full model, bolt holes drilled
    python gh_build.py --noholes  # skip drilling (much faster)
"""
import math, sys, json
import cadquery as cq
from gh_geometry import *
import gh_plates as GP

DRILL = "--noholes" not in sys.argv

frame, glass, MAN = [], [], {}          # MAN = manifest (counts by member type)

def add(sol, tag, n=1):
    if sol is None:
        return
    frame.append(sol)
    MAN[tag] = MAN.get(tag, 0) + n


def addg(sol, tag, n=1):
    """Add to the glazing group, which renders transparent."""
    if sol is None:
        return
    glass.append(sol)
    MAN[tag] = MAN.get(tag, 0) + n

# ---------------------------------------------------------------- ribs
rib_master = rib(P_GBAR[2][1], 0.0)
for z in RIB_Z:
    add(rib_master.translate((0, 0, z*IN)), "glazing bar rib (transverse)")

# ---------------------------------------------------------------- truss
# Face of the truss that the plates bolt to.  The 2"-deep webs and bottom
# chord present a face at z + 1.0; the plates sit flat on it.
PLATE_FACE = 1.0

def build_truss(z):
    out = []
    # top chords 2x3x3/16 angle, 127 5/16", outer face on the roof line
    for sx in (1, -1):
        p1 = (sx*TC_A[0], TC_A[1]); p2 = (sx*TC_B[0], TC_B[1])
        out.append((transverse(P_TOPCHORD, p1, p2, z, flip=(sx < 0)),
                    "truss top chord (2x3x3/16 L)"))
    # truss posts 1 1/2x3x3/16 channel; 3" web spans interior->exterior face
    for sx in (1, -1):
        ax = sx*(HWI + 1.5)
        out.append((transverse(P_POST, (ax, 0.0), (ax, POST_H), z,
                               rot=90, flip=(sx < 0)),
                    "truss post (1.5x3x3/16 C)"))
        # post cleats: one at the base, one at 36" for the side wall
        for cy, tag in ((1.5, "post cleat, base (2x3x3/16 L)"),
                        (36.0, "post cleat, side wall (2x3x3/16 L)")):
            out.append((transverse(P_CLEAT, (sx*(HWI - 1.0), cy),
                                   (sx*(HWI + 1.5), cy), z, flip=(sx < 0)), tag))
    # bottom chords 2x2x3/16 angle, 120 3/8"
    for sx in (1, -1):
        out.append((transverse(P_BOTCHORD, (sx*BC_A[0], BC_A[1]),
                               (sx*BC_B[0], BC_B[1]), z),
                    "truss bottom chord (2x2x3/16 L)"))
    # centre web 26 3/16" on the centreline
    out.append((transverse(P_WEB, WEB_C[0], WEB_C[1], z),
                "truss centre web (2x2x3/16 L)"))
    # long web 59 11/16" + short web 13 13/16", one pair per half
    for sx in (1, -1):
        a, b = WEB_L
        out.append((transverse(P_WEB, (sx*a[0], a[1]), (sx*b[0], b[1]), z),
                    "truss long web (2x2x3/16 L)"))
        a, b = WEB_S
        out.append((transverse(P_WEB, (sx*a[0], a[1]), (sx*b[0], b[1]), z),
                    "truss short web (2x2x3/16 L)"))
    # the eight 3/16" plates
    for pid, px, py, prot, pmir, tag in GP.PLACEMENTS:
        pl = plate(GP.OUTLINE[pid], px, py, z + PLATE_FACE,
                   rot_deg=prot, mirror=pmir, zdir=+1)
        if DRILL:
            for hx, hy in GP.HOLES[pid]:
                c, s = math.cos(math.radians(prot)), math.sin(math.radians(prot))
                ux = -hx if pmir else hx
                dx = ux*c - hy*s; dy = ux*s + hy*c
                pl = pl.cut(cq.Workplane("XY")
                            .circle(GP.BOLT_DIA/2*IN)
                            .extrude(3*PLATE_T*IN)
                            .translate(((px+dx)*IN, (py+dy)*IN,
                                        (z + PLATE_FACE - PLATE_T)*IN)))
        out.append((pl, f"truss plate 3/16 ({tag.split(',')[0]})"))
    return out

for z in TRUSS_Z:
    for s, t in build_truss(z):
        add(s, t)

# ------------------------------------------------- longitudinal members
Z0, Z1 = 0.0, LENGTH
add(longitudinal(P_PURLIN, -0.75, RIDGE_TOP-3.0, Z0, Z1), "ridge (1.5x3x3/16 C)")
for s in PURLIN_S:
    px, py = purlin_pt(s)
    for sx in (1, -1):
        add(longitudinal(P_PURLIN, sx*px-0.75, py-1.5, Z0, Z1),
            "roof purlin (1.5x3x3/16 C)")
for h in SIDE_RUN_H:                       # braces on the eave curve
    dx = math.sqrt(max(EAVE_R**2 - (h-ARC_C[1])**2, 0)) + ARC_C[0]
    for sx in (1, -1):
        add(longitudinal(P_SBRACE, sx*dx-1.0, h-0.5, Z0, Z1),
            "side-wall horiz brace (1x3/4 L)")
for sx in (1, -1):                         # stringer at bottom-chord level
    f  = STRINGER_S / BC_LEN
    bx = BC_A[0] + (BC_B[0]-BC_A[0])*f
    by = BC_A[1] + (BC_B[1]-BC_A[1])*f
    add(longitudinal(P_STRINGER, sx*bx-1.0, by-2.0, Z0, Z1), "stringer (2x2 L)")
    add(long_face(P_BASE, sx*HW, sx, 0.0, Z0, Z1), "side base (1x2 L)")

# ------------------------------------------------------------ gable end
def gable(z, zdir, fans=False):
    out = []
    T = lambda *a, **k: transverse(*a, zdir=zdir, **k)
    out.append((rib(P_GBAR[2][1], z, zdir), "gable end rib"))
    for x in GABLE_X:                                    # mullions / gable posts
        for sx in (1, -1):
            is_post = abs(x - GABLE_POST_X) < 1e-6
            prof = P_POST if is_post else P_GBAR
            top  = GABLE_POST_TOP if is_post else gable_top(x)
            out.append((T(prof, (sx*x, 0.0), (sx*x, top), z),
                        "gable post (1.5x3x3/16 C)" if is_post else "gable mullion"))
    for sx in (1, -1):                                   # door jambs
        out.append((T(P_POST, (sx*DOOR_HW, 0.0), (sx*DOOR_HW, DOOR_TOP), z),
                    "door jamb"))
    out.append((T(P_POST, (-DOOR_HW, DOOR_HEAD), (DOOR_HW, DOOR_HEAD), z),
                "door head"))
    # The door leaf's own stiles and rails replace what used to be a single
    # full-frame-width "door mid rail" at half the opening height; sheet 2
    # puts the mid rail at 46.000-47.013" and only across the leaf.
    dfr, dgl = door_leaf(z, zdir)
    out += dfr
    # upper horizontal brace: ONE member, 148 1/2", clears the door head
    out.append((T(P_HBRACE, (-HB_HI_X, HB_HI_Y), (HB_HI_X, HB_HI_Y), z),
                "gable horiz brace, upper (1x2x1/8 C)"))
    # lower horizontal braces: TWO members, 104 13/16" each, stopping at the
    # door jambs.  They do NOT run across the doorway.
    for sx in (1, -1):
        out.append((T(P_HBRACE, (sx*HB_LO_XIN, HB_LO_Y), (sx*HB_LO_XOUT, HB_LO_Y), z),
                    "gable horiz brace, lower (1x2x1/8 C)"))
    # gable purlin support: 107 3/8" of 2x2x3/16 angle up each rake
    for sx in (1, -1):
        out.append((T(P_PSUP, (sx*PSUP_A_PT[0], PSUP_A_PT[1]),
                      (sx*PSUP_B_PT[0], PSUP_B_PT[1]), z),
                    "gable purlin support (2x2x3/16 L)"))
    out.append((T(P_BASE_T, (-HWT, 0.5), (HWT, 0.5), z), "front base (1x2 L)"))
    for cx in SHUT_X:                                    # intake shutters
        for sx in (1, -1):
            out += shutter(sx*cx, z, zdir)
    return out

def shutter(cx, z, zdir=0):
    out = []; w, h = SHUT_W, SHUT_Y1 - SHUT_Y0
    yc = (SHUT_Y0 + SHUT_Y1)/2
    ring = (cq.Workplane("XY").box(w*IN, h*IN, 1.5*IN)
            .cut(cq.Workplane("XY").box((w-2)*IN, (h-2)*IN, 3*IN)))
    out.append((ring.translate((cx*IN, yc*IN, (z + zdir*0.75)*IN)),
                "intake shutter frame"))
    for i in range(4):
        yy = SHUT_Y0 + 3.4 + i*4.75
        sl = (cq.Workplane("XY").box((w-2.2)*IN, 0.9*IN, 1.0*IN)
              .rotate((0, 0, 0), (1, 0, 0), 22)
              .translate((cx*IN, yy*IN, (z + zdir*0.75)*IN)))
        out.append((sl, "intake shutter louvre"))
    return out

for s, t in gable(0.0, +1):
    add(s, t)
for s, t in gable(LENGTH, -1, True):
    add(s, t)

# ------------------------------------------------- end-wall glazing
# The end walls were unglazed: the roof/side skin is a tube extruded along
# the length and open at both ends, so each gable was a bare frame.
for z, zdir, fans in ((0.0, +1, False), (LENGTH, -1, True)):
    pane = gable_pane(z, zdir)
    if fans:
        pane = fan_cut(pane, z, zdir)
    addg(pane, "gable end glazing")
    _, dgl = door_leaf(z, zdir)
    for s, t in dgl:
        addg(s, t)

# ----------------------------------------------------------- roof vents
def roof_vent(zc, sx):
    x0, x1 = 0.0, VENT_RUN
    y0, y1 = RIDGE_TOP, RIDGE_TOP - VENT_RUN*TAN
    span = math.hypot(x1-x0, y1-y0)
    ring = (cq.Workplane("XY").box(span*IN, 1.6*IN, VENT_L*IN)
            .cut(cq.Workplane("XY").box((span-3)*IN, 3*IN, (VENT_L-3)*IN)))
    ring = ring.rotate((0, 0, 0), (0, 0, 1), -PITCH*sx)
    mx = sx*(x0+x1)/2; my = (y0+y1)/2 - 0.8/COS
    return ring.translate((mx*IN, my*IN, zc*IN))

for zc in VENT_Z:
    for sx in (1, -1):
        add(roof_vent(zc, sx), "roof vent sash")

# ----------------------------------------------------------- side vents
for zc in SIDEVENT_Z:
    for sx in (1, -1):
        h = SV_Y1 - SV_Y0
        rgn = (cq.Workplane("XY").box(1.6*IN, h*IN, SV_W*IN)
               .cut(cq.Workplane("XY").box(3*IN, (h-3)*IN, (SV_W-3)*IN)))
        add(rgn.translate((sx*(HW-0.8)*IN, (SV_Y0+SV_Y1)/2*IN, zc*IN)),
            "side vent frame")

# --------------------------------------------------------- glazing skin
SK = 0.40
skin = env_profile(0.0).extrude(LENGTH*IN).cut(env_profile(SK).extrude(LENGTH*IN))
skin = skin.cut(cq.Workplane("XY").box(OVERALL_W*1.2*IN, 3*IN, LENGTH*1.2*IN)
                .translate((0, 0, LENGTH/2*IN)))
# The door and fan openings used to be cut here.  They were no-ops: this
# skin is the envelope extruded along the length, so at the door's x range
# (|x| < 17.19") the only surface is roof at y > 119", far above the
# 76"-tall cutter, and the side walls sit out at |x| = 123.125".  Both
# openings belong in the end-wall panes, which is where they are now cut.
for zc in SIDEVENT_Z:                                            # side vents
    for sx in (1, -1):
        skin = skin.cut(cq.Workplane("XY").box(4*IN, (SV_Y1-SV_Y0)*IN, SV_W*IN)
                        .translate((sx*HW*IN, (SV_Y0+SV_Y1)/2*IN, zc*IN)))
glass.append(skin)

# ----------------------------------------------------------------- save
fc = cq.Compound.makeCompound([s.val() if hasattr(s, "val") else s for s in frame])
gc = cq.Compound.makeCompound([s.val() if hasattr(s, "val") else s for s in glass])
a = cq.Assembly()
a.add(fc, name="frame",   color=cq.Color(0.20, 0.22, 0.25, 1))
a.add(gc, name="glazing", color=cq.Color(0.62, 0.80, 0.92, 0.25))
def fix_glb_up(path):
    """Drop cadquery's Z-up -> Y-up root rotation from a GLB.

    cadquery assumes its models are authored Z-up and writes a -90 deg
    rotation about X on the root node to satisfy glTF's Y-up convention.
    This model is authored Y-up already (y is height throughout
    gh_geometry.py), so that rotation lays the building on its end: the
    615" length ends up vertical.  It is wrong in every consumer, not just
    our viewer -- Blender, Sketchfab and Unity all honour the node
    transform -- so the fix belongs in the file.

    Vertex data is already x=width, y=height, z=length, which is exactly
    what glTF wants, so the correct root rotation is identity.
    """
    import struct
    raw = open(path, "rb").read()
    if raw[:4] != b"glTF":
        raise ValueError(f"{path} is not a binary glTF")
    ver, total = struct.unpack("<II", raw[4:12])
    off, chunks = 12, []
    while off < len(raw):
        clen, ctype = struct.unpack("<II", raw[off:off+8])
        chunks.append((ctype, raw[off+8:off+8+clen]))
        off += 8 + clen
    jtype, jdata = chunks[0]
    gj = json.loads(jdata)
    changed = 0
    for n in gj.get("nodes", []):
        r = n.get("rotation")
        # the Z-up conversion is exactly (-sqrt(2)/2, 0, 0, sqrt(2)/2)
        if r and abs(r[0] + 0.7071067811865475) < 1e-6 and \
           abs(r[1]) < 1e-9 and abs(r[2]) < 1e-9 and \
           abs(r[3] - 0.7071067811865475) < 1e-6:
            del n["rotation"]
            changed += 1
    if not changed:
        return 0
    nj = json.dumps(gj, separators=(",", ":")).encode("utf-8")
    nj += b" " * (-len(nj) % 4)                      # JSON pads with spaces
    out = [struct.pack("<II", len(nj), jtype) + nj]
    for ctype, cdata in chunks[1:]:
        pad = b"\x00" * (-len(cdata) % 4)            # BIN pads with zeros
        out.append(struct.pack("<II", len(cdata) + len(pad), ctype) + cdata + pad)
    body = b"".join(out)
    with open(path, "wb") as f:
        f.write(b"glTF" + struct.pack("<II", ver, 12 + len(body)) + body)
    return changed


a.save("greenhouse.step")
a.save("greenhouse.glb", exportType="GLTF")
n = fix_glb_up("greenhouse.glb")
print(f"greenhouse.glb: removed {n} spurious Z-up root rotation(s)")
cq.exporters.export(fc, "frame.stl")
cq.exporters.export(gc, "glazing.stl")
if not DRILL:
    # Undrilled GLB for the web viewer: the 3/8" holes are invisible at
    # viewing scale but triple the triangle count.
    import shutil
    shutil.copyfile("greenhouse.glb", "greenhouse_web.glb")
    print("wrote greenhouse_web.glb (undrilled, for the viewer)")

print("\n--- MEMBER MANIFEST ---")
for k in sorted(MAN):
    print(f"  {MAN[k]:4d}  {k}")
print(f"  {len(frame):4d}  frame solids")
print(f"  {len(glass):4d}  glazing solids")
print(f"  {len(frame)+len(glass):4d}  TOTAL")
json.dump(MAN, open("manifest.json", "w"), indent=1)
print("\nwrote greenhouse.step, greenhouse.glb, frame.stl, glazing.stl, manifest.json")
