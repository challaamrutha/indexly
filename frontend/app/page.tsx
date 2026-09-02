"use client";

import { useState } from "react";

type SearchResult = {
  title: string;
  timestamp: string;
  description: string;
  video_url?: string;
};

export default function Home() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  async function handleSearch() {
    if (!query.trim()) {
      setMessage("Please enter a search query.");
      setResults([]);
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

      if (!response.ok) {
        throw new Error("Search request failed");
      }

      const data = await response.json();

      setResults(data.results || []);
      setMessage(data.message || "");
    } catch (error) {
      console.error(error);
      setMessage("Failed to connect to the backend.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload() {
    if (!selectedFile) {
      setUploadMessage("Please select a video first.");
      return;
    }

    setUploading(true);
    setUploadMessage("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      setUploadMessage(
        `✅ ${data.filename} uploaded successfully!`
      );
      setSelectedFile(null);
    } catch (error) {
      console.error(error);
      setUploadMessage("❌ Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "40px 20px",
        fontFamily: "Arial, sans-serif",
        background: "#f5f5f5",
      }}
    >
      <div
        style={{
          maxWidth: "900px",
          margin: "0 auto",
        }}
      >
        <h1
          style={{
            fontSize: "42px",
            marginBottom: "8px",
          }}
        >
          Indexly
        </h1>

        <p
          style={{
            color: "#666",
            marginBottom: "35px",
          }}
        >
          AI-powered search for your video library
        </p>

        {/* Upload section */}
        <section
          style={{
            background: "white",
            padding: "25px",
            borderRadius: "12px",
            marginBottom: "30px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <h2>Upload a Video</h2>

          <input
            type="file"
            accept="video/*"
            onChange={(event) => {
              const file = event.target.files?.[0] || null;
              setSelectedFile(file);
              setUploadMessage("");
            }}
            style={{
              marginTop: "10px",
              marginBottom: "15px",
            }}
          />

          {selectedFile && (
            <p>
              Selected: <strong>{selectedFile.name}</strong>
            </p>
          )}

          <button
            onClick={handleUpload}
            disabled={uploading}
            style={{
              padding: "10px 18px",
              border: "none",
              borderRadius: "8px",
              background: "#111",
              color: "white",
              cursor: uploading ? "not-allowed" : "pointer",
              marginTop: "5px",
            }}
          >
            {uploading ? "Uploading..." : "Upload Video"}
          </button>

          {uploadMessage && (
            <p style={{ marginTop: "15px" }}>{uploadMessage}</p>
          )}
        </section>

        {/* Search section */}
        <section
          style={{
            background: "white",
            padding: "25px",
            borderRadius: "12px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <h2>Search Videos</h2>

          <div
            style={{
              display: "flex",
              gap: "10px",
              marginTop: "15px",
            }}
          >
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSearch();
                }
              }}
              placeholder="Search for basketball, coach, football..."
              style={{
                flex: 1,
                padding: "12px",
                border: "1px solid #ccc",
                borderRadius: "8px",
                fontSize: "16px",
              }}
            />

            <button
              onClick={handleSearch}
              disabled={loading}
              style={{
                padding: "12px 20px",
                border: "none",
                borderRadius: "8px",
                background: "#111",
                color: "white",
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          {message && (
            <p
              style={{
                marginTop: "20px",
                color: "#555",
              }}
            >
              {message}
            </p>
          )}

          <div style={{ marginTop: "20px" }}>
            {results.map((result, index) => (
              <div
                key={index}
                style={{
                  border: "1px solid #ddd",
                  borderRadius: "10px",
                  padding: "18px",
                  marginBottom: "12px",
                }}
              >
                <h3 style={{ marginBottom: "8px" }}>
                  {result.title}
                </h3>

                <p>
                  <strong>Timestamp:</strong> {result.timestamp}
                </p>

                <p style={{ color: "#555" }}>
                  {result.description}
                </p>

                {result.video_url && (
                  <a
                    href={result.video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open Video
                  </a>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
