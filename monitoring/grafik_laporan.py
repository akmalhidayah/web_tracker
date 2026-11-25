def grafik_armada(baris, total):
    """Siapkan koordinat SVG. Unit armada dan ritase memakai skala terpisah."""
    bawah, tinggi = 158, 132
    kiri = 44
    lebar_plot = max(172, 94 * len(baris))
    bagian = 5

    def sumbu(maksimum):
        minimum = max(1, (maksimum + bagian - 1) // bagian)
        orde = 10 ** (len(str(minimum)) - 1)
        langkah = next(orde * angka for angka in (1, 2, 5, 10) if orde * angka >= minimum)
        return lambda nilai: bawah - round(tinggi * nilai / (langkah * bagian))

    maksimum_unit = max((max(item["ready"], item["operasi"]) for item in baris), default=0)
    y_unit = sumbu(maksimum_unit)
    y_ritase = sumbu(max((item["ritase"] for item in baris), default=0))

    def batang(nilai, x):
        y = y_unit(nilai)
        label_di_dalam = bawah - y >= 20
        return {
            "x": x, "y": y, "nilai": nilai, "tinggi": bawah - y,
            "label_x": x + 11,
            "label_y": bawah - 6 if label_di_dalam else y - 5,
            "label_di_dalam": label_di_dalam,
        }

    grup = []
    for indeks, item in enumerate(baris):
        x = kiri + round((indeks + .5) * lebar_plot / len(baris))
        ritase_y = y_ritase(item["ritase"])
        grup.append({
            "nama": item["nama"], "singkat": item["singkat"], "x": x,
            "ready": batang(item["ready"], x - 25),
            "operasi": batang(item["operasi"], x + 3),
            "utilisasi": item["utilisasi"], "ritase": item["ritase"],
            "ritase_y": ritase_y, "ritase_label_y": ritase_y - 13,
        })

    return {
        "lebar": lebar_plot + 2 * kiri,
        "lebar_minimum": lebar_plot + kiri,
        "per_ekspeditur": grup,
        "garis_ritase": " ".join(f'{g["x"]},{g["ritase_y"]}' for g in grup),
        "total": total,
    }
