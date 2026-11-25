from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AdminUserCreationForm, AuthenticationForm, UserChangeForm
from django.db.models import Q
from django.utils import timezone

from .akun import ekspeditur_akun
from .akun_sopir import nomor_hp_login, truk_untuk_sopir
from .models import AkunSopir, Ekspeditur, Pengemudi, Truk


class AksesPenggunaForm(forms.Form):
    ADMIN = "admin"
    VENDOR = "vendor"
    peran = forms.ChoiceField(choices=((ADMIN, "Admin"), (VENDOR, "Vendor")))
    ekspeditur = forms.ModelChoiceField(
        queryset=Ekspeditur.objects.all(),
        label="Ekspeditur",
        required=False,
        help_text="Wajib untuk Vendor. Akses vendor mengikuti status aktif Ekspeditur.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.setdefault("peran", self.ADMIN if self.instance.is_superuser else self.VENDOR)
        akses = getattr(self.instance, "akses_vendor", None)
        if akses:
            self.initial.setdefault("ekspeditur", akses.ekspeditur_id)

    def clean(self):
        data = super().clean()
        if data.get("peran") == self.VENDOR and not data.get("ekspeditur") and "ekspeditur" not in self.errors:
            self.add_error("ekspeditur", "Pilih Ekspeditur untuk akun Vendor.")
        return data


class PenggunaTambahForm(AksesPenggunaForm, AdminUserCreationForm):
    pass


class PenggunaUbahForm(AksesPenggunaForm, UserChangeForm):
    pass


class PilihanNomorLambung(forms.ModelMultipleChoiceField):
    def label_from_instance(self, truk):
        return f"{truk.nomor} · {truk.ekspeditur.nama_singkat}"


class PengemudiForm(forms.ModelForm):
    pin_baru = forms.RegexField(
        r"\A[0-9]{6}\Z", label="PIN baru", required=False, min_length=6, max_length=6,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "autocomplete": "new-password"}),
        error_messages={"invalid": "PIN harus tepat enam digit angka."},
        help_text="Isi untuk mengaktifkan login mobile atau mereset PIN. Reset mengakhiri sesi login sebelumnya.",
    )
    truk_ditugaskan = PilihanNomorLambung(
        queryset=Truk.objects.filter(aktif=True, ekspeditur__aktif=True).select_related("ekspeditur"),
        required=False, label="Truk yang ditugaskan",
        widget=FilteredSelectMultiple("nomor lambung", is_stacked=False),
        help_text="Cari dan pilih beberapa nomor lambung dari Ekspeditur pengemudi.",
    )

    class Meta:
        model = Pengemudi
        fields = ("nama", "ekspeditur", "nomor_hp", "aktif")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial.setdefault("truk_ditugaskan", truk_untuk_sopir(self.instance).values_list("pk", flat=True))

    def clean(self):
        data = super().clean()
        ekspeditur = data.get("ekspeditur")
        if ekspeditur and any(truk.ekspeditur_id != ekspeditur.pk for truk in data.get("truk_ditugaskan", ())):
            self.add_error("truk_ditugaskan", "Pilih truk dari Ekspeditur pengemudi ini.")

        if (data.get("pin_baru") or getattr(self.instance, "akun_sopir", None)) and "nomor_hp" in data:
            try:
                nomor = nomor_hp_login(data["nomor_hp"])
            except ValueError as error:
                self.add_error("nomor_hp", str(error))
            else:
                if AkunSopir.objects.filter(nomor_hp=nomor).exclude(pengemudi_id=self.instance.pk).exists():
                    self.add_error("nomor_hp", "Nomor HP ini sudah dipakai akun sopir lain.")
                else:
                    data["nomor_hp"] = nomor
        return data


class PilihanNomorLambungVendor(forms.ModelMultipleChoiceField):
    def label_from_instance(self, truk):
        return truk.nomor if truk.aktif else f"{truk.nomor} (Nonaktif)"


class PengemudiVendorForm(PengemudiForm):
    truk_ditugaskan = PilihanNomorLambungVendor(
        queryset=Truk.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Nomor lambung yang ditugaskan",
        help_text="Pilih nomor lambung yang boleh digunakan pengemudi di aplikasi sopir.",
    )

    class Meta(PengemudiForm.Meta):
        fields = ("nama", "nomor_hp", "pin_baru", "aktif", "truk_ditugaskan")
        widgets = {"nomor_hp": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        truk = Truk.objects.filter(ekspeditur_id=self.instance.ekspeditur_id)
        if self.instance.pk:
            penugasan = self.instance.penugasan_truk.filter(berakhir__isnull=True).values("truk_id")
            self.initial["truk_ditugaskan"] = truk.filter(pk__in=penugasan).values_list("pk", flat=True)
            truk = truk.filter(Q(aktif=True) | Q(pk__in=penugasan))
        else:
            truk = truk.filter(aktif=True)
        self.fields["truk_ditugaskan"].queryset = truk


class TrukVendorForm(forms.ModelForm):
    class Meta:
        model = Truk
        fields = ("nomor", "plat", "kapasitas", "aktif")

    def clean_nomor(self):
        nomor = self.cleaned_data["nomor"]
        if Truk.objects.filter(nomor__iexact=nomor).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Nomor lambung ini sudah terdaftar.")
        return nomor


class MasukForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Periksa kembali nama pengguna dan kata sandi Anda.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username = self.fields["username"].widget.attrs
        username.pop("autofocus", None)
        username.update({"autocapitalize": "none", "spellcheck": "false"})

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser and ekspeditur_akun(user) is None:
            raise forms.ValidationError("Akun ini memerlukan Ekspeditur aktif. Hubungi admin.")


class BuatLaporanForm(forms.Form):
    tanggal = forms.DateField(
        label="Tanggal laporan (WITA)",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    ready = forms.IntegerField(label="Armada ready (unit)", min_value=0)
    volume = forms.IntegerField(label="Realisasi pengiriman (ton)", min_value=0)
    operasi = forms.IntegerField(label="Realisasi armada operasi (unit)", min_value=0)
    ritase = forms.IntegerField(label="Realisasi ritase (ret)", min_value=0)
    target_volume = forms.IntegerField(label="Target pengiriman (ton)", min_value=0)
    target_operasi = forms.IntegerField(label="Target armada operasi (unit)", min_value=0)
    target_ritase = forms.IntegerField(label="Target ritase (ret)", min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hari_ini = timezone.localdate()
        self.fields["tanggal"].widget.attrs["max"] = self.hari_ini.isoformat()

    def clean_tanggal(self):
        tanggal = self.cleaned_data["tanggal"]
        if tanggal > self.hari_ini:
            raise forms.ValidationError("Tanggal laporan tidak boleh melewati hari ini (WITA).")
        return tanggal

    def clean(self):
        data = super().clean()
        if "operasi" in data and "ready" in data and data["operasi"] > data["ready"]:
            self.add_error("operasi", "Armada operasi maksimal sebanyak armada ready.")
        return data


class ProfilForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Nama depan",
            "last_name": "Nama belakang",
            "email": "Alamat email",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }
