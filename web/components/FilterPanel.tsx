"use client";

import { useEffect, useRef } from "react";

/**
 * Filters. The markup ships open, so they work without JavaScript at any width.
 * With JavaScript, phones fold them away unless a filter is active, and the
 * panel follows the breakpoint when the window is resized.
 */
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
      if (ref.current) ref.current.open = wide.matches || active;
    };
    sync();
    wide.addEventListener("change", sync);
    return () => wide.removeEventListener("change", sync);
  }, [active]);
  return (
    <details ref={ref} className={className} open>
      <summary>Filters</summary>
      {children}
    </details>
  );
}
