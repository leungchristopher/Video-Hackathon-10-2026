/** Renders text with `[12.5s]` citations as buttons that seek the player. */
export function Timestamped({ text, onSeek }: { text: string; onSeek: (s: number) => void }) {
  const parts = text.split(/(\[\d+(?:\.\d+)?s\])/g);
  return (
    <>
      {parts.map((part, i) => {
        const match = /^\[(\d+(?:\.\d+)?)s\]$/.exec(part);
        if (!match) return <span key={i}>{part}</span>;
        const s = Number(match[1]);
        return (
          <button key={i} type="button" className="stamp" onClick={() => onSeek(s)}>
            {part}
          </button>
        );
      })}
    </>
  );
}
