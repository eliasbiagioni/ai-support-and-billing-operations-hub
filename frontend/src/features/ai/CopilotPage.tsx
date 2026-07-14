import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import {
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  PageHeader,
  Select,
  Spinner,
  Textarea,
} from '@/components/ui';
import { useConversations } from '@/features/ai/aiApi';
import {
  useCopilotSocket,
  type CopilotChatMessage,
  type ConnectionStatus,
} from '@/features/ai/copilotSocket';
import { useCustomers } from '@/features/customers/customerApi';
import { apiRequest } from '@/lib/apiClient';
import { toErrorMessage } from '@/lib/errors';
import { humanize } from '@/lib/format';
import type { BadgeTone } from '@/components/ui';
import type { CheckoutSessionResponse, Citation, ProposedAction } from '@/types/api';

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  connecting: 'Connecting…',
  online: 'Live',
  offline: 'Reconnecting…',
};

const STATUS_TONE: Record<ConnectionStatus, BadgeTone> = {
  connecting: 'amber',
  online: 'green',
  offline: 'red',
};

function ConnectionBadge({ status }: { status: ConnectionStatus }) {
  return <Badge tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Badge>;
}

function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
        Sources
      </p>
      <ul className="space-y-1">
        {citations.map((citation, index) => (
          <li key={`${citation.article_id}-${index}`} className="text-xs text-slate-500">
            <span className="font-medium text-slate-600">{citation.title}</span>
            {citation.snippet ? ` — ${citation.snippet}` : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ProposedActionCard({ action }: { action: ProposedAction }) {
  const [status, setStatus] = useState<'idle' | 'working' | 'done' | 'error'>('idle');
  const [message, setMessage] = useState('');

  async function approveCheckout() {
    if (!action.customer_id) {
      setStatus('error');
      setMessage('This proposal has no customer attached.');
      return;
    }
    setStatus('working');
    try {
      const session = await apiRequest<CheckoutSessionResponse>(
        `/api/customers/${action.customer_id}/checkout-session`,
        { method: 'POST', body: { price_id: null } },
      );
      setStatus('done');
      setMessage('Checkout session created.');
      window.open(session.url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      setStatus('error');
      setMessage(toErrorMessage(error));
    }
  }

  return (
    <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
      <div className="flex items-center gap-2">
        <Badge tone="amber">Needs approval</Badge>
        <span className="text-sm font-medium text-amber-900">
          {humanize(action.type)}
        </span>
      </div>
      {action.reason ? (
        <p className="mt-1 text-sm text-amber-800">{action.reason}</p>
      ) : null}
      <div className="mt-2 flex items-center gap-2">
        {action.type === 'checkout_session' ? (
          <Button
            variant="primary"
            onClick={approveCheckout}
            disabled={status === 'working' || status === 'done'}
          >
            {status === 'working' ? 'Creating…' : 'Approve & open checkout'}
          </Button>
        ) : (
          <span className="text-xs text-amber-700">
            Handle this manually — the copilot cannot execute it.
          </span>
        )}
        {message ? (
          <span
            className={`text-xs ${status === 'error' ? 'text-rose-600' : 'text-emerald-700'}`}
          >
            {message}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function AssistantBubble({
  message,
}: {
  message: Extract<CopilotChatMessage, { role: 'assistant' }>;
}) {
  return (
    <Card className="p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge tone="indigo">AI generated</Badge>
        {message.tools_called.map((tool, index) => (
          <Badge key={`${tool}-${index}`} tone="blue">
            {humanize(tool)}
          </Badge>
        ))}
      </div>
      <p className="whitespace-pre-wrap text-sm text-slate-700">{message.answer}</p>
      <CitationList citations={message.citations} />
      {message.proposed_actions.map((action, index) => (
        <ProposedActionCard key={`${action.type}-${index}`} action={action} />
      ))}
    </Card>
  );
}

export function CopilotPage() {
  const [customerId, setCustomerId] = useState('');
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(
    null,
  );
  const [resetKey, setResetKey] = useState(0);
  const [message, setMessage] = useState('');

  const { data: customers } = useCustomers();
  const { data: conversations } = useConversations();
  const queryClient = useQueryClient();

  const { status, conversationId, messages, pending, activeTools, error, send } =
    useCopilotSocket({
      customerId: customerId || null,
      conversationId: selectedConversationId,
      resetKey,
      onReady: () => {
        void queryClient.invalidateQueries({ queryKey: ['ai', 'conversations'] });
      },
      onAnswer: () => {
        void queryClient.invalidateQueries({ queryKey: ['ai', 'conversations'] });
        void queryClient.invalidateQueries({ queryKey: ['ai', 'audit-logs'] });
      },
    });

  function submit() {
    const question = message.trim();
    if (!question || pending || status !== 'online') return;
    send(question);
    setMessage('');
  }

  function startNewConversation() {
    setSelectedConversationId(null);
    setResetKey((key) => key + 1);
  }

  function changeCustomer(value: string) {
    setCustomerId(value);
    setSelectedConversationId(null);
    setResetKey((key) => key + 1);
  }

  function resume(id: string) {
    if (id === conversationId) return;
    setSelectedConversationId(id);
    setResetKey((key) => key + 1);
  }

  const canSend = status === 'online' && !pending && Boolean(message.trim());

  return (
    <div>
      <PageHeader
        title="Billing Copilot"
        subtitle="Ask about customers, invoices, payments, and policy. The copilot keeps the full conversation in context and queues risky actions for your approval."
      />

      <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
        <div className="space-y-3">
          <Button variant="primary" className="w-full" onClick={startNewConversation}>
            New conversation
          </Button>
          <Card className="p-2">
            <p className="px-2 py-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Recent conversations
            </p>
            {conversations && conversations.items.length > 0 ? (
              <ul className="space-y-1">
                {conversations.items.map((conversation) => {
                  const active = conversation.id === conversationId;
                  return (
                    <li key={conversation.id}>
                      <button
                        type="button"
                        onClick={() => resume(conversation.id)}
                        className={`w-full truncate rounded-md px-2 py-1.5 text-left text-sm ${
                          active
                            ? 'bg-brand-50 font-medium text-brand-700'
                            : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {conversation.title || 'Untitled conversation'}
                      </button>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="px-2 py-2 text-xs text-slate-400">No conversations yet.</p>
            )}
          </Card>
        </div>

        <div>
          <Card className="mb-4 p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-600">Conversation</span>
              <ConnectionBadge status={status} />
            </div>
            <Field label="Customer context (optional)">
              <Select
                className="w-full"
                value={customerId}
                onChange={(event) => changeCustomer(event.target.value)}
              >
                <option value="">No specific customer</option>
                {customers?.items.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.company_name}
                  </option>
                ))}
              </Select>
            </Field>
          </Card>

          {messages.length === 0 && !pending ? (
            <EmptyState
              title="Start a conversation"
              description="The copilot answers from your billing data and knowledge base, keeps prior turns in context, and never charges without your approval."
            />
          ) : (
            <div className="space-y-4">
              {messages.map((entry) =>
                entry.role === 'user' ? (
                  <div key={entry.id} className="flex justify-end">
                    <div className="max-w-xl rounded-lg bg-brand-600 px-4 py-2 text-sm text-white">
                      {entry.content}
                    </div>
                  </div>
                ) : (
                  <AssistantBubble key={entry.id} message={entry} />
                ),
              )}
              {pending ? (
                <Spinner
                  label={
                    activeTools.length > 0
                      ? `Using ${activeTools.map(humanize).join(', ')}…`
                      : 'Thinking…'
                  }
                />
              ) : null}
            </div>
          )}

          {error ? (
            <Card className="mt-4 border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
              {error}
            </Card>
          ) : null}

          <Card className="mt-4 p-4">
            <Field label="Your question">
              <Textarea
                rows={3}
                value={message}
                placeholder="e.g. Does this customer have any failed payments? What is our refund policy?"
                onChange={(event) => setMessage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
                    event.preventDefault();
                    submit();
                  }
                }}
              />
            </Field>
            <div className="mt-3 flex items-center justify-end gap-2">
              <span className="text-xs text-slate-400">Cmd/Ctrl + Enter to send</span>
              <Button onClick={submit} disabled={!canSend}>
                {pending ? 'Thinking…' : 'Ask copilot'}
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
