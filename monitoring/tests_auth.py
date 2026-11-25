from io import StringIO
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .akun_sopir import atur_pin, simpan_penugasan
from .models import AkunSopir, Ekspeditur, Pengemudi, PenugasanTruk, SesiLoginSopir, Truk


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AutentikasiSopirTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("admin-uji", password="Admin-uji-3456")
        cls.vendor = Ekspeditur.objects.create(kode="satu", nama="Vendor Satu", nama_singkat="Satu")
        cls.lain = Ekspeditur.objects.create(kode="dua", nama="Vendor Dua", nama_singkat="Dua")
        cls.sopir = Pengemudi.objects.create(nama="Sopir Uji", ekspeditur=cls.vendor, nomor_hp="+6281234567890")
        cls.akun = atur_pin(cls.sopir, cls.sopir.nomor_hp, "023456")
        cls.truk = Truk.objects.create(nomor="DT-01", ekspeditur=cls.vendor)
        cls.truk2 = Truk.objects.create(nomor="DT-02", ekspeditur=cls.vendor)
        cls.truk_lain = Truk.objects.create(nomor="DT-03", ekspeditur=cls.lain)
        simpan_penugasan(cls.sopir, {cls.truk.pk, cls.truk2.pk, cls.truk_lain.pk})

    def setUp(self):
        cache.clear()

    def masuk(self, pin="023456"):
        return self.client.post(reverse("api_masuk_sopir"), {
            "nomor_hp": "0812-3456-7890", "pin": pin, "instalasi": str(uuid4()),
        }, content_type="application/json")

    def armada(self, token):
        return self.client.get(reverse("api_truk_sopir"), HTTP_AUTHORIZATION=f"Bearer {token}")

    def kirim_api(self, nama, token, **data):
        return self.client.post(
            reverse(nama), data, content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    def test_login_membatasi_armada_dan_mengganti_perangkat_aktif(self):
        respons = self.masuk()
        self.assertEqual(respons.status_code, 200)
        token_lama = respons.json()["token"]
        self.assertNotEqual(self.akun.sesi_login.token_hash, token_lama)
        nomor = [truk["nomor_lambung"] for truk in self.armada(token_lama).json()["truk"]]
        self.assertEqual(nomor, ["DT-01", "DT-02"])
        token_baru = self.masuk().json()["token"]
        self.assertEqual(SesiLoginSopir.objects.count(), 1)
        self.assertEqual(self.armada(token_lama).status_code, 401)
        self.assertEqual(self.armada(token_baru).status_code, 200)
        self.assertEqual(self.client.post(reverse("api_keluar_sopir"), HTTP_AUTHORIZATION=f"Bearer {token_baru}").status_code, 204)
        self.assertEqual(self.armada(token_baru).status_code, 401)

    def test_sesi_diperpanjang_otomatis_dan_habis_setelah_30_hari_tidak_aktif(self):
        hari_pertama = timezone.now()
        with patch("monitoring.akun_sopir.timezone.now", return_value=hari_pertama):
            token = self.masuk().json()["token"]
        self.assertEqual(self.akun.sesi_login.kedaluwarsa, hari_pertama + timedelta(days=30))
        besok = hari_pertama + timedelta(days=1, hours=2)
        with patch("monitoring.api_sopir.timezone.now", return_value=besok):
            self.assertEqual(self.kirim_api("api_sesi_sopir", token).status_code, 200)
        self.akun.sesi_login.refresh_from_db()
        self.assertEqual(self.akun.sesi_login.kedaluwarsa, besok + timedelta(days=30))
        with patch("monitoring.api_sopir.timezone.now", return_value=besok + timedelta(days=30)):
            self.assertEqual(self.kirim_api("api_sesi_sopir", token).status_code, 401)

    def test_persetujuan_per_versi_bertahan_di_perangkat_baru(self):
        masuk = self.masuk().json()
        token = masuk["token"]
        versi = masuk["versi_persetujuan"]
        self.assertFalse(masuk["sudah_setuju"])
        self.assertEqual(self.kirim_api("api_setuju_sopir", token, versi=versi + 1).status_code, 409)
        for _ in range(2):
            self.assertEqual(self.kirim_api("api_setuju_sopir", token, versi=versi).status_code, 204)
        self.assertEqual(self.akun.persetujuan.count(), 1)
        self.assertIsNotNone(self.akun.persetujuan.get().disetujui_pada)
        self.assertEqual(self.kirim_api("api_keluar_sopir", token).status_code, 204)
        self.assertEqual(self.kirim_api("api_sesi_sopir", token).status_code, 401)
        baru = self.masuk().json()
        self.assertTrue(baru["sudah_setuju"])
        with patch("monitoring.api_sopir.VERSI_PERSETUJUAN_SOPIR", versi + 1):
            self.assertFalse(self.kirim_api("api_sesi_sopir", baru["token"]).json()["sudah_setuju"])

    def test_pemulihan_hanya_mengingat_truk_yang_masih_ditugaskan(self):
        token = self.masuk().json()["token"]
        self.assertEqual(self.kirim_api("api_pilih_truk_sopir", token, truk_id=self.truk.pk).status_code, 204)
        self.assertEqual(self.kirim_api("api_pilih_truk_sopir", token, truk_id=self.truk_lain.pk).status_code, 409)
        self.assertEqual(self.kirim_api("api_sesi_sopir", token).json()["truk_terpilih_id"], self.truk.pk)
        simpan_penugasan(self.sopir, {self.truk2.pk})
        profil = self.kirim_api("api_sesi_sopir", token).json()
        self.assertIsNone(profil["truk_terpilih_id"])
        self.assertEqual([unit["id"] for unit in profil["truk"]], [self.truk2.pk])
        self.sopir.aktif = False
        self.sopir.save(update_fields=["aktif"])
        self.assertEqual(self.kirim_api("api_sesi_sopir", token).status_code, 401)

    def test_pin_salah_dibatasi_dan_akun_nonaktif_gagal_login(self):
        for _ in range(4):
            self.assertEqual(self.masuk("999999").status_code, 401)
        self.assertEqual(self.masuk("999999").status_code, 429)
        self.assertEqual(self.masuk().status_code, 429)
        self.sopir.aktif = False
        self.sopir.save(update_fields=["aktif"])
        self.assertEqual(self.masuk().status_code, 401)

    def test_sesi_web_tidak_memberi_akses_ke_api_sopir(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("api_truk_sopir")).status_code, 401)

    @override_settings(ROOT_URLCONF="config.urls_sopir")
    def test_server_uji_di_wifi_hanya_menerima_api_sopir(self):
        respons = self.masuk()
        self.assertEqual(respons.status_code, 200)
        self.assertEqual(self.armada(respons.json()["token"]).status_code, 200)
        for alamat in ("/", "/masuk/", "/admin/"):
            self.assertEqual(self.client.get(alamat).status_code, 404)

    def test_admin_dapat_mereset_pin_dan_memilih_banyak_nomor_lambung(self):
        token = self.masuk().json()["token"]
        self.client.force_login(self.admin)
        ubah = reverse("admin:monitoring_pengemudi_change", args=[self.sopir.pk])
        data = {"nama": self.sopir.nama, "nomor_hp": "081234567890", "ekspeditur": self.vendor.pk,
                "aktif": "on", "pin_baru": "654321", "truk_ditugaskan": [self.truk_lain.pk]}
        self.assertContains(self.client.post(ubah, data), "Pilih truk dari Ekspeditur pengemudi ini.")
        self.assertEqual(self.client.post(ubah, {**data, "truk_ditugaskan": [self.truk.pk, self.truk2.pk]}).status_code, 302)
        self.akun.refresh_from_db()
        self.assertTrue(check_password("654321", self.akun.pin_hash))
        self.assertEqual(self.armada(token).status_code, 401)
        aktif = PenugasanTruk.objects.filter(pengemudi=self.sopir, berakhir__isnull=True)
        self.assertEqual(set(aktif.values_list("truk_id", flat=True)), {self.truk.pk, self.truk2.pk})


class AkunContohTests(TestCase):
    @override_settings(DEBUG=True, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
    @patch.dict("os.environ", {"TRACKER_DEMO_PASSWORD": "Khusus-Data-Uji-345"})
    def test_seed_semua_peran_tanpa_menimpa_data(self):
        for _ in range(2):
            call_command("isi_akun_contoh", stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 6)
        self.assertEqual(AkunSopir.objects.count(), 5)
        self.assertEqual(PenugasanTruk.objects.count(), 10)

        masuk = reverse("monitoring:masuk")
        with self.subTest(peran="admin"):
            respons = self.client.post(masuk, {"username": "demo-admin", "password": "Khusus-Data-Uji-345"}, follow=True)
            self.assertContains(respons, "Dashboard Admin")
            self.assertEqual(len(respons.context["peta"]["truk"]), 10)
            self.client.post(reverse("monitoring:keluar"))

        for kode, nomor_hp, lambung in (
            ("topabiring", "081234567890", {"DT-03", "DT-07"}),
            ("fajar", "081234567891", {"DT-31", "DT-32"}),
            ("koperasi", "081234567892", {"DT-51", "DT-52"}),
            ("prima", "081234567893", {"DT-61", "DT-63"}),
            ("tambahan", "081234567894", {"DT-91", "DT-92"}),
        ):
            with self.subTest(ekspeditur=kode):
                respons = self.client.post(masuk, {"username": f"demo-vendor-{kode}", "password": "Khusus-Data-Uji-345"}, follow=True)
                self.assertContains(respons, "Dashboard Vendor")
                self.assertEqual({truk["nomor"] for truk in respons.context["peta"]["truk"]}, lambung)
                self.client.post(reverse("monitoring:keluar"))

                respons = self.client.post(reverse("api_masuk_sopir"), {
                    "nomor_hp": nomor_hp, "pin": "123456", "instalasi": str(uuid4()),
                }, content_type="application/json")
                self.assertEqual(respons.status_code, 200)
                token = respons.json()["token"]
                respons = self.client.get(reverse("api_truk_sopir"), HTTP_AUTHORIZATION=f"Bearer {token}")
                self.assertEqual({truk["nomor_lambung"] for truk in respons.json()["truk"]}, lambung)
