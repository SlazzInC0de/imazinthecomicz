import Hero from "@/components/Hero";
import SearchPanel from "@/components/SearchPanel";
import Ticker from "@/components/Ticker";
import { KINDS, type Kind } from "@/lib";

type Params = Promise<Record<string, string | string[] | undefined>>;

const num = (v: unknown, fallback: number) => {
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 && n <= 1 ? n : fallback;
};

export default async function Home({ searchParams }: { searchParams: Params }) {
  const sp = await searchParams;
  const kind = (KINDS as readonly string[]).includes(String(sp.kind)) ? (sp.kind as Kind) : "all";
  const initial = {
    q: typeof sp.q === "string" ? sp.q.slice(0, 300) : "",
    kind,
    tone: num(sp.tone, 0.5),
    scope: num(sp.scope, 0.5),
    view: sp.view === "grid" ? ("grid" as const) : ("page" as const),
  };
  return (
    <>
      <Hero />
      <div className="wrap">
        <SearchPanel initial={initial} />
      </div>
      <Ticker />
    </>
  );
}
