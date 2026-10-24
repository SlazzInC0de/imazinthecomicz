"use client";

import { useState } from "react";
import { api, type Comic } from "@/lib";
import { usePeel } from "./PeelTransition";

export default function SurpriseButton() {
  const peelTo = usePeel();
  const [busy, setBusy] = useState(false);
  return (
    <button
      type="button"
      className="nav-random"
      disabled={busy}
      onClick={async () => {
        setBusy(true);
        try {
          const c = await api<Comic>("/api/random");
          peelTo(`/comic/${c.id}`);
        } finally {
          setBusy(false);
        }
      }}
    >
      {busy ? "Shuffling..." : "Surprise me!"}
    </button>
  );
}
