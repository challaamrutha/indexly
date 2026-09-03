"use client";

import { useRef, useState } from "react";

const API = "http://127.0.0.1:8000";

type SearchResult = {
  type: "transcript" | "visual";
  title: string;
  timestamp: string;
  timestamp_seconds?: number;
  start: number;
  end?: number;
  description?: string;
  summary?: string;
  video_url?: string;
  thumbnail_url?: string;
  score?: number;
  speech_score?: number;
  visual_score?: number;
  ocr_score?: number;
};

type UploadedVideo = {
  id: string;
  name: string;
  url: string;
};

function getVideoUrl(path?: string) {
  if (!path) return "";

  if (
    path.startsWith("http://") ||
    path.startsWith("https://")
  ) {
    return path;
  }

  return `${API}${path}`;
}

function formatScore(score?: number) {
  if (score === undefined) {
    return "";
  }

  return `${Math.round(score * 100)}% match`;
}

export default function Home() {
  const videoRef =
    useRef<HTMLVideoElement>(null);

  const [videos, setVideos] =
    useState<UploadedVideo[]>([]);

  const [activeVideo, setActiveVideo] =
    useState<UploadedVideo | null>(null);

  const [query, setQuery] =
    useState("");

  const [results, setResults] =
    useState<SearchResult[]>([]);

  const [uploading, setUploading] =
    useState(false);

  const [searching, setSearching] =
    useState(false);

  const [message, setMessage] =
    useState("");

  async function uploadVideo(file: File) {
    setUploading(true);
    setMessage("");
    setResults([]);

    try {
      const formData =
        new FormData();

      formData.append(
        "file",
        file
      );

      const response =
        await fetch(
          `${API}/upload`,
          {
            method: "POST",
            body: formData,
          }
        );

      if (!response.ok) {
        throw new Error(
          "Upload failed"
        );
      }

      const data =
        await response.json();

      if (data.error) {
        throw new Error(
          data.error
        );
      }

      const video: UploadedVideo = {
        id: data.video_id,
        name:
          data.filename ||
          file.name,
        url: getVideoUrl(
          data.video_url ||
            data.path
        ),
      };

      setVideos(
        (current) => [
          ...current,
          video,
        ]
      );

      setActiveVideo(video);

      setMessage(
        `${video.name} indexed successfully.`
      );
    } catch (error) {
      console.error(error);

      setMessage(
        "Could not upload and index the video."
      );
    } finally {
      setUploading(false);
    }
  }

  async function searchVideos() {
    const trimmedQuery =
      query.trim();

    if (!trimmedQuery) {
      setResults([]);
      setMessage("");
      return;
    }

    if (videos.length === 0) {
      setMessage(
        "Upload a video first."
      );
      return;
    }

    setSearching(true);
    setMessage("");

    try {
      const response =
        await fetch(
          `${API}/search`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              query:
                trimmedQuery,
            }),
          }
        );

      if (!response.ok) {
        throw new Error(
          "Search failed"
        );
      }

      const data =
        await response.json();

      const searchResults =
        Array.isArray(
          data.results
        )
          ? data.results
          : [];

      setResults(
        searchResults
      );

      if (
        searchResults.length ===
        0
      ) {
        setMessage(
          "No matching moments found."
        );
      }
    } catch (error) {
      console.error(error);

      setMessage(
        "Search failed. Please try again."
      );

      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  function openResult(
    result: SearchResult
  ) {
    const matchingVideo =
      videos.find(
        (video) =>
          result.video_url &&
          video.url ===
            getVideoUrl(
              result.video_url
            )
      );

    if (
      matchingVideo &&
      activeVideo?.url !==
        matchingVideo.url
    ) {
      setActiveVideo(
        matchingVideo
      );

      setTimeout(() => {
        seekVideo(
          result.start
        );
      }, 150);

      return;
    }

    seekVideo(
      result.start
    );
  }

  function seekVideo(
    seconds: number
  ) {
    const player =
      videoRef.current;

    if (!player) {
      return;
    }

    player.currentTime =
      Math.max(
        0,
        seconds
      );

    player.play().catch(() => {
      // Browser may require manual play.
    });
  }

  return (
    <main className="page">
      <div className="container">
        <header className="header">
          <div>
            <h1>
              Indexly
            </h1>

            <p>
              Search inside your videos.
            </p>
          </div>

          <label className="upload-button">
            {uploading
              ? "Indexing..."
              : "Upload Video"}

            <input
              type="file"
              accept="video/*"
              hidden
              disabled={uploading}
              onChange={(event) => {
                const file =
                  event.target
                    .files?.[0];

                if (file) {
                  uploadVideo(
                    file
                  );
                }

                event.target.value =
                  "";
              }}
            />
          </label>
        </header>

        {videos.length > 0 && (
          <section className="video-library">
            <h2>
              Video Library
            </h2>

            <div className="video-list">
              {videos.map(
                (video) => (
                  <button
                    key={video.id}
                    className={
                      activeVideo?.id ===
                      video.id
                        ? "video-item active"
                        : "video-item"
                    }
                    onClick={() =>
                      setActiveVideo(
                        video
                      )
                    }
                  >
                    {video.name}
                  </button>
                )
              )}
            </div>
          </section>
        )}

        <section className="search-section">
          <div className="search-box">
            <input
              type="text"
              value={query}
              placeholder="Search your videos..."
              onChange={(event) =>
                setQuery(
                  event.target.value
                )
              }
              onKeyDown={(event) => {
                if (
                  event.key ===
                  "Enter"
                ) {
                  searchVideos();
                }
              }}
            />

            <button
              onClick={
                searchVideos
              }
              disabled={
                searching ||
                videos.length ===
                  0
              }
            >
              {searching
                ? "Searching..."
                : "Search"}
            </button>
          </div>
        </section>

        {message && (
          <p className="message">
            {message}
          </p>
        )}

        {activeVideo && (
          <section className="video-section">
            <div className="video-header">
              <h2>
                {activeVideo.name}
              </h2>
            </div>

            <video
              ref={videoRef}
              className="video-player"
              src={
                activeVideo.url
              }
              controls
              preload="metadata"
            />
          </section>
        )}

        {results.length > 0 && (
          <section className="results-section">
            <div className="results-header">
              <div>
                <h2>
                  Search Results
                </h2>

                <p>
                  {results.length} matching moments
                </p>
              </div>
            </div>

            <div className="results">
              {results.map(
                (
                  result,
                  index
                ) => (
                  <button
                    className="result-card"
                    key={`${result.video_url}-${result.timestamp}-${index}`}
                    onClick={() =>
                      openResult(
                        result
                      )
                    }
                  >
                    {result.thumbnail_url ? (
                      <img
                        className="result-thumbnail"
                        src={getVideoUrl(
                          result.thumbnail_url
                        )}
                        alt=""
                      />
                    ) : (
                      <div className="result-thumbnail placeholder">
                        {result.type ===
                        "visual"
                          ? "VISUAL"
                          : "VIDEO"}
                      </div>
                    )}

                    <div className="result-time">
                      {
                        result.timestamp
                      }
                    </div>

                    <div className="result-content">
                      <div className="result-topline">
                        <span className="result-type">
                          {result.type ===
                          "visual"
                            ? "Visual match"
                            : "Transcript match"}
                        </span>

                        {result.score !==
                          undefined && (
                          <span className="result-score">
                            {formatScore(
                              result.score
                            )}
                          </span>
                        )}
                      </div>

                      <h3>
                        {result.title}
                      </h3>

                      {result.summary && (
                        <p className="result-summary">
                          {result.summary}
                        </p>
                      )}

                      {result.description &&
                        result.description !==
                          result.summary && (
                          <p className="result-description">
                            {result.description}
                          </p>
                        )}

                      <div className="result-signals">
                        {result.speech_score !==
                          undefined &&
                          result.speech_score >
                            0 && (
                            <span>
                              Speech
                            </span>
                          )}

                        {result.visual_score !==
                          undefined &&
                          result.visual_score >
                            0 && (
                            <span>
                              Vision
                            </span>
                          )}

                        {result.ocr_score !==
                          undefined &&
                          result.ocr_score >
                            0 && (
                            <span>
                              OCR
                            </span>
                          )}
                      </div>
                    </div>
                  </button>
                )
              )}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
