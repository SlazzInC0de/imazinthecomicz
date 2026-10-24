"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

type Phase = "idle" | "out" | "in";
const PeelContext = createContext<(href: string) => void>(() => {});

export const usePeel = () => useContext(PeelContext);

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Comic page-turn between routes: the paper peels in from the corner, the route changes, then it peels away. */
export default function PeelTransition({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [phase, setPhase] = useState<Phase>("idle");
  const target = useRef<string | null>(null);

  const peelTo = useCallback(
    (href: string) => {
      if (prefersReducedMotion()) {
        router.push(href);
        return;
      }
      target.current = href;
      setPhase("out");
    },
    [router],
  );

  // New route rendered: reveal it.
  useEffect(() => {
    setPhase((p) => (p === "out" && target.current === null ? "in" : p));
  }, [pathname]);

  return (
    <PeelContext.Provider value={peelTo}>
      {children}
      <div
        className={`peel peel-${phase}`}
        aria-hidden="true"
        onAnimationEnd={() => {
          if (phase === "out" && target.current) {
            const href = target.current;
            target.current = null;
            const samePage = new URL(href, window.location.href).pathname === window.location.pathname;
            router.push(href);
            if (samePage) setPhase("in"); // pathname won't change, so reveal right away
            else window.scrollTo({ top: 0 });
          } else if (phase === "in") {
            setPhase("idle");
          }
        }}
      />
    </PeelContext.Provider>
  );
}
