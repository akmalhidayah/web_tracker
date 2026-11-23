(() => {
  const tombol = document.querySelector('.login-password-toggle');
  const kolom = tombol && document.getElementById(tombol.getAttribute('aria-controls'));
  if (!kolom) return;

  tombol.hidden = false;
  tombol.addEventListener('click', () => {
    const tampil = kolom.type === 'password';
    kolom.type = tampil ? 'text' : 'password';
    tombol.setAttribute('aria-pressed', String(tampil));
  });
})();
