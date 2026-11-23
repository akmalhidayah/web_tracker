from math import ceil


def grafik_armada(baris, total):
    """Siapkan koordinat SVG. Unit armada dan ritase memakai skala terpisah."""
    bawah, tinggi = 176, 128
    bagian = 5

    def sumbu(maksimum, kelipatan):
        langkah = kelipatan * max(1, ceil(maksimum / (bagian * kelipatan)))
        return langkah, lambda nilai: bawah - round(tinggi * nilai / (langkah * bagian))

    maksimum_unit = max((max(item["ready"], item["operasi"]) for item in baris), default=0)
    langkah_unit, y_unit = sumbu(maksimum_unit, 10)
    langkah_ritase, y_ritase = sumbu(max((item["ritase"] for item in baris), default=0), 10)
    langkah_total, y_total = sumbu(max(total["ready"], total["operasi"]), 20)

    def batang(nilai, x, skala):
        y = skala(nilai)
        return {
            "x": x, "y": y, "nilai": nilai, "tinggi": bawah - y,
            "label_x": x + 10,
            "label_y": bawah - 6 if bawah - y >= 17 else y - 4,
        }

    grup = []
    for indeks, item in enumerate(baris):
        x = 38 + round((indeks + .5) * 468 / len(baris))
        operasi = batang(item["operasi"], x - 1, y_unit)
        grup.append({
            "nama": item["nama"], "singkat": item["singkat"], "x": x,
            "ready": batang(item["ready"], x - 24, y_unit),
            "operasi": operasi,
            "badge_x": operasi["label_x"],
            "badge_y": operasi["y"] - 21 if item["operasi"] else bawah - 30,
            "utilisasi": item["utilisasi"], "ritase": item["ritase"],
            "ritase_x": x + 33, "ritase_y": y_ritase(item["ritase"]),
            "ritase_label_y": y_ritase(item["ritase"]) - 10,
        })

    return {
        "skala": [
            {"y": y_unit(i * langkah_unit), "unit": i * langkah_unit, "ritase": i * langkah_ritase}
            for i in range(bagian + 1)
        ],
        "per_ekspeditur": grup,
        "garis_ritase": " ".join(f'{g["ritase_x"]},{g["ritase_y"]}' for g in grup),
        "total": {
            "ready": batang(total["ready"], 52, y_total),
            "operasi": batang(total["operasi"], 75, y_total),
            "utilisasi": total["utilisasi"],
            "badge_y": y_total(total["operasi"]) - 21 if total["operasi"] else bawah - 30,
            "skala": [
                {"y": y_total(i * langkah_total), "unit": i * langkah_total}
                for i in range(bagian + 1)
            ],
        },
    }
