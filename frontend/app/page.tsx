"use client";

import { useState } from "react";

export default function Home() {
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSearch() {
    if (!query.trim()) {
      setMessage("Please enter a search query.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch("http://127.0.0.1:8000/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
        }),
      });

      const data = await response.json();

      setMessage(data.message);
    } catch (error) {
      console.error(error);
      setMessage("Could not connect to the Indexly API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-12">
        <header className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Indexly</h1>

          <span className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-300">
            AI Video Search
          </span>
        </header>

        <section className="flex flex-1 flex-col items-center justify-center text-center">
          <h2 className="max-w-3xl text-5xl font-bold tracking-tight sm:text-6xl">
            Search your videos with AI
          </h2>

          <p className="mt-6 max-w-2xl text-lg text-slate-400">
            Upload your video library and find exactly what you are looking
            for using natural language.
          </p>

          <div className="mt-10 flex w-full max-w-2xl gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleSearch();
                }
              }}
              placeholder="Search your videos..."
              className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-5 py-4 outline-none placeholder:text-slate-500 focus:border-slate-500"
            />

            <button
              onClick={handleSearch}
              disabled={loading}
              className="rounded-xl bg-white px-6 py-4 font-semibold text-slate-950 hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          {message && (
            <p className="mt-6 rounded-xl border border-slate-800 bg-slate-900 px-5 py-3 text-slate-300">
              {message}
            </p>
          )}

          <div className="mt-12 grid w-full max-w-3xl gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <h3 className="font-semibold">Upload</h3>
              <p className="mt-2 text-sm text-slate-400">
                Add your video library.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <h3 className="font-semibold">Index</h3>
              <p className="mt-2 text-sm text-slate-400">
                AI understands your videos.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <h3 className="font-semibold">Find</h3>
              <p className="mt-2 text-sm text-slate-400">
                Search using natural language.
              </p>
            </div>
          </div>
        </section>

        <footer className="py-6 text-center text-sm text-slate-500">
          Indexly · AI-powered video search
        </footer>
      </div>
    </main>
  );
}
