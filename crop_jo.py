"""
crop_jo.py
-----------
Crop & scale PDF Job Order (report vendor, ukuran A4 penuh) supaya pas
dicetak di kertas continuous form custom 9.5" x 5.5".

CARA PAKAI:
1. Install Python (kalau belum ada): https://www.python.org/downloads/
2. Install library yang dibutuhkan (sekali aja, buka Command Prompt/Terminal):
       pip install pymupdf

3. Jalankan script ini lewat Command Prompt/Terminal:
       python crop_jo.py "nama_file_input.pdf"

   Hasilnya otomatis tersimpan sebagai "nama_file_input_9.5x5.5.pdf"
   di folder yang sama.

   Bisa juga tentuin nama file output sendiri:
       python crop_jo.py "JO.pdf" "JO_siap_print.pdf"

CATATAN:
- Script ini otomatis mendeteksi area yang ada isinya di tiap halaman
  (nyari teks & garis tabel paling atas/bawah/kiri/kanan), lalu crop
  dan scale supaya pas masuk ke kertas 9.5" x 5.5" tanpa distorsi.
- Kalau layout report vendor berubah drastis, hasil crop otomatis ini
  mungkin perlu dicek ulang -- selalu preview dulu sebelum print beneran.
"""

import sys
import fitz  # PyMuPDF

# ==== UKURAN KERTAS FISIK (custom form) ====
PAPER_W_IN = 9.5
PAPER_H_IN = 5.5

# Margin aman di dalam kertas (points, 72pt = 1 inch).
# Bottom margin dibuat lebih besar karena printer dot-matrix biasanya
# punya area "tidak bisa dicetak" (unprintable zone) di bagian paling
# bawah kertas -- kalau margin bawah kekecilan, baris paling bawah
# (misal garis tanda tangan) bisa kepotong walau PDF-nya sendiri sudah pas.
MARGIN_TOP_PT = 6
MARGIN_BOTTOM_PT = 26
MARGIN_LEFT_PT = 8
MARGIN_RIGHT_PT = 8

PAPER_W = PAPER_W_IN * 72
PAPER_H = PAPER_H_IN * 72


def get_content_bbox(page):
    """Cari batas kiri/kanan/atas/bawah dari semua teks & garis di halaman."""
    xs0, xs1, ys0, ys1 = [], [], [], []

    for block in page.get_text("dict")["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    xs0.append(x0)
                    xs1.append(x1)
                    ys0.append(y0)
                    ys1.append(y1)

    for drawing in page.get_drawings():
        r = drawing["rect"]
        xs0.append(r.x0)
        xs1.append(r.x1)
        ys0.append(r.y0)
        ys1.append(r.y1)

    if not xs0:
        # kalau gak ada konten kedetect, pakai seluruh halaman
        return page.rect

    pad = 4
    return fitz.Rect(
        max(0, min(xs0) - pad),
        max(0, min(ys0) - pad),
        min(page.rect.width, max(xs1) + pad),
        min(page.rect.height, max(ys1) + pad),
    )


def crop_and_scale(input_path, output_path):
    src = fitz.open(input_path)
    out = fitz.open()

    for i, page in enumerate(src):
        crop = get_content_bbox(page)
        cw, ch = crop.width, crop.height

        avail_w = PAPER_W - MARGIN_LEFT_PT - MARGIN_RIGHT_PT
        avail_h = PAPER_H - MARGIN_TOP_PT - MARGIN_BOTTOM_PT
        scale = min(avail_w / cw, avail_h / ch, 1.0)  # jangan diperbesar, cuma diperkecil kalau perlu
        new_w, new_h = cw * scale, ch * scale

        new_page = out.new_page(width=PAPER_W, height=PAPER_H)
        target_rect = fitz.Rect(MARGIN_LEFT_PT, MARGIN_TOP_PT,
                                 MARGIN_LEFT_PT + new_w, MARGIN_TOP_PT + new_h)
        new_page.show_pdf_page(target_rect, src, i, clip=crop)

        print(f"Halaman {i + 1}: konten {cw:.0f}x{ch:.0f}pt -> scale {scale*100:.0f}% "
              f"-> hasil {new_w:.0f}x{new_h:.0f}pt")

    out.save(output_path)
    out.close()
    src.close()
    print(f"\nSelesai! File tersimpan di: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cara pakai: python crop_jo.py <file_input.pdf> [file_output.pdf]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    if len(sys.argv) >= 3:
        output_pdf = sys.argv[2]
    else:
        if input_pdf.lower().endswith(".pdf"):
            output_pdf = input_pdf[:-4] + "_9.5x5.5.pdf"
        else:
            output_pdf = input_pdf + "_9.5x5.5.pdf"

    crop_and_scale(input_pdf, output_pdf)
