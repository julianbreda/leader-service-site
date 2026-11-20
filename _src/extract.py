"""One-time extraction of the legacy single-file site (legacy/index.html) into
reusable parts: CSS, images, and one HTML fragment per page.

Run from the repo root:  python3 _src/extract.py
Outputs:
  _src/legacy/pages/<name>.html   inner HTML of each former hash-route page
  _src/legacy/cine.html           the scroll-video hero markup (part of home)
  assets/css/legacy.css           every <style> block from the old file
  assets/img/*.webp               the base64 images, re-encoded
"""
import base64, io, re, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_src" / "legacy" / "index.html"
h = SRC.read_text(encoding="utf-8")

(ROOT / "assets/css").mkdir(parents=True, exist_ok=True)
(ROOT / "assets/img").mkdir(parents=True, exist_ok=True)
(ROOT / "_src/legacy/pages").mkdir(parents=True, exist_ok=True)

# ---- images: replace data: URIs in page markup with files -----------------
names = iter(["approach", "residential", "commercial", "technology", "extra1", "extra2"])
def save_img(m):
    mime, b64 = m.group(1), m.group(2)
    if mime == "svg+xml":
        return m.group(0)  # tiny favicon, leave
    name = next(names)
    im = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    if im.width > 1800:
        im = im.resize((1800, round(im.height * 1800 / im.width)), Image.LANCZOS)
    im.save(ROOT / f"assets/img/{name}.webp", "WEBP", quality=80, method=6)
    im.save(ROOT / f"assets/img/{name}.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    print("image", name, im.size)
    return f"/assets/img/{name}.webp"
h = re.sub(r"data:image/([a-z+]+);base64,([A-Za-z0-9+/=]+)", save_img, h)

# ---- css -------------------------------------------------------------------
css = "\n".join(re.findall(r"<style[^>]*>([\s\S]*?)</style>", h))
(ROOT / "assets/css/legacy.css").write_text(css, encoding="utf-8")

# ---- page fragments --------------------------------------------------------
body = h[h.find('<main id="app">'):h.find("<footer>")]
body = re.sub(r'<style id="techx-css">[\s\S]*?</style>', "", body)
starts = [(m.start(), m.end(), m.group(1)) for m in
          re.finditer(r'<div class="page[^"]*" data-page="([^"]+)">', body)]
for i, (s, e, name) in enumerate(starts):
    end = starts[i + 1][0] if i + 1 < len(starts) else body.rfind("</main>")
    inner = re.sub(r"(\s*<!--(?:(?!-->)[\s\S])*-->\s*)+$", "", body[e:end]).rstrip()
    assert inner.endswith("</div>"), name
    inner = inner[: -len("</div>")]
    (ROOT / f"_src/legacy/pages/{name}.html").write_text(inner, encoding="utf-8")
    print("page", name, len(inner))
