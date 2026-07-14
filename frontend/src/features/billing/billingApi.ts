import { useMutation, useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/apiClient';
import type {
  CheckoutSessionResponse,
  CustomerBillingSummary,
  Invoice,
  Page,
  Payment,
  WebhookEvent,
} from '@/types/api';

export function useInvoices(customerId?: string) {
  return useQuery({
    queryKey: ['invoices', customerId ?? 'all'],
    queryFn: ({ signal }) =>
      apiRequest<Page<Invoice>>('/api/invoices', {
        query: { limit: 100, customer_id: customerId },
        signal,
      }),
  });
}

export function usePayments(customerId?: string) {
  return useQuery({
    queryKey: ['payments', customerId ?? 'all'],
    queryFn: ({ signal }) =>
      apiRequest<Page<Payment>>('/api/payments', {
        query: { limit: 100, customer_id: customerId },
        signal,
      }),
  });
}

export function useWebhookEvents() {
  return useQuery({
    queryKey: ['webhook-events'],
    queryFn: ({ signal }) =>
      apiRequest<Page<WebhookEvent>>('/api/webhooks/events', {
        query: { limit: 50 },
        signal,
      }),
  });
}

export function useCustomerBilling(customerId: string) {
  return useQuery({
    queryKey: ['customer-billing', customerId],
    queryFn: ({ signal }) =>
      apiRequest<CustomerBillingSummary>(`/api/customers/${customerId}/billing`, {
        signal,
      }),
    enabled: customerId !== '',
  });
}

export function useCreateCheckoutSession(customerId: string) {
  return useMutation({
    mutationFn: (priceId?: string) =>
      apiRequest<CheckoutSessionResponse>(
        `/api/customers/${customerId}/checkout-session`,
        { method: 'POST', body: { price_id: priceId ?? null } },
      ),
  });
}
