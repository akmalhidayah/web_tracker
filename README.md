# Dashboard Admin Tracker Clinker Tonasa

Dashboard pengiriman clinker dari CP Tonasa ke Biringkassi. Django 5.2 mengelola login web, API login sopir, dan data master di SQLite. React dan Leaflet mengelola peta simulasi dan daftar truk.

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
- **Data Master → User Panel** menyediakan pilihan **Admin** dan **Vendor**. Pilih satu Ekspeditur untuk tiap akun Vendor. Vendor dapat membuka **Monitoring**, **Buat Laporan**, dan **Lihat Laporan** untuk Ekspeditur tersebut.
- **Data Master** menyimpan ekspeditur dan warna ikon, truk beserta nomor lambungnya, serta pengemudi. Pengelolaan Data Master dan User Panel tersedia untuk Admin.
- Di **Data Master → Pengemudi**, Admin dapat mengatur nomor HP, PIN enam digit, dan beberapa nomor lambung dari Ekspeditur yang sama. Biarkan **PIN baru** kosong saat memperbarui data tanpa mengganti PIN.
- Database lokal tersimpan di `db.sqlite3`. Perintah `isi_master_contoh` menambahkan lima ekspeditur dan sepuluh truk demo.

### Akun contoh lokal

Setelah migrasi, jalankan perintah ini dalam mode pengembangan. Ganti nilai `TRACKER_DEMO_PASSWORD` dengan sandi demo pilihan Anda, minimal 12 karakter.

```sh
TRACKER_DEMO_PASSWORD='ganti-dengan-sandi-demo' .venv/bin/python manage.py isi_akun_contoh
```

Perintah ini mengisi Data Master, akun `demo-admin`, akun `demo-vendor-{topabiring,fajar,koperasi,prima,tambahan}`, dan lima akun sopir bernomor `081234567890` hingga `081234567894` dengan PIN `123456`. Akun dan penugasan yang sudah ada dipertahankan saat perintah dijalankan ulang.

Flutter memakai `POST /api/v1/driver/login/` dengan `nomor_hp`, `pin`, dan UUID `instalasi`. Token dari respons dipakai sebagai bearer. `POST /api/v1/driver/session/` memeriksa status akun dan penugasan serta memperbarui batas 30 hari. `POST /api/v1/driver/consent/` mencatat persetujuan per versi dengan waktu dari Django. `POST /api/v1/driver/selected-truck/` menyimpan pilihan nomor lambung yang masih ditugaskan. Login baru atau `POST /api/v1/driver/logout/` mencabut token sebelumnya.

Saat memperbarui teks persetujuan, naikkan versi di `monitoring/akun_sopir.py` dan `lib/data/services/akun_sopir_api.dart` pada repo aplikasi sopir, lalu rilis bersama. Versi baru meminta persetujuan ulang. Terapkan migrasi Django sebelum menjalankan build aplikasi dengan alur ini.

### Uji iPhone lewat Wi-Fi

Pada Mac dan iPhone yang terhubung ke Wi-Fi yang sama, jalankan proses API berikut
dari root dashboard. Proses ini memakai `db.sqlite3` yang sama dengan dashboard.

```sh
IP_MAC=$(ipconfig getifaddr en0)
DJANGO_SOPIR_DEV_ONLY=1 DJANGO_ALLOWED_HOSTS="$IP_MAC" \
  .venv/bin/python manage.py runserver "$IP_MAC:8001" --noreload --nostatic
```

Gunakan `AUTH_API_URL=http://IP_MAC:8001` pada build debug iPhone, dengan
`IP_MAC` diganti alamat dari perintah di atas. Port `8001` hanya melayani API sopir.
Untuk pengujian HTTP lokal, gunakan akun contoh.

## Monitoring dan laporan

- **Monitoring** membaca daftar dan warna truk aktif dari Data Master. Sepuluh truk demo memiliki posisi simulasi. Truk baru dengan nomor lambung lain tampil di daftar dengan status **Belum ada posisi**. Ikon truk bermuatan bergerak ke area bongkar dan truk kosong kembali ke area muat. Pencarian dan filter memperbarui peta dan daftar sekaligus. Posisi dengan data lebih dari 10 menit ditandai abu-abu, berdasarkan waktu cuplikan.
- Pin **Muat** dan **Bongkar** memakai pasangan lintang dan bujur dari mapping manual di daftar `AREA` dalam `monitoring/data_contoh.py`.
- Rute demo menghubungkan kedua pin dengan data jalan OpenStreetMap yang dihitung oleh [OSRM/FOSSGIS](https://routing.openstreetmap.de/about.html). Penghubung pendek dari jalan ke masing-masing pin adalah ilustrasi.
- **Lihat Laporan** memakai cuplikan 17 November 2026 pukul 13.00 WITA. Angka operasi, utilisasi, dan tonase berasal dari tabel laporan yang diberikan. Volume ditampilkan dalam ton penuh. Vendor dapat menyimpan pratinjau untuk tanggal yang dipilih selama sesi login. Pratinjau ini hanya tersedia di sesi vendor yang membuatnya.
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
