import Link from "next/link";

import SearchBalloon from "@/components/SearchBalloon";

export default function NotFound() {
  return (
    <section style={{ marginTop: 64, display: "grid", gap: 20, maxWidth: 760 }}>
      <h1 style={{ fontFamily: "var(--letter)", fontSize: "clamp(2rem, 5vw, 3rem)", fontWeight: 800 }}>
        This page was never printed.
      </h1>
      <p style={{ margin: 0, fontSize: "1.15rem" }}>
        The link is wrong or the title left the catalog. Describe what you were after and search again, or go back to
        the <Link href="/">front page</Link>.
      </p>
      <SearchBalloon />
    </section>
  );
}
