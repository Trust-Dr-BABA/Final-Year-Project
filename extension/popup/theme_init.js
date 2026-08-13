/**
 * theme_init.js — Applies the persisted theme before the popup paints.
 * A separate, non-module file loaded synchronously (no `type="module"`, no `defer`) so it blocks
 * rendering until it runs — the same effect an inline <script> would have, but as an external
 * file, which manifest.json's CSP (`script-src 'self'`) permits and inline script content does not.
 */
(function () {
  var stored = localStorage.getItem("esa-theme");
  var theme = stored === "light" || stored === "dark"
    ? stored
    : (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", theme);
})();
