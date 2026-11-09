"""Generate receipt-specific 1200x630 PNG for Open Graph previews."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DEST = Path(__file__).resolve().parents[1] / "public" / "simple-receipt" / "og-image.png"
font_candidates = [
    "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
]
regular_candidates = [
    "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]
bold = next((p for p in font_candidates if Path(p).is_file()), None)
regular = next((p for p in regular_candidates if Path(p).is_file()), None) or bold
if not bold:
    raise SystemExit("Korean font not available: install fonts-nanum")

def font(size, strong=True):
    return ImageFont.truetype(bold if strong else regular, size)

W, H = 1200, 630
im = Image.new("RGB", (W, H), "#173f59")
d = ImageDraw.Draw(im)
d.rounded_rectangle((38, 38, 1162, 592), radius=34, fill="#245b78")
white, pale, navy = "#fff", "#d7f5fa", "#173b57"
d.text((83, 74), "백세푸드 무료 서식", font=font(32), fill=pale)
d.text((78, 162), "무료 온라인", font=font(66), fill=white)
d.text((78, 249), "간이영수증", font=font(91), fill=white)
d.rounded_rectangle((82, 393, 545, 464), radius=16, fill="#dff6ff")
d.text((107, 409), "15품목 자동계산 · PDF 저장", font=font(29), fill=navy)
d.text((82, 516), "A4 세로 한 장 · 공급자용 / 공급받는 자용", font=font(24, False), fill=pale)

def draw_receipt(x, y, title, fill):
    w, h = 222, 375
    d.rounded_rectangle((x, y, x+w, y+h), radius=7, fill=white, outline="#bdd5df", width=2)
    d.rectangle((x+12, y+12, x+w-12, y+65), fill=fill)
    box = d.textbbox((0,0), title, font=font(20))
    tw = box[2]-box[0]
    d.text((x+(w-tw)//2, y+25), title, font=font(20), fill=navy)
    for i in range(8):
        top=y+78+i*35
        d.rectangle((x+12, top, x+w-12, top+33), outline="#a9bbc4", width=1)
        d.line((x+80, top, x+80, top+33), fill="#a9bbc4")
        d.line((x+145, top, x+145, top+33), fill="#a9bbc4")

draw_receipt(643, 162, "공급자 보관용", "#dcf4e8")
draw_receipt(883, 162, "공급받는 자용", "#dfeef9")
d.line((875, 173, 875, 526), fill=pale, width=4)
im.quantize(colors=48, method=Image.Quantize.MEDIANCUT).save(
    DEST, format="PNG", optimize=True, compress_level=9
)
print("RECEIPT_OG_PNG_GENERATED", DEST, DEST.stat().st_size)
