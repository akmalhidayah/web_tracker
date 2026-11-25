from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


WAKTU_CONTOH = datetime(2026, 11, 17, 13, 0, tzinfo=ZoneInfo("Asia/Makassar"))

EKSPEDITUR = {
    "fajar": ("PT. Fajar Trans Sejahtera", "Fajar Trans"),
    "koperasi": ("Koperasi Produsen Karyawan Semen Tonasa", "Koperasi ST"),
    "topabiring": ("PT. Topabiring Trans Logistik", "Topabiring"),
    "prima": ("PT. Prima Karya Manunggal", "Prima Karya"),
    "tambahan": ("Armada Tambahan", "Armada Tambahan"),
}

# Ready, operasi, ritase, volume (ton penuh), dan target (ton) dari laporan.
LAPORAN = {
    "fajar": (45, 38, 68, 2288, 6075),
    "koperasi": (17, 11, 21, 611, 2040),
    "topabiring": (12, 10, 21, 627, 1800),
    "prima": (15, 10, 17, 513, 2250),
    "tambahan": (5, 0, 0, 0, 600),
}

TARGET_RITASE_CONTOH = {
    "fajar": 203, "koperasi": 68, "topabiring": 60, "prima": 75, "tambahan": 20,
}

# Volume ton penuh, armada operasi, dan jumlah ritase dari laporan harian.
LAPORAN_HARIAN = {
    date(2026, 11, 13): {
        "fajar": (6490, 46, 186), "koperasi": (1329, 15, 45),
        "topabiring": (1616, 12, 55), "prima": (2549, 16, 85),
        "tambahan": (181, 3, 6),
    },
    date(2026, 11, 14): {
        "fajar": (6801, 43, 208), "koperasi": (1821, 17, 63),
        "topabiring": (1690, 11, 59), "prima": (1829, 15, 62),
        "tambahan": (189, 3, 7),
    },
    date(2026, 11, 15): {
        "fajar": (6753, 50, 187), "koperasi": (2054, 17, 72),
        "topabiring": (1221, 8, 40), "prima": (1751, 11, 59),
        "tambahan": (89, 3, 3),
    },
    date(2026, 11, 16): {
        "fajar": (4819, 47, 141), "koperasi": (781, 15, 26),
        "topabiring": (986, 10, 33), "prima": (1749, 12, 58),
        "tambahan": (0, 0, 0),
    },
    WAKTU_CONTOH.date(): {
        kode: (volume, operasi, ritase)
        for kode, (_, operasi, ritase, volume, _) in LAPORAN.items()
    },
}

# Koordinat pin hasil mapping.
AREA = [
    {
        "nama": "Muat · Limestone Crusher 2",
        "jenis": "muat",
        "posisi": (-4.7835447437522305, 119.62012886932237),
    },
    {
        "nama": "Bongkar · Biringkassi",
        "jenis": "bongkar",
        "posisi": (-4.818083399198741, 119.49784845111566),
    },
]

# Rute demo berdasarkan OSRM/FOSSGIS dan data jalan OpenStreetMap.
# Segmen pendek yang menyambung jalan ke masing-masing pin adalah ilustrasi.
RUTE = (
    AREA[0]["posisi"],
    (-4.787019, 119.619387), (-4.787206, 119.618777), (-4.788369, 119.618620),
    (-4.787516, 119.617588), (-4.787467, 119.615357), (-4.788838, 119.615167),
    (-4.789808, 119.611832), (-4.799642, 119.607357), (-4.800599, 119.606003),
    (-4.802312, 119.597268), (-4.800588, 119.587864), (-4.801320, 119.580551),
    (-4.806854, 119.573131), (-4.809870, 119.557159), (-4.812198, 119.553396),
    (-4.813123, 119.549421), (-4.814974, 119.545397), (-4.813215, 119.540819),
    (-4.8146665, 119.5221265), (-4.816118, 119.503434), (-4.817203, 119.503368),
    (-4.817425, 119.499013), (-4.817972, 119.498981),
    AREA[-1]["posisi"],
)

# Nomor lambung, ekspeditur, tahap, posisi, umur dalam menit, ritase, baterai.
TRUK = (
    ("DT-31", "fajar", "muat", RUTE[0], 2, 3, 84),
    ("DT-32", "fajar", "bermuatan", RUTE[7], 3, 2, 91),
    ("DT-51", "koperasi", "kosong", RUTE[9], 3, 3, 77),
    ("DT-52", "koperasi", "bermuatan", RUTE[11], 2, 2, 86),
    ("DT-03", "topabiring", "kosong", RUTE[13], 1, 2, 74),
    ("DT-07", "topabiring", "bongkar", RUTE[-1], 2, 3, 92),
    ("DT-61", "prima", "bermuatan", RUTE[14], 2, 2, 58),
    ("DT-63", "prima", "kosong", RUTE[18], 4, 2, 71),
    ("DT-91", "tambahan", "kosong", RUTE[19], 15, 1, 49),
    ("DT-92", "tambahan", "bermuatan", RUTE[10], 3, 2, 82),
)

# Sesi selesai simulasi. Nama dan nomor lambung mengikuti akun serta armada demo.
# Pengemudi, ekspeditur, nomor lambung, jam mulai WITA, jam selesai WITA, ritase.
SESI_ARMADA_CONTOH = {
    WAKTU_CONTOH.date(): (
        ("Rahmat", "topabiring", "DT-07", time(6, 0), time(9, 25), 3),
        ("Rahmat", "topabiring", "DT-03", time(9, 50), time(12, 20), 2),
        ("Hasan", "fajar", "DT-31", time(5, 55), time(9, 15), 3),
        ("Hasan", "fajar", "DT-32", time(9, 35), time(12, 40), 2),
        ("Yusuf", "koperasi", "DT-51", time(6, 10), time(10, 5), 3),
        ("Yusuf", "koperasi", "DT-52", time(10, 24), time(12, 52), 2),
        ("Andi", "prima", "DT-61", time(6, 20), time(9, 40), 2),
        ("Andi", "prima", "DT-63", time(10, 0), time(12, 35), 2),
        ("Dedi", "tambahan", "DT-91", time(7, 0), time(9, 30), 1),
        ("Dedi", "tambahan", "DT-92", time(9, 50), time(12, 30), 2),
    ),
    WAKTU_CONTOH.date() - timedelta(days=1): (
        ("Rahmat", "topabiring", "DT-07", time(22, 15), time(2, 30), 3),
    ),
}


def sesi_armada_contoh(tanggal, kode_ekspeditur, cari, nama_ekspeditur):
    hasil = []
    kata = cari.casefold()
    kapasitas_ton = 30
    for pengemudi, kode, nomor, jam_mulai, jam_selesai, ritase in SESI_ARMADA_CONTOH.get(tanggal, ()):
        if kode_ekspeditur is not None and kode != kode_ekspeditur:
            continue
        if kata not in pengemudi.casefold() and kata not in nomor.casefold():
            continue
        mulai = datetime.combine(tanggal, jam_mulai, WAKTU_CONTOH.tzinfo)
        selesai = datetime.combine(tanggal, jam_selesai, WAKTU_CONTOH.tzinfo)
        if selesai < mulai:
            selesai += timedelta(days=1)
        jam, menit = divmod((selesai - mulai) // timedelta(minutes=1), 60)
        hasil.append({
            "pengemudi": pengemudi,
            "ekspeditur": nama_ekspeditur.get(kode, EKSPEDITUR[kode][1]),
            "nomor": nomor,
            "mulai": mulai,
            "selesai": selesai,
            "lintas_hari": selesai.date() != tanggal,
            "durasi": f"{jam} j {menit:02d} m",
            "ritase": ritase,
            "estimasi_muatan": ritase * kapasitas_ton,
        })
    return sorted(hasil, key=lambda sesi: sesi["mulai"], reverse=True)


def data_peta(daftar_ekspeditur, daftar_truk):
    posisi_contoh = {
        (nomor, kode): {
            "tahap": tahap,
            "posisi": posisi,
            "ritase": ritase,
            "baterai": baterai,
            "terakhir": (WAKTU_CONTOH - timedelta(minutes=umur)).isoformat(),
        }
        for nomor, kode, tahap, posisi, umur, ritase, baterai in TRUK
    }
    return {
        "waktu": WAKTU_CONTOH.isoformat(),
        "ekspeditur": [
            {"id": kode, "nama": nama, "singkat": singkat, "warna": warna}
            for kode, nama, singkat, warna in daftar_ekspeditur
        ],
        "rute": RUTE,
        "area": AREA,
        "truk": [
            {
                "nomor": nomor,
                "ekspeditur": kode,
                **posisi_contoh.get((nomor.upper(), kode), {"posisi": None}),
            }
            for nomor, kode in daftar_truk
        ],
    }
