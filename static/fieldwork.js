"use strict";
const taskSearch = document.getElementById("task-search");
const taskStatus = document.getElementById("task-status");
function filterTasks() {
  const query = taskSearch.value.trim().toLocaleLowerCase("id-ID");
  const cards = [...document.querySelectorAll("[data-task]")];
  let count = 0;
  cards.forEach(card => {
    const matchesStatus = !taskStatus.value || (taskStatus.value === "TODO" ? card.dataset.todo === "1" : card.dataset.status === taskStatus.value);
    card.hidden = !matchesStatus || !card.dataset.search.toLocaleLowerCase("id-ID").includes(query);
    if (!card.hidden) count++;
  });
  document.getElementById("task-count").textContent = `${count} dari ${cards.length} tugas ditampilkan`;
  document.getElementById("task-no-match").hidden = count > 0;
}
taskSearch?.addEventListener("input", filterTasks);
taskStatus?.addEventListener("change", filterTasks);
const reportForm = document.getElementById("field-report-form");
if (reportForm) {
  const number = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 });
  const value = name => { const raw = reportForm.elements.namedItem(name).value; return raw === "" ? null : Number(raw); };
  function updateSummary() {
    const total = value("evacuees"), vulnerable = value("vulnerable_people");
    const stock = value("available_package_equivalents"), required = value("required_package_equivalents");
    const distance = value("distance_to_epicenter_km");
    document.getElementById("vulnerable-preview").textContent = total !== null && vulnerable !== null && vulnerable <= total && total >= 0 && vulnerable >= 0 ? number.format(total ? vulnerable / total * 100 : 0) + "%" : "Belum lengkap";
    document.getElementById("logistics-preview").textContent = required === 0 ? "Perlu verifikasi" : stock !== null && required > 0 && stock >= 0 ? number.format(Math.min(100, stock / required * 100)) + "%" : "Belum lengkap";
    document.getElementById("distance-preview").textContent = distance !== null && Number.isFinite(distance) && distance >= 0 ? number.format(distance) + " km" : "Belum lengkap";
  }
  reportForm.addEventListener("input", updateSummary);
  reportForm.addEventListener("focusout", event => {
    const input = event.target;
    if (!input.matches("input:not([type=hidden]),textarea,select") || !input.value) return;
    const error = document.getElementById(input.name + "-error");
    if (!error) return;
    const message = input.validity.valid ? "" : input.validationMessage;
    error.textContent = message; error.hidden = !message;
    input.setAttribute("aria-invalid", message ? "true" : "false");
  });
  reportForm.addEventListener("submit", event => {
    if (reportForm.dataset.sending) { event.preventDefault(); return; }
    reportForm.dataset.sending = "1"; reportForm.setAttribute("aria-busy", "true");
    if (event.submitter) event.submitter.textContent = event.submitter.value === "draft" ? "Menyimpan draf…" : "Mengirim laporan…";
  });
  updateSummary();
}
document.getElementById("report-errors")?.focus();
window.addEventListener("pageshow", event => { if (event.persisted && reportForm) window.location.reload(); });
