from django import template
from django.contrib import admin
from django.urls import reverse

from ..akun import ekspeditur_akun


register = template.Library()
register.simple_tag(ekspeditur_akun)


@register.simple_tag(takes_context=True)
def menu_master(context, ekspeditur_vendor=None):
    request = context["request"]
    if ekspeditur_vendor is not None:
        links = []
        for label, nama_url, icon in (
            ("Pengemudi", "monitoring:master_pengemudi", "orang"),
            ("Nomor Lambung", "monitoring:master_nomor_lambung", "truk"),
        ):
            url = reverse(nama_url)
            links.append({"label": label, "url": url, "icon": icon, "current": request.path.startswith(url)})
        return links
    if not request.user.is_superuser or not admin.site.has_permission(request):
        return []

    apps = context.get("available_apps")
    if apps is None:
        apps = admin.site.get_app_list(request)
    models = {
        (app["app_label"], model["object_name"]): model
        for app in apps
        for model in app["models"]
    }
    entries = (
        ("monitoring", "Ekspeditur", "Ekspeditur", "vendor"),
        ("monitoring", "Truk", "Truk", "truk"),
        ("monitoring", "Pengemudi", "Pengemudi", "orang"),
        ("auth", "User", "User Panel", "akses"),
    )
    match = request.resolver_match
    admin_route = (match.url_name or "") if match and match.namespace == "admin" else ""
    links = []
    for app_label, model_name, label, icon in entries:
        model = models.get((app_label, model_name), {})
        destination = model.get("admin_url") or model.get("add_url")
        if destination:
            prefix = f"{app_label}_{model_name.lower()}_"
            current = admin_route.startswith(prefix) or (
                model_name == "User" and admin_route.startswith("auth_group_")
            )
            links.append({"label": label, "url": destination, "current": current, "icon": icon})
    return links


IKON_MODEL = {
    "ekspeditur": "vendor",
    "truk": "truk",
    "pengemudi": "orang",
    "user": "akses",
    "group": "akses",
}


@register.simple_tag
def panel_ikon(opts):
    """Nama ikon di partials/ikon.html untuk model ``opts``."""
    return IKON_MODEL.get(opts.model_name, "master")
