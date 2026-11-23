from decimal import Decimal

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
