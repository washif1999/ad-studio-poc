"use client";

import { useState } from "react";
import "./globals.css";

export default function Home() {
  const [url, setUrl] = useState("");
  const [jobId, setJobId] = useState("");
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("Awaiting URL input...");
  const [isGenerating, setIsGenerating] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");

  const handleGenerate = async () => {
    if (!url) return;
    
    setIsGenerating(true);
    setProgress(5);
    setStatus("Initiating connection to backend...");
    setVideoUrl("");
    
    try {
      // Hit the FastAPI backend
      const res = await fetch("http://127.0.0.1:8000/api/ads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, tenant_id: "demo-frontend" })
      });
      
      const data = await res.json();
      const id = data.job_id;
      setJobId(id);
      
      // Connect to the SSE stream via EventSource
      const eventSource = new EventSource(`http://127.0.0.1:8000/api/ads/stream/${id}`);
      
      eventSource.onmessage = (event) => {
        const msg = event.data;
        
        // Match progress percentages like "[40%] [40%] Writing Script..."
        // The backend currently sends double brackets due to a formatting quirk, so we parse it safely.
        const match = msg.match(/\[(\d+)%\]\s*(?:\[\d+%\]\s*)?(.*)/);
        
        if (match) {
          setProgress(Number(match[1]));
          const currentStatus = match[2];
          
          if (currentStatus.includes("SUCCESS")) {
            const urlMatch = currentStatus.split("|");
            const finalUrl = urlMatch.length > 1 ? urlMatch[1] : "ready";
            setStatus("Ad generation complete! Video Rendered.");
            eventSource.close();
            setVideoUrl(finalUrl); 
            setIsGenerating(false);
          } else if (currentStatus.includes("FAILED")) {
            setStatus(currentStatus);
            eventSource.close();
            setIsGenerating(false);
          } else {
            setStatus(currentStatus);
          }
        }
      };
      
      eventSource.onerror = () => {
        setStatus("Lost connection to progress stream.");
        eventSource.close();
        setIsGenerating(false);
      }
      
    } catch (e) {
      setStatus("Failed to connect to backend. Is Uvicorn running?");
      setIsGenerating(false);
    }
  };

  return (
    <div className="container">
      <header className="hero-header">
        <h1>Studio BE</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "1.2rem", marginTop: "10px" }}>
          Transform any URL into a high-converting video ad in seconds.
        </p>
      </header>

      <div className="glass-panel">
        <div className="input-group">
          <input 
            type="url" 
            className="input-field" 
            placeholder="Paste landing page URL (e.g., https://apple.com)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isGenerating}
          />
          <button 
            className="btn-primary" 
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? "Generating..." : "Create Ad"}
          </button>
        </div>

        {(isGenerating || progress > 0) && (
          <div>
            <div className="progress-container">
              <div className="progress-bar" style={{ width: `${progress}%` }}></div>
            </div>
            <div className="status-text">{status}</div>
          </div>
        )}
      </div>

      {videoUrl && (
        <div className="video-frame">
          <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
            <h2 style={{ color: "var(--accent)", margin: 0, fontSize: "2rem", marginBottom: "20px" }}>Video Rendered Successfully!</h2>
            {videoUrl !== "ready" && videoUrl.startsWith("http") ? (
              <video 
                controls 
                autoPlay 
                style={{ width: "100%", maxWidth: "800px", borderRadius: "12px", border: "2px solid var(--accent)" }}
              >
                <source src={videoUrl} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            ) : (
              <p style={{ color: "var(--text-muted)", marginTop: "15px" }}>
                (Check your Turso DB row for the real Creatomate MP4 link)
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
