def ekspeditur_akun(pengguna):
    if pengguna.is_superuser:
        return None
    akses = getattr(pengguna, "akses_vendor", None)
    if akses and akses.ekspeditur.aktif:
        return akses.ekspeditur
    return None
