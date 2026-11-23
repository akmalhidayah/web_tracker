"""Gaya halaman pengelolaan bersama untuk Ekspeditur, Truk, Pengemudi, dan User Panel.

Setiap halaman daftar memakai kerangka yang sama: kartu judul, kartu ringkasan,
tab penyaring dengan jumlah, kolom pencarian, dan tombol aksi per baris.
Tampilannya ada di ``templates/admin/change_list.html`` dan ``admin.css``.
"""

from django.contrib.admin.utils import quote
from django.urls import reverse
from django.utils.formats import number_format
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

_SVG = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" '
    'aria-hidden="true" focusable="false">{}</svg>'
)
IKON_UBAH = mark_safe(_SVG.format('<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>'))
IKON_HAPUS = mark_safe(_SVG.format('<path d="M3 6h18M8 6V4h8v2m-9 0 1 14h8l1-14M10 11v6m4-6v6"/>'))

# Opsi untuk tab "Semua" dan pilihan status aktif/nonaktif.
SEMUA = {"label": "Semua", "params": {}, "saring": {}}


def opsi_status(kolom="aktif", param="aktif__exact"):
    """Pilihan Semua / Aktif / Nonaktif untuk kolom boolean ``kolom``."""
    return [
        SEMUA,
        {"label": "Aktif", "params": {param: "1"}, "saring": {kolom: True}},
        {"label": "Nonaktif", "params": {param: "0"}, "saring": {kolom: False}},
    ]


def kartu(label, nilai, keterangan):
    """Satu kartu ringkasan; angka diformat gaya Indonesia (titik ribuan)."""
    return {
        "label": label,
        "nilai": number_format(nilai, decimal_pos=0, force_grouping=True),
        "keterangan": keterangan,
    }


def pil_status(aktif):
    return format_html(
        '<span class="pil {}">{}</span>',
        "pil-aktif" if aktif else "pil-nonaktif",
        "Aktif" if aktif else "Nonaktif",
    )


def chip_ekspeditur(ekspeditur):
    return format_html(
        '<span class="chip-warna"><i style="background:{}"></i>{}</span>',
        ekspeditur.warna,
        ekspeditur.nama_singkat,
    )


class PanelAdminMixin:
    """Menambahkan kartu ringkasan, tab, dan kolom aksi ke daftar admin.

    Subkelas mengisi ``panel_*`` dan menimpa ``panel_kartu``, ``panel_tab``,
    serta ``panel_status`` bila perlu. Parameter tab memakai nama filter bawaan
    admin (misalnya ``aktif__exact``), jadi harus ada di ``list_filter``.
    """

    panel_ikon = "master"
    panel_judul = ""  # kosong: memakai nama jamak model
    panel_tambah = ""  # teks setelah "Tambah", misalnya "Truk"
    panel_deskripsi = ""
    panel_cari = "Cari…"

    def panel_kartu(self, request):
        return []

    def panel_tab(self, request):
        return []

    def panel_status(self, request):
        return []

    def get_list_display(self, request):
        return [*super().get_list_display(request), self._kolom_aksi(request)]

    def _kolom_aksi(self, request):
        opts = self.opts
        nama_url = f"{self.admin_site.name}:{opts.app_label}_{opts.model_name}_"
        boleh_ubah = self.has_change_permission(request)
        boleh_hapus = self.has_delete_permission(request)

        def aksi(obj):
            tombol = []
            if boleh_ubah:
                tombol.append(
                    format_html(
                        '<a class="aksi-ikon aksi-ubah" href="{}" title="Ubah" aria-label="Ubah {}">{}</a>',
                        reverse(nama_url + "change", args=(quote(obj.pk),)),
                        obj,
                        IKON_UBAH,
                    )
                )
            if boleh_hapus:
                tombol.append(
                    format_html(
                        '<a class="aksi-ikon aksi-hapus" href="{}" title="Hapus" aria-label="Hapus {}">{}</a>',
                        reverse(nama_url + "delete", args=(quote(obj.pk),)),
                        obj,
                        IKON_HAPUS,
                    )
                )
            return format_html(
                '<div class="aksi-baris">{}</div>',
                format_html_join("", "{}", ((t,) for t in tombol)),
            )

        aksi.short_description = "Aksi"
        return aksi

    def _kelompok(self, request, opsi, hitung):
        """Menyiapkan tautan, status aktif, dan jumlah untuk satu baris tab."""
        kunci = {k for o in opsi for k in o["params"]}
        hasil = []
        for o in opsi:
            query = request.GET.copy()
            for k in (*kunci, "p", "e"):
                query.pop(k, None)
            for k, v in o["params"].items():
                query[k] = v
            if o["params"]:
                aktif = all(request.GET.get(k) == v for k, v in o["params"].items())
            else:
                aktif = not any(k in request.GET for k in kunci)
            jumlah = None
            if hitung:
                jumlah = number_format(
                    self.model._default_manager.filter(**o["saring"]).count(),
                    force_grouping=True,
                )
            hasil.append(
                {
                    "label": o["label"],
                    "url": "?" + query.urlencode(),
                    "aktif": aktif,
                    "jumlah": jumlah,
                }
            )
        return hasil

    def changelist_view(self, request, extra_context=None):
        panel = {
            "ikon": self.panel_ikon,
            "judul": self.panel_judul,
            "tambah": self.panel_tambah,
            "deskripsi": self.panel_deskripsi,
            "cari": self.panel_cari,
            "kartu": self.panel_kartu(request),
            "tab": self._kelompok(request, self.panel_tab(request), hitung=True),
            "status": self._kelompok(request, self.panel_status(request), hitung=False),
        }
        return super().changelist_view(request, {"panel": panel, **(extra_context or {})})
