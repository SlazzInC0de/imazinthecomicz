import type { Metadata } from "next";
import Link from "next/link";

import styles from "./about.module.css";

export const metadata: Metadata = {
  title: "How the search works",
  description: "How Imazinthecomics ranks manga and comics by the story you describe: embeddings, keyword search and tone sliders.",
  alternates: { canonical: "/about" },
};

const REPO = "https://github.com/SlazzInC0de/imazinthecomicz";

export default function About() {
  return (
    <article className={styles.page}>
      <h1>How the search works</h1>
      <p className={styles.lede}>
        Most comic sites search titles and tags. Here you describe the story, and the search ranks titles by what their
        synopsis is about.
      </p>

      <h2>Where the titles come from</h2>
      <p>
        Manga, manhwa and manhua come from <a href="https://anilist.co">AniList</a>, with their synopses, genres, ranked
        themes, creators and covers. Western series come from <a href="https://metron.cloud">Metron</a> (and{" "}
        <a href="https://comicvine.gamespot.com">Comic Vine</a> when a key is set): the longest-running series with a real
        synopsis, plus the cover of their first issue.
        Light novels, adult titles and entries with no real synopsis are left out. The catalog is rebuilt by a GitHub
        Actions job, so the numbers on the home page are always from the last build.
      </p>

      <h2>Ranking</h2>
      <p>Every query is scored twice:</p>
      <ul>
        <li>
          <strong>By meaning.</strong> Each title&apos;s synopsis, genres and themes are turned into a vector with the{" "}
          <code>bge-small-en-v1.5</code> embedding model. Your query gets one too, and titles are scored by how close
          the two point.
        </li>
        <li>
          <strong>By words.</strong> BM25 keyword scoring over the same text, with the title counted three times, so
          typing a series or character name still finds it.
        </li>
      </ul>
      <p>
        The two scores are blended 70 to 30. A title that matches your query exactly jumps to the top, and popularity
        only breaks near ties. There is no &ldquo;95% match&rdquo; badge on results: the benchmark showed that raw
        similarity scores of good and bad hits overlap almost completely, so a percentage would be made up. Results only
        say which of your words they share with a title&apos;s genres or themes.
      </p>

      <h2>Tone and scale</h2>
      <p>
        AniList ranks how strongly each theme applies to a title, like Tragedy at 87% or Iyashikei at 92%. Themes and
        genres push a title toward darker or lighter, and toward grounded or world-ending. Each title then gets its
        position as a percentile of the whole catalog, so the middle of a slider is the middle of the catalog. The
        sliders are off until you switch them on, and even then they only reorder close matches.
      </p>

      <h2>Does it actually work?</h2>
      <p>
        The repo ships a benchmark of 35 queries. Most describe a story without using the genre or theme name
        (&ldquo;spirits haunting an old house&rdquo; for Horror or Ghost), so keyword search alone cannot cheat. It
        compares random picks, keyword only, meaning only and the blended ranking on precision at 5 and 10.{" "}
        <a href={`${REPO}/blob/main/eval/results.md`}>Latest results</a>.
      </p>

      <h2>Stack</h2>
      <p>
        A FastAPI service holds the catalog and the embedding matrix in memory and answers searches in tens of
        milliseconds. This site is Next.js, rendered on the server, so every comic page is a real page with its own
        title, description and preview image. <a href={REPO}>Source code on GitHub</a>.
      </p>

      <p className={styles.back}>
        <Link href="/">Back to search</Link>
      </p>
    </article>
  );
}
