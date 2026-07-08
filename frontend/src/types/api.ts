// Hand-written TypeScript contracts mirroring the FastAPI/Pydantic response
// models (PRD 11.3). Kept in one place so integration drift surfaces at compile
// time.

export type CustomerStatus =
  | 'active'
  | 'suspended'
  | 'overdue'
  | 'trial'
  | 'enterprise';

export type TicketStatus =
  | 'new'
  | 'open'
  | 'pending_customer'
  | 'pending_billing'
  | 'resolved'
  | 'closed';

export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';

export type TicketCategory =
  | 'billing'
  | 'technical'
  | 'account'
  | 'product'
  | 'other';

export type MessageAuthorType = 'agent' | 'customer' | 'ai' | 'system';

export type MessageVisibility = 'internal' | 'public';

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface PlanRead {
  id: number;
  name: string;
  currency: string;
}

export interface Customer {
  id: number;
  company_name: string;
  contact_name: string | null;
  email: string;
  status: CustomerStatus;
  plan_id: number | null;
  plan: PlanRead | null;
  stripe_customer_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  company_name: string;
  contact_name?: string | null;
  email: string;
  status?: CustomerStatus;
  plan_id?: number | null;
  notes?: string | null;
}

export type CustomerUpdate = Partial<CustomerCreate>;

export interface CustomerSummary {
  id: number;
  company_name: string;
  email: string;
  status: string;
}

export interface TicketMessage {
  id: number;
  ticket_id: number;
  author_type: MessageAuthorType;
  author_id: number | null;
  body: string;
  visibility: MessageVisibility;
  ai_generated: boolean;
  approved_by: number | null;
  created_at: string;
}

export interface Ticket {
  id: number;
  customer_id: number;
  subject: string;
  description: string;
  source: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: TicketCategory;
  assigned_to: number | null;
  ai_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketDetail extends Ticket {
  customer: CustomerSummary | null;
  messages: TicketMessage[];
}

export interface TicketCreate {
  customer_id: number;
  subject: string;
  description: string;
  source?: string;
  category?: TicketCategory;
  priority?: TicketPriority;
  status?: TicketStatus;
  assigned_to?: number | null;
}

export interface TicketUpdate {
  subject?: string;
  description?: string;
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
  assigned_to?: number | null;
}

export interface TicketMessageCreate {
  body: string;
  author_type?: MessageAuthorType;
  visibility?: MessageVisibility;
  ai_generated?: boolean;
}

export interface DashboardSummary {
  open_tickets: number;
  high_priority_tickets: number;
  billing_tickets: number;
  unresolved_tickets: number;
  total_customers: number;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
