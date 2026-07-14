import type { BadgeTone } from '@/components/ui';
import type {
  CustomerStatus,
  InvoiceStatus,
  PaymentStatus,
  TicketCategory,
  TicketPriority,
  TicketStatus,
} from '@/types/api';

export function formatMoney(amount: string | number, currency = 'usd'): string {
  const value = typeof amount === 'string' ? Number(amount) : amount;
  if (Number.isNaN(value)) return String(amount);
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currency.toUpperCase()}`;
  }
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export function humanize(value: string): string {
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export const ticketStatusTone: Record<TicketStatus, BadgeTone> = {
  new: 'blue',
  open: 'indigo',
  pending_customer: 'amber',
  pending_billing: 'amber',
  resolved: 'green',
  closed: 'slate',
};

export const ticketPriorityTone: Record<TicketPriority, BadgeTone> = {
  low: 'slate',
  medium: 'blue',
  high: 'amber',
  urgent: 'red',
};

export const ticketCategoryTone: Record<TicketCategory, BadgeTone> = {
  billing: 'indigo',
  technical: 'blue',
  account: 'amber',
  product: 'green',
  other: 'slate',
};

export const invoiceStatusTone: Record<InvoiceStatus, BadgeTone> = {
  draft: 'slate',
  open: 'amber',
  paid: 'green',
  void: 'slate',
  uncollectible: 'red',
};

export const paymentStatusTone: Record<PaymentStatus, BadgeTone> = {
  pending: 'amber',
  succeeded: 'green',
  failed: 'red',
  refunded: 'slate',
};

export const customerStatusTone: Record<CustomerStatus, BadgeTone> = {
  active: 'green',
  suspended: 'red',
  overdue: 'amber',
  trial: 'blue',
  enterprise: 'indigo',
};

export const TICKET_STATUSES: TicketStatus[] = [
  'new',
  'open',
  'pending_customer',
  'pending_billing',
  'resolved',
  'closed',
];

export const TICKET_PRIORITIES: TicketPriority[] = ['low', 'medium', 'high', 'urgent'];

export const TICKET_CATEGORIES: TicketCategory[] = [
  'billing',
  'technical',
  'account',
  'product',
  'other',
];

export const CUSTOMER_STATUSES: CustomerStatus[] = [
  'active',
  'suspended',
  'overdue',
  'trial',
  'enterprise',
];
