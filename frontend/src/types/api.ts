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
  id: string;
  name: string;
  currency: string;
}

export interface Customer {
  id: string;
  company_name: string;
  contact_name: string | null;
  email: string;
  status: CustomerStatus;
  plan_id: string | null;
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
  plan_id?: string | null;
  notes?: string | null;
}

export type CustomerUpdate = Partial<CustomerCreate>;

export interface CustomerSummary {
  id: string;
  company_name: string;
  email: string;
  status: string;
}

export interface TicketMessage {
  id: string;
  ticket_id: string;
  author_type: MessageAuthorType;
  author_id: string | null;
  body: string;
  visibility: MessageVisibility;
  ai_generated: boolean;
  approved_by: string | null;
  created_at: string;
}

export interface Ticket {
  id: string;
  customer_id: string;
  subject: string;
  description: string;
  source: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: TicketCategory;
  assigned_to: string | null;
  ai_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketDetail extends Ticket {
  customer: CustomerSummary | null;
  messages: TicketMessage[];
}

export interface TicketCreate {
  customer_id: string;
  subject: string;
  description: string;
  source?: string;
  category?: TicketCategory;
  priority?: TicketPriority;
  status?: TicketStatus;
  assigned_to?: string | null;
}

export interface TicketUpdate {
  subject?: string;
  description?: string;
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
  assigned_to?: string | null;
}

export interface TicketMessageCreate {
  body: string;
  author_type?: MessageAuthorType;
  visibility?: MessageVisibility;
  ai_generated?: boolean;
}

export type ArticleVisibility = 'internal' | 'public';

export interface KnowledgeChunk {
  id: string;
  article_id: string;
  chunk_index: number;
  content: string;
  token_count: number;
}

export interface KnowledgeArticle {
  id: string;
  title: string;
  content: string;
  tags: string[];
  visibility: ArticleVisibility;
  active: boolean;
  created_by: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface ArticleCreate {
  title: string;
  content: string;
  tags?: string[];
  visibility?: ArticleVisibility;
  active?: boolean;
}

export interface ArticleUpdate {
  title?: string;
  content?: string;
  tags?: string[];
  visibility?: ArticleVisibility;
  active?: boolean;
}

export interface KnowledgeSearchResult {
  article_id: string;
  title: string;
  visibility: ArticleVisibility;
  chunk_id: string | null;
  snippet: string;
}

export interface TicketClassification {
  category: TicketCategory;
  urgency: TicketPriority;
  sentiment: 'positive' | 'neutral' | 'negative';
  billing_lookup_required: boolean;
  suggested_team: string;
  reasoning_summary: string;
}

export interface AiSummaryResult {
  summary: string;
}

export interface AiSuggestedReplyResult {
  reply: string;
  citations: Citation[];
  risk_flags: string[];
}

export interface AiAuditLog {
  id: string;
  user_id: string | null;
  ticket_id: string | null;
  customer_id: string | null;
  action_type: string;
  input_summary: string;
  output: unknown;
  tools_called: string[];
  risk_flags: string[];
  approved: boolean;
  created_at: string;
}

export interface Citation {
  article_id: string;
  chunk_id: string | null;
  title: string;
  snippet: string;
}

export interface ProposedAction {
  type: string;
  customer_id: string | null;
  reason: string;
  requires_approval: boolean;
}

export interface CopilotRequest {
  message: string;
  customer_id?: string | null;
  ticket_id?: string | null;
}

export interface CopilotResponse {
  answer: string;
  tools_called: string[];
  citations: Citation[];
  proposed_actions: ProposedAction[];
  risk_flags: string[];
}

export interface ConversationRead {
  id: string;
  user_id: string | null;
  customer_id: string | null;
  ticket_id: string | null;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessageRead {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tools_called: string[];
  citations: Citation[];
  proposed_actions: ProposedAction[];
  risk_flags: string[];
  created_at: string;
}

export interface ConversationDetail extends ConversationRead {
  messages: ConversationMessageRead[];
}

// Server -> client events over the copilot WebSocket.
export interface CopilotReadyEvent {
  type: 'ready';
  conversation_id: string;
  customer_id: string | null;
  history: ConversationMessageRead[];
}

export interface CopilotToolActivityEvent {
  type: 'tool_activity';
  tool: string;
}

export interface CopilotAnswerEvent extends CopilotResponse {
  type: 'answer';
  message_id: string;
  created_at: string;
}

export interface CopilotErrorEvent {
  type: 'error';
  message: string;
}

export type CopilotWsEvent =
  | CopilotReadyEvent
  | CopilotToolActivityEvent
  | CopilotAnswerEvent
  | CopilotErrorEvent;

export type InvoiceStatus = 'draft' | 'open' | 'paid' | 'void' | 'uncollectible';

export type PaymentStatus = 'pending' | 'succeeded' | 'failed' | 'refunded';

export interface Invoice {
  id: string;
  customer_id: string;
  stripe_invoice_id: string | null;
  amount_due: string;
  amount_paid: string;
  currency: string;
  status: InvoiceStatus;
  description: string | null;
  due_date: string | null;
  created_at: string;
}

export interface Payment {
  id: string;
  customer_id: string;
  invoice_id: string | null;
  stripe_payment_intent_id: string | null;
  amount: string;
  currency: string;
  status: PaymentStatus;
  failure_reason: string | null;
  created_at: string;
}

export interface CustomerBillingSummary {
  customer_id: string;
  plan_name: string | null;
  outstanding_balance: string;
  latest_invoice: Invoice | null;
  latest_payment: Payment | null;
  invoices: Invoice[];
  payments: Payment[];
}

export interface CheckoutSessionResponse {
  id: string;
  url: string;
}

export interface WebhookEvent {
  id: string;
  provider: string;
  event_id: string;
  event_type: string;
  processed: boolean;
  created_at: string;
}

export interface DashboardSummary {
  open_tickets: number;
  high_priority_tickets: number;
  billing_tickets: number;
  unresolved_tickets: number;
  total_customers: number;
}

export type UserRole = 'admin' | 'support_agent' | 'billing_agent' | 'viewer';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
  role?: UserRole;
  active?: boolean;
}

export interface UserUpdate {
  name?: string;
  role?: UserRole;
  active?: boolean;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
