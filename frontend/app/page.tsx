import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen grid place-items-center px-6">
      <div className="max-w-xl text-center">
        <h1 className="font-serif text-4xl mb-4">Luxury Brochure Studio</h1>
        <p className="text-lg text-neutral-700 mb-8">
          Generate editorial-grade hotel brochures in seconds.
        </p>
        <div className="flex justify-center gap-3">
          <Link className="px-5 py-3 bg-black text-white" href="/login">Log In</Link>
          <Link className="px-5 py-3 border border-black" href="/signup">Sign Up</Link>
        </div>
      </div>
    </main>
  );
}
