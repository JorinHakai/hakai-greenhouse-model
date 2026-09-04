"""Fraction parser for the dimension text on the CAD sheets.

Dimension strings arrive concatenated in the PDF text layer ('1031516"' is
103 15/16"), so whole / numerator / denominator have to be recovered by
requiring lowest terms, denominators in {2,4,8,16,32}, and rejecting
leading-zero numerators -- which is what disambiguates '12038"' as 120 3/8"
rather than 12 3/8".

Linework extraction lives in extract_truss.py and extract_plates.py.
"""
import pymupdf, re, math, json, collections

PDF = "drawings_source.pdf"      # the supplied vendor CAD set (not committed)
DENS = ["32", "16", "8", "4", "2"]

def parse_dim(s):
    """'1031516\"' -> 103.9375 ; \"20'-614\\\"\\\"\" -> 246.25 ; '98\"' -> 98.0"""
    t = s.replace('"', '').replace('”', '').strip()
    if not t: return None
    feet = 0.0
    m = re.match(r"^(\d+)'-(.*)$", t)
    if m:
        feet = float(m.group(1)) * 12.0
        t = m.group(2)
    if t == "": return feet
    if not t.isdigit():
        m2 = re.match(r"^([\d.]+)", t)
        return feet + float(m2.group(1)) if m2 else None
    if len(t) <= 2:              # plain whole number
        return feet + float(t)
    for den in DENS:             # try fraction split
        if t.endswith(den) and len(t) > len(den):
            rest = t[:-len(den)]
            D = int(den)
            for nl in (2, 1):    # 2-digit numerator first (103|15|16), then 1-digit
                if len(rest) > nl - 1 and len(rest) >= nl:
                    if nl == 2 and rest[-2] == "0":   # '03' invalid numerator
                        continue
                    num = int(rest[-nl:]); whole = rest[:-nl]
                    if 0 < num < D and num % 2 == 1:      # lowest terms
                        if whole == "" or whole.isdigit():
                            w = float(whole) if whole else 0.0
                            return feet + w + num / D
            for nl in (2, 1):    # fallback: allow even numerator (e.g. 2/32)
                if len(rest) >= nl:
                    if nl == 2 and rest[-2] == "0": continue
                    num = int(rest[-nl:]); whole = rest[:-nl]
                    if 0 < num < D and (whole == "" or whole.isdigit()):
                        w = float(whole) if whole else 0.0
                        return feet + w + num / D
    return feet + float(t)

def page_items(pno):
    doc = pymupdf.open(PDF); p = doc[pno]
    R = p.rotation_matrix
    words = []
    for w in p.get_text("words"):
        r = pymupdf.Rect(w[:4]) * R
        words.append({"t": w[4], "x": (r.x0+r.x1)/2, "y": (r.y0+r.y1)/2,
                      "w": abs(r.width), "h": abs(r.height)})
    lines = []
    for dr in p.get_drawings():
        for it in dr["items"]:
            if it[0] == "l":
                a = pymupdf.Point(it[1]) * R; b = pymupdf.Point(it[2]) * R
                lines.append((a.x, a.y, b.x, b.y))
            elif it[0] == "re":
                r = pymupdf.Rect(it[1]) * R
                lines += [(r.x0,r.y0,r.x1,r.y0),(r.x1,r.y0,r.x1,r.y1),
                          (r.x1,r.y1,r.x0,r.y1),(r.x0,r.y1,r.x0,r.y0)]
            elif it[0] == "c":
                pts = [pymupdf.Point(q) * R for q in it[1:5]]
                for i in range(3):
                    lines.append((pts[i].x,pts[i].y,pts[i+1].x,pts[i+1].y))
    doc.close()
    return words, lines

if __name__ == "__main__":
    tests = ['1031516"','3438"','7418"','98"','''20'-614""''','''10'-278""''',
             '4312"','431516"','12558"','12038"','591116"','131316"','26316"',
             '62116"','8614"','4234"','61514"','11912"','1252","']
    for t in tests:
        print(f"  {t:>14} -> {parse_dim(t)}")
