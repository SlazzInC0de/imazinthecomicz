"use client";

import Link from "next/link";
import { usePeel } from "./PeelTransition";

/** A real link (works with keyboard, middle-click, new tab) that plays the page turn on a normal click. */
export default function PeelLink({ href, className, children, ...rest }: React.ComponentProps<typeof Link> & { href: string }) {
  const peelTo = usePeel();
  return (
    <Link
      href={href}
      className={className}
      onClick={(e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        peelTo(href);
      }}
      {...rest}
    >
      {children}
    </Link>
  );
}
