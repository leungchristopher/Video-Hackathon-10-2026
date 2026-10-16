import { forwardRef, useState } from "react";
import type { Video } from "../api";
import { seconds } from "../format";

export const VideoPlayer = forwardRef<HTMLVideoElement, { video: Video }>(({ video }, ref) => {
  const [time, setTime] = useState(0);
  return (
    <section className="panel">
      <h2>{video.title}</h2>
      <video
        ref={ref}
        src={video.media_url}
        controls
        preload="metadata"
        onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)}
      />
      <p className="muted">Position: {seconds(time)} (source-video time)</p>
    </section>
  );
});
