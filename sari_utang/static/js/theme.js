// Light / dark theme. Loaded in <head> so the theme is set before the page is drawn (no flash).
// "auto" follows the device; a person's choice is kept in this browser only.

(() => {
  const KEY = "sari-utang-theme";
  const CHOICES = ["auto", "light", "dark"];
  const LABELS = { auto: "Auto", light: "Light", dark: "Dark" };
  const dark = window.matchMedia("(prefers-color-scheme: dark)");

  // saved() -> "auto", "light" or "dark" (the saved choice; "auto" if none or storage is blocked)
  const saved = () => {
    try {
      const value = localStorage.getItem(KEY);
      return CHOICES.includes(value) ? value : "auto";
    } catch {
      return "auto";
    }
  };

  // apply("auto") -> sets data-bs-theme to "dark" or "light" by what the device prefers
  const apply = (choice) => {
    const theme = choice === "auto" ? (dark.matches ? "dark" : "light") : choice;
    document.documentElement.setAttribute("data-bs-theme", theme);
  };

  // showButtons("dark") -> every theme button says "Theme: Dark"
  const showButtons = (choice) => {
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.textContent = `Theme: ${LABELS[choice]}`;
    });
  };

  // No colour animation while the first theme is applied (removed once the page has loaded).
  document.documentElement.classList.add("preload");
  window.addEventListener("load", () => {
    requestAnimationFrame(() => document.documentElement.classList.remove("preload"));
  });

  apply(saved());
  dark.addEventListener("change", () => apply(saved()));

  // An invoice is always printed dark on white paper, whatever the theme on screen.
  window.addEventListener("beforeprint", () => document.documentElement.setAttribute("data-bs-theme", "light"));
  window.addEventListener("afterprint", () => apply(saved()));

  document.addEventListener("DOMContentLoaded", () => {
    showButtons(saved());
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const next = CHOICES[(CHOICES.indexOf(saved()) + 1) % CHOICES.length];
        try {
          localStorage.setItem(KEY, next);
        } catch {
          // Private window or blocked storage: the choice only lasts for this page.
        }
        apply(next);
        showButtons(next);
      });
    });
  });
})();
