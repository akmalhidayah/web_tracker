# Peta kode Tracker Clinker Tonasa

Dokumen ini memetakan kode dashboard admin dan aplikasi supir. Untuk perintah kerja, baca [AGENTS.md](AGENTS.md). Untuk status integrasi, baca [RINGKASAN.md](RINGKASAN.md).

## Gambaran aliran data

```text
Dashboard admin
Browser → URL Django → sesi/izin → view → template HTML
                                  ├─ SQLite: akun, ekspeditur, truk, pengemudi
                                  └─ data_contoh.py: posisi simulasi, rute, angka laporan
        HTML halaman Monitoring → JSON data-armada → React → Leaflet

Aplikasi supir
Widget Flutter → AppScope / AppState → TrackingService
                                     └─ FakeTrackingService → snapshot & ringkasan
                                                             └─ MesinRitase
```

Keduanya memakai rute demo yang sama, tetapi belum bertukar data. Permintaan jaringan untuk peta dasar berasal dari masing-masing klien.

## Dashboard admin

| Bagian | Titik masuk | Alur dan catatan |
| --- | --- | --- |
| Konfigurasi | [config/settings.py](config/settings.py), [config/urls.py](config/urls.py), [manage.py](manage.py) | Django, aplikasi `monitoring`, SQLite, `Asia/Makassar`, bahasa Indonesia, template dan aset statis. Nama variabel lingkungan untuk konfigurasi: `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_DB_PATH`. |
| Login dan logout | [monitoring/urls.py](monitoring/urls.py), [monitoring/forms.py](monitoring/forms.py), [masuk.html](monitoring/templates/monitoring/masuk.html) | `/masuk/` memakai `LoginView` dan `MasukForm`; sukses kembali ke tujuan valid atau ke Monitoring. `/keluar/` memakai `LogoutView` via POST. Form akun web menggunakan data dan sesi Django. |
| Profil dan sandi | [monitoring/views.py](monitoring/views.py), [profil.html](monitoring/templates/monitoring/profil.html), [sandi.html](monitoring/templates/monitoring/sandi.html) | `/profil/` mengubah nama serta email pengguna yang sedang login; `/profil/ganti-sandi/` memakai mekanisme ganti sandi Django. |
| Tampilan daftar Data Master | [monitoring/panel.py](monitoring/panel.py), [change_list.html](templates/admin/change_list.html), [panel_hero.html](monitoring/templates/monitoring/partials/panel_hero.html), bagian "Panel pengelolaan" di [admin.css](monitoring/static/monitoring/admin.css) | `PanelAdminMixin` menambah kartu ringkasan, tab penyaring dengan jumlah, dan kolom aksi ke Ekspeditur, Truk, Pengemudi, User, dan Grup. Kartu judul yang sama tampil di halaman daftar dan formulir. Parameter tab memakai nama filter bawaan admin, jadi harus ada di `list_filter`. |
| Data Master | [monitoring/models.py](monitoring/models.py), [monitoring/admin.py](monitoring/admin.py), [templates/admin/base.html](templates/admin/base.html) | `Ekspeditur` menyimpan kode, warna, dan status aktif. `Truk` dan `Pengemudi` terkait ke ekspeditur. Relasi ekspeditur dilindungi dari penghapusan jika masih dirujuk. Pengemudi belum terhubung ke akun login Flutter. |
| User Panel | [monitoring/admin.py](monitoring/admin.py), [templatetags/navigasi.py](monitoring/templatetags/navigasi.py) | Di bawah Data Master; pengelolaan User dan Group memakai kelas admin yang membatasi akses ke superuser. Master lain memakai izin Django. Nama model internal `Ekspeditur` dipakai untuk rute admin. |
| Skema dan seed | [monitoring/migrations/](monitoring/migrations/), [isi_master_contoh.py](monitoring/management/commands/isi_master_contoh.py) | Migrasi `0001` membuat model. `0002` dan `0003` mencatat perubahan istilah tampilan. Perintah seed menyiapkan ekspeditur dan truk contoh, bukan sumber telemetri atau laporan produksi. |
| Kerangka halaman | [base.html](monitoring/templates/monitoring/base.html), [topbar.html](monitoring/templates/monitoring/partials/topbar.html), [sidebar.html](monitoring/templates/monitoring/partials/sidebar.html) | Header dan sidebar dipakai bersama halaman web dan admin. `navigasi.js` menangani panel menu HP, penutupan dari luar, dan pilihan buka/tutup di desktop. |
| Gaya dan ikon | [dashboard.css](monitoring/static/monitoring/dashboard.css), [admin.css](monitoring/static/monitoring/admin.css), [aset.py](monitoring/templatetags/aset.py) | Tema merah dan konten putih; foto login `login-tonasa.avif` berasal dari `start-bg.avif`. Ikon merek `tracker-icon.png` dibedakan dari favicon, logo SIG/Semen Tonasa, dan SVG truk. `aset_versi` memasukkan versi aset berdasarkan waktu modifikasi. |

### Monitoring

1. `monitoring()` di [views.py](monitoring/views.py) mengambil ekspeditur dan truk aktif dari SQLite. [data_contoh.py](monitoring/data_contoh.py) menyusun fixture posisi berdasarkan nomor lambung, serta rute `RUTE` dan titik `AREA`. Truk aktif tanpa posisi contoh tetap masuk daftar.
2. [monitoring.html](monitoring/templates/monitoring/monitoring.html) menanam JSON `data-armada` dan memuat bundel React. [monitoring.jsx](frontend/src/monitoring.jsx) mengelola ringkasan, pencarian, filter ekspeditur/status, pilihan truk, legenda, dan kontrol layar penuh.
3. [gerak_armada.js](frontend/src/gerak_armada.js) memindahkan ikon truk demo di lintasan; posisi itu hanya berubah di browser. [peta_ringkas.js](frontend/src/peta_ringkas.js) menggambar tile vektor OpenFreeMap dengan Canvas. Mode Detail dan fallback memakai tile raster OpenStreetMap.
4. [frontend/build.mjs](frontend/build.mjs) membundel JS/CSS ke `monitoring/static/monitoring/app/`. Tidak ada server React terpisah untuk preview biasa.

### Laporan

| Bagian | Sumber |
| --- | --- |
| Judul, waktu, tabel ringkas | [laporan.html](monitoring/templates/monitoring/laporan.html) dan `laporan()` di [views.py](monitoring/views.py) |
| Grafik batang vertikal, garis ritase, dan grafik total | [grafik_laporan.py](monitoring/grafik_laporan.py), [grafik_armada.html](monitoring/templates/monitoring/partials/grafik_armada.html), [batang_laporan.html](monitoring/templates/monitoring/partials/batang_laporan.html) |
| Kalender dan tabel harian `?tanggal=YYYY-MM-DD` | [riwayat_laporan.py](monitoring/riwayat_laporan.py), [riwayat_armada.html](monitoring/templates/monitoring/partials/riwayat_armada.html), [baris_laporan_harian.html](monitoring/templates/monitoring/partials/baris_laporan_harian.html) |
| Fixture dan target | [data_contoh.py](monitoring/data_contoh.py): `LAPORAN`, `LAPORAN_HARIAN`, `TARGET_RITASE_CONTOH`, dan `WAKTU_CONTOH` |

Grafik dan tabel ringkas memakai cuplikan 17 November 2026 pukul 13.00 WITA. Kalender hanya mengubah tabel harian. Tabel harian menampilkan satu baris per ekspeditur dan total; rata-rata ritase = ritase ÷ unit operasi, muatan per ritase = volume ÷ ritase, dan capaian = realisasi ÷ target. Nilai yang tidak dapat dihitung tampil sebagai **—**.

## Aplikasi supir

| Bagian | Titik masuk | Alur dan catatan |
| --- | --- | --- |
| Bootstrap | [lib/main.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/main.dart), [lib/app/app_scope.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/app/app_scope.dart) | `AplikasiSupir` membuat `AppState` dengan `FakeTrackingService`; widget mendapat state melalui `AppScope`. |
| Rute dan penjagaan alur | [nama_rute.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/app/nama_rute.dart), [routes.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/app/routes.dart), [app_state.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/state/app_state.dart) | `lindungiRute` menyesuaikan layar dengan login, persetujuan, kesiapan, truk, dan sesi. Rute debug dan galeri hanya terbuka di build debug. |
| Pembuka dan login | [features/awal/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/features/awal), [features/masuk/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/features/masuk) | `LayarAwal` membuka panel login. `AppState.masuk` mencocokkan nomor dengan akun demo, bukan dengan Django. |
| Persetujuan dan kesiapan | [features/persetujuan/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/features/persetujuan), [features/kesiapan/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/features/kesiapan) | Ketentuan privasi dan pengaturan HP demo disimpan dalam state runtime. Tombol di layar kesiapan tidak mengubah izin perangkat sungguhan. |
| Armadanya supir | [features/pilih_truk/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/features/pilih_truk), [features/beranda/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/features/beranda), [dummy_data.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/data/dummy/dummy_data.dart) | Daftar truk disaring menurut vendor akun demo. QR adalah simulasi pemilihan unit. `AppState.bolehMulai` memeriksa semua syarat sesi. |
| Sesi dan ringkasan | [layar_sesi.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/features/sesi_aktif/layar_sesi.dart), [layar_ringkasan.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/features/ringkasan/layar_ringkasan.dart) | Sesi membaca `SnapshotSesi`, menampilkan status dan pengiriman simulasi, lalu menghasilkan `RingkasanSesi`. Ringkasan menampilkan tanggal, durasi, ritase, dan estimasi muatan. |
| Peta | [peta_sesi.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/features/peta/peta_sesi.dart), [layar_peta.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/features/peta/layar_peta.dart), [kontrol_peta.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/features/peta/kontrol_peta.dart) | Peta mini dan layar peta penuh, ikuti truk, perbesar seluruh rute, legenda dan filter warna tile. `KonfigurasiPeta` menyediakan `TANPA_TILE` dan `TILE_URL`. |
| Kontrak layanan | [tracking_service.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/data/services/tracking_service.dart), [fake_tracking_service.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/data/services/fake_tracking_service.dart), [konfigurasi_simulasi.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/data/services/konfigurasi_simulasi.dart) | Layanan demo membuat snapshot dengan waktu virtual, antrean dan konfirmasi kirim (ACK) di memori, serta mengelola sesi selesai/manual/otomatis. Adapter nyata kelak masuk lewat kontrak ini. |
| Aturan ritase | [mesin_ritase.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/data/services/mesin_ritase.dart), [lib/data/models/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/data/models), [geo.dart](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/lib/core/utils/geo.dart) | Transisi memerlukan urutan muat → bermuatan → bongkar → keluar; cek posisi dalam area, akurasi, waktu berhenti, dan jeda data. Poligon pada fixture belum geofence resmi. |
| Desain bersama | [lib/core/theme/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/core/theme), [lib/core/widgets/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/lib/core/widgets) | Warna, tipografi, ukuran, komponen UI dan logo. `BingkaiHp` membatasi lebar Flutter web ke 430 px. |
| Rilis dan aset | [pubspec.yaml](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/pubspec.yaml), [web/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/web), [android/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/android), [scripts/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/scripts) | Launcher Android legacy/adaptive, favicon dan manifest web berada di proyek ini. Build release Android masih memakai signing debug untuk demo. |
| Pengujian | [test/](https://github.com/akmalhidayah/mobileapp-tracker/tree/main/test) | `app_state_test.dart`: aturan alur. `alur_widget_test.dart`: layar dan interaksi. `fake_tracking_service_test.dart`: waktu, ritase, jeda, antrean dan ACK simulasi. Ada juga tes format dan kontras. |

### Titik perubahan yang sering dicari

| Jika ingin mengubah… | Mulai di… |
| --- | --- |
| Sidebar, login, dan tema web | Partial Django dan CSS biasa dashboard; login web supir adalah halaman Flutter yang berbeda. |
| Peta di halaman Monitoring | `frontend/src/monitoring.jsx` dan `dashboard.css`; build ulang jika JSX berubah. |
| Titik Muat/Bongkar atau jalur demo | `AREA`/`RUTE` di Python dan `titikMuat`/`titikBongkar`/`ruteHauling` di Dart. |
| Sumber angka laporan harian | `LAPORAN_HARIAN` dan `riwayat_laporan.py`; jangan isi tanggal tanpa catatan dengan cuplikan lama. |
| Beralih dari demo ke API | Tambahkan kontrak API Django dan adapter Flutter melalui `TrackingService`; pindahkan master akun dan penugasan sebelum mengandalkan laporan aktual. |
