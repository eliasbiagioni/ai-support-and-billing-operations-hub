import { useCallback, useEffect, useRef, useState } from 'react';
import ReconnectingWebSocket from 'reconnecting-websocket';

import { getToken, setToken } from '@/lib/authToken';
import type {
  Citation,
  ConversationMessageRead,
  CopilotWsEvent,
  ProposedAction,
} from '@/types/api';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
);

const AUTH_CLOSE_CODE = 4401;

export type ConnectionStatus = 'connecting' | 'online' | 'offline';

export type CopilotChatMessage =
  | { id: string; role: 'user'; content: string }
  | {
      id: string;
      role: 'assistant';
      answer: string;
      tools_called: string[];
      citations: Citation[];
      proposed_actions: ProposedAction[];
      risk_flags: string[];
    };

interface UseCopilotSocketOptions {
  customerId?: string | null;
  conversationId?: string | null;
  // Bump to force a brand-new socket/conversation even when the other inputs
  // are unchanged (e.g. the "New conversation" button).
  resetKey?: number;
  onReady?: (conversationId: string) => void;
  onAnswer?: (conversationId: string | null) => void;
}

interface UseCopilotSocketResult {
  status: ConnectionStatus;
  conversationId: string | null;
  messages: CopilotChatMessage[];
  pending: boolean;
  activeTools: string[];
  error: string | null;
  send: (message: string) => void;
}

function buildWsUrl(customerId?: string | null, conversationId?: string | null): string {
  const url = new URL(`${BASE_URL}/api/ai/copilot/ws`);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  const token = getToken();
  if (token) url.searchParams.set('token', token);
  if (conversationId) url.searchParams.set('conversation_id', conversationId);
  if (customerId) url.searchParams.set('customer_id', customerId);
  return url.toString();
}

function fromHistory(message: ConversationMessageRead): CopilotChatMessage {
  if (message.role === 'assistant') {
    return {
      id: message.id,
      role: 'assistant',
      answer: message.content,
      tools_called: message.tools_called,
      citations: message.citations,
      proposed_actions: message.proposed_actions,
      risk_flags: message.risk_flags,
    };
  }
  return { id: message.id, role: 'user', content: message.content };
}

export function useCopilotSocket(
  options: UseCopilotSocketOptions = {},
): UseCopilotSocketResult {
  const {
    customerId,
    conversationId: requestedId,
    resetKey = 0,
    onReady,
    onAnswer,
  } = options;

  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [conversationId, setConversationId] = useState<string | null>(
    requestedId ?? null,
  );
  const [messages, setMessages] = useState<CopilotChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [activeTools, setActiveTools] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<ReconnectingWebSocket | null>(null);
  const conversationIdRef = useRef<string | null>(requestedId ?? null);

  // Keep callbacks fresh without re-opening the socket on every render.
  const onReadyRef = useRef(onReady);
  const onAnswerRef = useRef(onAnswer);
  useEffect(() => {
    onReadyRef.current = onReady;
    onAnswerRef.current = onAnswer;
  });

  useEffect(() => {
    setMessages([]);
    setActiveTools([]);
    setPending(false);
    setError(null);
    setStatus('connecting');
    conversationIdRef.current = requestedId ?? null;
    setConversationId(requestedId ?? null);

    const rws = new ReconnectingWebSocket(
      () => buildWsUrl(customerId, conversationIdRef.current),
      [],
      { maxReconnectionDelay: 10000, minReconnectionDelay: 1000 },
    );
    socketRef.current = rws;

    rws.addEventListener('open', () => setStatus('online'));

    rws.addEventListener('message', (event) => {
      let data: CopilotWsEvent;
      try {
        data = JSON.parse(event.data as string) as CopilotWsEvent;
      } catch {
        return;
      }
      switch (data.type) {
        case 'ready': {
          conversationIdRef.current = data.conversation_id;
          setConversationId(data.conversation_id);
          setMessages(data.history.map(fromHistory));
          setActiveTools([]);
          setPending(false);
          onReadyRef.current?.(data.conversation_id);
          break;
        }
        case 'tool_activity': {
          setActiveTools((prev) =>
            prev.includes(data.tool) ? prev : [...prev, data.tool],
          );
          break;
        }
        case 'answer': {
          setMessages((prev) => [
            ...prev,
            {
              id: data.message_id,
              role: 'assistant',
              answer: data.answer,
              tools_called: data.tools_called,
              citations: data.citations,
              proposed_actions: data.proposed_actions,
              risk_flags: data.risk_flags,
            },
          ]);
          setPending(false);
          setActiveTools([]);
          onAnswerRef.current?.(conversationIdRef.current);
          break;
        }
        case 'error': {
          setError(data.message);
          setPending(false);
          setActiveTools([]);
          break;
        }
      }
    });

    rws.addEventListener('close', (event) => {
      if (event.code === AUTH_CLOSE_CODE) {
        rws.close();
        setToken(null);
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.assign('/login');
        }
        return;
      }
      setStatus('offline');
    });

    rws.addEventListener('error', () => setStatus('offline'));

    return () => {
      socketRef.current = null;
      rws.close();
    };
  }, [customerId, requestedId, resetKey]);

  const send = useCallback((message: string) => {
    const socket = socketRef.current;
    const trimmed = message.trim();
    if (!socket || !trimmed) return;
    setError(null);
    setPending(true);
    setActiveTools([]);
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', content: trimmed },
    ]);
    socket.send(JSON.stringify({ message: trimmed }));
  }, []);

  return { status, conversationId, messages, pending, activeTools, error, send };
}
