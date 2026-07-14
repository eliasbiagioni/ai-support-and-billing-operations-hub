import { useMutation, useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/apiClient';
import type {
  AiAuditLog,
  AiSuggestedReplyResult,
  AiSummaryResult,
  Page,
  TicketClassification,
} from '@/types/api';

export function useClassifyTicket(ticketId: string) {
  return useMutation({
    mutationFn: () =>
      apiRequest<TicketClassification>(`/api/ai/tickets/${ticketId}/classify`, {
        method: 'POST',
      }),
  });
}

export function useSummarizeTicket(ticketId: string) {
  return useMutation({
    mutationFn: () =>
      apiRequest<AiSummaryResult>(`/api/ai/tickets/${ticketId}/summarize`, {
        method: 'POST',
      }),
  });
}

export function useSuggestReply(ticketId: string) {
  return useMutation({
    mutationFn: () =>
      apiRequest<AiSuggestedReplyResult>(`/api/ai/tickets/${ticketId}/suggest-reply`, {
        method: 'POST',
      }),
  });
}

export function useAiAuditLogs(actionType?: string) {
  return useQuery({
    queryKey: ['ai', 'audit-logs', actionType ?? 'all'],
    queryFn: ({ signal }) =>
      apiRequest<Page<AiAuditLog>>('/api/ai/audit-logs', {
        query: { limit: 100, action_type: actionType },
        signal,
      }),
  });
}
