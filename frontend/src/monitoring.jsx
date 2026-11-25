import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Boxes, ChevronRight, Layers, LocateFixed, Maximize, Minimize, Route, Search, TriangleAlert, Truck, X } from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { buatLintasan, gerakkanTruk } from "./gerak_armada.js";
import { buatPetaRingkas } from "./peta_ringkas.js";

const STATUS = {
  kosong: "Kosong",
  muat: "Muat",
  bermuatan: "Bermuatan",
  bongkar: "Bongkar",
  terlambat: "Data terlambat",
  "tanpa-data": "Belum ada posisi",
};
const ZONA_WITA = "Asia/Makassar";
const JAM_WITA = new Intl.DateTimeFormat("id-ID", {
  timeZone: ZONA_WITA,
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});
const HARI_KALENDER = new Intl.DateTimeFormat("id-ID", { weekday: "short", timeZone: "UTC" });
const TANGGAL_KALENDER = new Intl.DateTimeFormat("id-ID", { dateStyle: "full", timeZone: "UTC" });
const TANGGAL_WITA = new Intl.DateTimeFormat("id-ID", { dateStyle: "full", timeZone: ZONA_WITA });
const JAM_LENGKAP_WITA = new Intl.DateTimeFormat("id-ID", {
  hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false, timeZone: ZONA_WITA,
});
const MILIDETIK_PER_HARI = 86_400_000;
const BATAS_TERLAMBAT_MENIT = 10;
const KUERI_KURANGI_GERAK = "(prefers-reduced-motion: reduce)";
const normalisasi = (teks) => teks.trim().toUpperCase().replace(/[\s-]/g, "");

function gayaEkspeditur(ekspeditur) {
  const warna = ekspeditur.warna ?? "#475569";
  return { "--vendor-ink": warna, "--vendor-tint": `${warna}18` };
}

function RingkasanArmada({ truk }) {
  const tepatWaktu = truk.filter((unit) => unit.posisi && unit.status !== "terlambat");
  const perjalanan = tepatWaktu.filter(({ tahap }) => tahap === "kosong" || tahap === "bermuatan");
  const metrik = [
    { label: "Armada aktif", nilai: truk.length, ikon: Truck, warna: "jingga" },
    { label: "Dalam perjalanan", nilai: perjalanan.length, ikon: Route, warna: "ungu" },
    { label: "Muat atau bongkar", nilai: tepatWaktu.length - perjalanan.length, ikon: Boxes, warna: "toska" },
    { label: "Data terlambat", nilai: truk.filter((unit) => unit.status === "terlambat").length, ikon: TriangleAlert, warna: "merah-muda" },
  ];
  return (
    <dl className="metrics monitor-metrics" aria-label="Ringkasan seluruh armada simulasi">
      {metrik.map(({ label, nilai, ikon: Ikon, warna }) => (
        <div className={`metric monitor-metric monitor-metric-${warna}`} key={label}>
          <dt><span className="tile-icon"><Ikon size={19} aria-hidden="true" /></span>{label}</dt>
          <dd>{nilai} <small>unit</small></dd>
        </div>
      ))}
    </dl>
  );
}

function JamPeta() {
  const [sekarang, aturSekarang] = useState(() => new Date());

  useEffect(() => {
    const interval = window.setInterval(() => aturSekarang(new Date()), 1000);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <h2 className="map-clock">
      <time dateTime={sekarang.toISOString()}>
        <span>{TANGGAL_WITA.format(sekarang)}</span>
        <span className="map-clock-time">{JAM_LENGKAP_WITA.format(sekarang)} WITA</span>
      </time>
    </h2>
  );
}

function KalenderPeta({ tanggal, tanggalPeta, hariIni, pilihTanggal, children }) {
  const terpilih = new Date(tanggal);
  const geser = (hari) => new Date(terpilih.getTime() + hari * MILIDETIK_PER_HARI);
  const awal = (terpilih.getUTCDay() + 6) % 7;
  const pekan = Array.from({ length: 7 }, (_, indeks) => geser(indeks - awal));
  const iso = (hari) => hari.toISOString().slice(0, 10);

  return (
    <div className="map-calendar">
      <div className="map-calendar-heading">
        <JamPeta />
        {children}
      </div>
      <div className="map-week-days" role="group" aria-label="Tanggal data peta">
        {pekan.map((hari) => {
          const nilai = iso(hari);
          const punyaPosisi = nilai === tanggalPeta;
          const label = TANGGAL_KALENDER.format(hari);

          return (
            <button
              className="map-day" type="button" key={nilai} disabled={nilai > hariIni}
              aria-label={punyaPosisi ? `${label}, data simulasi tersedia` : label}
              aria-pressed={nilai === tanggal} aria-current={nilai === hariIni ? "date" : undefined}
              onClick={() => pilihTanggal(nilai)}
            >
              <span>{HARI_KALENDER.format(hari)}</span>
              <time dateTime={nilai}>{hari.getUTCDate()}</time>
              {punyaPosisi && <span className="map-day-dot" aria-hidden="true" />}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function buatLabel(teks, kelas) {
  const label = document.createElement("span");
  label.textContent = teks;
  if (kelas) label.className = kelas;
  return label;
}

function buatLabelLokasi(nama, jenis) {
  const label = document.createElement("div");
  label.className = `isi-label-lokasi tone-${jenis}`;
  label.append(
    buatLabel(STATUS[jenis], "jenis-lokasi"),
    buatLabel(nama.replace(/^(Muat|Bongkar)\s*·\s*/, ""), "nama-lokasi"),
  );
  return label;
}

function LegendaPeta({ ekspeditur }) {
  return (
    <aside className="map-legend" aria-label="Legenda peta">
      <div className="legend-group">
        <h3>Ekspeditur</h3>
        <ul className="legend" aria-label="Warna ikon truk per ekspeditur">
          {ekspeditur.map((vendor) => (
            <li key={vendor.id} style={gayaEkspeditur(vendor)}>
              <Truck size={14} className="legend-truck" aria-hidden="true" />{vendor.singkat}
            </li>
          ))}
        </ul>
      </div>
      <div className="legend-group">
        <h3>Status truk</h3>
        <ul className="legend" aria-label="Warna titik status">
          {Object.entries(STATUS).map(([id, label]) => (
            <li key={id} title={id === "terlambat" ? "Data lebih dari 10 menit" : undefined}>
              <span className={`status-dot tone-${id}`} />{label}
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

function PetaArmada({ data, ekspeditur, truk, terpilih, pilihTruk }) {
  const tanggalPeta = data.waktu.slice(0, 10);
  const [tanggal, pilihTanggal] = useState(tanggalPeta);
  const adaPosisi = tanggal === tanggalPeta;
  const wadah = useRef(null);
  const panel = useRef(null);
  const tombolLayarPenuh = useRef(null);
  const elemen = useRef(null);
  const peta = useRef(null);
  const marker = useRef(new Map());
  const trukBerjalan = useRef([]);
  const waktuGerak = useRef({ detik: 0 });
  const lintasan = useMemo(() => buatLintasan(data.rute), [data.rute]);
  const [detailPeta, setDetailPeta] = useState(false);
  const [ringkasGagal, setRingkasGagal] = useState(false);
  const [petaDasarTidakLengkap, setPetaDasarTidakLengkap] = useState(false);
  const [kurangiGerak, setKurangiGerak] = useState(() => window.matchMedia(KUERI_KURANGI_GERAK).matches);
  const [layarPenuh, setLayarPenuh] = useState(null);

  useEffect(() => {
    const sinkronkanLayarPenuh = () => {
      if (document.fullscreenElement === panel.current) setLayarPenuh("native");
      else setLayarPenuh((mode) => mode === "native" ? null : mode);
    };
    document.addEventListener("fullscreenchange", sinkronkanLayarPenuh);
    return () => document.removeEventListener("fullscreenchange", sinkronkanLayarPenuh);
  }, []);

  useLayoutEffect(() => {
    if (!layarPenuh) wadah.current.style.minHeight = "";
    if (layarPenuh !== "jendela") return;

    // Saat fullscreen native tidak tersedia, batasi interaksi ke panel yang memenuhi jendela.
    const luarPeta = [];
    for (let node = panel.current; node !== document.body; node = node.parentElement) {
      for (const saudara of node.parentElement.children) {
        if (saudara !== node && !saudara.hasAttribute("inert")) {
          saudara.setAttribute("inert", "");
          luarPeta.push(saudara);
        }
      }
    }
    const root = document.documentElement;
    const overflow = root.style.overflow;
    root.style.overflow = "hidden";
    tombolLayarPenuh.current.focus({ preventScroll: true });
    const keluar = (event) => {
      if (event.key === "Escape") setLayarPenuh(null);
    };
    document.addEventListener("keydown", keluar);
    return () => {
      document.removeEventListener("keydown", keluar);
      luarPeta.forEach((node) => node.removeAttribute("inert"));
      root.style.overflow = overflow;
      tombolLayarPenuh.current?.focus({ preventScroll: true });
    };
  }, [layarPenuh]);

  async function ubahLayarPenuh() {
    if (layarPenuh === "jendela") {
      setLayarPenuh(null);
      return;
    }
    if (document.fullscreenElement === panel.current) {
      await document.exitFullscreen().catch(() => {});
      return;
    }
    const panelPeta = panel.current;
    wadah.current.style.minHeight = `${panelPeta.offsetHeight}px`;
    if (document.fullscreenEnabled && panelPeta.requestFullscreen) {
      try {
        await panelPeta.requestFullscreen();
        return;
      } catch { /* Gunakan seluruh jendela browser sebagai cadangan. */ }
    }
    if (panel.current === panelPeta) setLayarPenuh("jendela");
  }

  useEffect(() => {
    const preferensi = window.matchMedia(KUERI_KURANGI_GERAK);
    const ikutiPreferensi = (event) => setKurangiGerak(event.matches);
    preferensi.addEventListener("change", ikutiPreferensi);
    return () => preferensi.removeEventListener("change", ikutiPreferensi);
  }, []);

  useEffect(() => {
    const map = L.map(elemen.current, {
      zoomControl: false,
      scrollWheelZoom: false,
      zoomSnap: 0.5,
    });
    const batasRute = L.latLngBounds(data.rute);
    data.area.forEach(({ posisi }) => batasRute.extend(posisi));
    const lihatRute = () => map.fitBounds(batasRute, { padding: [60, 66], maxZoom: 16, animate: false });
    lihatRute();

    const standar = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors · <a href="https://www.openstreetmap.org/fixthemap">Koreksi peta</a>',
    });
    const kontrol = new AbortController();
    let layerAktif;
    let ringkas;
    let modeDetail = false;
    const pasang = (layer) => {
      if (layerAktif === layer) return;
      layerAktif?.remove();
      layerAktif = layer;
      setPetaDasarTidakLengkap(false);
      layer.addTo(map);
    };
    const tampilkanDetail = (detail) => {
      modeDetail = detail;
      if (detail) pasang(standar);
      else if (ringkas) pasang(ringkas);
    };
    const gunakanCadangan = () => {
      setRingkasGagal(true);
      setDetailPeta(true);
      tampilkanDetail(true);
    };
    const pantauTile = (layer, cadangan) => {
      let gagal = false;
      let pernahBerhasil = false;
      layer.on("loading", () => { gagal = false; });
      layer.on("tileerror", () => { gagal = true; });
      layer.on("tileload", () => { pernahBerhasil = true; });
      layer.on("load", () => {
        if (layerAktif !== layer) return;
        if (gagal && !pernahBerhasil && cadangan) {
          queueMicrotask(() => {
            if (!kontrol.signal.aborted && layerAktif === layer) cadangan();
          });
        } else {
          setPetaDasarTidakLengkap(gagal);
        }
      });
    };
    pantauTile(standar);
    const batasWaktu = window.setTimeout(() => {
      kontrol.abort();
      gunakanCadangan();
    }, 4500);
    buatPetaRingkas(kontrol.signal).then((layer) => {
      if (kontrol.signal.aborted) return;
      ringkas = layer;
      pantauTile(ringkas, gunakanCadangan);
      if (!modeDetail) pasang(ringkas);
    }).catch(() => {
      if (!kontrol.signal.aborted) gunakanCadangan();
    }).finally(() => window.clearTimeout(batasWaktu));

    map.attributionControl.setPrefix(false);
    L.control.zoom({ position: "topleft", zoomInTitle: "Perbesar", zoomOutTitle: "Perkecil" }).addTo(map);
    const gambarRute = { interactive: false, lineCap: "round", lineJoin: "round" };
    L.polyline(data.rute, { ...gambarRute, color: "#314359", weight: 11, opacity: 0.14 }).addTo(map);
    L.polyline(data.rute, { ...gambarRute, color: "#fff", weight: 8, opacity: 1 }).addTo(map);
    L.polyline(data.rute, { ...gambarRute, color: "#24477b", weight: 4.5, opacity: 1 }).addTo(map);

    data.area.forEach(({ nama, jenis, posisi }) => {
      const muat = jenis === "muat";
      const ikon = L.divIcon({
        className: `pin-lokasi tone-${jenis}`,
        html: buatLabel("", "simbol-lokasi"),
        iconSize: [26, 26],
        iconAnchor: [13, 26],
      });
      L.marker(posisi, { icon: ikon, interactive: false, keyboard: false, zIndexOffset: 150 })
        .bindTooltip(buatLabelLokasi(nama, jenis), {
          permanent: true,
          direction: muat ? "top" : "bottom",
          offset: muat ? [0, -25] : [0, 12],
          className: "label-lokasi",
        })
        .addTo(map);
    });

    const layerTruk = L.layerGroup().addTo(map);
    peta.current = { map, lihatRute, layerTruk, tampilkanDetail };
    const observer = new ResizeObserver(() => map.invalidateSize({ debounceMoveend: true }));
    observer.observe(elemen.current);
    return () => {
      peta.current = null;
      observer.disconnect();
      window.clearTimeout(batasWaktu);
      kontrol.abort();
      map.remove();
    };
  }, [data]);

  useEffect(() => {
    const { layerTruk } = peta.current;
    layerTruk.clearLayers();
    marker.current.clear();

    trukBerjalan.current = [];
    const { detik } = waktuGerak.current;
    truk.forEach((unit) => {
      if (!unit.posisi) return;
      const vendor = ekspeditur[unit.ekspeditur];
      const arah = unit.status === "bermuatan" ? 1 : unit.status === "kosong" ? -1 : 0;
      const bergerak = Boolean(arah && lintasan.panjang);
      const jarakAwal = bergerak ? lintasan.jarakTerdekat(unit.posisi) : 0;
      const { posisi, hadapKiri } = bergerak
        ? lintasan.posisiBergerak(jarakAwal, arah, detik)
        : { posisi: unit.posisi, hadapKiri: false };
      const judul = `${unit.nomor} · ${vendor.singkat} · ${STATUS[unit.status]}`;
      const gambarTruk = buatLabel("", "pin-truk");
      gambarTruk.setAttribute("aria-hidden", "true");
      gambarTruk.append(buatLabel("", "status-dot pin-status"));
      const ikon = L.divIcon({
        className: `truck-pin tone-${unit.status}${hadapKiri ? " pin-arah-balik" : ""}`,
        html: gambarTruk,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        tooltipAnchor: [0, -16],
      });
      const titik = L.marker(posisi, { icon: ikon, title: judul })
        .bindTooltip(buatLabel(judul), { direction: "top", className: "truck-tooltip" })
        .on("click", () => pilihTruk(unit.nomor))
        .addTo(layerTruk);
      const penanda = titik.getElement();
      penanda.setAttribute("aria-label", judul);
      for (const [nama, nilai] of Object.entries(gayaEkspeditur(vendor))) {
        penanda.style.setProperty(nama, nilai);
      }
      marker.current.set(unit.nomor, titik);
      if (bergerak) trukBerjalan.current.push({ marker: titik, jarakAwal, arah });
    });
  }, [lintasan, ekspeditur, truk, pilihTruk]);

  useEffect(() => {
    return gerakkanTruk(trukBerjalan.current, lintasan, waktuGerak.current, kurangiGerak);
  }, [kurangiGerak, lintasan, truk, pilihTruk]);

  useEffect(() => {
    marker.current.forEach((titik, nomor) => {
      const aktif = nomor === terpilih?.nomor;
      titik.getElement().classList.toggle("selected-pin", aktif);
      titik.setZIndexOffset(aktif ? 1000 : 0);
      if (!aktif) titik.closeTooltip();
    });
    const titik = marker.current.get(terpilih?.nomor);
    if (!titik) return;
    const { map } = peta.current;
    map.setView(titik.getLatLng(), Math.max(map.getZoom(), 16), { animate: false });
    titik.openTooltip();
  }, [truk, terpilih]);

  const labelLayarPenuh = layarPenuh ? "Keluar layar penuh" : "Layar penuh";
  return (
    <div className="map-slot" ref={wadah}>
      <section
        className="panel map-panel" ref={panel} data-layar={layarPenuh} aria-label="Peta armada"
        role={layarPenuh === "jendela" ? "dialog" : undefined}
        aria-modal={layarPenuh === "jendela" ? true : undefined}
      >
        <KalenderPeta tanggal={tanggal} tanggalPeta={tanggalPeta} hariIni={data.hariIni ?? tanggalPeta} pilihTanggal={pilihTanggal}>
          <div className="map-actions" role="group" aria-label="Kontrol peta">
            {!ringkasGagal && (
              <button
                type="button" className="button map-detail-toggle" aria-pressed={detailPeta}
                aria-label="Detail peta" title="Detail peta" disabled={!adaPosisi}
                onClick={() => {
                  const detail = !detailPeta;
                  setDetailPeta(detail);
                  peta.current?.tampilkanDetail(detail);
                }}
              >
                <Layers size={18} aria-hidden="true" />
              </button>
            )}
            <button type="button" className="button map-fit-button" aria-label="Lihat seluruh rute" title="Lihat seluruh rute" disabled={!adaPosisi} onClick={() => peta.current?.lihatRute()}>
              <LocateFixed size={18} aria-hidden="true" />
            </button>
            <button type="button" className="button map-fullscreen-toggle" ref={tombolLayarPenuh} onClick={ubahLayarPenuh}
              aria-label={labelLayarPenuh} title={labelLayarPenuh} disabled={!adaPosisi && !layarPenuh}>
              {layarPenuh ? <Minimize size={18} aria-hidden="true" /> : <Maximize size={18} aria-hidden="true" />}
            </button>
          </div>
        </KalenderPeta>
        {!adaPosisi && (
          <div className="map-empty">
            <p role="status">Belum ada data posisi untuk {TANGGAL_KALENDER.format(new Date(tanggal))} WITA.</p>
            <button type="button" className="button" onClick={() => pilihTanggal(tanggalPeta)}>Kembali ke data simulasi</button>
          </div>
        )}
        <div className="map-frame" hidden={!adaPosisi}>
          <div ref={elemen} className="map-canvas" />
          <LegendaPeta ekspeditur={data.ekspeditur} />
          {petaDasarTidakLengkap && (
            <p className="map-message" role="status">Peta dasar belum lengkap. Data simulasi tetap tersedia.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function DetailTruk({ unit, ekspeditur, tutup }) {
  return (
    <section className="truck-detail" aria-label={`Detail ${unit.nomor}`} style={gayaEkspeditur(ekspeditur)}>
      <div className="detail-heading">
        <div>
          <h3>{unit.nomor}</h3>
          <p className="vendor-name">{ekspeditur.nama}</p>
        </div>
        <button type="button" className="icon-button" onClick={tutup} aria-label="Tutup detail truk">
          <X size={17} aria-hidden="true" />
        </button>
      </div>
      <p className={`status-pill tone-${unit.status}`}><span className="status-dot" />{STATUS[unit.status]}</p>
      <dl className="truck-facts">
        <div><dt>Ritase sesi</dt><dd>{unit.ritase == null ? "—" : `${unit.ritase} ret`}</dd></div>
        <div><dt>Baterai HP</dt><dd>{unit.baterai == null ? "—" : `${unit.baterai}%`}</dd></div>
        <div>
          <dt>Posisi terakhir</dt>
          <dd>{unit.terakhir ? <time dateTime={unit.terakhir}>{JAM_WITA.format(new Date(unit.terakhir))} WITA</time> : "—"}</dd>
        </div>
      </dl>
      {unit.status === "terlambat" && <p className="muted detail-note">Status terakhir: {STATUS[unit.tahap]} · {unit.umur} menit lalu.</p>}
    </section>
  );
}

function DaftarArmada({ ekspeditur, truk, terpilih, pilihTruk, filter, ubahFilter, cakupanVendor }) {
  const daftar = useRef(null);
  const adaFilter = Boolean(filter.cari || filter.vendor || filter.status);

  useEffect(() => {
    const list = daftar.current;
    const baris = list?.querySelector("[aria-pressed='true']");
    if (!baris) return;
    const batas = list.getBoundingClientRect();
    const posisi = baris.getBoundingClientRect();
    if (posisi.top < batas.top) {
      list.scrollTop += posisi.top - batas.top;
    } else if (posisi.bottom > batas.bottom) {
      list.scrollTop += posisi.bottom - batas.bottom;
    }
  }, [terpilih]);

  return (
    <section className="panel fleet-panel" aria-labelledby="judul-armada">
      <div className="panel-heading">
        <h2 id="judul-armada">Daftar armada</h2>
        <span className="unit-count" aria-live="polite">{truk.length} unit</span>
      </div>
      <div className="fleet-filters">
        <label className="search">
          <Search size={16} aria-hidden="true" />
          <input type="search" aria-label="Cari nomor lambung" placeholder="Cari nomor lambung…" value={filter.cari} onChange={(event) => ubahFilter({ ...filter, cari: event.target.value })} />
        </label>
        <div className="selects">
          {!cakupanVendor && (
            <select aria-label="Filter ekspeditur" value={filter.vendor} onChange={(event) => ubahFilter({ ...filter, vendor: event.target.value })}>
              <option value="">Semua ekspeditur</option>
              {Object.values(ekspeditur).map(({ id, singkat }) => <option key={id} value={id}>{singkat}</option>)}
            </select>
          )}
          <select aria-label="Filter status" value={filter.status} onChange={(event) => ubahFilter({ ...filter, status: event.target.value })}>
            <option value="">Semua status</option>
            {Object.entries(STATUS).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
        </div>
      </div>
      {truk.length > 0 ? (
        <ul className="fleet-list" ref={daftar}>
          {truk.map((unit) => (
            <li key={unit.nomor}>
              <button type="button" className="fleet-truck" aria-pressed={terpilih?.nomor === unit.nomor} onClick={() => pilihTruk(unit.nomor)} style={gayaEkspeditur(ekspeditur[unit.ekspeditur])}>
                <span className="tile-icon vendor-icon"><Truck size={17} aria-hidden="true" /></span>
                <span className="truck-name">
                  <strong>{unit.nomor}</strong>
                  <small className="vendor-name">{ekspeditur[unit.ekspeditur].singkat}</small>
                </span>
                <span className="truck-state">
                  <span className={`status-text tone-${unit.status}`}>{STATUS[unit.status]}</span>
                  {unit.umur != null && <small>{unit.umur} menit lalu</small>}
                </span>
                <ChevronRight size={14} className="row-arrow" aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <div className="fleet-empty">
          <p>Tidak ada truk yang cocok.</p>
          {adaFilter && <button type="button" className="button" onClick={() => ubahFilter({ vendor: "", status: "", cari: "" })}>Hapus filter</button>}
        </div>
      )}
      {terpilih && (
        <DetailTruk unit={terpilih} ekspeditur={ekspeditur[terpilih.ekspeditur]} tutup={() => pilihTruk(null)} />
      )}
    </section>
  );
}

function Monitoring({ data }) {
  const [filter, ubahFilter] = useState({ vendor: "", status: "", cari: "" });
  const [nomorTerpilih, pilihTruk] = useState(null);
  const ekspeditur = useMemo(() => Object.fromEntries(data.ekspeditur.map((vendor) => [vendor.id, vendor])), [data]);
  const truk = useMemo(() => data.truk.map((unit) => {
    if (!unit.posisi) return { ...unit, status: "tanpa-data" };
    const umur = Math.floor((Date.parse(data.waktu) - Date.parse(unit.terakhir)) / 60000);
    return { ...unit, umur, status: umur > BATAS_TERLAMBAT_MENIT ? "terlambat" : unit.tahap };
  }), [data]);

  const tampil = useMemo(() => {
    const cari = normalisasi(filter.cari);
    return truk.filter((unit) =>
      normalisasi(unit.nomor).includes(cari) &&
      (!filter.vendor || unit.ekspeditur === filter.vendor) &&
      (!filter.status || unit.status === filter.status)
    );
  }, [filter, truk]);
  const terpilih = tampil.find((unit) => unit.nomor === nomorTerpilih);

  return (
    <>
      <RingkasanArmada truk={truk} />
      <div className="monitor-grid">
        <PetaArmada data={data} ekspeditur={ekspeditur} truk={tampil} terpilih={terpilih} pilihTruk={pilihTruk} />
        <DaftarArmada ekspeditur={ekspeditur} truk={tampil} terpilih={terpilih} pilihTruk={pilihTruk} filter={filter} ubahFilter={ubahFilter} cakupanVendor={data.cakupanVendor} />
      </div>
    </>
  );
}

const data = JSON.parse(document.getElementById("data-armada").textContent);
createRoot(document.getElementById("monitoring-app")).render(<Monitoring data={data} />);
