/* Jam WIB pada header. Hanya tampilan; tidak memengaruhi data kejadian. */
"use strict";

(() => {
  const clocks = document.querySelectorAll("[data-clock]");
  if (!clocks.length) return;
  const format = new Intl.DateTimeFormat("id-ID", {
    timeZone: "Asia/Jakarta", day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  });
  const tick = () => {
    const now = new Date();
    const text = format.format(now).replace(/\./g, ":").replace(" pukul ", " · ");
    clocks.forEach(clock => {
      clock.textContent = text;
      clock.dateTime = now.toISOString();
    });
  };
  tick();
  setInterval(tick, 1000);
})();
