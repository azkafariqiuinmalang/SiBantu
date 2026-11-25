/* Peta poligon lokal. Geometri tetap tersedia saat koneksi internet terputus. */
"use strict";

const canvas = document.getElementById("malang-map");
const ctx = canvas.getContext("2d");
const message = document.getElementById("map-message");
const regency = document.getElementById("regency-filter");
const districtSelect = document.getElementById("district-filter");
const detail = document.getElementById("district-detail");
const mapMode = document.getElementById("map-mode");
const affectedOnly = document.getElementById("affected-only");
// Warna peta dibaca dari token tema (static/theme.css), bukan ditulis di sini.
const token = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const palette = {
  land: token("--map-land"), edge: token("--map-edge"), affected: token("--map-affected"),
  affectedEdge: token("--map-affected-edge"), selected: token("--map-selected"),
  high: token("--map-priority-high"), low: token("--map-priority-low"),
  label: token("--map-label"), halo: token("--map-halo"),
};
const colors = {
  UNREGISTERED: palette.land, PENDING: token("--map-pending"), ASSIGNED: token("--map-assigned"),
  DRAFT: token("--map-assigned"), SUBMITTED: token("--map-submitted"), REJECTED: token("--map-rejected"), VERIFIED: token("--map-verified"),
};
function mix(from, to, amount) {
  const parse = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
  const a = parse(from);
  const b = parse(to);
  return `rgb(${a.map((value, i) => Math.round(value + (b[i] - value) * amount)).join(", ")})`;
}
let features = [];
let visible = [];
let selected = "";
let scale = 1;
let baseScale = 1;
let offset = { x: 0, y: 0 };
let width = 0;
let height = 0;
let drag = null;
let criteriaMeta = [];
let activeRound = null;
let isSimulation = false;

function fillColor(feature) {
  if (mapMode.value === "status") return colors[feature.status];
  if (!feature.is_affected) return colors.UNREGISTERED;
  if (mapMode.value === "priority" && feature.group_rank) {
    const count = features.filter(item => item.group_rank).length;
    const step = (feature.group_rank - 1) / Math.max(1, count - 1);
    return mix(palette.high, palette.low, step);
  }
  return palette.affected;
}

function updateLegend() {
  for (const mode of ["impact", "status", "priority"]) {
    document.getElementById(mode + "-legend").hidden = mapMode.value !== mode;
  }
  const descriptions = {
    impact: "Warna merah menandai wilayah terdampak yang tercatat; bukan skala tingkat bahaya.",
    status: "Warna menunjukkan status pendataan laporan terbaru.",
    priority: "Warna menunjukkan prioritas kelompok dari snapshot ronde penilaian, terpisah dari status laporan terbaru.",
  };
  document.getElementById("map-view-description").textContent = descriptions[mapMode.value];
  draw();
}

function project(point) {
  return [point[0] * Math.cos(8 * Math.PI / 180), -point[1]];
}

function prepare(feature) {
  const polygons = feature.geometry.type === "Polygon" ? [feature.geometry.coordinates] : feature.geometry.coordinates;
  const path = new Path2D();
  const points = [];
  polygons.forEach(polygon => polygon.forEach(ring => {
    ring.forEach((point, index) => {
      const [x, y] = project(point);
      if (index === 0) path.moveTo(x, y);
      else path.lineTo(x, y);
      points.push([x, y]);
    });
    path.closePath();
  }));
  const bounds = {
    minX: Math.min(...points.map(p => p[0])), maxX: Math.max(...points.map(p => p[0])),
    minY: Math.min(...points.map(p => p[1])), maxY: Math.max(...points.map(p => p[1])),
  };
  return { ...feature.properties, path, bounds, anchor: labelAnchor(polygons, path, bounds) };
}

/* Titik label: centroid luas cincin terbesar; bila jatuh di luar poligon (bentuk cekung),
   pakai titik dalam poligon terdekat ke centroid. Dihitung sekali per fitur. */
function labelAnchor(polygons, path, bounds) {
  let best = null;
  polygons.forEach(polygon => {
    const ring = polygon[0].map(project);
    let area = 0, cx = 0, cy = 0;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const cross = ring[j][0] * ring[i][1] - ring[i][0] * ring[j][1];
      area += cross;
      cx += (ring[j][0] + ring[i][0]) * cross;
      cy += (ring[j][1] + ring[i][1]) * cross;
    }
    if (area && (!best || Math.abs(area) > Math.abs(best.area))) best = { area, x: cx / (3 * area), y: cy / (3 * area) };
  });
  const center = best || { x: (bounds.minX + bounds.maxX) / 2, y: (bounds.minY + bounds.maxY) / 2 };
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  let anchor = ctx.isPointInPath(path, center.x, center.y, "evenodd") ? { x: center.x, y: center.y } : null;
  if (!anchor) {
    const steps = 24, dx = (bounds.maxX - bounds.minX) / steps, dy = (bounds.maxY - bounds.minY) / steps;
    let distance = Infinity;
    for (let i = 0; i <= steps; i++) for (let k = 0; k <= steps; k++) {
      const x = bounds.minX + i * dx, y = bounds.minY + k * dy;
      const d = (x - center.x) ** 2 + (y - center.y) ** 2;
      if (d < distance && ctx.isPointInPath(path, x, y, "evenodd")) { distance = d; anchor = { x, y }; }
    }
  }
  ctx.restore();
  return anchor || { x: center.x, y: center.y };
}

/* Penempatan label tanpa tumpang tindih. Wilayah terdampak dan terpilih didahulukan;
   label yang digeser diberi garis penunjuk ke titik wilayahnya. */
function drawLabels() {
  const placed = [];
  const overlaps = rect => placed.some(other => rect.x < other.x + other.w && other.x < rect.x + rect.w && rect.y < other.y + other.h && other.y < rect.y + rect.h);
  const area = item => (item.bounds.maxX - item.bounds.minX) * (item.bounds.maxY - item.bounds.minY);
  const candidates = visible.filter(feature => {
    const b = feature.bounds;
    if (mapMode.value !== "status" && !feature.is_affected) return false;
    return feature.is_affected || feature.code === selected || ((b.maxX - b.minX) * scale > 55 && (b.maxY - b.minY) * scale > 26);
  }).sort((a, b) => (b.code === selected) - (a.code === selected) || b.is_affected - a.is_affected || area(b) - area(a));
  const shifts = [[0, 0], [0, -15], [0, 15], [0, -28], [0, 28], [-40, 0], [40, 0], [-40, -15], [40, 15], [40, -15], [-40, 15], [0, -42], [0, 42]];
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  candidates.forEach(feature => {
    const important = feature.is_affected || feature.code === selected;
    ctx.font = (important ? "600 12px " : "11px ") + token("--font-sans");
    const label = (mapMode.value === "priority" && feature.group_rank ? `#${feature.group_rank} ` : "") + feature.name;
    const ax = offset.x + feature.anchor.x * scale;
    const ay = offset.y + feature.anchor.y * scale;
    const w = ctx.measureText(label).width + 8;
    const h = important ? 15 : 13;
    let spot = null;
    for (const [dx, dy] of shifts) {
      const rect = { x: ax + dx - w / 2, y: ay + dy - h / 2, w, h };
      if (!overlaps(rect)) { spot = { x: ax + dx, y: ay + dy, rect, moved: dx || dy }; break; }
      if (!important) break;
    }
    if (!spot) return;
    placed.push(spot.rect);
    if (spot.moved) {
      ctx.strokeStyle = palette.label;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(spot.x, spot.y + (spot.y > ay ? -h / 2 : h / 2));
      ctx.stroke();
      ctx.fillStyle = palette.label;
      ctx.beginPath();
      ctx.arc(ax, ay, 2, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.strokeStyle = palette.halo;
    ctx.lineWidth = 3.5;
    ctx.lineJoin = "round";
    ctx.strokeText(label, spot.x, spot.y);
    ctx.fillStyle = palette.label;
    ctx.fillText(label, spot.x, spot.y);
  });
}

function fit() {
  if (!visible.length || !width || !height) return;
  const minX = Math.min(...visible.map(f => f.bounds.minX));
  const maxX = Math.max(...visible.map(f => f.bounds.maxX));
  const minY = Math.min(...visible.map(f => f.bounds.minY));
  const maxY = Math.max(...visible.map(f => f.bounds.maxY));
  baseScale = Math.min((width - 80) / (maxX - minX), (height - 70) / (maxY - minY));
  scale = baseScale;
  offset = { x: width / 2 - (minX + maxX) * scale / 2, y: height / 2 - (minY + maxY) * scale / 2 };
  draw();
}

function draw() {
  const ratio = window.devicePixelRatio || 1;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.translate(offset.x, offset.y);
  ctx.scale(scale, scale);
  visible.forEach(feature => {
    ctx.fillStyle = fillColor(feature);
    ctx.fill(feature.path, "evenodd");
    ctx.strokeStyle = feature.is_affected && mapMode.value !== "status" ? palette.affectedEdge : palette.edge;
    ctx.lineWidth = (feature.is_affected ? 1.4 : 0.8) / scale;
    ctx.stroke(feature.path);
  });
  // Kecamatan terpilih digambar terakhir agar garis sinyalnya tidak tertutup tetangga.
  visible.filter(feature => feature.code === selected).forEach(feature => {
    ctx.strokeStyle = palette.halo;
    ctx.lineWidth = 5.5 / scale;
    ctx.stroke(feature.path);
    ctx.strokeStyle = palette.selected;
    ctx.lineWidth = 3 / scale;
    ctx.stroke(feature.path);
  });
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  drawLabels();
}

function choose(code) {
  selected = code;
  districtSelect.value = code;
  detail.replaceChildren();
  const feature = features.find(item => item.code === code);
  const heading = document.createElement("h3");
  heading.textContent = feature ? feature.name : "Pilih wilayah";
  detail.append(heading);
  if (!feature) {
    const hint = document.createElement("p");
    hint.textContent = "Klik kecamatan pada peta atau pilih dari daftar untuk melihat status pendataan dan nilai kriterianya.";
    detail.append(hint);
  }
  if (feature) {
    [feature.regency, feature.status_label, feature.is_affected ? "Tercatat terdampak" : "Belum tercatat pada kejadian ini"].forEach(text => {
      const line = document.createElement("p");
      line.textContent = text;
      detail.append(line);
    });
    if (isSimulation && feature.is_affected) {
      const note = document.createElement("p");
      note.className = "simulation-note";
      note.textContent = "SIMULASI: angka contoh untuk latihan.";
      detail.append(note);
    }
    if (feature.criterion_values) {
      const label = document.createElement("p");
      label.textContent = "Nilai kriteria laporan terbaru";
      detail.append(label);
      const values = document.createElement("dl");
      values.className = "map-criteria";
      const number = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 });
      criteriaMeta.forEach((criterion, index) => {
        const term = document.createElement("dt");
        const value = document.createElement("dd");
        term.textContent = criterion.code + " " + criterion.name;
        value.textContent = feature.criterion_values[index] == null ? "Belum diisi" : number.format(feature.criterion_values[index]) + " " + criterion.unit;
        values.append(term, value);
      });
      detail.append(values);
    }
    if (activeRound && feature.is_affected) {
      const ranking = document.createElement("p");
      ranking.textContent = activeRound.legacy ? "Perbarui C6 pada laporan untuk membuka ronde penilaian terbaru." : feature.group_rank
        ? `Prioritas kelompok #${feature.group_rank}, ${feature.group_points} poin, ronde ${activeRound.id}`
        : `Menunggu penilaian lengkap: ${activeRound.submitted_count}/3 aktor sudah mengirim`;
      detail.append(ranking);
    }
    if (feature.case_url) {
      const link = document.createElement("a");
      link.textContent = "Buka kejadian";
      link.href = feature.case_url;
      detail.append(link);
    }
  }
  draw();
}

function filter() {
  visible = features.filter(item => (!regency.value || item.regency_code === regency.value) && (!affectedOnly.checked || item.is_affected));
  document.querySelectorAll("tr[data-regency]").forEach(row => {
    row.hidden = Boolean((regency.value && row.dataset.regency !== regency.value) || (affectedOnly.checked && row.dataset.affected !== "1"));
  });
  [...districtSelect.options].forEach(option => {
    const item = features.find(feature => feature.code === option.value);
    option.hidden = Boolean(item && ((regency.value && item.regency_code !== regency.value) || (affectedOnly.checked && !item.is_affected)));
  });
  if (!visible.some(item => item.code === selected)) choose("");
  document.getElementById("district-count").textContent = visible.length + " kecamatan";
  fit();
}

function zoom(factor, x = width / 2, y = height / 2) {
  const updated = Math.max(baseScale * .7, Math.min(baseScale * 12, scale * factor));
  offset.x = x - (x - offset.x) * updated / scale;
  offset.y = y - (y - offset.y) * updated / scale;
  scale = updated;
  draw();
}

new ResizeObserver(() => {
  width = canvas.clientWidth;
  height = canvas.clientHeight;
  canvas.width = Math.round(width * (window.devicePixelRatio || 1));
  canvas.height = Math.round(height * (window.devicePixelRatio || 1));
  fit();
}).observe(canvas);
document.getElementById("zoom-in").addEventListener("click", () => zoom(1.3));
document.getElementById("zoom-out").addEventListener("click", () => zoom(1 / 1.3));
document.getElementById("reset-map").addEventListener("click", fit);
regency.addEventListener("change", filter);
affectedOnly.addEventListener("change", filter);
mapMode.addEventListener("change", updateLegend);
districtSelect.addEventListener("change", () => choose(districtSelect.value));
document.querySelectorAll(".select-district").forEach(button => button.addEventListener("click", () => {
  choose(button.dataset.code);
  canvas.scrollIntoView({ behavior: "smooth", block: "center" });
}));
canvas.addEventListener("wheel", event => {
  event.preventDefault();
  const bounds = canvas.getBoundingClientRect();
  zoom(event.deltaY < 0 ? 1.15 : 1 / 1.15, event.clientX - bounds.left, event.clientY - bounds.top);
}, { passive: false });
canvas.addEventListener("pointerdown", event => {
  drag = { startX: event.clientX, startY: event.clientY, x: event.clientX, y: event.clientY, moved: false };
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove", event => {
  if (!drag) return;
  drag.moved ||= Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 4;
  offset.x += event.clientX - drag.x;
  offset.y += event.clientY - drag.y;
  drag.x = event.clientX;
  drag.y = event.clientY;
  draw();
});
canvas.addEventListener("pointerup", event => {
  if (drag && !drag.moved) {
    const b = canvas.getBoundingClientRect();
    const x = (event.clientX - b.left - offset.x) / scale;
    const y = (event.clientY - b.top - offset.y) / scale;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const hit = [...visible].reverse().find(item => ctx.isPointInPath(item.path, x, y, "evenodd"));
    ctx.restore();
    choose(hit ? hit.code : "");
  }
  drag = null;
});
canvas.addEventListener("pointercancel", () => { drag = null; });

fetch(canvas.dataset.url, { credentials: "same-origin" }).then(response => {
  if (!response.ok || !response.headers.get("Content-Type")?.includes("application/json")) {
    throw new Error("Peta gagal dimuat. Coba muat ulang atau masuk kembali.");
  }
  return response.json();
}).then(data => {
  criteriaMeta = data.criteria;
  activeRound = data.round;
  isSimulation = data.is_simulation;
  features = data.features.map(prepare);
  message.textContent = "Geser untuk menjelajah, gulir untuk memperbesar.";
  filter();
  updateLegend();
}).catch(error => {
  message.textContent = error.message;
});
