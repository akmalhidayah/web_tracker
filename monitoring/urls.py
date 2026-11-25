from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import MasukForm
from .views import GantiSandi, buat_laporan, form_master_vendor, laporan, laporan_armada, master_vendor, monitoring, profil


app_name = "monitoring"
urlpatterns = [
    path(
        "masuk/",
        LoginView.as_view(
            template_name="monitoring/masuk.html",
            authentication_form=MasukForm,
            redirect_authenticated_user=True,
        ),
        name="masuk",
    ),
    path("keluar/", LogoutView.as_view(), name="keluar"),
    path("", monitoring, name="monitoring"),
    path("laporan/", laporan, name="laporan"),
    path("laporan/armada/", laporan_armada, name="laporan_armada"),
    path("laporan/buat/", buat_laporan, name="buat_laporan"),
    path("data-master/pengemudi/", master_vendor, {"jenis": "pengemudi"}, name="master_pengemudi"),
    path("data-master/pengemudi/tambah/", form_master_vendor, {"jenis": "pengemudi"}, name="master_pengemudi_tambah"),
    path("data-master/pengemudi/<int:pk>/ubah/", form_master_vendor, {"jenis": "pengemudi"}, name="master_pengemudi_ubah"),
    path("data-master/nomor-lambung/", master_vendor, {"jenis": "nomor_lambung"}, name="master_nomor_lambung"),
    path("data-master/nomor-lambung/tambah/", form_master_vendor, {"jenis": "nomor_lambung"}, name="master_nomor_lambung_tambah"),
    path("data-master/nomor-lambung/<int:pk>/ubah/", form_master_vendor, {"jenis": "nomor_lambung"}, name="master_nomor_lambung_ubah"),
    path("profil/", profil, name="profil"),
    path("profil/ganti-sandi/", GantiSandi.as_view(), name="ganti_sandi"),
]
