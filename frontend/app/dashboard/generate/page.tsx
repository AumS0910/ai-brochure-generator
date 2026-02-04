"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { apiGenerate } from "../../../lib/api";

const pageMotion = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

const defaultPrompts = [
  "Create a luxury brochure for Aurora Vista Resort in Santorini with cliffside suites, a sunset terrace, and a private spa.",
  "Design a premium brochure for Azure Meridian Resort in Maldives with overwater villas, a calm lagoon, and chef-led dining.",
  "Generate a luxury brochure for Verdant Tide Resort in Seychelles with beachfront villas, palm-lined pool, and open-air wellness rituals.",
];

const presetsKey = "brochure_presets";

export default function GeneratePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [presets, setPresets] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("token");
    if (!token) {
      router.replace("/login");
      return;
    }
    const stored = localStorage.getItem(presetsKey);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) setPresets(parsed);
      } catch {
        setPresets([]);
      }
    }
  }, [router]);

  const isPromptValid = prompt.trim().length >= 12;

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!isPromptValid) {
      setError("Prompt is too short. Please add more detail.");
      return;
    }
    setLoading(true);
    try {
      const res = await apiGenerate(prompt.trim());
      setResult(res);
    } catch (err: any) {
      const msg = err.message || "Generation failed";
      if (msg.toLowerCase().includes("session expired")) {
        router.replace("/login");
        return;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleRetry() {
    if (!isPromptValid || loading) return;
    setError("");
    setLoading(true);
    try {
      const res = await apiGenerate(prompt.trim());
      setResult(res);
    } catch (err: any) {
      const msg = err.message || "Generation failed";
      if (msg.toLowerCase().includes("session expired")) {
        router.replace("/login");
        return;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function handleSavePreset() {
    if (!isPromptValid) return;
    const next = [prompt.trim(), ...presets].slice(0, 6);
    setPresets(next);
    localStorage.setItem(presetsKey, JSON.stringify(next));
  }

  const allPrompts = [...defaultPrompts, ...presets];

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
              Brochure Studio
            </span>
            <h1 className="font-serif text-4xl md:text-5xl">Generate a luxury brochure</h1>
            <p className="max-w-2xl text-base text-white/70">
              Craft a refined prompt and produce a premium cover with cinematic imagery, editorial copy, and instant exports.
            </p>
          </div>
          <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
            <Link
              className="rounded-full border border-white/20 px-6 py-3 text-sm uppercase tracking-[0.25em] text-white/80 transition hover:border-white/40"
              href="/dashboard/history"
            >
              View history
            </Link>
          </motion.div>
        </header>

        <section className="grid gap-8 lg:grid-cols-[1fr_1fr]">
          <motion.div
            className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur"
            whileHover={{ y: -3, boxShadow: "0 20px 50px rgba(0,0,0,0.35)" }}
            transition={{ duration: 0.25 }}
          >
            <h2 className="font-serif text-2xl">Prompt</h2>
            <p className="mt-2 text-sm text-white/65">
              Describe the resort, tone, and key amenities. Keep it calm, editorial, and brand-ready.
            </p>

            <form onSubmit={handleGenerate} className="mt-6 grid gap-4">
              <textarea
                className="min-h-[200px] w-full rounded-2xl border border-white/15 bg-transparent px-4 py-4 text-white placeholder-white/35 outline-none transition focus:border-white/50 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.12)]"
                placeholder="Create a luxury brochure for Aurora Vista Resort in Santorini..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                required
              />

              <div className="flex flex-wrap items-center gap-3">
                {allPrompts.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setPrompt(item)}
                    className="rounded-full border border-white/15 px-4 py-2 text-xs text-white/70 transition hover:border-white/40"
                  >
                    Use preset
                  </button>
                ))}
                <button
                  type="button"
                  onClick={handleSavePreset}
                  className="rounded-full border border-white/25 px-4 py-2 text-xs uppercase tracking-[0.25em] text-white/80 transition hover:border-white/40"
                >
                  Save prompt
                </button>
              </div>

              {!isPromptValid && prompt.length > 0 && (
                <p className="text-xs text-white/50">Add a little more detail for a stronger result.</p>
              )}

              {error && (
                <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                  <div>{error}</div>
                  <button
                    type="button"
                    onClick={handleRetry}
                    className="mt-2 text-xs uppercase tracking-[0.25em] text-red-100 underline underline-offset-4"
                  >
                    Retry
                  </button>
                </div>
              )}

              {result && !loading && !error && (
                <div className="rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-xs uppercase tracking-[0.25em] text-white/70">
                  Generation complete
                </div>
              )}

              <motion.button
                className="mt-2 w-full rounded-2xl bg-white px-5 py-4 text-sm font-semibold uppercase tracking-[0.3em] text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-60"
                type="submit"
                disabled={loading || !isPromptValid}
                whileHover={{ scale: loading || !isPromptValid ? 1 : 1.02 }}
                whileTap={{ scale: loading || !isPromptValid ? 1 : 0.98 }}
              >
                {loading ? "Generating..." : "Generate brochure"}
              </motion.button>
            </form>
          </motion.div>

          <motion.div
            className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/8 via-white/3 to-transparent p-8"
            whileHover={{ y: -3, boxShadow: "0 20px 50px rgba(0,0,0,0.35)" }}
            transition={{ duration: 0.25 }}
          >
            <h2 className="font-serif text-2xl">Preview</h2>
            <p className="mt-2 text-sm text-white/65">Your latest export will appear here once generated.</p>
            {result && !loading && !error && (
              <p className="mt-2 text-xs uppercase tracking-[0.25em] text-white/60">Ready to download</p>
            )}

            <div className="mt-6 overflow-hidden rounded-2xl border border-white/10 bg-black/40">
              {loading ? (
                <div className="flex h-[520px] flex-col items-center justify-center gap-4">
                  <div className="text-xs uppercase tracking-[0.35em] text-white/50">Rendering</div>
                  <div className="h-3 w-44 animate-pulse rounded-full bg-white/15" />
                  <div className="h-3 w-56 animate-pulse rounded-full bg-white/10" />
                </div>
              ) : result ? (
                <img
                  className="h-full w-full object-cover"
                  src={`http://localhost:8000${result.png_url}`}
                  alt="Brochure preview"
                />
              ) : (
                <div className="flex h-[520px] items-center justify-center text-sm text-white/50">
                  Generate a brochure to preview the layout.
                </div>
              )}
            </div>

            {result && (
              <div className="mt-6 flex flex-wrap gap-3">
                <a
                  className="rounded-full border border-white/20 px-5 py-3 text-xs uppercase tracking-[0.25em] text-white/80"
                  href={`http://localhost:8000${result.png_url}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download PNG
                </a>
                <a
                  className="rounded-full bg-white px-5 py-3 text-xs font-semibold uppercase tracking-[0.25em] text-black"
                  href={`http://localhost:8000${result.pdf_url}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download PDF
                </a>
              </div>
            )}
          </motion.div>
        </section>
      </div>
    </motion.main>
  );
}
