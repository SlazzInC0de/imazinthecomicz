import Link from "next/link";

import { matchText, metaLine } from "@/lib/format";
import type { Card } from "@/lib/types";

import Cover from "./Cover";

type Props = {
  comic: Card;
  splash?: boolean;
  priority?: boolean;
};

export default function ComicCard({ comic, splash = false, priority = false }: Props) {
  const href = `/comic/${comic.id}`;
  const label = matchText(comic.match?.label);
  const matched = comic.match?.matched ?? [];
  return (
    <li className={splash ? "card splash" : "card"}>
      <Link href={href} className="cover-link" tabIndex={-1} aria-hidden="true">
        <Cover src={comic.cover} title={comic.title} color={comic.cover_color} priority={priority} />
      </Link>
      <div className="card-text">
        <h3 className="card-title">
          <Link href={href}>{comic.title}</Link>
        </h3>
        <p className="card-meta">{metaLine(comic)}</p>
        {label && (
          <p className={`match ${comic.match?.label}`}>
            <strong>{label}</strong>
            {matched.length > 0 && <>, mentions {matched.join(", ").toLowerCase()}</>}
          </p>
        )}
        {splash && comic.blurb && <p className="blurb">{comic.blurb}</p>}
      </div>
    </li>
  );
}
