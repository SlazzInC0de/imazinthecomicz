"use client";

import { useState } from "react";

type Props = {
  src: string | null;
  title: string;
  color: string | null;
  priority?: boolean;
};

/** Cover art with a lettered stand-in when the image is missing or fails. */
export default function Cover({ src, title, color, priority = false }: Props) {
  const [failed, setFailed] = useState(!src);
  return (
    <div className="cover" style={{ background: color ?? "#26323a" }}>
      {failed ? (
        <span className="cover-fallback">{title}</span>
      ) : (
        // Covers come from AniList / Comic Vine CDNs and are already sized,
        // so they skip Next image optimisation.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src!}
          alt={`Cover of ${title}`}
          width={460}
          height={690}
          loading={priority ? "eager" : "lazy"}
          fetchPriority={priority ? "high" : "auto"}
          decoding="async"
          referrerPolicy="no-referrer"
          onError={() => setFailed(true)}
        />
      )}
    </div>
  );
}
