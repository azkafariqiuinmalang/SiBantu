/* The original selects remain the canonical POST fields and no-JS fallback. */
(function () {
  "use strict";
  const strengths = {
    2: "Nilai antara sama penting dan sedikit lebih penting",
    3: "Sedikit lebih penting",
    4: "Nilai antara sedikit dan kuat",
    5: "Lebih penting secara kuat",
    6: "Nilai antara kuat dan sangat",
    7: "Sangat lebih penting",
    8: "Nilai antara sangat dan mutlak",
    9: "Mutlak lebih penting",
  };

  function decode(value) {
    if (value === "1") return { direction: "equal", magnitude: null };
    if (/^[2-9]$/.test(value)) return { direction: "left", magnitude: Number(value) };
    if (/^1\/[2-9]$/.test(value)) return { direction: "right", magnitude: Number(value.slice(2)) };
    return { direction: "", magnitude: null };
  }

  function encode(direction, magnitude) {
    if (direction === "equal") return "1";
    if (!Number.isInteger(magnitude) || magnitude < 2 || magnitude > 9) return "";
    if (direction === "left") return String(magnitude);
    if (direction === "right") return `1/${magnitude}`;
    return "";
  }

  function describe(value, left, right) {
    const state = decode(value);
    if (state.direction === "equal") return `${left} dan ${right} sama penting.`;
    if (!state.direction) return "Belum dijawab. Pilih kriteria dan tingkat kepentingannya.";
    const winner = state.direction === "left" ? left : right;
    const other = state.direction === "left" ? right : left;
    const level = strengths[state.magnitude].toLowerCase();
    return state.magnitude % 2
      ? `${winner} ${level} daripada ${other}.`
      : `${winner} lebih penting daripada ${other}, dengan ${level} (skala ${state.magnitude}).`;
  }

  // Export the same conversion used by the UI for independent round-trip tests.
  if (typeof module !== "undefined" && module.exports) module.exports = { decode, encode, describe };
  if (typeof document === "undefined") return;

  function element(tag, text, attributes = {}) {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, value));
    return node;
  }

  function enhance(form) {
    const pairs = Array.from(form.querySelectorAll(".pair"));
    if (!pairs.length || pairs[0].querySelector("select").disabled) return;
    const selects = pairs.map(pair => pair.querySelector("select"));
    const originalActions = form.querySelector(".ahp-actions");
    const draft = originalActions.querySelector('[value="draft"]');
    const check = originalActions.querySelector('[value="preview"]');
    const submit = originalActions.querySelector('[value="submit"]');
    const top = element("div", "", { class: "ahp-progress" });
    const position = element("p", "", { class: "ahp-position" });
    const count = element("p", "", { "aria-live": "polite", "aria-atomic": "true" });
    const progress = element("progress", "", { max: pairs.length, value: 0, "aria-label": "Jumlah perbandingan yang sudah dijawab" });
    top.append(position, count, progress);
    form.prepend(top);

    const review = element("section", "", { class: "ahp-review", hidden: "" });
    const reviewHeading = element("h3", "Tinjau jawaban Anda", { tabindex: "-1" });
    const reviewHelp = element("p", "Periksa kembali pilihan Anda, lalu cek konsistensi atau kirim penilaian. Jika CR melebihi 0,10, ubah perbandingan sesuai pertimbangan Anda.");
    const reviewList = element("ol", "", { class: "ahp-review-list" });
    review.append(reviewHeading, reviewHelp, reviewList);
    form.querySelector(".pairs").after(review);
    const controls = element("div", "", { class: "ahp-steps", hidden: "" });
    const previous = element("button", "Sebelumnya", { type: "button", class: "secondary" });
    const next = element("button", "Berikutnya", { type: "button" });
    controls.append(previous, next);
    review.after(controls);
    const overview = element("button", "Tinjau semua jawaban", { type: "button", class: "secondary" });
    originalActions.append(overview);
    let current = 0;
    let reviewing = false;
    const cards = [];

    pairs.forEach((pair, index) => {
      const select = selects[index];
      let state = decode(select.value);
      const left = pair.dataset.left;
      const right = pair.dataset.right;
      const title = element("h3", "Mana yang lebih penting untuk menentukan prioritas bantuan?", { tabindex: "-1", id: `ahp-title-${index}` });
      const directionGroup = element("fieldset", "", { class: "ahp-options" });
      directionGroup.append(element("legend", "1. Pilih kriteria"));
      const strengthGroup = element("fieldset", "", { class: "ahp-options" });
      const strengthLegend = element("legend", "2. Seberapa besar perbedaan kepentingannya?");
      strengthGroup.append(strengthLegend);
      const mainLevels = element("div", "", { class: "ahp-levels" });
      const extra = element("details", "", { class: "ahp-intermediate" });
      extra.append(element("summary", "Butuh nilai antara? (2, 4, 6, 8)"));
      const extraLevels = element("div", "", { class: "ahp-levels" });
      extra.append(extraLevels);
      strengthGroup.append(mainLevels, extra);
      const summary = element("p", "", { class: "ahp-answer", "aria-live": "polite", "aria-atomic": "true" });
      const error = element("p", "", { class: "ahp-error", role: "alert", hidden: "", id: `ahp-error-${index}` });
      pair.setAttribute("aria-labelledby", title.id);
      pair.setAttribute("role", "group");
      pair.append(title, directionGroup, strengthGroup, summary, error);

      function option(group, value, text, name, isChecked, change) {
        const label = element("label", "", { class: "ahp-choice" });
        const input = element("input", "", { type: "radio", name, value });
        input.checked = isChecked;
        input.addEventListener("change", () => { if (input.checked) change(); });
        label.append(input, element("span", text));
        group.append(label);
      }

      function sync() {
        select.value = encode(state.direction, state.magnitude);
        strengthGroup.hidden = !state.direction || state.direction === "equal";
        strengthLegend.textContent = `2. Seberapa besar ${state.direction === "right" ? right : left} lebih penting?`;
        summary.textContent = describe(select.value, left, right);
        error.hidden = true;
        pair.removeAttribute("aria-describedby");
        updateCount();
      }

      [["left", left], ["equal", "Keduanya sama penting"], ["right", right]].forEach(([value, text]) => {
        option(directionGroup, value, text, `direction_${index}`, state.direction === value, () => {
          state.direction = value;
          sync();
        });
      });
      [3, 5, 7, 9, 2, 4, 6, 8].forEach(level => {
        option(level % 2 ? mainLevels : extraLevels, String(level), `${strengths[level]} (${level})`,
          `strength_${index}`, state.magnitude === level, () => { state.magnitude = level; sync(); });
      });
      if (state.magnitude && state.magnitude % 2 === 0) extra.open = true;
      pair.querySelector("label").hidden = true; // The original fallback label.
      select.hidden = true;
      cards.push({ title, directionGroup, strengthGroup, error });
      sync();
    });

    function updateCount() {
      const answered = selects.filter(select => Boolean(select.value)).length;
      progress.value = answered;
      count.textContent = `${answered} dari ${pairs.length} perbandingan sudah dijawab`;
    }

    function show(index, focus = true) {
      current = Math.max(0, Math.min(pairs.length - 1, index));
      reviewing = false;
      pairs.forEach((pair, i) => { pair.hidden = i !== current; });
      review.hidden = true;
      controls.hidden = false;
      previous.disabled = current === 0;
      next.textContent = current === pairs.length - 1 ? "Tinjau jawaban" : "Berikutnya";
      position.textContent = `Perbandingan ${current + 1} dari ${pairs.length}`;
      check.hidden = true;
      submit.hidden = true;
      overview.hidden = false;
      if (focus) cards[current].title.focus();
    }

    function showReview(focus = true) {
      reviewing = true;
      pairs.forEach(pair => { pair.hidden = true; });
      controls.hidden = true;
      review.hidden = false;
      check.hidden = false;
      submit.hidden = false;
      overview.hidden = true;
      position.textContent = "Langkah terakhir: tinjau jawaban";
      reviewList.replaceChildren();
      selects.forEach((select, index) => {
        const pair = pairs[index];
        const row = element("li");
        const answer = element("p", describe(select.value, pair.dataset.left, pair.dataset.right));
        const edit = element("button", "Ubah", { type: "button", class: "secondary", "aria-label": `Ubah perbandingan ${index + 1}: ${pair.dataset.left} dan ${pair.dataset.right}` });
        edit.addEventListener("click", () => show(index));
        row.append(answer, edit);
        reviewList.append(row);
      });
      if (focus) reviewHeading.focus();
    }

    function requireAnswer(index) {
      if (selects[index].value) return true;
      show(index);
      const card = cards[index];
      const selectedDirection = card.directionGroup.querySelector("input:checked");
      card.error.textContent = selectedDirection
        ? "Pilih tingkat kepentingannya terlebih dahulu."
        : "Pilih kriteria yang lebih penting atau keduanya sama penting.";
      card.error.hidden = false;
      pairs[index].setAttribute("aria-describedby", card.error.id);
      (selectedDirection ? card.strengthGroup : card.directionGroup).querySelector("input").focus();
      return false;
    }

    previous.addEventListener("click", () => show(current - 1));
    next.addEventListener("click", () => {
      if (!requireAnswer(current)) return;
      if (current === pairs.length - 1) showReview();
      else show(current + 1);
    });
    overview.addEventListener("click", () => showReview());
    let sending = false;
    form.addEventListener("submit", event => {
      if (sending) { event.preventDefault(); return; }
      const action = event.submitter ? event.submitter.value : "draft";
      if (action !== "draft") {
        const missing = selects.findIndex(select => !select.value);
        if (missing !== -1) { event.preventDefault(); requireAnswer(missing); return; }
        if (!reviewing) { event.preventDefault(); showReview(); return; }
      }
      sending = true;
      form.setAttribute("aria-busy", "true");
      const button = event.submitter || draft;
      button.dataset.originalText = button.textContent;
      button.textContent = action === "preview" ? "Menghitung..." : "Menyimpan...";
      // Keep the submitter enabled: its action must be included in the POST.
    });
    window.addEventListener("pageshow", () => {
      sending = false;
      form.removeAttribute("aria-busy");
      originalActions.querySelectorAll("[data-original-text]").forEach(button => {
        button.textContent = button.dataset.originalText;
        delete button.dataset.originalText;
      });
    });
    form.classList.add("is-guided");
    form.closest(".work-area").classList.add("ahp-work-area");
    const missing = selects.findIndex(select => !select.value);
    if (form.dataset.review === "true" || missing === -1) showReview(false);
    else show(missing, false);
    updateCount();
  }

  document.querySelectorAll(".ahp-form").forEach(enhance);
})();
