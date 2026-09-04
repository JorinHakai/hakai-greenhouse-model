"""Render inspection views of the built model to greenhouse_preview.png.

Uses a small numpy z-buffer rasteriser so it needs no GPU, display or
pyglet -- it runs anywhere the build runs.

    python gh_build.py --noholes && python gh_preview.py
"""
import json, numpy as np, trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, H = 1150, 780


def load():
    f = trimesh.load("frame.stl")
    g = trimesh.load("glazing.stl")
    return f, g


def look_at(eye, tgt, up=(0, 1, 0)):
    eye = np.asarray(eye, float); tgt = np.asarray(tgt, float)
    f = tgt - eye; f /= np.linalg.norm(f)
    u = np.asarray(up, float)
    s = np.cross(f, u); n = np.linalg.norm(s)
    if n < 1e-9:
        u = np.array([0, 0, 1.0]); s = np.cross(f, u); n = np.linalg.norm(s)
    s /= n
    u2 = np.cross(s, f)
    R = np.stack([s, u2, -f])
    return R, eye


def raster(tris, cols, eye, tgt, fov=42.0, up=(0, 1, 0)):
    """tris (N,3,3) world; cols (N,3) rgb 0..1.  Returns HxWx3 float image."""
    R, e = look_at(eye, tgt, up)
    V = (tris.reshape(-1, 3) - e) @ R.T
    V = V.reshape(-1, 3, 3)
    z = -V[:, :, 2]
    keep = (z > 1e-3).all(axis=1)
    V, cols, z = V[keep], cols[keep], z[keep]
    fpx = (H/2) / np.tan(np.radians(fov)/2)
    xs = V[:, :, 0]/z*fpx + W/2
    ys = -V[:, :, 1]/z*fpx + H/2

    img = np.zeros((H, W, 3), float)
    img[:] = np.array([0.067, 0.082, 0.102])
    zb = np.full((H, W), np.inf)

    order = np.argsort(-z.mean(axis=1))          # far to near
    for i in order:
        x0, x1 = xs[i].min(), xs[i].max()
        y0, y1 = ys[i].min(), ys[i].max()
        if x1 < 0 or x0 > W-1 or y1 < 0 or y0 > H-1:
            continue
        ix0, ix1 = max(int(np.floor(x0)), 0), min(int(np.ceil(x1)), W-1)
        iy0, iy1 = max(int(np.floor(y0)), 0), min(int(np.ceil(y1)), H-1)
        if ix1 < ix0 or iy1 < iy0:
            continue
        px, py = np.meshgrid(np.arange(ix0, ix1+1), np.arange(iy0, iy1+1))
        ax, ay = xs[i, 0], ys[i, 0]
        bx, by = xs[i, 1], ys[i, 1]
        cx, cy = xs[i, 2], ys[i, 2]
        d = (by-cy)*(ax-cx) + (cx-bx)*(ay-cy)
        if abs(d) < 1e-9:
            continue
        w0 = ((by-cy)*(px-cx) + (cx-bx)*(py-cy))/d
        w1 = ((cy-ay)*(px-cx) + (ax-cx)*(py-cy))/d
        w2 = 1.0 - w0 - w1
        m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not m.any():
            continue
        zz = w0*z[i, 0] + w1*z[i, 1] + w2*z[i, 2]
        sub = zb[iy0:iy1+1, ix0:ix1+1]
        upd = m & (zz < sub)
        if not upd.any():
            continue
        sub[upd] = zz[upd]
        img[iy0:iy1+1, ix0:ix1+1][upd] = cols[i]
    return img


def shade(mesh, base, eye, light=(0.45, 0.8, 0.35), amb=0.32):
    n = mesh.face_normals
    l = np.asarray(light, float); l /= np.linalg.norm(l)
    diff = np.clip(n @ l, 0, 1)
    # two-sided so interior faces are lit too
    diff = np.maximum(diff, np.clip(-(n @ l), 0, 1)*0.55)
    k = (amb + (1-amb)*diff)[:, None]
    return np.clip(np.asarray(base, float)[None, :]*k, 0, 1)


if __name__ == "__main__":
    fr, gl = load()
    ftris = fr.triangles
    gtris = gl.triangles
    box = np.vstack([fr.bounds, gl.bounds])
    lo, hi = box.min(axis=0), box.max(axis=0)
    ctr = (lo+hi)/2
    ctr[1] = lo[1]
    S = (hi-lo)

    tris = np.concatenate([ftris, gtris])
    VIEWS = [
        ("Isometric",
         ctr + np.array([S[0]*1.5, S[1]*1.9, S[2]*0.85]), ctr + [0, S[1]*0.4, 0], 40),
        ("Gable end",
         ctr + np.array([S[0]*0.28, S[1]*0.75, S[2]*1.02]), ctr + [0, S[1]*0.42, 0], 40),
        ("Interior, looking down the length",
         ctr + np.array([0, S[1]*0.52, S[2]*0.40]), ctr + [0, S[1]*0.46, -S[2]*0.3], 62),
        ("Truss bay, plates visible",
         ctr + np.array([S[0]*0.34, S[1]*0.66, S[2]*0.26]),
         ctr + [0, S[1]*0.62, S[2]*0.05], 34),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(19.5, 13.2),
                             facecolor="#0f1319")
    for ax, (title, eye, tgt, fov) in zip(axes.ravel(), VIEWS):
        show_glass = "Truss" not in title
        if show_glass:
            cols = np.concatenate([
                shade(fr, (0.845, 0.870, 0.902), eye),
                shade(gl, (0.560, 0.720, 0.840), eye, amb=0.55)])
            T = tris
        else:
            cols = shade(fr, (0.845, 0.870, 0.902), eye)
            T = ftris
        img = raster(T, cols, eye, tgt, fov=fov)
        ax.imshow(img, interpolation="bilinear")
        ax.set_title(title, color="#e7edf3", fontsize=14, pad=9)
        ax.axis("off")
    try:
        man = json.load(open("manifest.json"))
        rep = json.load(open("verification_report.json"))
        npass = sum(1 for r in rep["dimensional"] if r["pass"])
        sub = (f"{sum(man.values())} solids, "
               f"{sum(v for k, v in man.items() if 'truss plate' in k)} truss plates, "
               f"end walls glazed, "
               f"{npass}/{len(rep['dimensional'])} dimensional checks pass")
    except Exception:
        sub = "inspection views"
    fig.suptitle("Greenhouse digital twin  -  " + sub,
                 color="#e7edf3", fontsize=17, y=0.975)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    fig.savefig("greenhouse_preview.png", dpi=100, facecolor="#0f1319")
    print("-> greenhouse_preview.png")
