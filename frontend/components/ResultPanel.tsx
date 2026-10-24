import Cover from "./Cover";
import PeelLink from "./PeelLink";
import { metaLine, shortText, type Comic } from "@/lib";

/** One comic panel. Hover or keyboard focus: ink misregistration + a caption box with the synopsis. */
export default function ResultPanel({ comic, slot, rank }: { comic: Comic; slot?: number; rank?: number }) {
  return (
    <li className={`panel${slot !== undefined ? ` slot-${slot}` : ""}`}>
      <PeelLink href={`/comic/${comic.id}`} className="panel-link" aria-describedby={`syn-${comic.id}`}>
        <span className="panel-frame">
          <Cover comic={comic} />
          <span className="panel-kind">{comic.kind}</span>
          {comic.match !== undefined && (
            <span className="panel-match" title="How closely this title matches your description">
              {Math.round(comic.match * 100)}% match
            </span>
          )}
          <span className="panel-label">
            <span className="panel-title">
              {rank !== undefined && <span className="sr-only">Result {rank}: </span>}
              {comic.title}
            </span>
            <span className="panel-meta">{metaLine(comic)}</span>
          </span>
        </span>
        <span className="panel-tip" id={`syn-${comic.id}`} role="tooltip">
          {comic.description ? shortText(comic.description, 160) : "No synopsis on file yet."}
        </span>
      </PeelLink>
    </li>
  );
}
