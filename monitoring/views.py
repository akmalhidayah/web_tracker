from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .data_contoh import EKSPEDITUR, LAPORAN, WAKTU_CONTOH, data_peta
from .forms import ProfilForm
from .grafik_laporan import grafik_armada
from .models import Ekspeditur, Truk
from .riwayat_laporan import riwayat_armada


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
    vendor = Ekspeditur.objects.filter(aktif=True).order_by("pk").values_list(
        "kode", "nama", "nama_singkat", "warna"
    )
    unit = Truk.objects.filter(aktif=True, ekspeditur__aktif=True).order_by(
        "ekspeditur_id", "nomor"
    ).values_list("nomor", "ekspeditur__kode")
    return render(
        request,
        "monitoring/monitoring.html",
        {"menu": "monitoring", "waktu": WAKTU_CONTOH, "peta": data_peta(vendor, unit)},
    )


def _persentase(nilai, dasar):
    return round(nilai * 100 / dasar) if dasar else 0


@never_cache
@login_required
def laporan(request):
    baris = [
        {
            "nama": EKSPEDITUR[kode][0],
            "singkat": EKSPEDITUR[kode][1],
            "ready": ready, "operasi": operasi, "ritase": ritase,
            "volume": volume,
            "utilisasi": _persentase(operasi, ready),
            "rata_ritase": ritase / operasi if operasi else None,
        }
        for kode, (ready, operasi, ritase, volume, _) in LAPORAN.items()
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
            "waktu": WAKTU_CONTOH,
            "baris": baris,
            "total": total,
            "grafik": grafik_armada(baris, total),
            "riwayat": riwayat_armada(request.GET.get("tanggal", "")),
        },
    )
