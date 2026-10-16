import type { Source } from "../api";

export function SourceBadge({ source }: { source: Source }) {
  return source === "test" ? (
    <span className="badge test" title="Canned test response; no external service was called">
      TEST RESPONSE
    </span>
  ) : (
    <span className="badge live">LIVE</span>
  );
}
