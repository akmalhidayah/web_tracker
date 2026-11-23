from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Count, Sum
from django.utils.formats import date_format, number_format
from django.utils.html import format_html
from django.utils.timezone import localtime

from .models import Ekspeditur, Pengemudi, Truk
from .panel import (
    SEMUA,
    PanelAdminMixin,
    chip_ekspeditur,
    kartu,
    opsi_status,
    pil_status,
)


class KhususAdministrator:
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


def tab_ekspeditur():
    """Semua, lalu satu tab per ekspeditur."""
    return [
        SEMUA,
        *(
            {
                "label": e.nama_singkat,
                "params": {"ekspeditur__id__exact": str(e.pk)},
                "saring": {"ekspeditur_id": e.pk},
            }
            for e in Ekspeditur.objects.order_by("nama_singkat")
        ),
    ]


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class PenggunaAdmin(KhususAdministrator, PanelAdminMixin, UserAdmin):
    panel_ikon = "akses"
    panel_judul = "User Panel"
    panel_tambah = "User"
    panel_deskripsi = "Akun yang dapat masuk ke dashboard ini beserta peran aksesnya."
    panel_cari = "Cari nama, username, atau email…"
    list_display = ("nama_lengkap", "username", "email", "peran", "status", "bergabung")

    @admin.display(description="Nama", ordering="first_name")
    def nama_lengkap(self, obj):
        return obj.get_full_name() or obj.username

    @admin.display(description="Peran")
    def peran(self, obj):
        if obj.is_superuser:
            kelas, teks = "pil-admin", "Administrator"
        elif obj.is_staff:
            kelas, teks = "pil-staf", "Staf"
        else:
            kelas, teks = "pil-nonaktif", "Operator"
        return format_html('<span class="pil {}">{}</span>', kelas, teks)

    @admin.display(description="Status", ordering="is_active")
    def status(self, obj):
        return pil_status(obj.is_active)

    @admin.display(description="Bergabung", ordering="date_joined")
    def bergabung(self, obj):
        return date_format(localtime(obj.date_joined), "j M Y")

    def panel_kartu(self, request):
        pengguna = User.objects
        return [
            kartu("Total pengguna", pengguna.count(), "Akun yang terdaftar."),
            kartu("Administrator", pengguna.filter(is_superuser=True).count(), "Akses penuh, termasuk User Panel."),
            kartu("Staf", pengguna.filter(is_staff=True, is_superuser=False).count(), "Dapat mengelola data sesuai izin."),
            kartu("Aktif", pengguna.filter(is_active=True).count(), "Dapat masuk saat ini."),
        ]

    def panel_tab(self, request):
        return [
            SEMUA,
            {
                "label": "Administrator",
                "params": {"is_superuser__exact": "1"},
                "saring": {"is_superuser": True},
            },
            {
                "label": "Staf",
                "params": {"is_staff__exact": "1", "is_superuser__exact": "0"},
                "saring": {"is_staff": True, "is_superuser": False},
            },
            {
                "label": "Operator",
                "params": {"is_staff__exact": "0", "is_superuser__exact": "0"},
                "saring": {"is_staff": False, "is_superuser": False},
            },
        ]

    def panel_status(self, request):
        return opsi_status("is_active", "is_active__exact")


@admin.register(Group)
class GrupAdmin(KhususAdministrator, PanelAdminMixin, GroupAdmin):
    panel_ikon = "akses"
    panel_judul = "User Panel"
    panel_tambah = "Grup"
    panel_deskripsi = "Grup mengelompokkan izin supaya mudah diberikan ke banyak akun."
    panel_cari = "Cari nama grup…"
    list_display = ("name", "jumlah_izin", "jumlah_pengguna")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _izin=Count("permissions", distinct=True),
                _pengguna=Count("user", distinct=True),
            )
        )

    @admin.display(description="Izin", ordering="_izin")
    def jumlah_izin(self, obj):
        return obj._izin

    @admin.display(description="Pengguna", ordering="_pengguna")
    def jumlah_pengguna(self, obj):
        return obj._pengguna

    def panel_kartu(self, request):
        return [
            kartu("Total grup", Group.objects.count(), "Kelompok izin yang tersedia."),
            kartu("Izin tersedia", Permission.objects.count(), "Izin yang dapat diberikan ke grup."),
            kartu(
                "Pengguna dalam grup",
                User.objects.filter(groups__isnull=False).distinct().count(),
                "Akun yang tergabung di minimal satu grup.",
            ),
        ]


@admin.register(Ekspeditur)
class EkspediturAdmin(PanelAdminMixin, admin.ModelAdmin):
    panel_ikon = "vendor"
    panel_tambah = "Ekspeditur"
    panel_deskripsi = "Perusahaan pemilik armada. Nama singkat dan warnanya dipakai di Monitoring dan Laporan."
    panel_cari = "Cari nama, kode, atau nama singkat…"
    list_display = ("nama", "kode", "nama_singkat", "warna_chip", "status")
    list_filter = ("aktif",)
    search_fields = ("nama", "nama_singkat", "kode")
    prepopulated_fields = {"kode": ("nama_singkat",)}

    @admin.display(description="Warna", ordering="warna")
    def warna_chip(self, obj):
        return format_html(
            '<span class="chip-warna"><i style="background:{}"></i>{}</span>',
            obj.warna,
            obj.get_warna_display(),
        )

    @admin.display(description="Status", ordering="aktif")
    def status(self, obj):
        return pil_status(obj.aktif)

    def panel_kartu(self, request):
        total = Ekspeditur.objects.count()
        aktif = Ekspeditur.objects.filter(aktif=True).count()
        return [
            kartu("Total ekspeditur", total, "Terdaftar di data master."),
            kartu("Aktif", aktif, "Ekspeditur yang sedang beroperasi."),
            kartu("Nonaktif", total - aktif, "Tidak sedang beroperasi."),
            kartu("Total truk", Truk.objects.count(), "Armada seluruh ekspeditur."),
        ]

    def panel_tab(self, request):
        return opsi_status()


@admin.register(Truk)
class TrukAdmin(PanelAdminMixin, admin.ModelAdmin):
    panel_ikon = "truk"
    panel_tambah = "Truk"
    panel_deskripsi = "Nomor lambung, nomor polisi, dan kapasitas tiap armada ekspeditur."
    panel_cari = "Cari nomor lambung, plat, atau ekspeditur…"
    list_display = ("nomor", "ekspeditur_chip", "plat", "kapasitas_ton", "status")
    list_filter = ("ekspeditur", "aktif")
    search_fields = ("nomor", "plat", "ekspeditur__nama")
    list_select_related = ("ekspeditur",)

    @admin.display(description="Ekspeditur", ordering="ekspeditur__nama")
    def ekspeditur_chip(self, obj):
        return chip_ekspeditur(obj.ekspeditur)

    @admin.display(description="Kapasitas", ordering="kapasitas")
    def kapasitas_ton(self, obj):
        if obj.kapasitas is None:
            return "—"
        return f"{teks_ton(obj.kapasitas)} ton"

    @admin.display(description="Status", ordering="aktif")
    def status(self, obj):
        return pil_status(obj.aktif)

    def panel_kartu(self, request):
        truk = Truk.objects
        total = truk.count()
        aktif = truk.filter(aktif=True).count()
        kapasitas = truk.filter(aktif=True).aggregate(jumlah=Sum("kapasitas"))["jumlah"] or 0
        return [
            kartu("Total truk", total, "Nomor lambung terdaftar."),
            kartu("Aktif", aktif, "Tampil di Monitoring."),
            kartu("Nonaktif", total - aktif, "Tidak tampil di Monitoring."),
            kartu("Kapasitas aktif", round(kapasitas), "Ton, jumlah truk aktif."),
        ]

    def panel_tab(self, request):
        return tab_ekspeditur()

    def panel_status(self, request):
        return opsi_status()


@admin.register(Pengemudi)
class PengemudiAdmin(PanelAdminMixin, admin.ModelAdmin):
    panel_ikon = "orang"
    panel_tambah = "Pengemudi"
    panel_deskripsi = "Pengemudi per ekspeditur beserta nomor HP yang dipakai untuk masuk ke aplikasi."
    panel_cari = "Cari nama, nomor HP, atau ekspeditur…"
    list_display = ("nama", "ekspeditur_chip", "nomor_hp_tampil", "status")
    list_filter = ("ekspeditur", "aktif")
    search_fields = ("nama", "nomor_hp", "ekspeditur__nama")
    list_select_related = ("ekspeditur",)

    @admin.display(description="Ekspeditur", ordering="ekspeditur__nama")
    def ekspeditur_chip(self, obj):
        return chip_ekspeditur(obj.ekspeditur)

    @admin.display(description="Nomor HP", ordering="nomor_hp")
    def nomor_hp_tampil(self, obj):
        return obj.nomor_hp or "—"

    @admin.display(description="Status", ordering="aktif")
    def status(self, obj):
        return pil_status(obj.aktif)

    def panel_kartu(self, request):
        pengemudi = Pengemudi.objects
        total = pengemudi.count()
        aktif = pengemudi.filter(aktif=True).count()
        return [
            kartu("Total pengemudi", total, "Terdaftar di data master."),
            kartu("Aktif", aktif, "Pengemudi yang sedang bertugas."),
            kartu("Nonaktif", total - aktif, "Tidak sedang bertugas."),
            kartu("Tanpa nomor HP", pengemudi.filter(nomor_hp="").count(), "Perlu dilengkapi."),
        ]

    def panel_tab(self, request):
        return tab_ekspeditur()

    def panel_status(self, request):
        return opsi_status()


def teks_ton(nilai):
    """Kapasitas dalam ton: 30,00 tampil 30, sedangkan 27,5 tetap 27,5."""
    utuh = nilai == nilai.to_integral_value()
    return number_format(nilai, decimal_pos=0 if utuh else 2)
