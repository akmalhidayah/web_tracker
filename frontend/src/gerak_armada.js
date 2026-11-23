const METER_PER_DERAJAT = 111195;
const DURASI_LINTASAN_DETIK = 180;
const JEDA_POSISI_MS = 2500;

export function buatLintasan(koordinat) {
  const skalaBujur = METER_PER_DERAJAT * Math.cos(koordinat[0][0] * Math.PI / 180);
  let panjang = 0;
  const ruas = [];

  for (let i = 1; i < koordinat.length; i += 1) {
    const [lat, lon] = koordinat[i - 1];
    const [latAkhir, lonAkhir] = koordinat[i];
    const utara = (latAkhir - lat) * METER_PER_DERAJAT;
    const timur = (lonAkhir - lon) * skalaBujur;
    const jarak = Math.hypot(utara, timur);
    if (!jarak) continue;
    ruas.push({ lat, lon, utara, timur, jarak, awal: panjang });
    panjang += jarak;
  }

  function jarakTerdekat([lat, lon]) {
    let jarakAwal = 0;
    let selisihMin = Infinity;
    for (const ruasRute of ruas) {
      const utara = (lat - ruasRute.lat) * METER_PER_DERAJAT;
      const timur = (lon - ruasRute.lon) * skalaBujur;
      const proyeksi = (utara * ruasRute.utara + timur * ruasRute.timur) / ruasRute.jarak ** 2;
      const fraksi = Math.max(0, Math.min(1, proyeksi));
      const selisih = Math.hypot(utara - fraksi * ruasRute.utara, timur - fraksi * ruasRute.timur);
      if (selisih < selisihMin) {
        selisihMin = selisih;
        jarakAwal = ruasRute.awal + fraksi * ruasRute.jarak;
      }
    }
    return jarakAwal;
  }

  function posisiBergerak(jarakAwal, arah, detik) {
    // Setelah mencapai tujuan, ulangi perjalanan demo menurut arah semula.
    const jarak = jarakAwal + arah * detik * panjang / DURASI_LINTASAN_DETIK;
    const padaRute = ((jarak % panjang) + panjang) % panjang;
    const ruasRute = ruas.find((item) => padaRute < item.awal + item.jarak) ?? ruas[ruas.length - 1];
    const fraksi = (padaRute - ruasRute.awal) / ruasRute.jarak;
    return {
      posisi: [
        ruasRute.lat + fraksi * ruasRute.utara / METER_PER_DERAJAT,
        ruasRute.lon + fraksi * ruasRute.timur / skalaBujur,
      ],
      hadapKiri: arah * ruasRute.timur < 0,
    };
  }

  return { panjang, jarakTerdekat, posisiBergerak };
}

export function gerakkanTruk(truk, lintasan, waktuGerak, kurangiGerak) {
  if (!truk.length) return;

  function perbaruiPosisi(milidetik) {
    waktuGerak.detik += milidetik / 1000;
    for (const { marker, jarakAwal, arah } of truk) {
      const { posisi, hadapKiri } = lintasan.posisiBergerak(jarakAwal, arah, waktuGerak.detik);
      marker.setLatLng(posisi);
      marker.getElement()?.classList.toggle("pin-arah-balik", hadapKiri);
    }
  }

  if (kurangiGerak) {
    const timer = window.setInterval(() => {
      if (!document.hidden) perbaruiPosisi(JEDA_POSISI_MS);
    }, JEDA_POSISI_MS);
    return () => window.clearInterval(timer);
  }

  let frame;
  let pembaruanTerakhir = performance.now();

  function perbarui(waktu) {
    if (waktu - pembaruanTerakhir >= 40) {
      perbaruiPosisi(Math.min(waktu - pembaruanTerakhir, 100));
      pembaruanTerakhir = waktu;
    }
    frame = requestAnimationFrame(perbarui);
  }

  frame = requestAnimationFrame(perbarui);
  return () => cancelAnimationFrame(frame);
}
