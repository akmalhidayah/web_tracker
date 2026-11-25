from django.urls import path

from monitoring.api_sopir import (
    KeluarSopir,
    MasukSopir,
    PilihTrukSopir,
    PulihkanSesiSopir,
    SetujuSopir,
    TrukSopir,
)


urlpatterns = [
    path("api/v1/driver/login/", MasukSopir.as_view(), name="api_masuk_sopir"),
    path("api/v1/driver/session/", PulihkanSesiSopir.as_view(), name="api_sesi_sopir"),
    path("api/v1/driver/consent/", SetujuSopir.as_view(), name="api_setuju_sopir"),
    path("api/v1/driver/logout/", KeluarSopir.as_view(), name="api_keluar_sopir"),
    path("api/v1/driver/trucks/", TrukSopir.as_view(), name="api_truk_sopir"),
    path("api/v1/driver/selected-truck/", PilihTrukSopir.as_view(), name="api_pilih_truk_sopir"),
]
