from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from .akun import ekspeditur_akun
from .akun_sopir import simpan_akun_dan_penugasan_sopir
from .data_contoh import EKSPEDITUR, LAPORAN, WAKTU_CONTOH, data_peta, sesi_armada_contoh
from .forms import BuatLaporanForm, PengemudiVendorForm, ProfilForm, TrukVendorForm
from .grafik_laporan import grafik_armada
from .models import Ekspeditur, PenugasanTruk, Pengemudi, Truk
from .riwayat_laporan import riwayat_armada, tanggal_laporan


def _cakupan_dashboard(pengguna):
    ekspeditur = ekspeditur_akun(pengguna)
    if ekspeditur is None and not pengguna.is_superuser:
        raise PermissionDenied("Akun ini memerlukan Ekspeditur aktif.")
    return ekspeditur


def _kunci_laporan(request, ekspeditur):
    return f"laporan_demo:{request.user.pk}:{ekspeditur.pk}"


@never_cache
@login_required
@require_http_methods(["GET", "HEAD"])
def master_vendor(request, jenis):
    ekspeditur = _cakupan_dashboard(request.user)
    daftar_pengemudi = jenis == "pengemudi"
    if ekspeditur is None:
        model = "pengemudi" if daftar_pengemudi else "truk"
        return redirect(f"admin:monitoring_{model}_changelist")

    cari = request.GET.get("q", "").strip()[:120]
    if daftar_pengemudi:
        penugasan = PenugasanTruk.objects.filter(
            berakhir__isnull=True, truk__ekspeditur=ekspeditur, truk__aktif=True,
        ).select_related("truk").order_by("truk__nomor")
        data = Pengemudi.objects.filter(
            Q(nama__icontains=cari) | Q(nomor_hp__icontains=cari), ekspeditur=ekspeditur,
        ).order_by("nama", "pk").prefetch_related(
            Prefetch("penugasan_truk", queryset=penugasan, to_attr="penugasan_aktif")
        )
    else:
        data = Truk.objects.filter(
            Q(nomor__icontains=cari) | Q(plat__icontains=cari), ekspeditur=ekspeditur,
        )

    return render(request, "monitoring/master_vendor.html", {
        "ekspeditur": ekspeditur,
        "judul": "Pengemudi" if daftar_pengemudi else "Nomor Lambung",
        "ikon": "orang" if daftar_pengemudi else "truk",
        "daftar_pengemudi": daftar_pengemudi,
        "alamat_tambah": reverse(f"monitoring:master_{jenis}_tambah"),
        "nama_url_ubah": f"monitoring:master_{jenis}_ubah",
        "cari": cari,
        "halaman": Paginator(data, 25).get_page(request.GET.get("page")),
    })


@never_cache
@sensitive_post_parameters("pin_baru")
@login_required
@require_http_methods(["GET", "HEAD", "POST"])
def form_master_vendor(request, jenis, pk=None):
    nama_url_daftar = f"monitoring:master_{jenis}"
    daftar_pengemudi = jenis == "pengemudi"
    model, kelas_form, label, ikon = (
        (Pengemudi, PengemudiVendorForm, "Pengemudi", "orang")
        if daftar_pengemudi else (Truk, TrukVendorForm, "Nomor Lambung", "truk")
    )
    kirim = request.method == "POST"
    form = None
    try:
        with transaction.atomic():
            ekspeditur = _cakupan_dashboard(request.user)
            if ekspeditur is None:
                return redirect(nama_url_daftar)
            daftar = model.objects.filter(ekspeditur=ekspeditur)
            if kirim:
                daftar = daftar.select_for_update()
            objek = get_object_or_404(daftar, pk=pk) if pk is not None else model(ekspeditur=ekspeditur)
            form = kelas_form(request.POST if kirim else None, instance=objek)
            if kirim and form.is_valid():
                objek = form.save()
                if daftar_pengemudi:
                    simpan_akun_dan_penugasan_sopir(
                        objek,
                        pin_baru=form.cleaned_data["pin_baru"],
                        truk_ids={truk.pk for truk in form.cleaned_data["truk_ditugaskan"]},
                        ekspeditur_sebelumnya=ekspeditur.pk,
                    )
    except IntegrityError:
        if form is None:
            raise
        form.add_error(None, "Data bentrok dengan perubahan lain. Periksa isian dan coba lagi.")
    except OperationalError as error:
        if form is None or not kirim or "database is locked" not in str(error):
            raise
        form.add_error(None, "Data sedang disimpan oleh pengguna lain. Coba lagi.")

    if kirim and not form.errors:
        messages.success(request, f"{label} berhasil disimpan.")
        return redirect(nama_url_daftar)

    aksi = "Ubah" if pk is not None else "Tambah"
    return render(request, "monitoring/form_master_vendor.html", {
        "ekspeditur": ekspeditur,
        "judul": f"{aksi} {label}",
        "ikon": ikon,
        "form": form,
        "alamat_daftar": reverse(nama_url_daftar),
    })


@never_cache
@login_required
@require_http_methods(["GET", "HEAD", "POST"])
def profil(request):
    data = request.POST if request.method == "POST" else None
    form = ProfilForm(data, instance=request.user)
    if request.method == "POST" and form.is_valid():
        if form.has_changed():
            akun = form.save(commit=False)
            akun.save(update_fields=form.changed_data)
        messages.success(request, "Profil berhasil disimpan.")
        return redirect("monitoring:profil")
    return render(request, "monitoring/profil.html", {"form": form})


class GantiSandi(SuccessMessageMixin, PasswordChangeView):
    template_name = "monitoring/sandi.html"
    success_url = reverse_lazy("monitoring:profil")
    success_message = "Kata sandi berhasil diperbarui."


@never_cache
@login_required
def monitoring(request):
    ekspeditur = _cakupan_dashboard(request.user)
    vendor = Ekspeditur.objects.filter(aktif=True).order_by("pk")
    unit = Truk.objects.filter(aktif=True, ekspeditur__aktif=True).order_by("ekspeditur_id", "nomor")
    if ekspeditur is not None:
        vendor = vendor.filter(pk=ekspeditur.pk)
        unit = unit.filter(ekspeditur=ekspeditur)
    peta = data_peta(
        vendor.values_list("kode", "nama", "nama_singkat", "warna"),
        unit.values_list("nomor", "ekspeditur__kode"),
    )
    peta["cakupanVendor"] = ekspeditur is not None
    peta["hariIni"] = timezone.localdate().isoformat()
    return render(
        request,
        "monitoring/monitoring.html",
        {"menu": "monitoring", "ekspeditur": ekspeditur, "peta": peta},
    )


def _persentase(nilai, dasar):
    return round(nilai * 100 / dasar) if dasar else 0


@never_cache
@login_required
def laporan(request):
    ekspeditur = _cakupan_dashboard(request.user)
    demo = request.session.get(_kunci_laporan(request, ekspeditur)) if ekspeditur is not None else None
    riwayat = riwayat_armada(request.GET.get("tanggal", ""), ekspeditur, demo)
    if ekspeditur is None:
        sumber = [(EKSPEDITUR[kode], angka[:4]) for kode, angka in LAPORAN.items()]
    else:
        pratinjau = riwayat["pratinjau"]
        angka = (
            tuple(pratinjau[kolom] for kolom in ("ready", "operasi", "ritase", "volume"))
            if pratinjau is not None else LAPORAN.get(ekspeditur.kode, ())[:4]
        )
        sumber = [((ekspeditur.nama, ekspeditur.nama_singkat), angka)] if angka else []

    baris = [
        {
            "nama": nama,
            "singkat": singkat,
            "ready": ready, "operasi": operasi, "ritase": ritase,
            "volume": volume,
            "utilisasi": _persentase(operasi, ready),
            "rata_ritase": ritase / operasi if operasi else None,
        }
        for (nama, singkat), (ready, operasi, ritase, volume) in sumber
    ]
    total = {
        kolom: sum(item[kolom] for item in baris)
        for kolom in ("ready", "operasi", "ritase", "volume")
    }
    total["utilisasi"] = _persentase(total["operasi"], total["ready"])
    total["rata_ritase"] = total["ritase"] / total["operasi"] if total["operasi"] else None
    return render(
        request,
        "monitoring/laporan.html",
        {
            "menu": "laporan",
            "ekspeditur": ekspeditur,
            "waktu": WAKTU_CONTOH,
            "baris": baris,
            "total": total,
            "grafik": grafik_armada(baris, total),
            "riwayat": riwayat,
        },
    )


@never_cache
@login_required
@require_http_methods(["GET", "HEAD"])
def laporan_armada(request):
    ekspeditur = _cakupan_dashboard(request.user)
    hari_ini = timezone.localdate()
    tanggal_contoh = WAKTU_CONTOH.date()
    tanggal = tanggal_laporan(request.GET.get("tanggal", tanggal_contoh.isoformat()), hari_ini)
    cari = request.GET.get("q", "").strip()[:120]
    tab_ekspeditur = []
    filter_ekspeditur = ""
    nama_ekspeditur = {}
    if ekspeditur is None:
        nama_ekspeditur = {kode: singkat for kode, (_, singkat) in EKSPEDITUR.items()}
        nama_ekspeditur.update(Ekspeditur.objects.values_list("kode", "nama_singkat"))
        kode_diminta = request.GET.get("ekspeditur", "")
        if kode_diminta in nama_ekspeditur:
            filter_ekspeditur = kode_diminta

        query = {"tanggal": tanggal.isoformat()}
        if cari:
            query["q"] = cari
        opsi = [("", "Semua"), *sorted(nama_ekspeditur.items(), key=lambda item: item[1].casefold())]
        tab_ekspeditur = [
            {
                "label": label,
                "aktif": kode == filter_ekspeditur,
                "url": reverse(
                    "monitoring:laporan_armada", query={**query, "ekspeditur": kode} if kode else query
                ),
            }
            for kode, label in opsi
        ]

    kode_ekspeditur = ekspeditur.kode if ekspeditur is not None else filter_ekspeditur or None
    return render(
        request,
        "monitoring/laporan_armada.html",
        {
            "menu": "laporan_armada",
            "ekspeditur": ekspeditur,
            "hari_ini": hari_ini,
            "tanggal": tanggal,
            "cari": cari,
            "tab_ekspeditur": tab_ekspeditur,
            "filter_ekspeditur": filter_ekspeditur,
            "sesi": sesi_armada_contoh(tanggal, kode_ekspeditur, cari, nama_ekspeditur),
        },
    )


@never_cache
@login_required
@require_http_methods(["GET", "HEAD", "POST"])
def buat_laporan(request):
    ekspeditur = _cakupan_dashboard(request.user)
    if ekspeditur is None:
        raise PermissionDenied("Pembuatan laporan tersedia untuk akun Vendor.")

    kunci = _kunci_laporan(request, ekspeditur)
    catatan = request.session.get(kunci, {})
    dipilih = tanggal_laporan(request.GET.get("tanggal", ""), timezone.localdate())
    awal = {**catatan.get(dipilih.isoformat(), {}), "tanggal": dipilih}
    data = request.POST if request.method == "POST" else None
    form = BuatLaporanForm(data, initial=awal)
    if request.method == "POST" and form.is_valid():
        tanggal = form.cleaned_data["tanggal"].isoformat()
        nilai = {kolom: nilai for kolom, nilai in form.cleaned_data.items() if kolom != "tanggal"}
        request.session[kunci] = {**catatan, tanggal: nilai}
        messages.success(request, "Pratinjau laporan disimpan untuk sesi login ini.")
        return redirect(reverse("monitoring:laporan", query={"tanggal": tanggal}))
    return render(
        request,
        "monitoring/buat_laporan.html",
        {
            "menu": "buat_laporan",
            "ekspeditur": ekspeditur,
            "form": form,
            "metrik": (
                ("Volume pengiriman", "ton", form["volume"], form["target_volume"]),
                ("Armada operasi", "unit", form["operasi"], form["target_operasi"]),
                ("Jumlah ritase", "ret", form["ritase"], form["target_ritase"]),
            ),
        },
    )
