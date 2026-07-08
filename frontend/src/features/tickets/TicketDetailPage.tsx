import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  PageHeader,
  Select,
  Spinner,
  Textarea,
} from '@/components/ui';
import { ConfirmDialog } from '@/components/ui/Modal';
import {
  useAddTicketMessage,
  useResolveTicket,
  useTicket,
  useUpdateTicket,
} from '@/features/tickets/ticketApi';
import { toErrorMessage } from '@/lib/errors';
import {
  customerStatusTone,
  formatDateTime,
  humanize,
  TICKET_PRIORITIES,
  TICKET_STATUSES,
  ticketCategoryTone,
  ticketPriorityTone,
  ticketStatusTone,
} from '@/lib/format';
import type {
  MessageVisibility,
  TicketMessage,
  TicketPriority,
  TicketStatus,
} from '@/types/api';

const authorTone: Record<TicketMessage['author_type'], string> = {
  agent: 'border-brand-200 bg-brand-50',
  customer: 'border-slate-200 bg-white',
  ai: 'border-emerald-200 bg-emerald-50',
  system: 'border-slate-200 bg-slate-50',
};

export function TicketDetailPage() {
  const params = useParams();
  const ticketId = Number(params.ticketId);

  const { data: ticket, isLoading, isError, error, refetch } = useTicket(ticketId);
  const updateTicket = useUpdateTicket(ticketId);
  const resolveTicket = useResolveTicket(ticketId);
  const addMessage = useAddTicketMessage(ticketId);

  const [body, setBody] = useState('');
  const [visibility, setVisibility] = useState<MessageVisibility>('internal');
  const [confirmOpen, setConfirmOpen] = useState(false);

  if (isLoading) return <Spinner label="Loading ticket…" />;
  if (isError || !ticket) {
    return <ErrorState message={toErrorMessage(error)} onRetry={() => refetch()} />;
  }

  function submitMessage() {
    addMessage.mutate(
      { body, visibility, author_type: 'agent' },
      {
        onSuccess: () => {
          setBody('');
          setConfirmOpen(false);
        },
      },
    );
  }

  const isPublicReply = visibility === 'public';

  return (
    <div>
      <PageHeader
        title={ticket.subject}
        subtitle={`Ticket #${ticket.id}`}
        actions={
          <Button
            variant="secondary"
            onClick={() => resolveTicket.mutate()}
            disabled={
              resolveTicket.isPending ||
              ticket.status === 'resolved' ||
              ticket.status === 'closed'
            }
          >
            {resolveTicket.isPending ? 'Resolving…' : 'Mark resolved'}
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="p-5">
            <div className="mb-4 flex flex-wrap gap-2">
              <Badge tone={ticketStatusTone[ticket.status]}>{humanize(ticket.status)}</Badge>
              <Badge tone={ticketPriorityTone[ticket.priority]}>
                {humanize(ticket.priority)}
              </Badge>
              <Badge tone={ticketCategoryTone[ticket.category]}>
                {humanize(ticket.category)}
              </Badge>
            </div>
            <p className="whitespace-pre-wrap text-sm text-slate-700">{ticket.description}</p>
            <p className="mt-3 text-xs text-slate-400">
              Opened {formatDateTime(ticket.created_at)}
            </p>
          </Card>

          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold text-slate-700">Timeline</h2>
            {ticket.messages.length === 0 ? (
              <EmptyState title="No messages yet" description="Add the first note or reply." />
            ) : (
              <ul className="space-y-3">
                {ticket.messages.map((message) => (
                  <li
                    key={message.id}
                    className={`rounded-lg border p-3 ${authorTone[message.author_type]}`}
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-600">
                        {humanize(message.author_type)}
                        {message.ai_generated ? ' · AI draft' : ''}
                      </span>
                      <span className="flex items-center gap-2">
                        <Badge tone={message.visibility === 'public' ? 'blue' : 'slate'}>
                          {message.visibility === 'public' ? 'Customer reply' : 'Internal note'}
                        </Badge>
                        <span className="text-xs text-slate-400">
                          {formatDateTime(message.created_at)}
                        </span>
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap text-sm text-slate-700">{message.body}</p>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold text-slate-700">Add message</h2>
            <div className="space-y-3">
              <Field label="Type">
                <Select
                  className="w-full"
                  value={visibility}
                  onChange={(event) =>
                    setVisibility(event.target.value as MessageVisibility)
                  }
                >
                  <option value="internal">Internal note</option>
                  <option value="public">Customer reply</option>
                </Select>
              </Field>
              <Textarea
                rows={4}
                value={body}
                onChange={(event) => setBody(event.target.value)}
                placeholder={
                  isPublicReply
                    ? 'Write a reply to the customer…'
                    : 'Write an internal note for your team…'
                }
              />
              {addMessage.isError ? (
                <p className="text-sm text-rose-600">{toErrorMessage(addMessage.error)}</p>
              ) : null}
              <div className="flex justify-end">
                <Button
                  disabled={body.trim() === ''}
                  onClick={() => {
                    if (isPublicReply) setConfirmOpen(true);
                    else submitMessage();
                  }}
                >
                  {isPublicReply ? 'Send reply' : 'Add note'}
                </Button>
              </div>
            </div>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-1">
          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold text-slate-700">Customer</h2>
            {ticket.customer ? (
              <div className="space-y-2 text-sm">
                <Link
                  to={`/customers/${ticket.customer.id}`}
                  className="font-medium text-brand-600 hover:underline"
                >
                  {ticket.customer.company_name}
                </Link>
                <p className="text-slate-500">{ticket.customer.email}</p>
                <Badge tone={customerStatusTone[ticket.customer.status as never] ?? 'slate'}>
                  {humanize(ticket.customer.status)}
                </Badge>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No customer linked.</p>
            )}
          </Card>

          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold text-slate-700">Manage</h2>
            <div className="space-y-3">
              <Field label="Status">
                <Select
                  className="w-full"
                  value={ticket.status}
                  onChange={(event) =>
                    updateTicket.mutate({ status: event.target.value as TicketStatus })
                  }
                  disabled={updateTicket.isPending}
                >
                  {TICKET_STATUSES.map((option) => (
                    <option key={option} value={option}>
                      {humanize(option)}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Priority">
                <Select
                  className="w-full"
                  value={ticket.priority}
                  onChange={(event) =>
                    updateTicket.mutate({ priority: event.target.value as TicketPriority })
                  }
                  disabled={updateTicket.isPending}
                >
                  {TICKET_PRIORITIES.map((option) => (
                    <option key={option} value={option}>
                      {humanize(option)}
                    </option>
                  ))}
                </Select>
              </Field>
              {updateTicket.isError ? (
                <p className="text-sm text-rose-600">{toErrorMessage(updateTicket.error)}</p>
              ) : null}
            </div>
          </Card>
        </div>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="Send customer reply?"
        description="This will be recorded as a customer-facing reply on the ticket timeline."
        confirmLabel="Send reply"
        loading={addMessage.isPending}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={submitMessage}
      />
    </div>
  );
}
