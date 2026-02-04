"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

const pageMotion = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("token");
    if (!token) {
      router.replace("/login");
    }
  }, [router]);

  return (
    <motion.main
      className="min-h-screen bg-[#0b0d12] text-white"
      initial="initial"
      animate="animate"
      variants={pageMotion}
    >
      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(1200px_800px_at_18%_12%,rgba(255,255,255,0.10),rgba(11,13,18,0)),radial-gradient(900px_700px_at_82%_22%,rgba(90,120,255,0.12),rgba(11,13,18,0)),radial-gradient(1200px_900px_at_50%_85%,rgba(255,255,255,0.06),rgba(11,13,18,0))]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0),rgba(0,0,0,0.45))]" />
        </div>

        <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-12 px-6 py-16">
          <header className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-4">
              <span className="inline-flex items-center gap-2 rounded-full border border-white/20 px-4 py-2 text-xs uppercase tracking-[0.35em] text-white/70">
                Studio Dashboard
              </span>
              <h1 className="font-serif text-4xl leading-tight md:text-5xl">Luxury brochure command center</h1>
              <p className="max-w-xl text-base text-white/70">
                Generate refined marketing covers, review recent exports, and keep your brand visuals consistent.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
                <Link
                  className="rounded-full border border-white/20 px-6 py-3 text-sm uppercase tracking-[0.25em] text-white/80 transition hover:border-white/40"
                  href="/dashboard/history"
                >
                  View history
                </Link>
              </motion.div>
              <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
                <Link
                  className="rounded-full bg-white px-6 py-3 text-sm font-semibold uppercase tracking-[0.25em] text-black transition hover:bg-white/90"
                  href="/dashboard/generate"
                >
                  Generate brochure
                </Link>
              </motion.div>
            </div>
          </header>

          <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <motion.div
              className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur"
              whileHover={{ y: -4, boxShadow: "0 20px 50px rgba(0,0,0,0.35)" }}
              transition={{ duration: 0.25 }}
            >
              <h2 className="font-serif text-2xl">Recent workflow</h2>
              <p className="mt-3 text-sm text-white/70">
                Start with a prompt, review the editorial copy, then export PNG or PDF for client delivery.
              </p>
              <div className="mt-6 grid gap-4 text-sm text-white/75">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <span>1. Draft your prompt</span>
                  <span className="text-white/45">15 sec</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <span>2. Generate AI visual + copy</span>
                  <span className="text-white/45">45 sec</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>3. Export and share</span>
                  <span className="text-white/45">Instant</span>
                </div>
              </div>
            </motion.div>

            <motion.div
              className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/8 via-white/3 to-transparent p-8"
              whileHover={{ y: -4, boxShadow: "0 20px 50px rgba(0,0,0,0.35)" }}
              transition={{ duration: 0.25 }}
            >
              <h3 className="text-xs uppercase tracking-[0.35em] text-white/60">Quick actions</h3>
              <div className="mt-5 grid gap-4 text-sm text-white/75">
                <div className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4">
                  Create a premium brochure for a new resort concept.
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4">
                  Review exports and deliver final PDFs to stakeholders.
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4">
                  Maintain a consistent editorial aesthetic across launches.
                </div>
              </div>
            </motion.div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            {[{ label: "Editorial layouts", value: "1080x1350" }, { label: "Export formats", value: "PNG + PDF" }, { label: "Image generation", value: "AI assisted" }].map((item) => (
              <motion.div
                key={item.label}
                className="rounded-2xl border border-white/10 bg-white/5 p-5"
                whileHover={{ y: -3, boxShadow: "0 18px 40px rgba(0,0,0,0.35)" }}
                transition={{ duration: 0.25 }}
              >
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">{item.label}</p>
                <p className="mt-3 text-lg font-semibold text-white/90">{item.value}</p>
              </motion.div>
            ))}
          </section>
        </div>
      </div>
    </motion.main>
  );
}
