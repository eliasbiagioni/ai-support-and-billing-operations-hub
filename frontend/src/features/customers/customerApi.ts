import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/apiClient';
import type {
  Customer,
  CustomerCreate,
  CustomerUpdate,
  Page,
} from '@/types/api';

const customerKeys = {
  all: ['customers'] as const,
  list: (limit: number, offset: number) => ['customers', 'list', limit, offset] as const,
  detail: (id: number) => ['customers', 'detail', id] as const,
};

export function useCustomers(limit = 50, offset = 0) {
  return useQuery({
    queryKey: customerKeys.list(limit, offset),
    queryFn: ({ signal }) =>
      apiRequest<Page<Customer>>('/api/customers', { query: { limit, offset }, signal }),
  });
}

export function useCustomer(customerId: number) {
  return useQuery({
    queryKey: customerKeys.detail(customerId),
    queryFn: ({ signal }) =>
      apiRequest<Customer>(`/api/customers/${customerId}`, { signal }),
    enabled: Number.isFinite(customerId),
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CustomerCreate) =>
      apiRequest<Customer>('/api/customers', { method: 'POST', body: payload }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: customerKeys.all });
    },
  });
}

export function useUpdateCustomer(customerId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CustomerUpdate) =>
      apiRequest<Customer>(`/api/customers/${customerId}`, {
        method: 'PATCH',
        body: payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: customerKeys.all });
    },
  });
}
