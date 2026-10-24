import Link from "next/link";
import SurpriseButton from "./SurpriseButton";

const LINKS = [
  { href: "/?kind=Manga", label: "Manga" },
  { href: "/?kind=Manhwa", label: "Manhwa" },
  { href: "/?kind=Marvel", label: "Marvel" },
  { href: "/?kind=DC", label: "DC" },
  { href: "/?kind=Western", label: "Western" },
];

export default function Nav() {
  return (
    <header className="nav">
      <Link href="/" className="nav-logo" aria-label="IMAZINTHECOMICS home">
        <svg viewBox="0 0 118 62" aria-hidden="true">
          <path d="M59 1 L68 14 L86 4 L84 19 L112 14 L96 28 L117 40 L92 42 L100 60 L78 50 L64 61 L56 48 L34 60 L38 44 L6 48 L24 34 L1 20 L28 20 L22 4 L44 13Z" />
        </svg>
        <span>
          IMAZIN
          <br />
          COMICS
        </span>
      </Link>
      <nav aria-label="Browse by type">
        <ul>
          {LINKS.map((l) => (
            <li key={l.href}>
              <Link href={l.href}>{l.label}</Link>
            </li>
          ))}
        </ul>
      </nav>
      <SurpriseButton />
    </header>
  );
}
