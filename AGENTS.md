# Panduan kerja dashboard admin Tracker Clinker Tonasa

Panduan ini berlaku dari akar repositori. Gunakan [CODE_MAP.md](CODE_MAP.md) untuk mencari kode dan [RINGKASAN.md](RINGKASAN.md) untuk melihat status fitur serta integrasi.

Pertahankan istilah yang sudah dipilih di antarmuka, seperti **Tracker Clinker Tonasa**, **nomor lambung**, **ritase**, dan tanggal laporan dalam **WITA**. Dashboard memakai **Ekspeditur**. Masing-masing target memiliki proses build dan preview sendiri.

Aplikasi supir tersedia di [mobileapp-tracker](https://github.com/akmalhidayah/mobileapp-tracker).

## Dashboard admin

- Sumber tampilan bersama ada di `monitoring/templates/monitoring/` dan `monitoring/static/monitoring/dashboard.css`. Navigasi dan formulir masuk memakai JavaScript kecil di folder statis yang sama. Penyesuaian admin berada di `templates/admin/` dan `monitoring/static/monitoring/admin.css`.
- Edit peta interaktif di `frontend/src/`, bukan di bundel `monitoring/static/monitoring/app/`. Jalankan build npm jika sumber React berubah. Perubahan CSS biasa dan template Django tidak memerlukan build React.
- Jangan menghapus kredit peta atau menutupnya dengan legenda. Pertahankan fallback peta, interaksi layar penuh, dan navigasi di HP saat menyentuh bagian terkait.
- Gunakan sesi, CSRF, serta pemeriksaan izin Django untuk akun web. Jangan menyalin kunci rahasia, kata sandi, data pengguna asli, atau `db.sqlite3` ke dokumentasi atau Git. Gunakan basis data sementara untuk percobaan yang menulis akun/data.
- Perubahan model yang benar-benar diperlukan harus punya migrasi. Pertahankan migrasi historis; penggantian label tampilan saja tidak memerlukan penggantian nama tabel atau kolom. Jangan mengosongkan basis data atau mengulang pengisian data contoh untuk memperbaiki tampilan.
- Laporan harian memilih tanggal lokal WITA dan hanya memakai data tanggal itu. Gunakan kondisi kosong jika data belum ada; jangan mengganti tanggal kosong dengan angka dari hari lain. Grafik serta tabel ringkas di atas masih merupakan cuplikan tanggal yang tertulis di header.

Dari akar repositori:

```sh
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Bila port 8000 sudah melayani dashboard, gunakan server itu. Setelah perubahan Python atau template yang tersimpan di cache, hentikan server lama dengan `Ctrl+C` lalu jalankan lagi. Aset lokal diberi versi melalui tag `aset_versi`; biasanya cukup refresh setelah perubahan aset. Lihat [README dashboard](README.md) untuk inisialisasi basis data dan akun.

Dari folder `frontend/`:

```sh
npm ci
npm run build
```

Jika memilih Node lokal di `.tools/node/bin`, gunakan `PATH="$PWD/../.tools/node/bin:$PATH" npm run build`. `npm ci` diperlukan saat memasang dependensi dari awal atau jika lockfile berubah.
