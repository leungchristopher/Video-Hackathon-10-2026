import { useState } from "react";

export function QuestionForm({ disabled, onAsk }: { disabled: boolean; onAsk: (q: string) => void }) {
  const [question, setQuestion] = useState("");
  return (
    <form
      className="panel question"
      onSubmit={(e) => {
        e.preventDefault();
        if (question.trim()) onAsk(question.trim());
      }}
    >
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question about the video"
        maxLength={2000}
      />
      <button type="submit" disabled={disabled || !question.trim()}>
        Ask
      </button>
    </form>
  );
}
