import { VectorTile } from "@mapbox/vector-tile";
import Pbf from "pbf";
import L from "leaflet";

const TILEJSON = "https://tiles.openfreemap.org/planet";
const ATRIBUSI = '&copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> · &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
const JALAN_UTAMA = new Set(["motorway", "trunk", "primary", "secondary", "tertiary"]);
const JALAN_LOKAL = new Set(["minor", "service", "track"]);

function gambarLapisan(kanvas, layer, properti, jenis, saring = () => true) {
  if (!layer) return;
  kanvas.beginPath();
  for (let i = 0; i < layer.length; i++) {
    const fitur = layer.feature(i);
    if (fitur.type !== jenis || !saring(fitur.properties)) continue;
    const skala = 256 / fitur.extent;
    for (const [awal, ...garis] of fitur.loadGeometry()) {
      if (!awal) continue;
      kanvas.moveTo(awal.x * skala, awal.y * skala);
      for (const titik of garis) kanvas.lineTo(titik.x * skala, titik.y * skala);
      if (jenis === 3) kanvas.closePath();
    }
  }
  if (jenis === 3) {
    kanvas.fillStyle = properti;
    kanvas.fill();
  } else {
    const [warna, lebar, warnaTepi, lebarTepi] = properti;
    if (warnaTepi) {
      kanvas.strokeStyle = warnaTepi;
      kanvas.lineWidth = lebarTepi;
      kanvas.stroke();
    }
    kanvas.strokeStyle = warna;
    kanvas.lineWidth = lebar;
    kanvas.stroke();
  }
}

function gambarPeta(elemen, data, zoom) {
  const ctx = elemen.getContext("2d");
  ctx.scale(elemen.width / 256, elemen.height / 256);
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.fillStyle = "#f1f2ee";
  ctx.fillRect(0, 0, 256, 256);
  gambarLapisan(ctx, data.landcover, "#e6eee1", 3, ({ class: jenis }) => jenis === "wood" || jenis === "grass");
  gambarLapisan(ctx, data.landuse, "#eceae5", 3, ({ class: jenis }) => jenis === "industrial" || jenis === "quarry");
  gambarLapisan(ctx, data.water, "#cfe5ec", 3);
  gambarLapisan(ctx, data.waterway, ["#c3dde7", 1.1], 2, ({ class: jenis }) => jenis === "river" || jenis === "canal");
  if (zoom >= 12) {
    gambarLapisan(ctx, data.transportation, ["#fff", 1.15, "#dde1da", 1.9], 2, ({ class: jenis }) => JALAN_LOKAL.has(jenis));
  }
  gambarLapisan(ctx, data.transportation, ["#fff9e9", 2.2, "#ddd1b7", 3.2], 2, ({ class: jenis }) => JALAN_UTAMA.has(jenis));
}

export async function buatPetaRingkas(signal) {
  const respons = await fetch(TILEJSON, { signal });
  if (!respons.ok) throw new Error("Sumber peta ringkas tidak tersedia.");
  const { tiles: [url], maxzoom } = await respons.json();
  const unduhan = new WeakMap();
  const layer = L.gridLayer({ attribution: ATRIBUSI, maxNativeZoom: maxzoom, maxZoom: 19 });
  layer.createTile = (titik, selesai) => {
    const tile = document.createElement("canvas");
    const skala = Math.min(2, window.devicePixelRatio || 1);
    tile.width = tile.height = Math.round(256 * skala);
    const kontrol = new AbortController();
    unduhan.set(tile, kontrol);
    fetch(L.Util.template(url, titik), { signal: kontrol.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Bagian peta ringkas gagal dimuat.");
        return response.arrayBuffer();
      })
      .then((buffer) => {
        if (kontrol.signal.aborted) return;
        gambarPeta(tile, new VectorTile(new Pbf(new Uint8Array(buffer))).layers, titik.z);
        selesai(null, tile);
      })
      .catch((error) => {
        if (!kontrol.signal.aborted) selesai(error, tile);
      })
      .finally(() => unduhan.delete(tile));
    return tile;
  };
  layer.on("tileunload", ({ tile }) => unduhan.get(tile)?.abort());
  return layer;
}
