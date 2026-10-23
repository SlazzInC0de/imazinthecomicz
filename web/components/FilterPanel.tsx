"use client";

import { useEffect, useRef } from "react";

/** Filters stay folded on phones unless some are active; always open on wider screens. */
export default function FilterPanel({
  className,
  active,
  children,
}: {
  className?: string;
  active: boolean;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const wide = window.matchMedia("(min-width: 861px)");
    const sync = () => {
      if (wide.matches && ref.current) ref.current.open = true;
    };
    sync();
    wide.addEventListener("change", sync);
    return () => wide.removeEventListener("change", sync);
  }, []);
  return (
    <details ref={ref} className={className} open={active || undefined}>
      <summary>Filters</summary>
      {children}
    </details>
  );
}
