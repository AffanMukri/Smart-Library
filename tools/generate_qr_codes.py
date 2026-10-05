"""Generate scannable Smart Library demo QR labels and a printable sheet."""

from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_M


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "qrcodes"
OUTPUT.mkdir(parents=True, exist_ok=True)

RECORDS = [
    ("student", "23IT101", "Affan Mukri"),
    ("student", "23IT102", "Sara Khan"),
    ("student", "23CS103", "Rohan Mehta"),
    ("book", "BOOK001", "Database Management Systems"),
    ("book", "BOOK002", "Clean Code"),
    ("book", "BOOK003", "Introduction to Algorithms"),
]


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


TITLE_FONT, CODE_FONT, NAME_FONT = font(24, True), font(32, True), font(18)


def centered(draw: ImageDraw.ImageDraw, text: str, y: int, selected_font, width: int) -> None:
    bounds = draw.textbbox((0, 0), text, font=selected_font)
    draw.text(((width - (bounds[2] - bounds[0])) / 2, y), text, fill="#172033", font=selected_font)


def create_label(kind: str, code: str, name: str) -> Image.Image:
    qr = qrcode.QRCode(version=2, error_correction=ERROR_CORRECT_M, box_size=12, border=5)
    qr.add_data(code)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    label = Image.new("RGB", (560, 670), "white")
    draw = ImageDraw.Draw(label)
    accent = "#4359c7" if kind == "student" else "#059669"
    draw.rounded_rectangle((4, 4, 555, 665), radius=24, outline=accent, width=6)
    centered(draw, f"SMART LIBRARY • {kind.upper()}", 28, TITLE_FONT, label.width)
    label.paste(qr_image, ((label.width - qr_image.width) // 2, 82))
    centered(draw, code, 550, CODE_FONT, label.width)
    display_name = name if len(name) <= 34 else name[:31] + "..."
    centered(draw, display_name, 602, NAME_FONT, label.width)
    return label


labels: list[Image.Image] = []
for record_kind, record_code, record_name in RECORDS:
    generated = create_label(record_kind, record_code, record_name)
    generated.save(OUTPUT / f"{record_kind}-{record_code}.png", optimize=True)
    labels.append(generated)

sheet = Image.new("RGB", (1200, 2140), "white")
sheet_draw = ImageDraw.Draw(sheet)
centered(sheet_draw, "SMART LIBRARY DEMO QR CODES", 34, font(36, True), sheet.width)
sheet_draw.text((54, 96), "Students", fill="#4359c7", font=font(27, True))
sheet_draw.text((626, 96), "Books", fill="#059669", font=font(27, True))
for row in range(3):
    sheet.paste(labels[row], (40, 140 + row * 660))
    sheet.paste(labels[row + 3], (610, 140 + row * 660))
sheet.save(OUTPUT / "smart-library-qr-sheet.png", optimize=True)

print(f"Generated {len(labels)} QR labels and one printable sheet in {OUTPUT}")
