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

  /* Urutan kriteria hanya alat bantu: tidak mengisi atau mengubah jawaban.
     order berisi indeks kriteria dari yang paling penting. Mengembalikan null bila
     arah jawaban sesuai urutan (atau sama penting); selain itu, kriteria yang
     menurut urutan seharusnya lebih penting dan kriteria yang dipilih. */
  function orderConflict(order, leftIndex, rightIndex, value) {
    if (!Array.isArray(order)) return null;
    const leftRank = order.indexOf(leftIndex);
    const rightRank = order.indexOf(rightIndex);
    if (leftRank < 0 || rightRank < 0) return null;
    const { direction } = decode(value);
    if (direction === "left" && leftRank > rightRank) return { expected: rightIndex, chosen: leftIndex };
    if (direction === "right" && rightRank > leftRank) return { expected: leftIndex, chosen: rightIndex };
    return null;
  }

  function moveItem(order, from, to) {
    const result = order.slice();
    if (to < 0 || to >= result.length || from === to) return result;
    const [item] = result.splice(from, 1);
    result.splice(to, 0, item);
    return result;
  }

  function validOrder(order, size) {
    return Array.isArray(order) && order.length === size &&
      order.every(item => Number.isInteger(item) && item >= 0 && item < size) &&
      new Set(order).size === size;
  }

  const SAATY = ["1/9", "1/8", "1/7", "1/6", "1/5", "1/4", "1/3", "1/2", "1", "2", "3", "4", "5", "6", "7", "8", "9"];

  function toNumber(value) {
    const { direction, magnitude } = decode(value);
    if (direction === "equal") return 1;
    if (direction === "left") return magnitude;
    if (direction === "right") return 1 / magnitude;
    return null;
  }

  function nearestSaaty(ratio) {
    return SAATY.reduce((best, value) =>
      Math.abs(Math.log(toNumber(value) / ratio)) < Math.abs(Math.log(toNumber(best) / ratio)) ? value : best, "1");
  }

  /* Perkiraan transitif: a_ij ≈ a_ik × a_kj dari jawaban lain yang sudah diisi.
     answers memetakan "i-j" (i < j) ke nilai skala Saaty. Hanya panduan; tidak
     pernah menjadi jawaban. Mengembalikan null bila belum ada dasar perkiraan. */
  function transitiveEstimate(answers, i, j, size) {
    const ratio = (a, b) => {
      const value = a < b ? toNumber(answers[`${a}-${b}`] || "") : toNumber(answers[`${b}-${a}`] || "");
      if (value === null) return null;
      return a < b ? value : 1 / value;
    };
    const logs = [];
    const via = [];
    for (let k = 0; k < size; k += 1) {
      if (k === i || k === j) continue;
      const first = ratio(i, k);
      const second = ratio(k, j);
      if (first === null || second === null) continue;
      logs.push(Math.log(first) + Math.log(second));
      via.push(k);
    }
    if (!logs.length) return null;
    const mean = logs.reduce((sum, value) => sum + value, 0) / logs.length;
    const ratioValue = Math.exp(Math.max(Math.log(1 / 9), Math.min(Math.log(9), mean)));
    return { value: nearestSaaty(ratioValue), ratio: ratioValue, via };
  }

  // Pilihan dianggap jauh dari perkiraan bila berbeda sekitar empat kali lipat atau lebih.
  function farFromEstimate(value, estimate) {
    const chosen = toNumber(value);
    if (chosen === null || !estimate) return false;
    return Math.abs(Math.log(chosen / estimate.ratio)) >= Math.log(4) - 1e-9;
  }

  // Export the same conversion used by the UI for independent round-trip tests.
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { decode, encode, describe, orderConflict, moveItem, validOrder,
      toNumber, nearestSaaty, transitiveEstimate, farFromEstimate };
  }
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
    let initialValues = null; // diisi setelah semua kartu siap, untuk mendeteksi perubahan belum disimpan
    let unsavedNote = null;
    // Saran pasangan dari server (hanya ada bila CR > 0,10), ditampilkan juga di tinjauan.
    const serverHints = {};
    document.querySelectorAll(".ahp-hint-list li[data-pair]").forEach(item => {
      const suggestion = item.querySelector(".ahp-hint-suggestion");
      serverHints[Number(item.dataset.pair)] = { chosen: item.dataset.chosen, suggestion: suggestion ? suggestion.textContent : "" };
    });

    // ---------- Langkah awal: urutkan kriteria ----------
    const names = {};
    const codes = {};
    pairs.forEach(pair => {
      names[pair.dataset.leftIndex] = pair.dataset.left;
      names[pair.dataset.rightIndex] = pair.dataset.right;
      codes[pair.dataset.leftIndex] = pair.dataset.leftCode;
      codes[pair.dataset.rightIndex] = pair.dataset.rightCode;
    });
    const size = Object.keys(names).length;
    const roundInput = form.querySelector('input[name="round_id"]');
    const storageKey = "sibantu-ahp-order:" + (roundInput ? roundInput.value : "") + ":" + location.pathname;
    let order = null;
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
      if (validOrder(saved, size)) order = saved;
    } catch (error) { order = null; }
    let draftOrder = order ? order.slice() : Array.from({ length: size }, (_, index) => index);
    const label = index => `${codes[index]} ${names[index]}`;

    const ranking = element("section", "", { class: "ahp-ranking", hidden: "" });
    const rankingHeading = element("h3", "Langkah awal: urutkan kriteria dari yang paling penting", { tabindex: "-1" });
    const rankingHelp = element("p", "Urutan ini membantu Anda menjawab 15 perbandingan secara konsisten. Sistem tidak mengisi jawaban; sistem hanya memberi peringatan bila pilihan Anda berlawanan dengan urutan ini. Urutan disimpan di browser ini saja.");
    const rankingList = element("ol", "", { class: "ahp-ranking-list" });
    const rankingStatus = element("p", "", { class: "visually-hidden", "aria-live": "polite" });
    const rankingActions = element("div", "", { class: "ahp-steps" });
    const skipRanking = element("button", "Lewati", { type: "button", class: "secondary" });
    const startPairs = element("button", "Simpan urutan dan mulai", { type: "button" });
    rankingActions.append(skipRanking, startPairs);
    ranking.append(rankingHeading, rankingHelp, rankingList, rankingStatus, rankingActions);
    form.querySelector(".pairs").before(ranking);
    const editOrder = element("button", "Ubah urutan kriteria", { type: "button", class: "secondary ahp-edit-order" });
    top.append(editOrder);

    function renderRanking(focusIndex = null, focusUp = true) {
      rankingList.replaceChildren();
      draftOrder.forEach((criterion, place) => {
        const item = element("li", "", { class: "ahp-rank-item" });
        const text = element("span", label(criterion), { class: "ahp-rank-name" });
        const buttons = element("span", "", { class: "ahp-rank-buttons" });
        const up = element("button", "Naik", { type: "button", class: "secondary", "aria-label": `Naikkan ${label(criterion)}` });
        const down = element("button", "Turun", { type: "button", class: "secondary", "aria-label": `Turunkan ${label(criterion)}` });
        up.disabled = place === 0;
        down.disabled = place === draftOrder.length - 1;
        up.addEventListener("click", () => moveRank(place, place - 1, true));
        down.addEventListener("click", () => moveRank(place, place + 1, false));
        buttons.append(up, down);
        item.append(text, buttons);
        rankingList.append(item);
        if (focusIndex === place) {
          const target = focusUp ? (up.disabled ? down : up) : (down.disabled ? up : down);
          target.focus();
        }
      });
    }

    function moveRank(from, to, upward) {
      draftOrder = moveItem(draftOrder, from, to);
      renderRanking(to, upward);
      rankingStatus.textContent = `${label(draftOrder[to])} sekarang di urutan ${to + 1}.`;
    }

    function showRanking(focus = true) {
      reviewing = false;
      if (order) draftOrder = order.slice();
      renderRanking();
      pairs.forEach(pair => { pair.hidden = true; });
      review.hidden = true;
      controls.hidden = true;
      ranking.hidden = false;
      check.hidden = true;
      submit.hidden = true;
      overview.hidden = true;
      editOrder.hidden = true;
      position.textContent = "Langkah awal: urutkan kriteria";
      if (focus) rankingHeading.focus();
    }

    function leaveRanking() {
      const missing = selects.findIndex(select => !select.value);
      if (missing === -1) showReview();
      else show(missing);
    }

    startPairs.addEventListener("click", () => {
      order = draftOrder.slice();
      try { localStorage.setItem(storageKey, JSON.stringify(order)); } catch (error) { /* tetap berjalan tanpa penyimpanan */ }
      cards.forEach(card => card.refreshOrder());
      leaveRanking();
    });
    skipRanking.addEventListener("click", leaveRanking);
    editOrder.addEventListener("click", () => showRanking());

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
      const guide = element("div", "", { class: "ahp-guide" });
      const orderNote = element("p", "", { class: "ahp-order-note", hidden: "" });
      const estimateNote = element("p", "", { class: "ahp-estimate-note", hidden: "" });
      guide.append(orderNote, estimateNote);
      const warning = element("p", "", { class: "ahp-order-warning", role: "status", hidden: "" });
      const estimateWarning = element("p", "", { class: "ahp-order-warning", role: "status", hidden: "" });
      const summary = element("p", "", { class: "ahp-answer", "aria-live": "polite", "aria-atomic": "true" });
      const error = element("p", "", { class: "ahp-error", role: "alert", hidden: "", id: `ahp-error-${index}` });
      pair.setAttribute("aria-labelledby", title.id);
      pair.setAttribute("role", "group");
      pair.append(title, guide, directionGroup, warning, strengthGroup, summary, estimateWarning, error);
      const leftIndex = Number(pair.dataset.leftIndex);
      const rightIndex = Number(pair.dataset.rightIndex);

      function refreshOrder() {
        if (!order) { orderNote.hidden = true; warning.hidden = true; return; }
        const first = order.indexOf(leftIndex) < order.indexOf(rightIndex) ? leftIndex : rightIndex;
        const second = first === leftIndex ? rightIndex : leftIndex;
        orderNote.textContent = `Urutan Anda: ${names[first]} (ke-${order.indexOf(first) + 1}) di atas ${names[second]} (ke-${order.indexOf(second) + 1}).`;
        orderNote.hidden = false;
        const conflict = orderConflict(order, leftIndex, rightIndex, select.value);
        warning.hidden = !conflict;
        if (conflict) {
          warning.textContent = `Berlawanan dengan urutan Anda: ${names[conflict.chosen]} dipilih di atas ${names[conflict.expected]}. Arah yang berlawanan sering membuat CR melebihi 0,10. Pilih kembali, atau ubah urutan bila memang ini pendapat Anda.`;
        }
      }

      function refreshEstimate() {
        // Saran dari cek konsistensi memperhitungkan semua jawaban; selama jawaban
        // pasangan ini belum diubah, tampilkan satu panduan saja agar tidak bertentangan.
        const hint = serverHints[index];
        if (hint && select.value === hint.chosen) {
          estimateNote.textContent = `Saran dari cek konsistensi: ${hint.suggestion}.`;
          estimateNote.hidden = false;
          estimateWarning.hidden = true;
          return;
        }
        const estimate = transitiveEstimate(currentAnswers(index), leftIndex, rightIndex, size);
        estimateNote.hidden = !estimate;
        estimateWarning.hidden = true;
        if (!estimate) return;
        const basis = estimate.via.map(k => codes[k]).join(", ");
        estimateNote.textContent = `Perkiraan dari jawaban Anda sebelumnya (lewat ${basis}): ${describe(estimate.value, left, right)}`;
        if (farFromEstimate(select.value, estimate)) {
          estimateWarning.hidden = false;
          estimateWarning.textContent = "Pilihan ini cukup jauh dari perkiraan di atas, sehingga dapat menaikkan CR. Jika memang disengaja, tidak apa-apa; jika ragu, pilih nilai yang mendekati perkiraan.";
        }
      }

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
        refreshOrder();
        refreshEstimate();
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
      cards.push({ title, directionGroup, strengthGroup, error, refreshOrder, refreshEstimate });
      sync();
    });

    // Jawaban lain yang sudah diisi (tanpa pasangan yang sedang dilihat), kunci "i-j".
    function currentAnswers(except) {
      const answers = {};
      pairs.forEach((pair, i) => {
        if (i !== except && selects[i].value) answers[`${pair.dataset.leftIndex}-${pair.dataset.rightIndex}`] = selects[i].value;
      });
      return answers;
    }

    initialValues = selects.map(select => select.value);
    unsavedNote = element("p", "Ada perubahan yang belum disimpan. Klik Simpan draf sebelum meninggalkan halaman.", { class: "ahp-unsaved", hidden: "" });
    top.append(unsavedNote);

    function isDirty() {
      return Boolean(initialValues) && selects.some((select, i) => select.value !== initialValues[i]);
    }

    function updateCount() {
      const answered = selects.filter(select => Boolean(select.value)).length;
      progress.value = answered;
      count.textContent = `${answered} dari ${pairs.length} perbandingan sudah dijawab`;
      if (unsavedNote) unsavedNote.hidden = !isDirty();
    }

    let returnToReview = false;
    function show(index, focus = true, fromReview = false) {
      current = Math.max(0, Math.min(pairs.length - 1, index));
      reviewing = false;
      returnToReview = fromReview;
      pairs.forEach((pair, i) => { pair.hidden = i !== current; });
      cards[current].refreshEstimate();
      ranking.hidden = true;
      editOrder.hidden = false;
      review.hidden = true;
      controls.hidden = false;
      previous.disabled = current === 0;
      next.textContent = returnToReview ? "Kembali ke tinjauan"
        : current === pairs.length - 1 ? "Tinjau jawaban" : "Berikutnya";
      position.textContent = `Perbandingan ${current + 1} dari ${pairs.length}`;
      check.hidden = true;
      submit.hidden = true;
      overview.hidden = false;
      if (focus) cards[current].title.focus();
    }

    function showReview(focus = true) {
      reviewing = true;
      pairs.forEach(pair => { pair.hidden = true; });
      ranking.hidden = true;
      editOrder.hidden = false;
      controls.hidden = true;
      review.hidden = false;
      check.hidden = false;
      submit.hidden = false;
      overview.hidden = true;
      position.textContent = "Langkah terakhir: tinjau jawaban";
      returnToReview = false;
      reviewList.replaceChildren();
      selects.forEach((select, index) => {
        const pair = pairs[index];
        const row = element("li");
        const answer = element("p", describe(select.value, pair.dataset.left, pair.dataset.right));
        const edit = element("button", "Ubah", { type: "button", class: "secondary", "aria-label": `Ubah perbandingan ${index + 1}: ${pair.dataset.left} dan ${pair.dataset.right}` });
        edit.addEventListener("click", () => show(index, true, true));
        row.append(answer);
        const hint = serverHints[index];
        if (hint && select.value === hint.chosen) {
          row.classList.add("is-hinted");
          row.append(element("p", `Disarankan ditinjau. Lebih konsisten: ${hint.suggestion}.`, { class: "ahp-review-hint" }));
        }
        const conflict = orderConflict(order, Number(pair.dataset.leftIndex), Number(pair.dataset.rightIndex), select.value);
        if (conflict) {
          row.classList.add("has-conflict");
          row.append(element("p", `Berlawanan dengan urutan kriteria Anda (${names[conflict.expected]} di atas ${names[conflict.chosen]}).`, { class: "ahp-order-warning" }));
        }
        row.append(edit);
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
      if (returnToReview || current === pairs.length - 1) showReview();
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
    window.addEventListener("beforeunload", event => {
      if (sending || !isDirty()) return;
      event.preventDefault();
      event.returnValue = "";
    });
    form.classList.add("is-guided");
    form.closest(".work-area").classList.add("ahp-work-area");
    document.querySelectorAll(".ahp-hint-link").forEach(link => {
      link.addEventListener("click", event => {
        const index = Number(link.dataset.pair);
        if (!Number.isInteger(index) || index < 0 || index >= pairs.length) return;
        event.preventDefault();
        show(index, true, true);
        form.scrollIntoView({ block: "start" });
      });
    });
    const missing = selects.findIndex(select => !select.value);
    const untouched = selects.every(select => !select.value);
    if (form.dataset.review === "true" || missing === -1) showReview(false);
    else if (untouched && !order) showRanking(false);
    else show(missing, false);
    updateCount();
  }

  document.querySelectorAll(".ahp-form").forEach(enhance);
})();
