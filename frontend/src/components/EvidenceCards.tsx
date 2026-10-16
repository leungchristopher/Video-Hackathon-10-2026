import type { EvidenceCard } from "../api";
import { seconds } from "../format";
import { SourceBadge } from "./SourceBadge";

export function EvidenceCards({ cards, onSeek }: { cards: EvidenceCard[]; onSeek: (s: number) => void }) {
  if (!cards.length) return null;
  return (
    <section className="cards">
      {cards.map((card) => (
        <article key={`${card.start_s}-${card.end_s}`} className="panel card">
          <button type="button" className="stamp" onClick={() => onSeek(card.start_s)}>
            {seconds(card.start_s)} – {seconds(card.end_s)}
          </button>
          <span className="muted"> score {card.score.toFixed(2)}</span>
          <h3>
            Search <SourceBadge source={card.search_source} />
          </h3>
          <p>{card.search_text}</p>
          <h3>
            Analysis <SourceBadge source={card.analysis.source} />
            {card.analysis.cached && <span className="badge cached">CACHED</span>}
          </h3>
          <p>{card.analysis.text}</p>
          <p className="muted">
            {card.analysis.model} · {card.analysis.prompt_version} · clip {card.clip_source}
          </p>
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
          <p className="muted">
            {card.detections.model} · {card.detections.prompt_version}
          </p>
        </article>
      ))}
    </section>
  );
}
