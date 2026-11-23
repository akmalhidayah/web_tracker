# Ringkasan proyek Tracker Clinker Tonasa

Audit proyek dilakukan pada **23 November 2026 (WITA)**. Peta file ada di [CODE_MAP.md](CODE_MAP.md). Panduan kerja ada di [AGENTS.md](AGENTS.md).

Tracker Clinker Tonasa mempunyai dua aplikasi. **Dashboard admin sudah punya autentikasi dan Data Master yang tersimpan. Aplikasi supir sudah mempunyai alur kerja demo dari login sampai ringkasan sesi. Posisi armada, ritase dan laporan di kedua aplikasi belum tersambung ke data operasional yang sama.**

| Area | Sudah ada | Batas saat ini |
| --- | --- | --- |
| Login dashboard | Login/logout Django, profil, ganti kata sandi, dan User Panel untuk superuser. Login memakai foto pabrik, dua panel, dan tombol lihat kata sandi. | Akun web tidak sekaligus menjadi akun supir Flutter. Dashboard masih dijalankan secara lokal. |
| Data Master | Ekspeditur, warna ikon, truk, nomor lambung, kapasitas, dan pengemudi disimpan di SQLite; akses pengelolaan mengikuti izin Django. | Belum ada kontrak untuk mengirim daftar truk, penugasan supir, atau perubahan master ke Flutter. |
| Monitoring web | Peta besar, ikon warna ekspeditur dan titik status, legenda tetap terlihat, pencarian, filter, daftar armada, detail truk, layar penuh, dan navigasi HP. | Posisi awal berasal dari fixture dan gerak ikon dihitung di browser. Truk baru tanpa fixture dapat muncul tanpa posisi. Tidak ada aliran GPS dari aplikasi supir. |
| Laporan web | Grafik vertikal dan garis ritase, total armada, tabel per ekspeditur, serta tabel harian horizontal dengan kalender WITA. | Grafik atas tetap cuplikan **17 November 2026 pukul 13.00 WITA**. Tabel harian memakai data **13–17 November 2026** dan memilih hari ini secara default. Pada tanggal tanpa data, kondisi kosong memang diharapkan. |
| Aplikasi supir | Pembuka dan panel login, persetujuan, cek kesiapan HP, pilihan truk sesuai vendor demo, sesi, peta, pengiriman simulasi, dan laporan sesi. | Nomor HP/PIN, QR, izin, baterai, GPS, dan konfirmasi kirim masih simulasi. Data sesi dan antreannya hilang ketika aplikasi dimulai ulang atau preview direfresh. |
| Rute bersama | Kedua proyek memakai rute demo Limestone Crusher 2 → Biringkassi. Dashboard menampilkan seluruh armada, Flutter menampilkan truk sesi supir. | Geometri disalin di Python dan Dart. Poligon muat/bongkar Flutter adalah ilustrasi untuk simulasi, sehingga belum boleh dipakai sebagai batas area operasional. |
| Distribusi | Aset ikon baru tersedia untuk dashboard, Flutter web, dan launcher Android. Perintah preview dan build tercatat di README masing-masing. | APK release memakai signing debug. Tidak ada klaim rilis produksi, pelacakan latar sungguhan, atau APK baru dari audit dokumentasi ini. |

## Keputusan yang perlu dijaga

- **Bedakan angka simulasi dan data aktual.** Dashboard memakai cuplikan riwayat yang diinput ke fixture. Flutter menampilkan estimasi muatan dari ritase × kapasitas truk, bukan hasil timbang. Jangan memakai keduanya sebagai data produksi tanpa sumber resmi.
- **Jaga arti waktu.** Tanggal harian dipilih menurut WITA. Waktu dashboard di header mengacu pada cuplikan di bagian atas, bukan tanggal yang dipilih untuk tabel harian. Suatu tanggal tanpa laporan tidak berarti nol produksi.
- **Samakan identitas sebelum menyambung data.** Nomor lambung membantu tampilan demo, tetapi integrasi perlu ID stabil untuk ekspeditur, supir, truk, penugasan, dan sesi. Contoh yang harus dibereskan: kode Prima Karya adalah `prima` di fixture dashboard dan `prima_karya` di Flutter.
- **Pisahkan posisi, status, dan hasil perjalanan.** Posisi terbaru, status operasi, keterlambatan pembaruan, dan ritase adalah hal berbeda. Pergerakan ikon, batas keterlambatan 10 menit di demo, serta durasi tunggu simulator tidak menetapkan aturan produksi.

## Urutan pengerjaan berikutnya

1. **Tetapkan kontrak data induk dan autentikasi supir.** Putuskan cara verifikasi akun/perangkat, ID ekspeditur dan truk, serta bagaimana admin menetapkan unit yang boleh dipakai supir. Selesai bila daftar unit Flutter berasal dari penugasan admin dan aplikasi menolak pilihan di luar penugasan itu.
2. **Bangun jalur sesi dan telemetri.** Tetapkan ID sesi, nomor urut titik, timestamp, akurasi, serta ACK idempoten sebelum menghubungkan GPS Android. Implementasikan antrean yang bertahan saat offline/restart, dan pastikan data ulang tidak menggandakan titik. Selesai bila posisi uji setelah tersambung kembali muncul di Monitoring dan keterlambatannya bisa dibedakan dari status operasi.
3. **Validasi operasi dengan data lapangan.** Sahkan batas geofence dan waktu minimum muat/bongkar, definisi ritase, sumber tonase aktual, dan aturan pembagian hari kerja WITA. Selesai bila beberapa perjalanan uji dapat direkonsiliasi dengan catatan lapangan tanpa menghitung ritase ganda.
4. **Siapkan rilis.** Pilih konfigurasi server, basis data, pengamanan akun, kebijakan akses dan penyimpanan GPS, penyedia tile, serta signing Android. Lakukan uji perangkat nyata untuk izin, background/Doze, kehilangan jaringan, baterai, dan pemulihan setelah restart sebelum menyebutnya siap produksi.

## Pemeriksaan dan repositori

- Versi lokal yang ditemukan: Python **3.12.16**, Django **5.2.19**, Node **22.23.5**, Flutter **3.50.0**, dan Dart **3.14.0**. Paket React dan Flutter punya lockfile; `requirements.txt` mengizinkan Django seri 5.2.
- Saat audit, `manage.py check` lulus, tidak ada perubahan model tanpa migrasi menurut `makemigrations --check --dry-run`, dan migrasi Monitoring `0001` sampai `0003` sudah tercatat di SQLite lokal.
- Suite Flutter sudah tersedia. Audit ini tidak menjalankan suite Flutter, membangun ulang APK/web, atau menguji perangkat nyata.
- Kode tersedia di [repo dashboard](https://github.com/akmalhidayah/web_tracker) dan [repo aplikasi supir](https://github.com/akmalhidayah/mobileapp-tracker).
- Panduan proyek: [README dashboard](README.md) dan [README aplikasi supir](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/README.md). Hand-off dan aset mobile: [HANDOFF.md](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/docs/HANDOFF.md), [ASSETS.md](https://github.com/akmalhidayah/mobileapp-tracker/blob/main/docs/ASSETS.md). Sebagian catatan lama memakai istilah “semen curah” atau menyebut HTMX; implementasi yang ditemukan sekarang adalah Django dengan React/Leaflet pada Monitoring.
