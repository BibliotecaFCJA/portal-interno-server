"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

function getStoredTheme(): "light" | "dark" {
  try {
    const stored = window.localStorage.getItem("portal:theme");
    if (stored === "dark" || stored === "light") return stored;
  } catch {
    // armazenamento indisponível
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme: "light" | "dark") {
  document.documentElement.classList.toggle("dark", theme === "dark");
  try {
    window.localStorage.setItem("portal:theme", theme);
  } catch {
    // armazenamento indisponível
  }
}

export function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const initial = getStoredTheme();
    setTheme(initial);
    setMounted(true);
    applyTheme(initial);
  }, []);

  function toggle() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
  }

  const isDark = theme === "dark";

  return (
    <button
      aria-label={isDark ? "Ativar modo claro" : "Ativar modo escuro"}
      className={`inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-foreground transition hover:border-primary hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${className ?? ""}`}
      onClick={toggle}
      title={isDark ? "Modo claro" : "Modo escuro"}
      type="button"
    >
      {mounted ? (
        isDark ? (
          <Sun aria-hidden="true" size={16} />
        ) : (
          <Moon aria-hidden="true" size={16} />
        )
      ) : (
        <span aria-hidden="true" className="block h-4 w-4" />
      )}
    </button>
  );
}