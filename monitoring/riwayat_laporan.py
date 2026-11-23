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


def riwayat_armada(nilai_tanggal):
    hari_ini = timezone.localdate()
    try:
        dipilih = min(date.fromisoformat(nilai_tanggal), hari_ini)
    except ValueError:
        dipilih = hari_ini

    catatan = LAPORAN_HARIAN.get(dipilih, {})
    baris, realisasi_harian, target_harian = [], [], []
    for kode, (nama, _) in EKSPEDITUR.items():
        if kode not in catatan:
            continue
        ready, _, _, _, target_volume = LAPORAN[kode]
        target = (target_volume, ready, TARGET_RITASE_CONTOH[kode])
        realisasi_harian.append(catatan[kode])
        target_harian.append(target)
        baris.append(_baris(nama, catatan[kode], target))

    total = None
    if baris:
        total = _baris(
            "Total ekspeditur",
            tuple(map(sum, zip(*realisasi_harian))),
            tuple(map(sum, zip(*target_harian))),
        )

    return {
        "hari_ini": hari_ini,
        "dipilih": dipilih,
        "contoh": max((hari for hari in LAPORAN_HARIAN if hari <= hari_ini), default=None),
        "baris": baris,
        "total": total,
    }
