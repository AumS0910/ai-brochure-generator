"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiLogin } from "../../lib/api";

const pageMotion = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const token = await apiLogin(email, password);
      localStorage.setItem("token", token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  }

  return (
    <motion.main
      className="relative min-h-screen overflow-hidden bg-[#0b0d12] text-white"
      initial="initial"
      animate="animate"
      variants={pageMotion}
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(1200px_800px_at_15%_10%,rgba(255,255,255,0.10),rgba(11,13,18,0)),radial-gradient(900px_700px_at_85%_20%,rgba(90,120,255,0.12),rgba(11,13,18,0)),radial-gradient(1200px_900px_at_50%_80%,rgba(255,255,255,0.06),rgba(11,13,18,0))]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0),rgba(0,0,0,0.45))]" />
      </div>

      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl items-center px-6 py-16">
        <div className="grid w-full grid-cols-1 gap-12 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="space-y-8">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 px-4 py-2 text-xs uppercase tracking-[0.35em] text-white/70">
              Luxury Brochures
            </div>
            <h1 className="font-serif text-4xl leading-tight text-white md:text-5xl">
              Welcome back to your editorial studio
            </h1>
            <p className="max-w-xl text-base leading-relaxed text-white/70">
              Generate premium hotel brochures in minutes. Refined layouts, cinematic imagery, and calm editorial
              copy built for luxury brands.
            </p>
            <div className="flex flex-wrap gap-4 text-sm text-white/70">
              <span className="rounded-full border border-white/15 px-4 py-2">1080x1350 exports</span>
              <span className="rounded-full border border-white/15 px-4 py-2">PNG + PDF</span>
              <span className="rounded-full border border-white/15 px-4 py-2">AI hero imagery</span>
            </div>
          </section>

          <motion.section
            className="rounded-3xl border border-white/10 bg-white/5 p-8 shadow-[0_30px_80px_rgba(0,0,0,0.35)] backdrop-blur"
            whileHover={{ y: -2 }}
            transition={{ duration: 0.25 }}
          >
            <div className="mb-8">
              <h2 className="font-serif text-3xl">Sign in</h2>
              <p className="mt-2 text-sm text-white/65">Access your brochures and manage new generations.</p>
            </div>

            <form onSubmit={handleSubmit} className="grid gap-4">
              <div className="grid gap-2">
                <label className="text-xs uppercase tracking-[0.25em] text-white/60">Email</label>
                <input
                  className="w-full rounded-xl border border-white/15 bg-transparent px-4 py-3 text-white placeholder-white/35 outline-none transition focus:border-white/50 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.12)]"
                  placeholder="you@hotelbrand.com"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="grid gap-2">
                <label className="text-xs uppercase tracking-[0.25em] text-white/60">Password</label>
                <input
                  className="w-full rounded-xl border border-white/15 bg-transparent px-4 py-3 text-white placeholder-white/35 outline-none transition focus:border-white/50 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.12)]"
                  placeholder="Enter your password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              {error && <p className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">{error}</p>}

              <motion.button
                className="mt-2 w-full rounded-xl bg-white px-5 py-3 text-sm font-semibold uppercase tracking-[0.3em] text-black transition hover:bg-white/90"
                type="submit"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Log In
              </motion.button>
            </form>

            <p className="mt-6 text-sm text-white/70">
              New here?{" "}
              <Link className="font-semibold text-white underline underline-offset-4" href="/signup">
                Create an account
              </Link>
            </p>
          </motion.section>
        </div>
      </div>
    </motion.main>
  );
}
