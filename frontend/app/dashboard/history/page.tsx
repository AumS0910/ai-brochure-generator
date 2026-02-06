"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion as fmMotion } from "framer-motion";
import { apiHistory } from "../../../lib/api";
const motion: any = fmMotion;

const pageMotion = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

function formatPresetLabel(preset?: string) {
  if (!preset) return "editorial luxury";
  return preset.replace(/_/g, " ");
}

export default function HistoryPage() {
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("token");
    if (!token) {
      router.replace("/login");
      return;
    }
    apiHistory()
      .then((data) => {
        setItems(data);
        setLoading(false);
      })
      .catch((e) => {
        const msg = e.message || "Failed to load";
        if (msg.toLowerCase().includes("session expired")) {
          router.replace("/login");
          return;
        }
        setError(msg);
        setLoading(false);
      });
  }, [router]);

  return (
    <motion.main
      className="min-h-screen bg-[#0b0d12] text-white"
      initial="initial"
      animate="animate"
      variants={pageMotion}
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(1200px_800px_at_18%_12%,rgba(255,255,255,0.10),rgba(11,13,18,0)),radial-gradient(900px_700px_at_82%_22%,rgba(90,120,255,0.12),rgba(11,13,18,0)),radial-gradient(1200px_900px_at_50%_85%,rgba(255,255,255,0.06),rgba(11,13,18,0))]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0),rgba(0,0,0,0.45))]" />
      </div>
      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-16">
        <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 px-4 py-2 text-xs uppercase tracking-[0.35em] text-white/70">
              Archive
            </span>
            <h1 className="font-serif text-4xl md:text-5xl">Brochure history</h1>
            <p className="max-w-2xl text-base text-white/70">
              Revisit your latest exports and keep the visual story consistent across resort launches.
            </p>
          </div>
          <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
            <Link
              className="rounded-full bg-white px-6 py-3 text-sm font-semibold uppercase tracking-[0.25em] text-black transition hover:bg-white/90"
              href="/dashboard/generate"
            >
              Generate brochure
            </Link>
          </motion.div>
        </header>

        {error && (
          <p className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">{error}</p>
        )}

        {loading ? (
          <section className="grid gap-6 lg:grid-cols-2">
            {[1, 2, 3, 4].map((item) => (
              <div key={item} className="rounded-3xl border border-white/10 bg-white/5 p-5">
                <div className="h-64 animate-pulse rounded-2xl bg-white/10" />
                <div className="mt-4 h-3 w-3/4 animate-pulse rounded-full bg-white/10" />
                <div className="mt-2 h-3 w-2/3 animate-pulse rounded-full bg-white/10" />
              </div>
            ))}
          </section>
        ) : items.length === 0 && !error ? (
          <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-white/70">
            No brochures yet. Generate your first luxury cover to see it here.
          </div>
        ) : (
          <section className="grid gap-6 lg:grid-cols-2">
            {items.map((item) => (
              <motion.article
                key={item.id}
                className="rounded-3xl border border-white/10 bg-white/5 p-5"
                whileHover={{ y: -4, boxShadow: "0 20px 50px rgba(0,0,0,0.35)" }}
                transition={{ duration: 0.25 }}
              >
                <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/40">
                  <img
                    className="h-full w-full object-cover"
                    src={`http://localhost:8000${item.png_url}`}
                    alt="Brochure"
                  />
                </div>
                <p className="mt-3 text-xs uppercase tracking-[0.25em] text-white/55">
                  Preset: {formatPresetLabel(item.preset)}
                </p>
                <p className="mt-4 text-sm text-white/70 line-clamp-3">{item.prompt}</p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <a
                    className="rounded-full border border-white/20 px-4 py-2 text-xs uppercase tracking-[0.25em] text-white/80"
                    href={`http://localhost:8000${item.png_url}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    PNG
                  </a>
                  <a
                    className="rounded-full bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-black"
                    href={`http://localhost:8000${item.pdf_url}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    PDF
                  </a>
                </div>
              </motion.article>
            ))}
          </section>
        )}
      </div>
    </motion.main>
  );
}
