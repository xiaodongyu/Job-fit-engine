import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const isDark = mounted ? resolvedTheme === "dark" : false;

  return (
    <button
      type="button"
      className="btn btn-secondary"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Dark mode is on" : "Light mode is on"}
      style={{ padding: "0.5rem 0.75rem" }}
    >
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
        {isDark ? "☾ Dark" : "☀ Light"}
      </span>
    </button>
  );
}

