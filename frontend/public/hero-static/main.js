"use strict";
if (document.documentElement.classList.contains("hero-embedded")) {
  window.addEventListener("wheel", event => {
    if (document.body.classList.contains("menu-open")) return;
    event.preventDefault();
    const scale = event.deltaMode === 1 ? 18 : event.deltaMode === 2 ? innerHeight : 1;
    window.parent.postMessage({ type: "verifai:hero-scroll", delta: event.deltaY * scale }, location.origin);
  }, { passive: false });
  let lastTouchY = null;
  window.addEventListener("touchstart", event => { lastTouchY = event.touches.length === 1 ? event.touches[0].clientY : null; }, { passive: true });
  window.addEventListener("touchmove", event => {
    if (lastTouchY === null || document.body.classList.contains("menu-open")) return;
    const y = event.touches[0].clientY;
    const delta = (lastTouchY - y) * 1.4;
    lastTouchY = y;
    if (Math.abs(delta) < 1) return;
    event.preventDefault();
    window.parent.postMessage({ type: "verifai:hero-scroll", delta }, location.origin);
  }, { passive: false });
  window.addEventListener("touchend", () => { lastTouchY = null; }, { passive: true });
}




const burger = document.querySelector(".burger");
const menu = document.querySelector(".mobile-menu");
const overlay = document.querySelector(".menu-overlay");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

// The full-bleed hero uses local, muted film. Keep its matching still as a
// reliable fallback, and never animate for visitors requesting reduced motion.
const heroVideo = document.querySelector(".bg-video");
const heroBackground = document.querySelector(".bg");
if (heroVideo) {
  heroVideo.addEventListener("playing", () => heroBackground?.classList.add("is-ready"));
  heroVideo.addEventListener("error", () => heroBackground?.classList.remove("is-ready"));
  const syncHeroVideo = () => {
    if (reducedMotion.matches || document.hidden) {
      heroVideo.pause();
      heroBackground?.classList.remove("is-ready");
    } else {
      void heroVideo.play().catch(() => heroBackground?.classList.remove("is-ready"));
    }
  };
  reducedMotion.addEventListener("change", syncHeroVideo);
  document.addEventListener("visibilitychange", syncHeroVideo);
  syncHeroVideo();
}

function setMenu(open) {
  if (!burger || !menu || !overlay) return;
  const shouldOpen = Boolean(open);
  burger.setAttribute("aria-expanded", String(shouldOpen));
  burger.setAttribute("aria-label", shouldOpen ? "Close menu" : "Open menu");
  menu.hidden = !shouldOpen;
  overlay.hidden = !shouldOpen;
  document.body.classList.toggle("menu-open", shouldOpen);
  if (shouldOpen) menu.querySelector("a")?.focus({ preventScroll: true });
}
burger?.addEventListener("click", () => setMenu(burger.getAttribute("aria-expanded") !== "true"));
overlay?.addEventListener("click", () => setMenu(false));
menu?.querySelectorAll("a").forEach(link => link.addEventListener("click", () => setMenu(false)));
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && burger?.getAttribute("aria-expanded") === "true") {
    setMenu(false);
    burger.focus({ preventScroll: true });
  }
});
window.addEventListener("resize", () => {
  if (window.innerWidth > 720) setMenu(false);
}, { passive: true });

const counters = [...document.querySelectorAll(".stat-value[data-target]")];
const easeOutCubic = t => 1 - Math.pow(1 - t, 3);
let counted = false;

function revealNumbers() {
  if (counted) return;
  counted = true;
  counters.forEach((element, index) => {
    const target = Number(element.dataset.target);
    const decimals = Number(element.dataset.decimals) || 0;
    const suffix = element.dataset.suffix || "";
    const width = Number(element.dataset.pad) || 0;
    const format = amount => amount.toFixed(decimals).padStart(width, "0") + suffix;
    const finalValue = format(target);

    if (reducedMotion.matches) {
      element.textContent = finalValue;
      return;
    }
    const duration = 1500 + index * 80;
    const delay = 480 + index * 90;
    window.setTimeout(() => {
      let start;
      const draw = now => {
        if (start === undefined) start = now;
        const amount = Math.min(1, (now - start) / duration);
        element.textContent = format(target * easeOutCubic(amount));
        if (amount < 1) requestAnimationFrame(draw);
        else element.textContent = finalValue;
      };
      requestAnimationFrame(draw);
    }, delay);
  });
}

const stats = document.querySelector(".stats");
if (stats && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting && entry.intersectionRatio >= 0.25)) {
      revealNumbers();
      observer.disconnect();
    }
  }, { threshold: [0.25] });
  observer.observe(stats);
} else {
  revealNumbers();
}
