import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from monitoring.akun_sopir import atur_pin, nomor_hp_login, simpan_penugasan
from monitoring.data_contoh import EKSPEDITUR, TRUK
from monitoring.models import AksesVendor, AkunSopir, Ekspeditur, Pengemudi, Truk


# Nama dan nomor akun dari DummyData aplikasi sopir.
SOPIR = (
    ("Rahmat", "081234567890", "topabiring"),
    ("Hasan", "081234567891", "fajar"),
    ("Yusuf", "081234567892", "koperasi"),
    ("Andi", "081234567893", "prima"),
    ("Dedi", "081234567894", "tambahan"),
)


class Command(BaseCommand):
    help = "Siapkan akun Admin, Vendor, dan Sopir contoh untuk dashboard lokal."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Akun contoh hanya dapat dibuat pada konfigurasi pengembangan.")
        sandi_web = os.environ.get("TRACKER_DEMO_PASSWORD", "")
        if len(sandi_web) < 12:
            raise CommandError("Isi TRACKER_DEMO_PASSWORD dengan sandi baru minimal 12 karakter.")

        call_command("isi_master_contoh", stdout=self.stdout)
        pengguna = get_user_model().objects
        web_baru = 0
        admin, dibuat = pengguna.get_or_create(username="demo-admin", defaults={
            "first_name": "Admin Demo", "is_staff": True, "is_superuser": True,
        })
        if dibuat:
            admin.set_password(sandi_web)
            admin.save(update_fields=["password"])
            web_baru += 1

        vendor = {
            kode: Ekspeditur.objects.filter(kode=kode).first() or Ekspeditur.objects.get(nama=nama)
            for kode, (nama, _) in EKSPEDITUR.items()
        }
        for kode, ekspeditur in vendor.items():
            akun, dibuat = pengguna.get_or_create(username=f"demo-vendor-{kode}", defaults={
                "first_name": ekspeditur.nama_singkat,
            })
            if dibuat:
                akun.set_password(sandi_web)
                akun.save(update_fields=["password"])
                AksesVendor.objects.create(pengguna=akun, ekspeditur=ekspeditur)
                web_baru += 1

        sopir_baru = 0
        for nama, hp, kode in SOPIR:
            nomor = nomor_hp_login(hp)
            if AkunSopir.objects.filter(nomor_hp=nomor).exists() or Pengemudi.objects.filter(nomor_hp__in=(hp, nomor)).exists():
                continue
            pengemudi = Pengemudi.objects.create(nama=nama, nomor_hp=nomor, ekspeditur=vendor[kode])
            atur_pin(pengemudi, nomor, "123456")
            lambung = [nomor for nomor, owner, *_ in TRUK if owner == kode]
            armada = Truk.objects.filter(nomor__in=lambung, aktif=True, ekspeditur=vendor[kode])
            simpan_penugasan(pengemudi, set(armada.values_list("pk", flat=True)))
            sopir_baru += 1

        self.stdout.write(self.style.SUCCESS(f"Akun baru: {web_baru} web dan {sopir_baru} sopir."))
