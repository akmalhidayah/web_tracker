from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Ekspeditur(models.Model):
    class Warna(models.TextChoices):
        BIRU = "#1754b1", "Biru"
        TOSKA = "#056c65", "Toska"
        UNGU = "#743aa5", "Ungu"
        JINGGA = "#96420d", "Jingga"
        MERAH_MUDA = "#9c3059", "Merah muda"
        ABU = "#475569", "Abu"

    kode = models.SlugField(max_length=32, unique=True)
    nama = models.CharField(max_length=150, unique=True)
    nama_singkat = models.CharField(max_length=40)
    warna = models.CharField(max_length=7, choices=Warna.choices, default=Warna.ABU)
    aktif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "ekspeditur"
        verbose_name_plural = "ekspeditur"
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class AksesVendor(models.Model):
    pengguna = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="akses_vendor"
    )
    ekspeditur = models.ForeignKey(Ekspeditur, on_delete=models.PROTECT)


class Truk(models.Model):
    nomor = models.CharField("Nomor lambung", max_length=32, unique=True)
    ekspeditur = models.ForeignKey(Ekspeditur, on_delete=models.PROTECT)
    plat = models.CharField("Nomor polisi", max_length=24, blank=True)
    kapasitas = models.DecimalField(
        "Kapasitas (ton)",
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "truk"
        verbose_name_plural = "truk"
        ordering = ["nomor"]
        constraints = [
            models.UniqueConstraint(models.functions.Lower("nomor"), name="nomor_truk_unik")
        ]

    def __str__(self):
        return self.nomor


class Pengemudi(models.Model):
    nama = models.CharField(max_length=120)
    ekspeditur = models.ForeignKey(Ekspeditur, on_delete=models.PROTECT)
    nomor_hp = models.CharField("Nomor HP", max_length=24, blank=True)
    aktif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "pengemudi"
        verbose_name_plural = "pengemudi"
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class AkunSopir(models.Model):
    pengemudi = models.OneToOneField(Pengemudi, on_delete=models.CASCADE, related_name="akun_sopir")
    nomor_hp = models.CharField(max_length=16, unique=True)
    pin_hash = models.CharField(max_length=128)
    percobaan_gagal = models.PositiveSmallIntegerField(default=0)
    terkunci_sampai = models.DateTimeField(null=True, blank=True)
    truk_terpilih = models.ForeignKey(Truk, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_authenticated(self):
        return True


class PersetujuanSopir(models.Model):
    akun = models.ForeignKey(AkunSopir, on_delete=models.CASCADE, related_name="persetujuan")
    versi = models.PositiveSmallIntegerField()
    disetujui_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("akun", "versi"), name="persetujuan_sopir_per_versi"),
        ]


class SesiLoginSopir(models.Model):
    akun = models.OneToOneField(AkunSopir, on_delete=models.CASCADE, related_name="sesi_login")
    instalasi = models.UUIDField()
    token_hash = models.CharField(max_length=64, unique=True)
    kedaluwarsa = models.DateTimeField()


class PenugasanTruk(models.Model):
    pengemudi = models.ForeignKey(Pengemudi, on_delete=models.CASCADE, related_name="penugasan_truk")
    truk = models.ForeignKey(Truk, on_delete=models.CASCADE, related_name="penugasan")
    mulai = models.DateTimeField(auto_now_add=True)
    berakhir = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("pengemudi", "truk"), condition=models.Q(berakhir__isnull=True),
                name="penugasan_truk_aktif_unik",
            ),
        ]
