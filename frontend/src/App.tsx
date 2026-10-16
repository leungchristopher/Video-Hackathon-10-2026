import { useEffect, useRef, useState } from "react";
import { api, type Job, type ServiceInfo, type Video } from "./api";
import { EvidenceCards } from "./components/EvidenceCards";
import { JobStatus } from "./components/JobStatus";
import { QuestionForm } from "./components/QuestionForm";
import { VideoPlayer } from "./components/VideoPlayer";

const POLL_MS = 750;

export default function App() {
  const [services, setServices] = useState<ServiceInfo[]>([]);
  const [video, setVideo] = useState<Video | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const player = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    Promise.all([api.health(), api.videos()])
      .then(([health, videos]) => {
        setServices(health.services);
        setVideo(videos[0] ?? null);
      })
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

  const ask = (question: string) => {
    if (!video) return;
    setError(null);
    api.createJob(video.id, question).then(setJob).catch((e: Error) => setError(e.message));
  };

  const seek = (s: number) => {
    const el = player.current;
    if (!el) return;
    el.currentTime = s;
    void el.play().catch(() => undefined);
  };

  const testServices = services.filter((s) => s.mode === "test");

  return (
    <main>
      <h1>Video analysis</h1>
      {testServices.length > 0 && (
        <div className="banner">
          <strong>Test responses in use</strong> for {testServices.map((s) => s.interface).join(", ")}.
          These results are canned and do not describe the video. Configure the service in{" "}
          <code>.env</code> to use it.
        </div>
      )}
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      {video && <VideoPlayer ref={player} video={video} />}
      <QuestionForm disabled={!video || running} onAsk={ask} />
      {job && <JobStatus job={job} onSeek={seek} />}
      {job?.result && <EvidenceCards cards={job.result.evidence} onSeek={seek} />}
    </main>
  );
}
