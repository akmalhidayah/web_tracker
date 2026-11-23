from django.contrib import admin
from django.urls import include, path, reverse_lazy


admin.site.site_header = "Administrasi Tracker Tonasa"
admin.site.site_title = "Tracker Tonasa"
admin.site.index_title = "Data master dan pengguna"
admin.site.site_url = reverse_lazy("monitoring:monitoring")
admin.site.enable_nav_sidebar = False

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("monitoring.urls")),
]
