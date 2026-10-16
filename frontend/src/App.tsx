import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { api, type AppConfig, type EvidenceCard, type Job, type Source } from "./api";

const POLL_MS = 750;

function SourceBadge({ source }: { source: Source }) {
  return <span className={`badge ${source}`}>{source === "test" ? "TEST" : "LIVE"}</span>;
}

function Timestamped({ text, onSeek }: { text: string; onSeek: (s: number) => void }) {
  return text.split(/(\[\d+(?:\.\d+)?s\])/g).map((part, index) => {
    const match = /^\[(\d+(?:\.\d+)?)s\]$/.exec(part);
    if (!match) return <span key={index}>{part}</span>;
    const seconds = Number(match[1]);
    return (
      <button key={index} type="button" className="stamp" onClick={() => onSeek(seconds)}>
        {part}
      </button>
    );
  });
}

function EvidenceCards({
  cards,
  onSeek,
}: {
  cards: EvidenceCard[];
  onSeek: (s: number) => void;
}) {
  if (!cards.length) return null;
  return (
    <section className="cards">
      {cards.map((card) => (
        <article key={`${card.start_s}-${card.end_s}`} className="panel">
          <button type="button" className="stamp" onClick={() => onSeek(card.start_s)}>
            {card.start_s.toFixed(1)}s – {card.end_s.toFixed(1)}s
          </button>
          <p className="muted">
            Search <SourceBadge source={card.search_source} /> · Clip retrieval{" "}
            <SourceBadge source={card.clip_source} />
          </p>
          <p>{card.search_text}</p>
          <h3>
            Analysis <SourceBadge source={card.analysis.source} />
            {card.analysis.cached && <span className="badge cached">CACHED</span>}
          </h3>
          <p>{card.analysis.text}</p>
          <h3>
            Objects <SourceBadge source={card.detections.source} />
            {card.detections.cached && <span className="badge cached">CACHED</span>}
          </h3>
          {card.detections.detections.length ? (
            <p>
              {card.detections.detections.map((detection, index) => (
                <span key={`${detection.time_s}-${detection.label}-${index}`}>
                  {index > 0 && ", "}
                  <button
                    type="button"
                    className="stamp"
                    onClick={() => onSeek(detection.time_s)}
                  >
                    {detection.label} {detection.confidence.toFixed(2)} @{" "}
                    {detection.time_s.toFixed(1)}s
                  </button>
                </span>
              ))}
            </p>
          ) : (
            <p className="muted">none</p>
          )}
        </article>
      ))}
    </section>
  );
}

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [question, setQuestion] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const player = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    api.config()
      .then(setConfig)
      .catch((e: Error) => setError(e.message));
  }, []);

  const jobId = job?.id;
  const running = job?.status === "queued" || job?.status === "running";
  useEffect(() => {
    if (!jobId || !running) return;
    const timer = setInterval(() => {
      api.job(jobId).then(setJob).catch((e: Error) => setError(e.message));
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [jobId, running]);

  const ask = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!config || !question.trim()) return;
    setError(null);
    api
      .createJob(config.video_id, question.trim())
      .then(setJob)
      .catch((e: Error) => setError(e.message));
  };

  const seek = (s: number) => {
    const el = player.current;
    if (!el) return;
    el.currentTime = s;
    void el.play().catch(() => undefined);
  };

  const testServices = config?.services.filter((service) => service.mode === "test") ?? [];

  return (
    <main>
      <h1>Video analysis</h1>
      {testServices.length > 0 && (
        <div className="banner">
          <strong>Test responses in use</strong> for{" "}
          {testServices.map((service) => service.interface).join(", ")}. These are canned and do
          not describe the video.
        </div>
      )}
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      {config && (
        <section className="panel">
          <video ref={player} src={config.video_url} controls preload="metadata" />
        </section>
      )}
      <form className="panel question" onSubmit={ask}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about the video"
          maxLength={2000}
        />
        <button type="submit" disabled={!config || running || !question.trim()}>
          Ask
        </button>
      </form>
      {job && (
        <section className="panel">
          <h2>
            Job <span className={`status ${job.status}`}>{job.status}</span>
          </h2>
          {running && <p className="muted">{job.stage}…</p>}
          {job.error && (
            <div className="error" role="alert">
              <strong>{job.error.service ?? "Job"} failed</strong> ({job.error.kind}):{" "}
              {job.error.message}
            </div>
          )}
          {job.result && (
            <div>
              <h3>
                Answer <SourceBadge source={job.result.answer.source} />
              </h3>
              <p>
                <Timestamped text={job.result.answer.text} onSeek={seek} />
              </p>
            </div>
          )}
        </section>
      )}
      {job?.result && <EvidenceCards cards={job.result.evidence} onSeek={seek} />}
    </main>
  );
}
