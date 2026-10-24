"use client";

import { useEffect, useRef } from "react";

/** Two halftone layers that drift at different speeds with the mouse. Hero only; off for touch and reduced motion. */
export default function HeroDots() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!window.matchMedia("(pointer: fine)").matches || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    const onMove = (e: MouseEvent) => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const x = e.clientX / window.innerWidth - 0.5;
        const y = e.clientY / window.innerHeight - 0.5;
        el.style.setProperty("--dx1", `${x * -14}px`);
        el.style.setProperty("--dy1", `${y * -14}px`);
        el.style.setProperty("--dx2", `${x * -34}px`);
        el.style.setProperty("--dy2", `${y * -34}px`);
      });
    };
    window.addEventListener("mousemove", onMove);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);
  return <div ref={ref} className="hero-dots" aria-hidden="true" />;
}
