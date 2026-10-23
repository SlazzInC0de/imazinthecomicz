import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import ComicCard from "@/components/ComicCard";
import Cover from "@/components/Cover";
import { api, ApiError } from "@/lib/api";
import { lengthText, metaLine, sourceName, summary } from "@/lib/format";
import type { BrowseResponse, Comic } from "@/lib/types";

import styles from "./comic.module.css";

type Params = Promise<{ id: string }>;

const ID = /^(al|cv|mt)-\d{1,9}$/;
const READABLE = /^[\p{Script=Latin}\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}\p{N}\p{P}\p{Zs}\p{S}]+$/u;

async function getComic(id: string): Promise<Comic | null> {
  if (!ID.test(id)) return null;
  try {
    return await api<Comic>(`/api/comics/${id}`, undefined, { revalidate: 86400 });
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const comic = await getComic((await params).id).catch(() => null);
  if (!comic) return { title: "Comic not found", robots: { index: false } };
  const description = summary(comic.description);
  return {
    title: `${comic.title} (${comic.kind}${comic.year ? `, ${comic.year}` : ""})`,
    description,
    alternates: { canonical: `/comic/${comic.id}` },
    openGraph: {
      title: comic.title,
      description,
      type: "article",
      images: comic.cover ? [{ url: comic.cover, alt: `Cover of ${comic.title}` }] : undefined,
    },
  };
}

function Scale(props: {
  label: string;
  low: string;
  high: string;
  lowMore: string;
  highMore: string;
  value: number;
}) {
  const { label, low, high, value } = props;
  const pct = Math.round(value * 100);
  const toward = value >= 0.5 ? props.highMore : props.lowMore;
  const share = Math.min(99, value >= 0.5 ? pct : 100 - pct);
  return (
    <div className={styles.scale}>
      <div className={styles.scaleHead}>
        <span>{label}</span>
        <span className={styles.scaleNote}>
          {Math.abs(value - 0.5) < 0.1 ? "about average" : `${toward} than ${share}% of titles`}
        </span>
      </div>
      <div className={styles.track} role="img" aria-label={`${label}: ${pct} out of 100, from ${low} to ${high}`}>
        <span className={styles.marker} style={{ left: `${pct}%` }} />
      </div>
      <div className={styles.ends} aria-hidden="true">
        <span>{low}</span>
        <span>{high}</span>
      </div>
    </div>
  );
}

export default async function ComicPage({ params }: { params: Params }) {
  const { id } = await params;
  const comic = await getComic(id);
  if (!comic) notFound();

  let similar: BrowseResponse["results"] = [];
  try {
    similar = (
      await api<BrowseResponse>(`/api/comics/${comic.id}/similar`, new URLSearchParams({ limit: "12" }), {
        revalidate: 86400,
      })
    ).results;
  } catch {}

  const length = lengthText(comic);
  const facts: [string, React.ReactNode][] = [
    ["Kind", comic.kind === "Western" ? "Western comic" : comic.kind],
    ["Format", comic.format],
    ["Started", comic.year],
    ["Status", comic.status],
    ["Length", length],
    ["Reader score", comic.score != null ? `${comic.score} / 100 on AniList` : null],
    ["Created by", comic.creators.length ? comic.creators.join(", ") : null],
    ["Publisher", comic.publisher],
  ];
  const paragraphs = comic.description.split(/\n{2,}/).filter(Boolean);
  // romaji and the original script; AniList synonyms also hold fan translations in many languages
  const altTitles = comic.alt_titles.filter((t) => READABLE.test(t)).slice(0, 2);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ComicSeries",
    name: comic.title,
    alternateName: comic.alt_titles.length ? comic.alt_titles : undefined,
    description: summary(comic.description, 300),
    image: comic.cover ?? undefined,
    genre: comic.genres,
    author: comic.creators.map((name) => ({ "@type": "Person", name })),
    publisher: comic.publisher ? { "@type": "Organization", name: comic.publisher } : undefined,
    startDate: comic.year ? String(comic.year) : undefined,
    sameAs: comic.url ?? undefined,
  };

  return (
    <article className={styles.page}>
      <script
        type="application/ld+json"
        // JSON.stringify output with "<" escaped cannot break out of the script tag
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }}
      />
      <div className={`blueline ${styles.coverPanel}`}>
        <Cover src={comic.cover} title={comic.title} color={comic.cover_color} priority />
      </div>

      <div className={styles.info}>
        <p className={styles.meta}>{metaLine(comic)}</p>
        <h1 className={styles.title}>{comic.title}</h1>
        {altTitles.length > 0 && <p className={styles.alt}>Also known as {altTitles.join(", ")}</p>}

        <div className={styles.synopsis}>
          {paragraphs.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>

        {comic.genres.length > 0 && (
          <ul className={styles.labels} aria-label="Genres">
            {comic.genres.map((g) => (
              <li key={g}>
                <Link href={`/search?genre=${encodeURIComponent(g)}`}>{g}</Link>
              </li>
            ))}
          </ul>
        )}
        {comic.tags.length > 0 && (
          <p className={styles.tags}>
            Themes:{" "}
            {comic.tags.map((t, i) => (
              <span key={t}>
                <Link href={`/search?q=${encodeURIComponent(t)}`}>{t}</Link>
                {i < comic.tags.length - 1 && ", "}
              </span>
            ))}
          </p>
        )}

        <dl className={styles.facts}>
          {facts
            .filter(([, v]) => v != null && v !== "")
            .map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
        </dl>

        <div className={styles.scales}>
          <Scale label="Tone" low="Lighter" high="Darker" lowMore="lighter" highMore="darker" value={comic.tone} />
          <Scale
            label="Scale"
            low="Grounded"
            high="World-ending"
            lowMore="more grounded"
            highMore="bigger in scale"
            value={comic.scope}
          />
        </div>

        {comic.url && (
          <p>
            <a href={comic.url} rel="noopener">
              Read more on {sourceName(comic)}
            </a>
          </p>
        )}
      </div>

      {similar.length > 0 && (
        <section className={styles.similar} aria-labelledby="similar">
          <h2 id="similar">If you liked {comic.title}</h2>
          <ul className="panels">
            {similar.map((c) => (
              <ComicCard key={c.id} comic={c} />
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
