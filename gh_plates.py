"""Truss plate outlines and placements  (generated - do not hand-edit).

Recovered from the CAD set's "3/16\" TRUSS PLATES" detail box by
extract_plates.py, and located on the truss by place_plates.py, which
matches each plate's 3/8" bolt pattern to the same pattern drawn in
place on the truss elevation.  Every plate fitted at scale 1.000 with
RMS <= 0.02", confirming the detail box is drawn at elevation scale.

Bolt tally, which corroborates the whole extraction:
    knee        2 x  9 = 18
    trapezoid   2 x  4 =  8
    square      2 x  7 = 14
    king-post   1 x  8 =  8
    peak        1 x 12 = 12   (+2 more to the ridge)
                        ----
                          60   = the fastener table's
                                 'Plates: 3/8" x 1 1/4" Bolt & Nut (60)'

OUTLINES are convex hulls of the drawn outline.  The drawn plates are
convex except for a small notch at the apex of the peak plate, which
the hull closes; that is the one place a plate is not shape-exact.

Coordinates in INCHES, each outline about its own centroid.
"""

# outline_id -> closed polygon about the centroid
OUTLINE = {
    # 13.63 x 21.97 in, 9 bolt holes
    0: [(-6.9562,-4.2133), (-3.0362,8.0267), (4.1638,10.1333), (5.3638,7.3600), (6.6704,1.8933), (-0.7696,-11.8400), (-5.4362,-11.3600)],
    # 5.52 x 7.60 in, 4 bolt holes
    1: [(-3.1511,2.2711), (0.5289,3.8444), (1.7023,1.0977), (2.3689,-2.9823), (0.5289,-3.7556), (-1.9777,-0.4755)],
    # 7.73 x 6.69 in, 7 bolt holes
    2: [(-4.1533,2.0267), (2.4334,3.4133), (3.5800,-2.1600), (-1.8600,-3.2800)],
    # 12.56 x 7.17 in, 8 bolt holes
    3: [(-6.2800,-1.1111), (-1.0000,4.1422), (1.0000,4.1422), (6.2800,-1.1111), (5.8800,-3.0311), (-5.8800,-3.0311)],
    # 12.51 x 12.16 in, 14 bolt holes
    4: [(-6.2445,2.4533), (-0.6711,4.8533), (0.6622,4.8533), (6.2622,2.4533), (5.5955,-7.3067), (-5.6045,-7.3067)],
    # 7.71 x 6.69 in, 7 bolt holes
    5: [(-3.5733,-2.1600), (-2.4266,3.4133), (4.1333,2.0267), (1.8667,-3.2800)],
    # 5.52 x 7.60 in, 4 bolt holes
    6: [(-2.3600,-2.9823), (-1.7200,1.0977), (-0.5200,3.8444), (3.1600,2.2711), (1.9600,-0.4755), (-0.5200,-3.7556)],
    # 13.63 x 21.97 in, 9 bolt holes
    7: [(-6.6629,1.8933), (-5.3562,7.3600), (-4.1829,10.1333), (3.0171,8.0267), (6.9638,-4.2133), (5.4438,-11.3600), (0.7771,-11.8400)],
}

# outline_id -> bolt-hole centres about the same centroid
HOLES = {
    0: [(-1.3962,2.6533), (0.5505,3.0533), (2.5238,3.4533), (0.1505,6.7867), (1.9905,7.5867), (3.8305,8.3600), (-3.9562,-5.9600), (-3.9562,-7.9600), (-3.9562,-9.9600)],
    1: [(1.0489,-2.4356), (0.2489,-0.5955), (-1.6444,1.2978), (0.1956,2.0978)],
    2: [(2.6333,-1.3200), (0.6867,-1.7200), (-1.2867,-2.1200), (1.6200,1.6400), (-0.0333,0.4933), (-2.1667,-0.0933), (-2.9400,1.7467)],
    3: [(-0.0267,1.1689), (-0.0267,3.1689), (1.1733,-1.0178), (3.1466,-1.4444), (5.0933,-1.8444), (-5.1200,-1.8444), (-3.1734,-1.4444), (-1.2000,-1.0178)],
    4: [(0.9156,-1.6400), (2.7556,-2.4133), (4.5956,-3.2133), (2.3823,-5.1867), (4.0089,-6.3600), (-0.0178,-4.3067), (-0.0178,-6.3067), (-4.0445,-6.3600), (-2.3911,-5.1867), (-4.6045,-3.2133), (-2.7644,-2.4133), (-0.9244,-1.6400), (-0.8989,3.9708), (0.8901,3.9708)],
    5: [(-2.6533,-1.3200), (-0.7067,-1.7200), (1.2667,-2.1200), (-1.6400,1.6400), (-0.0133,0.4933), (2.1200,-0.0933), (2.9200,1.7467)],
    6: [(-1.0667,-2.4356), (-0.2667,-0.5955), (1.6266,1.2978), (-0.2134,2.0978)],
    7: [(1.3771,2.6533), (-0.5695,3.0533), (-2.5429,3.4533), (-0.1695,6.7867), (-2.0095,7.5867), (-3.8495,8.3600), (3.9105,-5.9600), (3.9105,-7.9600), (3.9105,-9.9600)],
}

BOLT_DIA = 0.375        # 3/8" bolts through every plate

# One truss's eight plates: (outline_id, x, y, rot_deg, mirror, joint)
PLACEMENTS = [
    (0,  -115.670,   57.400,   -0.04, False, 'knee, left'),
    (7,   115.704,   57.397,    0.04, False, 'knee, right'),
    (6,   -56.629,   87.366,   46.47, False, 'short-web top, left'),
    (1,    56.641,   87.353,  -46.47, False, 'short-web top, right'),
    (2,   -49.593,   75.947,    0.00, False, 'mid joint, left'),
    (5,    49.613,   75.947,    0.00, False, 'mid joint, right'),
    (3,    -0.027,   85.191,    0.00, True , 'king-post base, centre'),
    (4,    -0.018,  114.827,    0.00, True , 'peak, centre'),
]

FIT = {
    0: dict(inliers=9, nholes=9, scale=1.0013, rms_in=0.017),
    1: dict(inliers=4, nholes=4, scale=0.9979, rms_in=0.0105),
    2: dict(inliers=7, nholes=7, scale=1.0, rms_in=0.0),
    3: dict(inliers=8, nholes=8, scale=1.0, rms_in=0.0188),
    4: dict(inliers=12, nholes=14, scale=1.0, rms_in=0.0172),
    5: dict(inliers=7, nholes=7, scale=1.0, rms_in=0.0142),
    6: dict(inliers=4, nholes=4, scale=0.9979, rms_in=0.0105),
    7: dict(inliers=9, nholes=9, scale=1.0022, rms_in=0.0159),
}

