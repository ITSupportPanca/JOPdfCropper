import io
import fitz  # PyMuPDF
import streamlit as st

st.set_page_config(page_title="JO PDF Cropper - PKR", page_icon="🖨️", layout="centered")

# ==== UKURAN KERTAS FISIK (custom continuous form) ====
DEFAULT_PAPER_W_IN = 9.5
DEFAULT_PAPER_H_IN = 5.5

# Margin aman di dalam kertas (points, 72pt = 1 inch).
# Bottom margin dibuat lebih besar karena printer dot-matrix biasanya
# punya area "tidak bisa dicetak" (unprintable zone) di bagian paling
# bawah kertas -- kalau margin bawah kekecilan, baris paling bawah
# (misal garis tanda tangan) bisa kepotong walau PDF-nya sendiri sudah pas.
MARGIN_TOP_PT = 16
MARGIN_BOTTOM_PT = 20
MARGIN_LEFT_PT = 8
MARGIN_RIGHT_PT = 8


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
        return page.rect

    pad = 4
    return fitz.Rect(
        max(0, min(xs0) - pad),
        max(0, min(ys0) - pad),
        min(page.rect.width, max(xs1) + pad),
        min(page.rect.height, max(ys1) + pad),
    )


def crop_and_scale(input_bytes, paper_w_in, paper_h_in):
    paper_w = paper_w_in * 72
    paper_h = paper_h_in * 72

    src = fitz.open(stream=input_bytes, filetype="pdf")
    out = fitz.open()

    page_info = []

    for i, page in enumerate(src):
        crop = get_content_bbox(page)
        cw, ch = crop.width, crop.height

        avail_w = paper_w - MARGIN_LEFT_PT - MARGIN_RIGHT_PT
        avail_h = paper_h - MARGIN_TOP_PT - MARGIN_BOTTOM_PT
        scale = min(avail_w / cw, avail_h / ch, 1.0)
        new_w, new_h = cw * scale, ch * scale

        new_page = out.new_page(width=paper_w, height=paper_h)
        target_rect = fitz.Rect(MARGIN_LEFT_PT, MARGIN_TOP_PT,
                                 MARGIN_LEFT_PT + new_w, MARGIN_TOP_PT + new_h)
        new_page.show_pdf_page(target_rect, src, i, clip=crop)

        page_info.append({"page": i + 1, "scale": round(scale * 100)})

    buf = io.BytesIO()
    out.save(buf)
    out.close()
    src.close()
    buf.seek(0)
    return buf, page_info


def render_preview(pdf_bytes, page_num=0, zoom=2.0):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img_bytes = pix.tobytes("png")
    total_pages = len(doc)
    doc.close()
    return img_bytes, total_pages


# ==================== UI ====================

st.title("🖨️ JO PDF Cropper")
st.caption("Upload PDF Job Order dari vendor (ukuran A4) → auto-crop & scale ke ukuran kertas continuous form → langsung print.")

with st.sidebar:
    st.header("⚙️ Ukuran Kertas")
    paper_w = st.number_input("Lebar kertas (inch)", value=DEFAULT_PAPER_W_IN, min_value=1.0, max_value=20.0, step=0.1)
    paper_h = st.number_input("Tinggi kertas (inch)", value=DEFAULT_PAPER_H_IN, min_value=1.0, max_value=20.0, step=0.1)
    st.markdown("---")
    st.markdown("**Default:** 9.5\" x 5.5\" (continuous form 2-ply job order)")
    st.markdown("Ubah angka di atas kalau suatu saat ganti jenis kertas.")

uploaded_file = st.file_uploader("Upload file PDF Job Order", type=["pdf"])

if uploaded_file is not None:
    input_bytes = uploaded_file.read()

    with st.spinner("Memproses PDF..."):
        try:
            output_buf, page_info = crop_and_scale(input_bytes, paper_w, paper_h)
        except Exception as e:
            st.error(f"Gagal memproses PDF: {e}")
            st.stop()

    output_bytes = output_buf.getvalue()

    st.success(f"Berhasil! {len(page_info)} halaman diproses ke ukuran {paper_w}\" x {paper_h}\".")

    # info per halaman
    with st.expander("Detail scaling per halaman"):
        for info in page_info:
            st.write(f"Halaman {info['page']}: di-scale {info['scale']}%")

    # preview
    st.subheader("Preview hasil")
    img_bytes, total_pages = render_preview(output_bytes, page_num=0)

    if total_pages > 1:
        page_choice = st.slider("Lihat halaman ke-", 1, total_pages, 1)
        img_bytes, _ = render_preview(output_bytes, page_num=page_choice - 1)

    st.image(img_bytes, use_container_width=True)

    st.markdown("---")

    out_name = uploaded_file.name.rsplit(".", 1)[0] + f"_{paper_w}x{paper_h}.pdf"
    st.download_button(
        label="⬇️ Download PDF siap print",
        data=output_bytes,
        file_name=out_name,
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

    st.info(
        "**Cara print:** buka file hasil download → Ctrl+P → pilih printer → "
        "di Properties pastikan Paper Size = custom form kertas fisik lo → "
        "pilih mode **Actual Size** (bukan Fit) → Print."
    )
else:
    st.info("Upload file PDF Job Order buat mulai.")
