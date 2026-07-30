/**
 * LeadChat — left panel of the split-screen demo UI.
 *
 * Shows message list with streaming token bubbles + text input + Send button.
 * Calls onSend(text) when user submits (Enter key or Send button click).
 *
 * Security: all message content rendered via JSX {content} — no dangerouslySetInnerHTML (T-06-02).
 */

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import type { Message } from "./types";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";

interface LeadChatProps {
  messages: Message[];
  onSend: (text: string) => void;
  agentName: string;
  industrySrc: string;
}

export function LeadChat({ messages, onSend, agentName, industrySrc }: LeadChatProps) {
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  function handleSubmit() {
    const text = inputText.trim();
    if (!text) return;
    onSend(text);
    setInputText("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <section
      className="panel"
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        position: "relative",
        borderRight: "1px solid var(--border)",
        backgroundImage: `url(${industrySrc})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {/* Low-opacity background overlay (~10%) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "var(--bg)",
          opacity: 0.9,
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* Header strip */}
      <div
        style={{
          height: 48,
          minHeight: 48,
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 var(--space-lg)",
          position: "relative",
          zIndex: 1,
        }}
      >
        <span
          style={{
            fontSize: "18px",
            fontWeight: 600,
            color: "var(--text)",
          }}
        >
          Lead Chat
        </span>
        <span
          style={{
            fontSize: "12px",
            fontWeight: 600,
            color: "var(--text-muted)",
          }}
        >
          {agentName}
        </span>
      </div>

      {/* Message list */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "var(--space-md)",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          position: "relative",
          zIndex: 1,
        }}
      >
        {messages.length === 0 ? (
          /* Empty state */
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              flex: 1,
              gap: "var(--space-sm)",
              textAlign: "center",
              padding: "var(--space-xl)",
            }}
          >
            <p
              style={{
                fontSize: "18px",
                fontWeight: 600,
                color: "var(--text-muted)",
                margin: 0,
              }}
            >
              Wala pang mensahe
            </p>
            <p
              style={{
                fontSize: "14px",
                color: "var(--text-muted)",
                margin: 0,
              }}
            >
              I-type ang mensahe mo sa ibaba para simulan ang usapan.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`message-bubble ${msg.role === "user" ? "user" : "agent"}${
                msg.streaming ? " streaming-cursor" : ""
              }`}
            >
              {msg.content}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area (72px) */}
      <div
        style={{
          height: 72,
          minHeight: 72,
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          padding: "0 var(--space-md)",
          gap: "var(--space-sm)",
          position: "relative",
          zIndex: 1,
        }}
      >
        <Input
          type="text"
          className="chat-input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Isulat ang mensahe..."
          style={{ flex: 1, height: 44 }}
        />
        <Button
          className="send-btn"
          onClick={handleSubmit}
          disabled={!inputText.trim()}
          aria-label="Ipadala ang mensahe"
          style={{
            width: 44,
            height: 44,
            minHeight: 44,
            padding: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Send size={18} />
        </Button>
      </div>
    </section>
  );
}
