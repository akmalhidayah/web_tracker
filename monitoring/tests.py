from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .data_contoh import WAKTU_CONTOH
from .models import AksesVendor, Ekspeditur, PenugasanTruk, Pengemudi, Truk


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DashboardVendorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        pengguna = get_user_model().objects
        cls.admin = pengguna.create_superuser("admin-uji", password="Tonasa-adm-5488")
        cls.vendor = pengguna.create_user("vendor-uji", password="Tonasa-vendor-5842")
        cls.vendor_lain = pengguna.create_user("vendor-lain")
        cls.ekspeditur = Ekspeditur.objects.create(kode="fajar", nama="Armada Satu", nama_singkat="Satu")
        cls.ekspeditur_lain = Ekspeditur.objects.create(kode="prima", nama="Armada Dua", nama_singkat="Dua")
        AksesVendor.objects.create(pengguna=cls.vendor, ekspeditur=cls.ekspeditur)
        AksesVendor.objects.create(pengguna=cls.vendor_lain, ekspeditur=cls.ekspeditur_lain)
        Truk.objects.create(nomor="UJI-01", ekspeditur=cls.ekspeditur)
        Truk.objects.create(nomor="UJI-02", ekspeditur=cls.ekspeditur_lain)

    def test_monitoring_vendor_memuat_armada_sendiri(self):
        self.client.force_login(self.vendor)
        respons = self.client.get(reverse("monitoring:monitoring"), {"ekspeditur": self.ekspeditur_lain.pk})
        self.assertContains(respons, "Dashboard Vendor")
        self.assertContains(respons, "Buat Laporan")
        self.assertContains(respons, "Lihat Laporan")
        self.assertContains(respons, "Data Master")
        self.assertContains(respons, f'href="{reverse("monitoring:master_pengemudi")}" title="Pengemudi"')
        self.assertContains(respons, f'href="{reverse("monitoring:master_nomor_lambung")}" title="Nomor Lambung"')
        self.assertNotContains(respons, 'title="User Panel"')
        self.assertNotContains(respons, 'title="Ekspeditur"')
        self.assertNotContains(respons, self.ekspeditur_lain.nama)
        self.assertEqual([unit["nomor"] for unit in respons.context["peta"]["truk"]], ["UJI-01"])
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 302)

    def test_master_vendor_hanya_menampilkan_data_ekspeditur_akun(self):
        pengemudi = Pengemudi.objects.create(nama="Sopir Satu", ekspeditur=self.ekspeditur)
        Pengemudi.objects.create(nama="Sopir Dua", ekspeditur=self.ekspeditur_lain)
        truk = Truk.objects.get(nomor="UJI-01")
        truk_lain = Truk.objects.get(nomor="UJI-02")
        PenugasanTruk.objects.create(pengemudi=pengemudi, truk=truk)
        PenugasanTruk.objects.create(pengemudi=pengemudi, truk=truk_lain)

        alamat_pengemudi = reverse("monitoring:master_pengemudi")
        alamat_truk = reverse("monitoring:master_nomor_lambung")
        self.assertEqual(self.client.get(alamat_pengemudi).status_code, 302)
        self.client.force_login(self.vendor)
        filter_lain = {"ekspeditur": self.ekspeditur_lain.pk}
        respons = self.client.get(alamat_pengemudi, filter_lain)
        self.assertContains(respons, "Sopir Satu")
        self.assertContains(respons, "UJI-01")
        self.assertNotContains(respons, "Sopir Dua")
        self.assertNotContains(respons, "UJI-02")
        respons = self.client.get(alamat_truk, filter_lain)
        self.assertContains(respons, "UJI-01")
        self.assertNotContains(respons, "UJI-02")
        self.assertContains(self.client.get(alamat_truk, {"q": "UJI-02"}), "Tidak ada data yang cocok")
        self.assertEqual(self.client.post(alamat_pengemudi).status_code, 405)

        self.client.force_login(self.vendor_lain)
        respons = self.client.get(alamat_pengemudi)
        self.assertContains(respons, "Sopir Dua")
        self.assertNotContains(respons, "Sopir Satu")
        respons = self.client.get(alamat_truk)
        self.assertContains(respons, "UJI-02")
        self.assertNotContains(respons, "UJI-01")

    def test_grafik_dan_riwayat_vendor_terbatas_ke_ekspeditur(self):
        self.client.force_login(self.vendor)
        respons = self.client.get(reverse("monitoring:laporan"), {"tanggal": WAKTU_CONTOH.date().isoformat()})
        self.assertEqual([baris["nama"] for baris in respons.context["baris"]], [self.ekspeditur.nama])
        self.assertEqual([baris["nama"] for baris in respons.context["riwayat"]["baris"]], [self.ekspeditur.nama])
        self.assertNotContains(respons, "Prima Karya")

    def test_vendor_menambah_dan_mengubah_nomor_lambung_sendiri(self):
        self.client.force_login(self.vendor)
        tambah = reverse("monitoring:master_nomor_lambung_tambah")
        daftar = reverse("monitoring:master_nomor_lambung")
        truk_lain = Truk.objects.get(nomor="UJI-02")
        ubah_lain = reverse("monitoring:master_nomor_lambung_ubah", args=[truk_lain.pk])
        data = {"nomor": "UJI-03", "plat": "DD 1943 UJ", "kapasitas": "27.5", "aktif": "1",
                "ekspeditur": self.ekspeditur_lain.pk}
        self.assertEqual(self.client.get(ubah_lain).status_code, 404)
        self.assertEqual(self.client.post(ubah_lain, data).status_code, 404)
        self.assertContains(self.client.post(tambah, {**data, "nomor": "uji-02"}), "Nomor lambung ini sudah terdaftar.")

        respons = self.client.post(tambah, data)
        self.assertRedirects(respons, daftar)
        truk = Truk.objects.get(nomor="UJI-03")
        self.assertEqual(truk.ekspeditur, self.ekspeditur)
        self.assertEqual(str(truk.kapasitas), "27.50")
        ubah = reverse("monitoring:master_nomor_lambung_ubah", args=[truk.pk])
        self.assertRedirects(self.client.post(ubah, {**data, "aktif": "", "nomor": "UJI-04"}), daftar)
        truk.refresh_from_db()
        self.assertEqual(truk.nomor, "UJI-04")
        self.assertFalse(truk.aktif)
        self.assertEqual(truk.ekspeditur, self.ekspeditur)

        klien_csrf = Client(enforce_csrf_checks=True)
        klien_csrf.force_login(self.vendor)
        self.assertEqual(klien_csrf.post(tambah, data).status_code, 403)

    def test_vendor_mengelola_pengemudi_dengan_penugasan_dan_login_mobile(self):
        truk1 = Truk.objects.get(nomor="UJI-01")
        truk2 = Truk.objects.create(nomor="UJI-03", ekspeditur=self.ekspeditur)
        truk_lain = Truk.objects.get(nomor="UJI-02")
        sopir_lain = Pengemudi.objects.create(nama="Sopir Lain", ekspeditur=self.ekspeditur_lain)
        tambah = reverse("monitoring:master_pengemudi_tambah")
        daftar = reverse("monitoring:master_pengemudi")
        ubah_lain = reverse("monitoring:master_pengemudi_ubah", args=[sopir_lain.pk])
        data = {"nama": "Sopir Baru", "nomor_hp": "081234567890", "pin_baru": "010203", "aktif": "1",
                "truk_ditugaskan": [truk_lain.pk], "ekspeditur": self.ekspeditur_lain.pk}

        self.client.force_login(self.vendor)
        self.assertNotContains(self.client.get(tambah), truk_lain.nomor)
        self.assertEqual(self.client.get(ubah_lain).status_code, 404)
        self.assertEqual(self.client.post(ubah_lain, data).status_code, 404)
        respons = self.client.post(tambah, data)
        self.assertTrue(respons.context["form"]["truk_ditugaskan"].errors)
        self.assertFalse(Pengemudi.objects.filter(nama=data["nama"]).exists())

        data["truk_ditugaskan"] = [truk1.pk, truk2.pk]
        self.assertRedirects(self.client.post(tambah, data), daftar)
        sopir = Pengemudi.objects.get(nama=data["nama"])
        self.assertEqual(sopir.ekspeditur, self.ekspeditur)
        self.assertEqual(sopir.nomor_hp, "+6281234567890")
        masuk = reverse("api_masuk_sopir")
        login = {"nomor_hp": data["nomor_hp"], "pin": data["pin_baru"], "instalasi": str(uuid4())}
        respons = self.client.post(masuk, login, content_type="application/json")
        self.assertEqual(respons.status_code, 200)
        armada = reverse("api_truk_sopir")
        header = {"HTTP_AUTHORIZATION": f'Bearer {respons.json()["token"]}'}
        self.assertEqual({truk["id"] for truk in self.client.get(armada, **header).json()["truk"]}, {truk1.pk, truk2.pk})

        ubah = reverse("monitoring:master_pengemudi_ubah", args=[sopir.pk])
        data.update(nama="Nama Baru", pin_baru="040506", truk_ditugaskan=[truk2.pk])
        self.assertRedirects(self.client.post(ubah, data), daftar)
        sopir.refresh_from_db()
        self.assertEqual(sopir.nama, "Nama Baru")
        self.assertEqual(sopir.ekspeditur, self.ekspeditur)
        self.assertEqual(self.client.get(armada, **header).status_code, 401)
        self.assertEqual(list(sopir.penugasan_truk.filter(berakhir__isnull=True).values_list("truk_id", flat=True)), [truk2.pk])

    @patch("monitoring.views.timezone.localdate", return_value=WAKTU_CONTOH.date())
    def test_laporan_armada_mengikuti_cakupan_akun(self, _):
        alamat = reverse("monitoring:laporan_armada")
        self.assertEqual(self.client.get(alamat).status_code, 302)

        self.client.force_login(self.vendor)
        respons = self.client.get(alamat, {"ekspeditur": self.ekspeditur_lain.kode})
        self.assertEqual({sesi["nomor"] for sesi in respons.context["sesi"]}, {"DT-31", "DT-32"})
        self.assertNotContains(respons, "DT-07")
        self.assertNotContains(respons, 'aria-label="Filter ekspeditur"')
        respons = self.client.get(alamat, {"q": " dt-32 "})
        self.assertEqual([sesi["nomor"] for sesi in respons.context["sesi"]], ["DT-32"])

        self.client.force_login(self.admin)
        respons = self.client.get(alamat)
        self.assertContains(respons, "DT-07")
        self.assertContains(respons, "DT-32")
        self.assertContains(respons, 'aria-current="true">Semua</a>')

    @patch("monitoring.views.timezone.localdate", return_value=WAKTU_CONTOH.date())
    def test_tab_laporan_armada_admin_mengikuti_filter(self, _):
        self.client.force_login(self.admin)
        tanggal = WAKTU_CONTOH.date().isoformat()
        query = {"tanggal": tanggal, "q": "dt-32", "ekspeditur": self.ekspeditur.kode}
        respons = self.client.get(reverse("monitoring:laporan_armada"), query)
        self.assertEqual([sesi["nomor"] for sesi in respons.context["sesi"]], ["DT-32"])
        self.assertContains(respons, 'aria-current="true">Satu</a>')
        self.assertContains(respons, 'type="hidden" name="ekspeditur" value="fajar"')
        tabs = {tab["label"]: tab["url"] for tab in respons.context["tab_ekspeditur"]}
        self.assertEqual(tabs["Semua"], reverse("monitoring:laporan_armada", query={"tanggal": tanggal, "q": "dt-32"}))
        kosong = self.client.get(tabs["Dua"])
        self.assertEqual(kosong.context["sesi"], [])
        self.assertContains(kosong, 'aria-current="true">Dua</a>')
        semua = self.client.get(tabs["Semua"])
        self.assertEqual([sesi["nomor"] for sesi in semua.context["sesi"]], ["DT-32"])

    @patch("monitoring.views.timezone.localdate", return_value=WAKTU_CONTOH.date())
    def test_laporan_armada_menyaring_tanggal_mulai_wita(self, _):
        self.client.force_login(self.admin)
        alamat = reverse("monitoring:laporan_armada")
        tanggal = WAKTU_CONTOH.date() - timedelta(days=1)
        respons = self.client.get(alamat, {"tanggal": tanggal.isoformat()})
        sesi, = respons.context["sesi"]
        self.assertEqual(sesi["selesai"].date(), WAKTU_CONTOH.date())
        self.assertEqual(sesi["durasi"], "4 j 15 m")
        self.assertContains(respons, 'datetime="2026-11-17T02:30:00+08:00"')

        respons = self.client.get(alamat, {"tanggal": (tanggal - timedelta(days=1)).isoformat()})
        self.assertEqual(respons.context["sesi"], [])
        self.assertContains(respons, "Belum ada data sesi")

    def test_pratinjau_mengikuti_ekspeditur_akun_dan_sesi_login(self):
        self.client.force_login(self.vendor)
        buat = reverse("monitoring:buat_laporan")
        tanggal = timezone.localdate().isoformat()
        data = {
            "tanggal": tanggal, "ready": 5, "operasi": 6, "ritase": 9, "volume": 1234,
            "target_volume": 1400, "target_operasi": 5, "target_ritase": 10,
            "ekspeditur": self.ekspeditur_lain.pk,
        }
        respons = self.client.post(buat, data)
        self.assertContains(respons, "Armada operasi maksimal sebanyak armada ready.")

        respons = self.client.post(buat, {**data, "operasi": 3}, follow=True)
        self.assertRedirects(respons, reverse("monitoring:laporan", query={"tanggal": tanggal}))
        baris, = respons.context["riwayat"]["baris"]
        self.assertEqual(baris["nama"], self.ekspeditur.nama)
        self.assertEqual(baris["metrik"][0]["nilai"], 1234)
        self.assertEqual(baris["rata_ritase"], 3)
        self.assertEqual(respons.context["baris"][0]["utilisasi"], 60)
        self.assertEqual(self.client.get(buat, {"tanggal": tanggal}).context["form"]["volume"].value(), 1234)

        self.client.post(reverse("monitoring:keluar"))
        for pengguna in (self.vendor_lain, self.vendor, self.admin):
            self.client.force_login(pengguna)
            respons = self.client.get(reverse("monitoring:laporan"), {"tanggal": tanggal})
            self.assertIsNone(respons.context["riwayat"]["pratinjau"])

    def test_admin_tetap_melihat_semua_ekspeditur(self):
        self.client.force_login(self.admin)
        respons = self.client.get(reverse("monitoring:monitoring"))
        self.assertContains(respons, "Data Master")
        self.assertContains(respons, "Lihat Laporan")
        self.assertNotContains(respons, "Buat Laporan")
        self.assertEqual(len(respons.context["peta"]["truk"]), 2)
        respons = self.client.get(reverse("monitoring:laporan"), {"tanggal": WAKTU_CONTOH.date().isoformat()})
        self.assertEqual(len(respons.context["riwayat"]["baris"]), 5)
        self.assertEqual(self.client.post(reverse("monitoring:buat_laporan")).status_code, 403)

    def test_akun_tanpa_ekspeditur_aktif_tidak_dapat_membuka_data(self):
        self.ekspeditur.aktif = False
        self.ekspeditur.save(update_fields=["aktif"])
        respons = self.client.post(reverse("monitoring:masuk"), {"username": self.vendor.username, "password": "Tonasa-vendor-5842"})
        self.assertContains(respons, "Akun ini memerlukan Ekspeditur aktif")
        self.client.force_login(self.vendor)
        for menu in ("monitoring", "laporan", "laporan_armada", "buat_laporan", "master_pengemudi", "master_nomor_lambung"):
            self.assertEqual(self.client.get(reverse(f"monitoring:{menu}")).status_code, 403)

    def test_user_panel_menyimpan_peran_dan_wajibkan_ekspeditur_vendor(self):
        self.client.force_login(self.admin)
        tambah = reverse("admin:auth_user_add")
        data = {
            "username": "vendor-baru", "usable_password": "true",
            "password1": "Akun-Baru!-4591", "password2": "Akun-Baru!-4591",
            "is_active": "on", "peran": "vendor",
        }
        respons = self.client.post(tambah, data)
        self.assertContains(respons, "Pilih Ekspeditur untuk akun Vendor.")
        respons = self.client.post(tambah, {**data, "ekspeditur": self.ekspeditur.pk})
        self.assertEqual(respons.status_code, 302)
        vendor = get_user_model().objects.get(username="vendor-baru")
        self.assertFalse(vendor.is_staff)
        self.assertEqual(vendor.akses_vendor.ekspeditur, self.ekspeditur)
        self.assertContains(self.client.get(reverse("admin:auth_user_changelist", query={"is_superuser__exact": "0"})), "vendor-baru")
        ubah = reverse("admin:auth_user_change", args=[vendor.pk])
        data_ubah = {"username": vendor.username, "is_active": "on", "peran": "admin", "date_joined_0": timezone.localdate().isoformat(), "date_joined_1": "08:00:00"}
        self.assertEqual(self.client.post(ubah, data_ubah).status_code, 302)
        vendor.refresh_from_db()
        self.assertTrue(vendor.is_superuser and vendor.is_staff)
        self.assertFalse(AksesVendor.objects.filter(pengguna=vendor).exists())
