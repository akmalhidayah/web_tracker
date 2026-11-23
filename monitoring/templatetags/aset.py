from pathlib import Path

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static


register = template.Library()


@register.simple_tag
def aset_versi(nama):
    """Ubah URL aset lokal setiap kali hasil build berubah."""
    url = static(nama)
    jalur = finders.find(nama)
    if not jalur:
        return url
    return f"{url}?v={Path(jalur).stat().st_mtime_ns:x}"
