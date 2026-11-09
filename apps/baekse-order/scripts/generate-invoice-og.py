"""Generate a 1200x630 PNG social sharing image for the free invoice page."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "public" / "manual-invoice" / "og-image.png"
FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf"),
]
REGULAR_CANDIDATES = [
    Path("/usr/share/fonts/truetype/nanum/NanumSquareR.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
]
BOLD = next((p for p in FONT_CANDIDATES if p.is_file()), None)
REGULAR = next((p for p in REGULAR_CANDIDATES if p.is_file()), None)
if not BOLD:
    raise SystemExit("Korean font missing: install fonts-nanum before generation")
if not REGULAR:
    REGULAR = BOLD

def font(size, bold=True):
    return ImageFont.truetype(str(BOLD if bold else REGULAR), size)

w, h = 1200, 630
image = Image.new("RGB", (w, h), "#073f3a")
d = ImageDraw.Draw(image)
white, mint, green, dark = "#ffffff", "#c9f5df", "#0a776b", "#173a35"
d.rounded_rectangle((40, 42, 1160, 588), radius=32, fill="#0c645b")
d.text((88, 78), "백세푸드 무료 서식", font=font(32), fill=mint)
d.text((82, 166), "무료 온라인", font=font(65), fill=white)
d.text((82, 255), "거래명세표", font=font(92), fill=white)
d.rounded_rectangle((82, 400, 535, 464), radius=15, fill="#d7ffeb")
d.text((106, 410), "작성 · 자동계산 · PDF 저장", font=font(31), fill=dark)
d.text((85, 515), "A4 가로 · 공급자용 / 공급받는 자용", font=font(25, False), fill=mint)

def preview(x, y, width, height, label):
    d.rounded_rectangle((x, y, x + width, y + height), radius=8, fill=white)
    d.rectangle((x + 13, y + 12, x + width - 13, y + 58), outline=green, width=3)
    box = d.textbbox((0, 0), label, font=font(22))
    tw = box[2] - box[0]
    d.text((x + (width - tw) // 2, y + 20), label, font=font(22), fill=dark)
    for i in range(8):
        yy = y + 72 + i * 36
        d.rectangle((x + 13, yy, x + width - 13, yy + 34), outline="#8da6a2", width=1)
        for sep in (x + 82, x + 158):
            d.line((sep, yy, sep, yy + 34), fill="#b4ccc5", width=1)

preview(635, 175, 230, 361, "공급자용")
preview(885, 175, 230, 361, "공급받는 자용")
d.line((875, 183, 875, 529), fill=mint, width=4)
d.text((755, 549), "두 장을 한 장에 인쇄", font=font(18), fill=white)
image.quantize(colors=28, method=Image.Quantize.MEDIANCUT).save(
    OUT, format="PNG", optimize=True, compress_level=9
)
print("OG_IMAGE_GENERATED", OUT, OUT.stat().st_size)
