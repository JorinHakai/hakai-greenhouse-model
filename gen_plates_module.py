"""Bake the extracted plate outlines + fitted placements into gh_plates.py.

Run this only if the extraction is re-done; gh_plates.py is the committed
artefact so that building the model never needs the source drawings.
"""
import json

plates = {p["id"]: p for p in json.load(open("truss_plates.json"))}
fit    = {f["plate"]: f for f in json.load(open("plate_placements.json"))}

# Joint assignment.  Eight joints per truss, eight plates.  The truss is
# symmetric, so RANSAC matched every side plate to whichever side it hit
# first; the opposite-hand instance is the same outline placed at -x.
#   (outline_id, x, y, rot_deg, mirror, joint name)
INSTANCES = [
    (0, -115.670,  57.400,   -0.04, False, "knee, left"),
    (7,  115.704,  57.397,    0.04, False, "knee, right"),
    (6,  -56.629,  87.366,   46.47, False, "short-web top, left"),
    (1,   56.641,  87.353,  -46.47, False, "short-web top, right"),
    (2,  -49.593,  75.947,    0.00, False, "mid joint, left"),
    (5,   49.613,  75.947,    0.00, False, "mid joint, right"),
    (3,   -0.027,  85.191,    0.00, True,  "king-post base, centre"),
    (4,   -0.018, 114.827,    0.00, True,  "peak, centre"),
]

L = []
L.append('"""Truss plate outlines and placements  (generated - do not hand-edit).')
L.append("")
L.append("Recovered from the CAD set's \"3/16\\\" TRUSS PLATES\" detail box by")
L.append("extract_plates.py, and located on the truss by place_plates.py, which")
L.append("matches each plate's 3/8\" bolt pattern to the same pattern drawn in")
L.append("place on the truss elevation.  Every plate fitted at scale 1.000 with")
L.append("RMS <= 0.02\", confirming the detail box is drawn at elevation scale.")
L.append("")
L.append("Bolt tally, which corroborates the whole extraction:")
L.append("    knee        2 x  9 = 18")
L.append("    trapezoid   2 x  4 =  8")
L.append("    square      2 x  7 = 14")
L.append("    king-post   1 x  8 =  8")
L.append("    peak        1 x 12 = 12   (+2 more to the ridge)")
L.append("                        ----")
L.append("                          60   = the fastener table's")
L.append("                                 'Plates: 3/8\" x 1 1/4\" Bolt & Nut (60)'")
L.append("")
L.append("OUTLINES are convex hulls of the drawn outline.  The drawn plates are")
L.append("convex except for a small notch at the apex of the peak plate, which")
L.append("the hull closes; that is the one place a plate is not shape-exact.")
L.append("")
L.append("Coordinates in INCHES, each outline about its own centroid.")
L.append('"""')
L.append("")
L.append("# outline_id -> closed polygon about the centroid")
L.append("OUTLINE = {")
for pid in sorted(plates):
    p = plates[pid]
    pts = ", ".join(f"({x:.4f},{y:.4f})" for x, y in p["poly"])
    L.append(f"    # {p['w']:.2f} x {p['h']:.2f} in, {len(p['holes'])} bolt holes")
    L.append(f"    {pid}: [{pts}],")
L.append("}")
L.append("")
L.append("# outline_id -> bolt-hole centres about the same centroid")
L.append("HOLES = {")
for pid in sorted(plates):
    pts = ", ".join(f"({x:.4f},{y:.4f})" for x, y in plates[pid]["holes"])
    L.append(f"    {pid}: [{pts}],")
L.append("}")
L.append("")
L.append("BOLT_DIA = 0.375        # 3/8\" bolts through every plate")
L.append("")
L.append("# One truss's eight plates: (outline_id, x, y, rot_deg, mirror, joint)")
L.append("PLACEMENTS = [")
for pid, x, y, r, m, tag in INSTANCES:
    L.append(f"    ({pid}, {x:9.3f}, {y:8.3f}, {r:7.2f}, {str(m):5s}, "
             f"{tag!r}),")
L.append("]")
L.append("")
L.append("FIT = {")
for pid in sorted(fit):
    f = fit[pid]
    L.append(f"    {pid}: dict(inliers={f['inliers']}, nholes={f['nholes']}, "
             f"scale={f['scale']}, rms_in={f['rms_in']}),")
L.append("}")
L.append("")

open("gh_plates.py", "w").write("\n".join(L) + "\n")
print(f"wrote gh_plates.py: {len(plates)} outlines, {len(INSTANCES)} placements")
for pid, x, y, r, m, tag in INSTANCES:
    p = plates[pid]
    print(f"  outline {pid} -> {tag:26s} ({x:8.3f},{y:8.3f}) "
          f"rot {r:6.2f}  {len(p['holes'])} holes")
