"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion as fmMotion } from "framer-motion";
import { apiEdit, apiGenerate, apiGenerateWithHero, apiUploadGallery, apiUpdateContact } from "../../../lib/api";

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
const stylePresets = ["editorial_luxury", "modern_minimal", "vibrant_resort", "wellness_calm"] as const;
const motion: any = fmMotion;

function formatPresetLabel(preset: string) {
  return preset.replace(/_/g, " ");
}

export default function GeneratePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [refineInput, setRefineInput] = useState("");
  const [refineError, setRefineError] = useState("");
  const [refineLoading, setRefineLoading] = useState(false);
  const [previewStamp, setPreviewStamp] = useState<number>(Date.now());
  const [presets, setPresets] = useState<string[]>([]);
  const [heroFile, setHeroFile] = useState<File | null>(null);
  const [galleryFiles, setGalleryFiles] = useState<File[]>([]);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [galleryError, setGalleryError] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [contactWebsite, setContactWebsite] = useState("");
  const [contactAddress, setContactAddress] = useState("");
  const [contactLoading, setContactLoading] = useState(false);
  const [contactError, setContactError] = useState("");
  const [selectedPreset, setSelectedPreset] = useState<string>("editorial_luxury");
  const [presetLoading, setPresetLoading] = useState(false);

  const qrPreviewUrl = (() => {
    const raw = result?.schema?.sections?.contact?.qr_code_url;
    if (!raw) return "";
    if (typeof raw === "string" && raw.startsWith("file:///")) {
      const parts = raw.split("/output/");
      if (parts.length > 1) {
        return `http://localhost:8000/files/${parts[1]}`.replace("\\", "/");
      }
    }
    return raw;
  })();

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

  useEffect(() => {
    const presetFromSchema = result?.schema?.preset;
    if (typeof presetFromSchema === "string" && presetFromSchema.length > 0) {
      setSelectedPreset(presetFromSchema);
    }
  }, [result?.schema?.preset]);

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
      const res = heroFile
        ? await apiGenerateWithHero(prompt.trim(), heroFile, selectedPreset)
        : await apiGenerate(prompt.trim(), selectedPreset);
      setResult(res);
      setSelectedPreset(res?.schema?.preset || selectedPreset);
      setPreviewStamp(Date.now());
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
      const res = heroFile
        ? await apiGenerateWithHero(prompt.trim(), heroFile, selectedPreset)
        : await apiGenerate(prompt.trim(), selectedPreset);
      setResult(res);
      setSelectedPreset(res?.schema?.preset || selectedPreset);
      setPreviewStamp(Date.now());
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

  async function handleRefine(e: React.FormEvent) {
    e.preventDefault();
    setRefineError("");
    if (!result?.id) return;
    if (!refineInput.trim()) {
      setRefineError("Add a short instruction to refine.");
      return;
    }
    setRefineLoading(true);
    try {
      const res = await apiEdit(result.id, refineInput.trim());
      if (res?.error) {
        setRefineError(res.message || "No valid edits detected.");
        return;
      }
      setResult((prev: any) => ({
        ...prev,
        schema: res.schema,
        png_url: res.png_url,
        pdf_url: res.pdf_url,
      }));
      if (res?.schema?.preset) {
        setSelectedPreset(res.schema.preset);
      }
      setPreviewStamp(Date.now());
      setRefineInput("");
    } catch (err: any) {
      const msg = err.message || "Refine failed";
      if (msg.toLowerCase().includes("session expired")) {
        router.replace("/login");
        return;
      }
      setRefineError(msg);
    } finally {
      setRefineLoading(false);
    }
  }

  async function handlePresetChange(nextPreset: string) {
    setSelectedPreset(nextPreset);
    if (!result?.id) return;
    if (result?.schema?.preset === nextPreset) return;
    setPresetLoading(true);
    setRefineError("");
    try {
      const res = await apiEdit(result.id, `Set preset to ${nextPreset}.`);
      if (res?.error) {
        setRefineError(res.message || "Preset update failed.");
        return;
      }
      setResult((prev: any) => ({
        ...prev,
        schema: res.schema,
        png_url: res.png_url,
        pdf_url: res.pdf_url,
      }));
      setSelectedPreset(res?.schema?.preset || nextPreset);
      setPreviewStamp(Date.now());
    } catch (err: any) {
      const msg = err.message || "Preset update failed";
      if (msg.toLowerCase().includes("session expired")) {
        router.replace("/login");
        return;
      }
      setRefineError(msg);
    } finally {
      setPresetLoading(false);
    }
  }

  async function handleGalleryUpload(e: React.FormEvent) {
    e.preventDefault();
    setGalleryError("");
    if (!result?.id) return;
    if (galleryFiles.length === 0) {
      setGalleryError("Select 1 to 5 images to upload.");
      return;
    }
    setGalleryLoading(true);
    try {
      const res = await apiUploadGallery(result.id, galleryFiles);
      setResult((prev: any) => ({
        ...prev,
        schema: res.schema,
        png_url: res.png_url,
        pdf_url: res.pdf_url,
      }));
      setPreviewStamp(Date.now());
      setGalleryFiles([]);
    } catch (err: any) {
      const msg = err.message || "Gallery upload failed";
      if (msg.toLowerCase().includes("session expired")) {
        router.replace("/login");
        return;
      }
      setGalleryError(msg);
    } finally {
      setGalleryLoading(false);
    }
  }

  async function handleContactSubmit(e: React.FormEvent) {
    e.preventDefault();
    setContactError("");
    if (!result?.id) return;
    setContactLoading(true);
    try {
      const res = await apiUpdateContact(result.id, {
        email: contactEmail || undefined,
        phone: contactPhone || undefined,
        website: contactWebsite || undefined,
        address: contactAddress || undefined,
      });
      setResult((prev: any) => ({
        ...prev,
        schema: res.schema,
        png_url: res.png_url,
        pdf_url: res.pdf_url,
      }));
      setPreviewStamp(Date.now());
    } catch (err: any) {
      const msg = err.message || "Contact update failed";
      if (msg.toLowerCase().includes("session expired")) {
        router.replace("/login");
        return;
      }
      setContactError(msg);
    } finally {
      setContactLoading(false);
    }
  }

  return (
    <motion.div
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

        <section className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
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

              <div className="grid gap-2">
                <label className="text-xs uppercase tracking-[0.25em] text-white/60">
                  Hero image (optional)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white/80 file:mr-3 file:rounded-full file:border-0 file:bg-white/15 file:px-4 file:py-2 file:text-xs file:uppercase file:tracking-[0.25em] file:text-white/70"
                  onChange={(e) => setHeroFile(e.target.files?.[0] ?? null)}
                />
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {allPrompts.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setPrompt(item)}
                    className="rounded-full border border-white/15 px-4 py-2 text-xs text-white/70 transition hover:border-white/40"
                  >
                    Use prompt
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

              <div className="flex flex-wrap items-center gap-3">
                {stylePresets.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => handlePresetChange(preset)}
                    className={`rounded-full border px-4 py-2 text-xs transition ${
                      selectedPreset === preset
                        ? "border-white/50 bg-white/10 text-white"
                        : "border-white/15 text-white/70 hover:border-white/40"
                    }`}
                    disabled={presetLoading}
                  >
                    {formatPresetLabel(preset)}
                  </button>
                ))}
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
                  src={`http://localhost:8000${result.png_url}?t=${previewStamp}`}
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

            {result && (
              <form onSubmit={handleGalleryUpload} className="mt-6 grid gap-3">
                <div className="text-[11px] uppercase tracking-[0.32em] text-white/55">
                  Enhance with additional images (optional)
                </div>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white/80 file:mr-3 file:rounded-full file:border-0 file:bg-white/15 file:px-4 file:py-2 file:text-xs file:uppercase file:tracking-[0.25em] file:text-white/70"
                  onChange={(e) => setGalleryFiles(Array.from(e.target.files ?? []))}
                />
                {galleryError && (
                  <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                    {galleryError}
                  </div>
                )}
                <motion.button
                  className="w-full rounded-2xl border border-white/25 px-5 py-3 text-xs uppercase tracking-[0.3em] text-white/80 transition hover:border-white/50 disabled:cursor-not-allowed disabled:opacity-60"
                  type="submit"
                  disabled={galleryLoading}
                  whileHover={{ scale: galleryLoading ? 1 : 1.02 }}
                  whileTap={{ scale: galleryLoading ? 1 : 0.98 }}
                >
                  {galleryLoading ? "Uploading..." : "Upload gallery"}
                </motion.button>
              </form>
            )}

            {result && (
              <form onSubmit={handleContactSubmit} className="mt-6 grid gap-3">
                <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.32em] text-white/55">
                  <span>Public contact details shown on the brochure</span>
                  <span className="h-px w-10 bg-white/15" />
                </div>
                <input
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white placeholder-white/35 outline-none transition focus:border-white/50 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.12)]"
                  placeholder="Email"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                />
                <input
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white placeholder-white/35 outline-none transition focus:border-white/50 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.12)]"
                  placeholder="Phone"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                />
                <input
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white placeholder-white/35 outline-none transition focus:border-white/50 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.12)]"
                  placeholder="Website (QR will appear after save)"
                  value={contactWebsite}
                  onChange={(e) => setContactWebsite(e.target.value)}
                />
                <input
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white placeholder-white/35 outline-none transition focus:border-white/50 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.12)]"
                  placeholder="Address"
                  value={contactAddress}
                  onChange={(e) => setContactAddress(e.target.value)}
                />
                {contactError && (
                  <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                    {contactError}
                  </div>
                )}
                <motion.button
                  className="w-full rounded-2xl border border-white/25 px-5 py-3 text-xs uppercase tracking-[0.3em] text-white/80 transition hover:border-white/50 disabled:cursor-not-allowed disabled:opacity-60"
                  type="submit"
                  disabled={contactLoading}
                  whileHover={{ scale: contactLoading ? 1 : 1.02 }}
                  whileTap={{ scale: contactLoading ? 1 : 0.98 }}
                >
                  {contactLoading ? "Saving..." : "Save contact"}
                </motion.button>
                {qrPreviewUrl && (
                  <div className="mt-2 rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-xs uppercase tracking-[0.25em] text-white/60">QR preview</div>
                    <img
                      className="mt-3 h-28 w-28 rounded-lg bg-white p-2"
                      src={qrPreviewUrl}
                      alt="QR code preview"
                    />
                  </div>
                )}
              </form>
            )}

            {result && (
              <form onSubmit={handleRefine} className="mt-6 grid gap-3">
                <div className="text-xs uppercase tracking-[0.35em] text-white/60">Refine with AI</div>
                <input
                  className="w-full rounded-2xl border border-white/15 bg-transparent px-4 py-3 text-sm text-white placeholder-white/35 outline-none transition focus:border-white/50 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.12)]"
                  placeholder="e.g. Make it more minimal, remove dining, emphasize spa."
                  value={refineInput}
                  onChange={(e) => setRefineInput(e.target.value)}
                />
                {refineError && (
                  <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                    {refineError}
                  </div>
                )}
                <motion.button
                  className="w-full rounded-2xl border border-white/25 px-5 py-3 text-xs uppercase tracking-[0.3em] text-white/80 transition hover:border-white/50 disabled:cursor-not-allowed disabled:opacity-60"
                  type="submit"
                  disabled={refineLoading || presetLoading}
                  whileHover={{ scale: refineLoading || presetLoading ? 1 : 1.02 }}
                  whileTap={{ scale: refineLoading || presetLoading ? 1 : 0.98 }}
                >
                  {refineLoading ? "Refining..." : presetLoading ? "Updating preset..." : "Apply refinement"}
                </motion.button>
              </form>
            )}
          </motion.div>
        </section>
      </div>
    </motion.div>
  );
}
