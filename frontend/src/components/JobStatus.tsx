import type { Job } from "../api";
import { SourceBadge } from "./SourceBadge";
import { Timestamped } from "./Timestamped";

export function JobStatus({ job, onSeek }: { job: Job; onSeek: (s: number) => void }) {
  return (
    <section className="panel">
      <h2>
        Job <code>{job.id.slice(0, 8)}</code> <span className={`status ${job.status}`}>{job.status}</span>
      </h2>
      {job.status !== "succeeded" && job.status !== "failed" && <p className="muted">{job.stage}…</p>}
      {job.error && (
        <div className="error" role="alert">
          <strong>{job.error.service ?? "Job"} failed</strong> ({job.error.kind}): {job.error.message}
        </div>
      )}
      {job.result && (
        <div className="answer">
          <SourceBadge source={job.result.answer.source} />{" "}
          <span className="muted">{job.result.answer.model}</span>
          <p>
            <Timestamped text={job.result.answer.text} onSeek={onSeek} />
          </p>
        </div>
      )}
    </section>
  );
}
