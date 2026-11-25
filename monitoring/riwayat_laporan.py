from datetime import date

from django.utils import timezone

from .data_contoh import EKSPEDITUR, LAPORAN, LAPORAN_HARIAN, TARGET_RITASE_CONTOH


def _rasio(nilai, pembagi):
    return nilai / pembagi if pembagi else None


def _baris(nama, realisasi, target):
    volume, operasi, ritase = realisasi
    return {
        "nama": nama,
        "metrik": [
            {"nilai": nilai, "target": batas, "capaian": round(nilai * 100 / batas) if batas else None}
            for nilai, batas in zip(realisasi, target)
        ],
        "rata_ritase": _rasio(ritase, operasi),
        "muatan": _rasio(volume, ritase),
    }


def tanggal_laporan(nilai, hari_ini):
    try:
        return min(date.fromisoformat(nilai), hari_ini)
    except ValueError:
        return hari_ini


def riwayat_armada(nilai_tanggal, ekspeditur=None, laporan_demo=None):
    hari_ini = timezone.localdate()
    dipilih = tanggal_laporan(nilai_tanggal, hari_ini)
    pratinjau = (laporan_demo or {}).get(dipilih.isoformat()) if ekspeditur is not None else None
    daftar = (
        {ekspeditur.kode: (ekspeditur.nama, ekspeditur.nama_singkat)}
        if ekspeditur is not None else EKSPEDITUR
    )

    catatan = LAPORAN_HARIAN.get(dipilih, {})
    baris, realisasi_harian, target_harian = [], [], []
    for kode, (nama, _) in daftar.items():
        if pratinjau is not None:
            realisasi = tuple(pratinjau[kolom] for kolom in ("volume", "operasi", "ritase"))
            target = tuple(pratinjau[kolom] for kolom in ("target_volume", "target_operasi", "target_ritase"))
        elif kode in catatan:
            ready, _, _, _, target_volume = LAPORAN[kode]
            realisasi = catatan[kode]
            target = (target_volume, ready, TARGET_RITASE_CONTOH[kode])
        else:
            continue
        realisasi_harian.append(realisasi)
        target_harian.append(target)
        baris.append(_baris(nama, realisasi, target))

    total = None
    if baris and ekspeditur is None:
        total = _baris(
            "Total ekspeditur",
            tuple(map(sum, zip(*realisasi_harian))),
            tuple(map(sum, zip(*target_harian))),
        )

    return {
        "hari_ini": hari_ini,
        "dipilih": dipilih,
        "contoh": max(
            (hari for hari, hari_data in LAPORAN_HARIAN.items() if hari <= hari_ini and daftar.keys() & hari_data.keys()),
            default=None,
        ),
        "baris": baris,
        "total": total,
        "pratinjau": pratinjau,
    }
