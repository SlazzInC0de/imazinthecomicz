"use client";
/* eslint-disable @next/next/no-img-element */
import { useState } from "react";
import type { Comic } from "@/lib";

/** Real cover when the source has one; a lettered title card when it doesn't or the image fails. Never fake art. */
export default function Cover({ comic, eager = false }: { comic: Comic; eager?: boolean }) {
  const [failed, setFailed] = useState(false);
  if (comic.cover && !failed) {
    return (
      <img
        className="cover-img"
        src={comic.cover}
        alt={`Cover of ${comic.title}`}
        loading={eager ? "eager" : "lazy"}
        decoding="async"
        onError={() => setFailed(true)}
      />
    );
  }
  return (
    <div className="cover-none" role="img" aria-label={`${comic.title} (no cover available)`}>
      <span>{comic.title}</span>
      <small>{failed ? "Cover didn't load" : "No cover on file"}</small>
    </div>
  );
}
