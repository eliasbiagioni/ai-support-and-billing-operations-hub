import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  PageHeader,
  Select,
  Spinner,
  Textarea,
} from '@/components/ui';
import { ConfirmDialog } from '@/components/ui/Modal';
import { useCustomers } from '@/features/customers/customerApi';
import { useCreateTicket, useTickets } from '@/features/tickets/ticketApi';
import { toErrorMessage } from '@/lib/errors';
import {
  formatDateTime,
  humanize,
  TICKET_CATEGORIES,
  TICKET_PRIORITIES,
  TICKET_STATUSES,
  ticketCategoryTone,
  ticketPriorityTone,
  ticketStatusTone,
} from '@/lib/format';
import type { TicketCategory, TicketCreate, TicketPriority } from '@/types/api';

const emptyForm: TicketCreate = {
  customer_id: 0,
  subject: '',
  description: '',
  category: 'other',
  priority: 'medium',
};

export function TicketsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const status = searchParams.get('status') ?? '';
  const category = searchParams.get('category') ?? '';
  const priority = searchParams.get('priority') ?? '';
  const q = searchParams.get('q') ?? '';

  const { data, isLoading, isError, error, refetch } = useTickets({
    status: status || undefined,
    category: category || undefined,
    priority: priority || undefined,
    q: q || undefined,
  });
  const customers = useCustomers();
  const createTicket = useCreateTicket();

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<TicketCreate>(emptyForm);

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next, { replace: true });
  }

  function resetAndClose() {
    setForm(emptyForm);
    setShowCreate(false);
  }

  function handleCreate() {
    createTicket.mutate(form, { onSuccess: resetAndClose });
  }

  const canSubmit =
    form.customer_id > 0 && form.subject.trim() !== '' && form.description.trim() !== '';

  return (
    <div>
      <PageHeader
        title="Tickets"
        subtitle="The support work queue across all customers."
        actions={<Button onClick={() => setShowCreate(true)}>New ticket</Button>}
      />

      <Card className="mb-4 flex flex-wrap gap-3 p-4">
        <Input
          placeholder="Search subject…"
          value={q}
          onChange={(event) => setFilter('q', event.target.value)}
          className="max-w-xs"
        />
        <Select value={status} onChange={(event) => setFilter('status', event.target.value)}>
          <option value="">All statuses</option>
          {TICKET_STATUSES.map((option) => (
            <option key={option} value={option}>
              {humanize(option)}
            </option>
          ))}
        </Select>
        <Select value={priority} onChange={(event) => setFilter('priority', event.target.value)}>
          <option value="">All priorities</option>
          {TICKET_PRIORITIES.map((option) => (
            <option key={option} value={option}>
              {humanize(option)}
            </option>
          ))}
        </Select>
        <Select value={category} onChange={(event) => setFilter('category', event.target.value)}>
          <option value="">All categories</option>
          {TICKET_CATEGORIES.map((option) => (
            <option key={option} value={option}>
              {humanize(option)}
            </option>
          ))}
        </Select>
      </Card>

      {isLoading ? <Spinner label="Loading tickets…" /> : null}
      {isError ? <ErrorState message={toErrorMessage(error)} onRetry={() => refetch()} /> : null}

      {data && data.items.length === 0 ? (
        <EmptyState
          title="No tickets match"
          description="Adjust the filters above or create a new ticket."
        />
      ) : null}

      {data && data.items.length > 0 ? (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Subject</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Priority</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((ticket) => (
                <tr key={ticket.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/tickets/${ticket.id}`}
                      className="font-medium text-brand-600 hover:underline"
                    >
                      {ticket.subject}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={ticketCategoryTone[ticket.category]}>
                      {humanize(ticket.category)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={ticketPriorityTone[ticket.priority]}>
                      {humanize(ticket.priority)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={ticketStatusTone[ticket.status]}>
                      {humanize(ticket.status)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {formatDateTime(ticket.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}

      <ConfirmDialog
        open={showCreate}
        title="Create ticket"
        confirmLabel="Create"
        loading={createTicket.isPending}
        onCancel={resetAndClose}
        onConfirm={() => {
          if (canSubmit) handleCreate();
        }}
      >
        <div className="space-y-3">
          <Field label="Customer">
            <Select
              className="w-full"
              value={form.customer_id || ''}
              onChange={(event) =>
                setForm({ ...form, customer_id: Number(event.target.value) })
              }
            >
              <option value="">Select a customer…</option>
              {(customers.data?.items ?? []).map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.company_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Subject">
            <Input
              value={form.subject}
              onChange={(event) => setForm({ ...form, subject: event.target.value })}
              placeholder="Short summary of the issue"
            />
          </Field>
          <Field label="Description">
            <Textarea
              rows={3}
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              placeholder="What is the customer experiencing?"
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Category">
              <Select
                className="w-full"
                value={form.category}
                onChange={(event) =>
                  setForm({ ...form, category: event.target.value as TicketCategory })
                }
              >
                {TICKET_CATEGORIES.map((option) => (
                  <option key={option} value={option}>
                    {humanize(option)}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Priority">
              <Select
                className="w-full"
                value={form.priority}
                onChange={(event) =>
                  setForm({ ...form, priority: event.target.value as TicketPriority })
                }
              >
                {TICKET_PRIORITIES.map((option) => (
                  <option key={option} value={option}>
                    {humanize(option)}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
          {createTicket.isError ? (
            <p className="text-sm text-rose-600">{toErrorMessage(createTicket.error)}</p>
          ) : null}
        </div>
      </ConfirmDialog>
    </div>
  );
}
