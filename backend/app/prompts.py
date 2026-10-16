# Bump a version whenever its prompt text changes: it is part of the cache key.
CLIP_PROMPT_VERSION = "clip-analysis-v1"
CLIP_PROMPT = (
    "Describe what happens in this video clip: people, objects, actions and any visible text. "
    "Be factual and concise."
)

ANSWER_PROMPT_VERSION = "answer-v1"
ANSWER_SYSTEM = (
    "You answer questions about a video using only the evidence provided. "
    "Cite evidence with its source-video timestamp in seconds, e.g. [12.0s]. "
    "If the evidence is insufficient, say so."
)


def answer_prompt(question: str, evidence: list[tuple[float, float, str]]) -> str:
    lines = [f"[{start:.1f}s-{end:.1f}s] {text}" for start, end, text in evidence]
    return f"Question: {question}\n\nEvidence:\n" + "\n".join(lines)
