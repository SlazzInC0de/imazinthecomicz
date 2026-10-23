import Link from "next/link";

import { metaLine } from "@/lib/format";
import type { Card } from "@/lib/types";

import Cover from "./Cover";

type Props = {
  comic: Card;
  splash?: boolean;
  priority?: boolean;
};

export default function ComicCard({ comic, splash = false, priority = false }: Props) {
  const href = `/comic/${comic.id}`;
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
        {matched.length > 0 && <p className="match">Mentions {matched.join(", ").toLowerCase()}</p>}
        {splash && comic.blurb && <p className="blurb">{comic.blurb}</p>}
      </div>
    </li>
  );
}
