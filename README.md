# Dashboard Admin Tracker Clinker Tonasa

Dashboard pengiriman clinker dari CP Tonasa ke Biringkassi. Django 5.2 mengelola login, akun pengguna, dan data master di SQLite. React dan Leaflet mengelola peta simulasi dan daftar truk.

## Menjalankan di Mac

Dari folder dashboard hasil clone (`web_tracker`) atau folder `dashboard_admin` di workspace Tracker Tonasa, jalankan perintah berikut untuk penyiapan awal. Jika `.venv` sudah disiapkan, mulai dari `migrate`.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py isi_master_contoh
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Buka `http://127.0.0.1:8000/masuk/` dan gunakan akun yang dibuat lewat `createsuperuser`. Untuk menjalankan kembali pada hari berikutnya, cukup jalankan `runserver`. Tekan `Ctrl+C` untuk menghentikan server.

## Akun dan data master

- Kelola nama, email, dan kata sandi melalui menu akun di kanan atas → **Profil Saya**.
- **Data Master → User Panel** tersedia untuk superuser. Gunakan submenu ini untuk membuat akun, mengganti kata sandi, menonaktifkan akun, atau menetapkan hak akses. Pengguna biasa dapat membuka Monitoring dan Laporan.
- **Data Master** menyimpan ekspeditur dan warna ikon, truk beserta nomor lambungnya, serta pengemudi. Superuser dapat mengelola semuanya. Untuk mendelegasikan pengelolaan, aktifkan status staf dan berikan izin untuk model yang diperlukan.
- Database lokal tersimpan di `db.sqlite3`. Perintah `isi_master_contoh` menambahkan lima ekspeditur dan sepuluh truk demo. Direktori pengemudi siap diisi dari data operasional.

## Monitoring dan laporan

- **Monitoring** membaca daftar dan warna truk aktif dari Data Master. Sepuluh truk demo memiliki posisi simulasi. Truk baru dengan nomor lambung lain tampil di daftar dengan status **Belum ada posisi**. Ikon truk bermuatan bergerak ke area bongkar dan truk kosong kembali ke area muat. Pencarian dan filter memperbarui peta dan daftar sekaligus. Posisi dengan data lebih dari 10 menit ditandai abu-abu, berdasarkan waktu cuplikan.
- Pin **Muat** dan **Bongkar** memakai pasangan lintang dan bujur dari mapping manual di daftar `AREA` dalam `monitoring/data_contoh.py`.
- Rute demo menghubungkan kedua pin dengan data jalan OpenStreetMap yang dihitung oleh [OSRM/FOSSGIS](https://routing.openstreetmap.de/about.html). Penghubung pendek dari jalan ke masing-masing pin adalah ilustrasi.
- **Laporan** memakai cuplikan 17 November 2026 pukul 13.00 WITA. Angka operasi, utilisasi, dan tonase berasal dari tabel laporan yang diberikan. Volume ditampilkan dalam ton penuh.
- Peta dasar ringkas memakai data OpenStreetMap lewat OpenFreeMap. Tombol **Detail peta** menampilkan peta standar OpenStreetMap, yang juga menjadi cadangan jika peta ringkas tidak tersedia. Peta dasar memerlukan koneksi internet; rute, area, dan ikon simulasi tetap tersedia dari proyek.
- Legenda di kanan bawah peta selalu menampilkan warna ekspeditur dan status. Gunakan **Layar penuh** untuk memperbesar peta, lalu klik **Keluar layar penuh** atau tekan `Esc` untuk kembali.

## Mengubah komponen React

Hasil build JavaScript dan CSS ada di `monitoring/static/monitoring/app/`, sehingga preview cukup dijalankan dengan Django. Setelah mengedit `frontend/src/`, gunakan Node.js dan jalankan:

```sh
cd frontend
npm ci
npm run build
```

Di Mac ini Node.js juga tersedia di `.tools/node/bin`. Dari folder `frontend`, jalankan `PATH="$PWD/../.tools/node/bin:$PATH" npm run build` jika `npm` belum ada di PATH.

## Struktur

| Lokasi | Isi |
|---|---|
| `config/` | Pengaturan proyek, URL, dan WSGI |
| `monitoring/models.py` | Model ekspeditur, truk, dan pengemudi |
| `monitoring/admin.py` | Halaman pengelolaan dan izin administrator |
| `monitoring/data_contoh.py` | Data contoh posisi armada dan cuplikan laporan |
| `monitoring/templates/` | HTML monitoring, laporan, dan navigasi bersama |
| `templates/admin/` | Tampilan pengelolaan Django dengan tema dashboard |
| `frontend/src/` | Sumber komponen React |
| `monitoring/static/` | CSS, ikon, dan logo |
