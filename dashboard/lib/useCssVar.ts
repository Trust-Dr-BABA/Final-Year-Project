"use client";

import { useEffect, useState } from "react";

// Resolves a CSS custom property to its current computed value, and re-reads it whenever the
// theme toggle flips `data-theme` on <html>. Charting libraries render to SVG attributes, which
// don't reliably resolve var(--x) themselves, so chart components need the literal colour.
export function useCssVar(name: string, fallback: string): string {
  const [value, setValue] = useState(fallback);

  useEffect(() => {
    const read = () => {
      const resolved = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      if (resolved) setValue(resolved);
    };
    read();

    const observer = new MutationObserver(read);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, [name]);

  return value;
}
