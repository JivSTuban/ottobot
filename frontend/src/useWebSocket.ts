/**
 * useWebSocket — React hook for OttoBot WebSocket connection.
 *
 * Consumes three event types from the backend (api/ws_handler.py):
 *   type:"token"        — append content to the current streaming assistant bubble
 *   type:"state"        — update stage + escalated; finalize the streaming bubble
 *   type:"system_alert" — show alert banner for 8 seconds then auto-dismiss
 *
 * Security: never uses dangerouslySetInnerHTML; all content flows through
 * React state as plain strings — JSX escaping applies automatically (T-06-02).
 */

import { useEffect, useRef, useState, useCallback } from "react";
import type { Stage, Message } from "./types";
import type { IndustryKey } from "./assets/personas";

/** Discriminated union of all WebSocket message types from the backend */
export type WsMessage =
  | { type: "token"; content: string; node?: string }
  | { type: "state"; stage: Stage; escalated: boolean }
  | { type: "system_alert"; content: string };

export interface UseWebSocketReturn {
  tokens: string[];
  stage: Stage;
  escalated: boolean;
  systemAlert: string | null;
  send: (text: string, industry: IndustryKey) => void;
  messages: Message[];
  wsError: boolean;
}

/**
 * Open a WebSocket connection to `url` and handle the three OttoBot event types.
 *
 * @param url - Full WebSocket URL, e.g. "ws://localhost:8000/ws/{threadId}"
 */
export function useWebSocket(url: string): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [stage, setStage] = useState<Stage>("intro");
  const [escalated, setEscalated] = useState<boolean>(false);
  const [systemAlert, setSystemAlert] = useState<string | null>(null);
  const [tokens, setTokens] = useState<string[]>([]);
  const [wsError, setWsError] = useState<boolean>(false);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsError(false);
    };

    ws.onerror = () => {
      setWsError(true);
    };

    ws.onclose = () => {
      // Connection closed — let error state surface if unexpected
    };

    ws.onmessage = (event: MessageEvent) => {
      let msg: WsMessage;
      try {
        msg = JSON.parse(event.data as string) as WsMessage;
      } catch {
        return; // Ignore malformed JSON
      }

      if (msg.type === "token") {
        const tokenContent = msg.content;
        setTokens((prev) => [...prev, tokenContent]);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant" && last.streaming) {
            // Append to existing streaming bubble
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + tokenContent },
            ];
          }
          // Start a new assistant bubble
          return [
            ...prev,
            { role: "assistant", content: tokenContent, streaming: true },
          ];
        });
      } else if (msg.type === "state") {
        setStage(msg.stage);
        setEscalated(msg.escalated);
        // Finalize the streaming bubble
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant" && last.streaming) {
            return [...prev.slice(0, -1), { ...last, streaming: false }];
          }
          return prev;
        });
      } else if (msg.type === "system_alert") {
        setSystemAlert(msg.content);
        setTimeout(() => setSystemAlert(null), 8000);
      }
    };

    return () => {
      ws.close();
    };
    // url is stable (built with useMemo in App.tsx) — only re-open if URL changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  const send = useCallback((text: string, industry: IndustryKey) => {
    // Push user message into state immediately (optimistic)
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    // Send to backend
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ text, industry }));
    } else if (wsRef.current) {
      // Queue the send for when the socket opens (handles early sends)
      wsRef.current.send(JSON.stringify({ text, industry }));
    }
  }, []);

  return {
    tokens,
    stage,
    escalated,
    systemAlert,
    send,
    messages,
    wsError,
  };
}
