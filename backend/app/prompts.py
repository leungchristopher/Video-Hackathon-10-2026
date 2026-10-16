from .models import EvidenceCard

# Bump a version whenever its prompt text changes: it is part of the cache key.
CLIP_PROMPT_VERSION = "clip-analysis-v1"
CLIP_PROMPT = (
    "Describe what happens in this video clip: people, objects, actions and any visible text. "
    "Be factual and concise."
)

# Bump this version when the detection configuration changes: it is part of the cache key.
DETECTION_CONFIG_VERSION = "detect-v1"

ANSWER_PROMPT_VERSION = "answer-v1"
ANSWER_SYSTEM = (
    "You answer questions about a video using only the evidence provided. "
    "Cite evidence with its source-video timestamp in seconds, e.g. [12.0s]. "
    "If the evidence is insufficient, say so."
)


def answer_prompt(question: str, evidence: list[EvidenceCard]) -> str:
    lines = [
        f"[{card.start_s:.1f}s-{card.end_s:.1f}s] {card.analysis.text} Objects: "
        + (
            ", ".join(
                f"{d.label} ({d.confidence:.2f} @ {d.time_s:.1f}s)"
                for d in card.detections.detections
            )
            or "none"
        )
        for card in evidence
    ]
    return f"Question: {question}\n\nEvidence:\n" + "\n".join(lines)
