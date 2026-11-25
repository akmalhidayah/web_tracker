import re

from django.conf import settings
from django.db.models.functions import Greatest
from django.http import HttpResponse
from django.utils import timezone
from django.utils.cache import add_never_cache_headers, patch_vary_headers
from rest_framework import serializers
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from .akun_sopir import (
    MASA_LOGIN_SOPIR,
    VERSI_PERSETUJUAN_SOPIR,
    hash_token,
    login_sopir,
    nomor_hp_login,
    truk_untuk_sopir,
)
from .models import SesiLoginSopir


def sesi_aktif():
    return SesiLoginSopir.objects.filter(
        kedaluwarsa__gt=timezone.now(),
        akun__pengemudi__aktif=True,
        akun__pengemudi__ekspeditur__aktif=True,
    )


def data_truk(truk):
    return {
        "id": truk.pk,
        "nomor_lambung": truk.nomor,
        "kapasitas_ton": str(truk.kapasitas) if truk.kapasitas is not None else None,
    }


def profil_sopir(akun):
    pengemudi = akun.pengemudi
    ekspeditur = pengemudi.ekspeditur
    truk = [data_truk(unit) for unit in truk_untuk_sopir(pengemudi)]
    versi = VERSI_PERSETUJUAN_SOPIR
    return {
        "pengemudi": {"id": pengemudi.pk, "nama": pengemudi.nama, "nomor_hp": akun.nomor_hp},
        "ekspeditur": {"id": ekspeditur.pk, "nama": ekspeditur.nama, "nama_singkat": ekspeditur.nama_singkat},
        "truk": truk,
        "truk_terpilih_id": next((unit["id"] for unit in truk if unit["id"] == akun.truk_terpilih_id), None),
        "versi_persetujuan": versi,
        "sudah_setuju": akun.persetujuan.filter(versi=versi).exists(),
    }


class TokenSopir(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request)
        if not header:
            return None
        cocok = re.fullmatch(rb"Bearer ([A-Za-z0-9_-]{43})", header, flags=re.IGNORECASE)
        if cocok:
            sesi = sesi_aktif().select_related("akun__pengemudi__ekspeditur").filter(
                token_hash=hash_token(cocok[1].decode()),
            ).first()
            if sesi:
                return sesi.akun, sesi
        raise AuthenticationFailed("Sesi login sudah habis. Masuk kembali.")


class BatasLoginSopir(SimpleRateThrottle):
    rate = "30/min"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": "login_sopir", "ident": request.META.get("REMOTE_ADDR", "")}


class DataLoginSopir(serializers.Serializer):
    nomor_hp = serializers.CharField(max_length=32)
    pin = serializers.RegexField(r"\A[0-9]{6}\Z", trim_whitespace=False, write_only=True)
    instalasi = serializers.UUIDField()

    def validate_nomor_hp(self, nilai):
        try:
            return nomor_hp_login(nilai)
        except ValueError as error:
            raise serializers.ValidationError(str(error)) from error


class DataPersetujuanSopir(serializers.Serializer):
    versi = serializers.IntegerField(min_value=1, max_value=32767)


class DataPilihanTruk(serializers.Serializer):
    truk_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1)


class ApiSopir(APIView):
    authentication_classes = (TokenSopir,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer,)

    def dispatch(self, request, *args, **kwargs):
        asal = request.headers.get("Origin")
        dev_browser = asal in settings.SOPIR_DEV_ORIGINS
        if dev_browser and request.method == "OPTIONS":
            respons = HttpResponse(status=204)
            respons["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            respons["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        else:
            respons = super().dispatch(request, *args, **kwargs)
        add_never_cache_headers(respons)
        patch_vary_headers(respons, ("Origin",))
        if dev_browser:
            respons["Access-Control-Allow-Origin"] = asal
        return respons


class MasukSopir(ApiSopir):
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = (BatasLoginSopir,)

    def post(self, request):
        form = DataLoginSopir(data=request.data)
        form.is_valid(raise_exception=True)
        data = form.validated_data
        akun, token, status = login_sopir(data["nomor_hp"], data["pin"], data["instalasi"])
        if status == 429:
            return Response({"detail": "Terlalu banyak percobaan. Coba lagi dalam 15 menit."}, status=429)
        if akun is None:
            return Response({"detail": "Periksa kembali nomor HP dan PIN Anda."}, status=401)
        return Response({"token": token, **profil_sopir(akun)})


class PulihkanSesiSopir(ApiSopir):
    def post(self, request):
        diperpanjang = sesi_aktif().filter(
            pk=request.auth.pk,
            token_hash=request.auth.token_hash,
        ).update(kedaluwarsa=Greatest("kedaluwarsa", timezone.now() + MASA_LOGIN_SOPIR))
        if not diperpanjang:
            raise AuthenticationFailed("Sesi login sudah habis. Masuk kembali.")
        return Response(profil_sopir(request.user))


class SetujuSopir(ApiSopir):
    def post(self, request):
        form = DataPersetujuanSopir(data=request.data)
        form.is_valid(raise_exception=True)
        versi = form.validated_data["versi"]
        if versi != VERSI_PERSETUJUAN_SOPIR:
            return Response({"detail": "Versi persetujuan berubah."}, status=409)
        request.user.persetujuan.get_or_create(versi=versi)
        return Response(status=204)


class PilihTrukSopir(ApiSopir):
    def post(self, request):
        form = DataPilihanTruk(data=request.data)
        form.is_valid(raise_exception=True)
        truk_id = form.validated_data["truk_id"]
        if not truk_untuk_sopir(request.user.pengemudi).filter(pk=truk_id).exists():
            return Response({"detail": "Truk ini tidak lagi ditugaskan kepada Anda."}, status=409)
        request.user.truk_terpilih_id = truk_id
        request.user.save(update_fields=["truk_terpilih"])
        return Response(status=204)


class KeluarSopir(ApiSopir):
    def post(self, request):
        SesiLoginSopir.objects.filter(pk=request.auth.pk, token_hash=request.auth.token_hash).delete()
        return Response(status=204)


class TrukSopir(ApiSopir):
    def get(self, request):
        return Response({"truk": [data_truk(truk) for truk in truk_untuk_sopir(request.user.pengemudi)]})
