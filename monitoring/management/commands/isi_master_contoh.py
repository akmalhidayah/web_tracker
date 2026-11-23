from django.core.management.base import BaseCommand
from django.db import transaction

from monitoring.data_contoh import EKSPEDITUR, TRUK
from monitoring.models import Ekspeditur, Truk


class Command(BaseCommand):
    help = "Isi data master dari ekspeditur dan truk contoh."

    @transaction.atomic
    def handle(self, *args, **options):
        warna = {
            "fajar": Ekspeditur.Warna.BIRU,
            "koperasi": Ekspeditur.Warna.TOSKA,
            "topabiring": Ekspeditur.Warna.UNGU,
            "prima": Ekspeditur.Warna.JINGGA,
            "tambahan": Ekspeditur.Warna.MERAH_MUDA,
        }
        vendor = {}
        baru_vendor = baru_truk = 0
        for kode, (nama, nama_singkat) in EKSPEDITUR.items():
            # Nama membantu mengenali data master yang kode vendornya telah diubah.
            item = Ekspeditur.objects.filter(kode=kode).first()
            if item is None:
                item, dibuat = Ekspeditur.objects.get_or_create(
                    nama=nama,
                    defaults={
                        "kode": kode,
                        "nama_singkat": nama_singkat,
                        "warna": warna[kode],
                    },
                )
                baru_vendor += dibuat
            vendor[kode] = item

        for nomor, kode, *_ in TRUK:
            _, dibuat = Truk.objects.get_or_create(
                nomor__iexact=nomor,
                defaults={"nomor": nomor, "ekspeditur": vendor[kode], "kapasitas": 30},
            )
            baru_truk += dibuat

        self.stdout.write(self.style.SUCCESS(
            f"Data contoh siap. Ditambahkan: {baru_vendor} ekspeditur dan {baru_truk} truk."
        ))
