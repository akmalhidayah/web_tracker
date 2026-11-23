from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import MasukForm
from .views import GantiSandi, laporan, monitoring, profil


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
    path("profil/", profil, name="profil"),
    path("profil/ganti-sandi/", GantiSandi.as_view(), name="ganti_sandi"),
]
