import re
from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from .models import AkunSopir, PenugasanTruk, SesiLoginSopir, Truk


MASA_LOGIN_SOPIR = timedelta(days=30)
# Naikkan bersama versi teks persetujuan di aplikasi sopir.
VERSI_PERSETUJUAN_SOPIR = 1


def nomor_hp_login(nilai):
    angka = re.sub(r"[\s+().-]", "", nilai)
    if angka.startswith("0"):
        angka = "62" + angka[1:]
    if re.fullmatch(r"628[0-9]{7,12}", angka):
        return "+" + angka
    raise ValueError("Masukkan nomor HP Indonesia yang valid (08 atau +62).")


@transaction.atomic
def atur_pin(pengemudi, nomor, pin):
    akun, _ = AkunSopir.objects.update_or_create(
        pengemudi=pengemudi,
        defaults={"nomor_hp": nomor, "pin_hash": make_password(pin), "percobaan_gagal": 0, "terkunci_sampai": None},
    )
    SesiLoginSopir.objects.filter(akun=akun).delete()
    return akun


def truk_untuk_sopir(pengemudi):
    return Truk.objects.filter(
        penugasan__pengemudi=pengemudi, penugasan__berakhir__isnull=True,
        ekspeditur_id=pengemudi.ekspeditur_id, aktif=True, ekspeditur__aktif=True,
    )


def simpan_penugasan(pengemudi, truk_ids):
    aktif = PenugasanTruk.objects.filter(pengemudi=pengemudi, berakhir__isnull=True)
    aktif.exclude(truk_id__in=truk_ids).update(berakhir=timezone.now())
    sudah_ada = set(aktif.values_list("truk_id", flat=True))
    PenugasanTruk.objects.bulk_create([
        PenugasanTruk(pengemudi=pengemudi, truk_id=pk) for pk in sorted(truk_ids - sudah_ada)
    ])


def simpan_akun_dan_penugasan_sopir(pengemudi, *, pin_baru, truk_ids, ekspeditur_sebelumnya):
    akun = getattr(pengemudi, "akun_sopir", None)
    if pin_baru:
        atur_pin(pengemudi, pengemudi.nomor_hp, pin_baru)
    elif akun and (
        not pengemudi.aktif
        or pengemudi.ekspeditur_id != ekspeditur_sebelumnya
        or akun.nomor_hp != pengemudi.nomor_hp
    ):
        AkunSopir.objects.filter(pk=akun.pk).update(nomor_hp=pengemudi.nomor_hp)
        SesiLoginSopir.objects.filter(akun=akun).delete()
    simpan_penugasan(pengemudi, truk_ids)


def hash_token(token):
    return sha256(token.encode()).hexdigest()


@transaction.atomic
def login_sopir(nomor, pin, instalasi):
    akun = AkunSopir.objects.select_for_update(of=("self",)).select_related("pengemudi__ekspeditur").filter(nomor_hp=nomor).first()
    sekarang = timezone.now()
    if akun is None or not (akun.pengemudi.aktif and akun.pengemudi.ekspeditur.aktif):
        make_password(pin)
        return None, None, 401
    if akun.terkunci_sampai and akun.terkunci_sampai > sekarang:
        return None, None, 429
    if not check_password(pin, akun.pin_hash):
        akun.percobaan_gagal = 1 if akun.terkunci_sampai else akun.percobaan_gagal + 1
        akun.terkunci_sampai = sekarang + timedelta(minutes=15) if akun.percobaan_gagal >= 5 else None
        akun.save(update_fields=["percobaan_gagal", "terkunci_sampai"])
        return None, None, 429 if akun.terkunci_sampai else 401

    if akun.percobaan_gagal:
        akun.percobaan_gagal = 0
        akun.terkunci_sampai = None
        akun.save(update_fields=["percobaan_gagal", "terkunci_sampai"])
    token = token_urlsafe(32)
    SesiLoginSopir.objects.update_or_create(akun=akun, defaults={
        "instalasi": instalasi, "token_hash": hash_token(token), "kedaluwarsa": sekarang + MASA_LOGIN_SOPIR,
    })
    return akun, token, 200
