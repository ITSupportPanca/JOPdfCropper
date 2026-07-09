# JO PDF Cropper

Tool internal PKR buat auto-crop & scale PDF Job Order (report vendor ukuran A4) ke ukuran kertas continuous form custom (default **9.5" x 5.5"**), supaya siap langsung print tanpa kepotong atau perlu scale manual di Acrobat.

## Kenapa dibikin

Report JO dari vendor di-generate pake JasperReports dengan page size A4 penuh (8.26" x 11.69"), padahal isi konten cuma butuh area ~setengah halaman. Kertas continuous form yang dipakai fisiknya cuma 9.5" x 5.5" per section, jadi kalau print langsung dari PDF asli, bagian bawah selalu kepotong.

App ini otomatis:
1. Deteksi area yang beneran ada isinya di tiap halaman (teks + garis tabel)
2. Crop bagian kosong yang gak perlu
3. Scale konten biar pas masuk ke ukuran kertas fisik
4. Hasilkan PDF baru yang siap di-print pakai mode **Actual Size**

## Cara pakai (untuk user)

1. Buka link app (lihat bagian Deploy di bawah)
2. Upload PDF Job Order dari vendor
3. Cek preview hasil crop
4. Klik **Download PDF siap print**
5. Buka hasil download → Ctrl+P → pilih printer → Properties → pastikan Paper Size = custom form kertas fisik → pilih mode **Actual Size** → Print

## Cara jalanin lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

Buka `http://localhost:8501` di browser.

## Deploy ke Streamlit Community Cloud

1. Push repo ini ke GitHub
2. Buka [streamlit.io/cloud](https://share.streamlit.io) → **New app**
3. Connect ke repo ini, pilih branch `main`, main file `app.py`
4. Deploy — nanti dapet URL publik (misal `pkr-jo-cropper.streamlit.app`)
5. Share link itu ke user yang butuh print JO

## Ubah ukuran kertas

Kalau suatu saat ganti jenis kertas continuous form, gak perlu ubah kode — tinggal ubah angka **Lebar** dan **Tinggi** di sidebar app pas lagi dipakai.

## Tech stack

- [Streamlit](https://streamlit.io) — web UI
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io) — baca, crop, dan render PDF
