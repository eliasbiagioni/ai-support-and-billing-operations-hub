import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/apiClient';
import type {
  Page,
  Ticket,
  TicketCreate,
  TicketDetail,
  TicketMessage,
  TicketMessageCreate,
  TicketUpdate,
} from '@/types/api';

export interface TicketListFilters {
  status?: string;
  category?: string;
  priority?: string;
  customer_id?: number;
  q?: string;
  limit?: number;
  offset?: number;
}

const ticketKeys = {
  all: ['tickets'] as const,
  list: (filters: TicketListFilters) => ['tickets', 'list', filters] as const,
  detail: (id: number) => ['tickets', 'detail', id] as const,
};

export function useTickets(filters: TicketListFilters) {
  return useQuery({
    queryKey: ticketKeys.list(filters),
    queryFn: ({ signal }) =>
      apiRequest<Page<Ticket>>('/api/tickets', {
        query: { limit: 100, ...filters },
        signal,
      }),
  });
}

export function useTicket(ticketId: number) {
  return useQuery({
    queryKey: ticketKeys.detail(ticketId),
    queryFn: ({ signal }) =>
      apiRequest<TicketDetail>(`/api/tickets/${ticketId}`, { signal }),
    enabled: Number.isFinite(ticketId),
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketCreate) =>
      apiRequest<TicketDetail>('/api/tickets', { method: 'POST', body: payload }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ticketKeys.all });
    },
  });
}

export function useUpdateTicket(ticketId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketUpdate) =>
      apiRequest<TicketDetail>(`/api/tickets/${ticketId}`, {
        method: 'PATCH',
        body: payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ticketKeys.all });
    },
  });
}

export function useResolveTicket(ticketId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<TicketDetail>(`/api/tickets/${ticketId}/resolve`, { method: 'POST' }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ticketKeys.all });
    },
  });
}

export function useAddTicketMessage(ticketId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketMessageCreate) =>
      apiRequest<TicketMessage>(`/api/tickets/${ticketId}/messages`, {
        method: 'POST',
        body: payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ticketKeys.detail(ticketId) });
    },
  });
}
