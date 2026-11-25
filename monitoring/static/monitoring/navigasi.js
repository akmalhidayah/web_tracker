(() => {
  const tombol = document.querySelector('.sidebar-toggle');
  const sidebar = document.getElementById('sidebar-utama');
  if (!tombol || !sidebar) return;

  const root = document.documentElement;
  const layarKecil = window.matchMedia('(max-width: 870px)');
  const kunci = 'tracker-tonasa.sidebar-desktop';
  const profil = document.querySelector('.profile-menu');
  const header = tombol.closest('.topbar');
  const latar = document.createElement('div');
  latar.className = 'sidebar-backdrop';
  latar.setAttribute('aria-hidden', 'true');
  sidebar.before(latar);
  const konten = document.querySelectorAll('.workspace > main, .tonasa-admin #main, .skip-link');
  const dinonaktifkan = new Set();
  let desktopTerbuka = true;
  try {
    desktopTerbuka = localStorage.getItem(kunci) !== 'tertutup';
  } catch {
    // Navigasi tetap bekerja jika browser memblokir penyimpanan.
  }

  function tampilkan(terbuka) {
    const label = terbuka ? 'Ringkas menu navigasi' : 'Perluas menu navigasi';
    root.dataset.sidebar = terbuka ? 'terbuka' : 'tertutup';
    tombol.setAttribute('aria-expanded', String(terbuka));
    tombol.setAttribute('aria-label', label);
    tombol.title = label;
    if (terbuka && layarKecil.matches) {
      for (const bagian of konten) {
        if (bagian.hasAttribute('inert')) continue;
        bagian.setAttribute('inert', '');
        dinonaktifkan.add(bagian);
      }
    } else {
      dinonaktifkan.forEach((bagian) => bagian.removeAttribute('inert'));
      dinonaktifkan.clear();
    }
  }

  function ukurHeader() {
    if (header) root.style.setProperty('--drawer-top', `${header.getBoundingClientRect().height}px`);
  }

  function sesuaikanLayar() {
    if (layarKecil.matches && sidebar.contains(document.activeElement)) tombol.focus({ preventScroll: true });
    tampilkan(!layarKecil.matches && desktopTerbuka);
  }

  tombol.hidden = false;
  sesuaikanLayar();
  ukurHeader();
  if (header) new ResizeObserver(ukurHeader).observe(header);
  layarKecil.addEventListener('change', sesuaikanLayar);

  tombol.addEventListener('click', (event) => {
    const terbuka = root.dataset.sidebar !== 'terbuka';
    tampilkan(terbuka);
    if (!layarKecil.matches) {
      desktopTerbuka = terbuka;
      try {
        localStorage.setItem(kunci, terbuka ? 'terbuka' : 'tertutup');
      } catch {
        // Pilihan tetap dipakai selama halaman ini terbuka.
      }
    }
    if (terbuka) {
      if (profil && layarKecil.matches) profil.open = false;
      if (event.detail === 0) sidebar.querySelector('nav a')?.focus({ preventScroll: true });
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape' || !layarKecil.matches || root.dataset.sidebar !== 'terbuka') return;
    tampilkan(false);
    tombol.focus({ preventScroll: true });
  });

  document.addEventListener('click', (event) => {
    if (!layarKecil.matches || root.dataset.sidebar !== 'terbuka') return;
    if (sidebar.contains(event.target) || tombol.contains(event.target)) return;
    if (sidebar.contains(document.activeElement)) tombol.focus({ preventScroll: true });
    tampilkan(false);
  });
})();
