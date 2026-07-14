import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  PageHeader,
  Select,
  Spinner,
  Textarea,
} from '@/components/ui';
import { ConfirmDialog } from '@/components/ui/Modal';
import {
  useCreateCheckoutSession,
  useCustomerBilling,
} from '@/features/billing/billingApi';
import { useCustomer, useUpdateCustomer } from '@/features/customers/customerApi';
import { useTickets } from '@/features/tickets/ticketApi';
import { toErrorMessage } from '@/lib/errors';
import {
  CUSTOMER_STATUSES,
  customerStatusTone,
  formatDateTime,
  formatMoney,
  humanize,
  invoiceStatusTone,
  paymentStatusTone,
  ticketPriorityTone,
  ticketStatusTone,
} from '@/lib/format';
import type { CustomerStatus } from '@/types/api';

export function CustomerDetailPage() {
  const params = useParams();
  const customerId = params.customerId ?? '';

  const { data: customer, isLoading, isError, error, refetch } = useCustomer(customerId);
  const tickets = useTickets({ customer_id: customerId });
  const updateCustomer = useUpdateCustomer(customerId);
  const billing = useCustomerBilling(customerId);
  const checkout = useCreateCheckoutSession(customerId);

  const [editing, setEditing] = useState(false);
  const [status, setStatus] = useState<CustomerStatus>('active');
  const [notes, setNotes] = useState('');
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  function startCheckout() {
    checkout.mutate(undefined, {
      onSuccess: (session) => {
        setCheckoutOpen(false);
        window.open(session.url, '_blank', 'noopener');
      },
    });
  }

  function startEditing() {
    if (!customer) return;
    setStatus(customer.status);
    setNotes(customer.notes ?? '');
    setEditing(true);
  }

  function saveEdits() {
    updateCustomer.mutate(
      { status, notes: notes || null },
      { onSuccess: () => setEditing(false) },
    );
  }

  if (isLoading) return <Spinner label="Loading customer…" />;
  if (isError || !customer) {
    return <ErrorState message={toErrorMessage(error)} onRetry={() => refetch()} />;
  }

  return (
    <div>
      <PageHeader
        title={customer.company_name}
        subtitle={customer.email}
        actions={
          editing ? (
            <>
              <Button variant="secondary" onClick={() => setEditing(false)}>
                Cancel
              </Button>
              <Button onClick={saveEdits} disabled={updateCustomer.isPending}>
                {updateCustomer.isPending ? 'Saving…' : 'Save'}
              </Button>
            </>
          ) : (
            <Button variant="secondary" onClick={startEditing}>
              Edit
            </Button>
          )
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-1">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">Profile</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Status</dt>
              <dd>
                {editing ? (
                  <Select
                    value={status}
                    onChange={(event) => setStatus(event.target.value as CustomerStatus)}
                  >
                    {CUSTOMER_STATUSES.map((option) => (
                      <option key={option} value={option}>
                        {humanize(option)}
                      </option>
                    ))}
                  </Select>
                ) : (
                  <Badge tone={customerStatusTone[customer.status]}>
                    {humanize(customer.status)}
                  </Badge>
                )}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Contact</dt>
              <dd className="text-slate-800">{customer.contact_name ?? '—'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Plan</dt>
              <dd className="text-slate-800">{customer.plan?.name ?? '—'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Created</dt>
              <dd className="text-slate-800">{formatDateTime(customer.created_at)}</dd>
            </div>
          </dl>

          <h3 className="mb-2 mt-6 text-sm font-semibold text-slate-700">Notes</h3>
          {editing ? (
            <Textarea
              rows={4}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Internal notes about this account…"
            />
          ) : (
            <p className="whitespace-pre-wrap text-sm text-slate-600">
              {customer.notes ?? 'No notes yet.'}
            </p>
          )}
          {updateCustomer.isError ? (
            <p className="mt-2 text-sm text-rose-600">{toErrorMessage(updateCustomer.error)}</p>
          ) : null}
        </Card>

        <Card className="p-5 lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">Tickets</h2>
          {tickets.isLoading ? <Spinner label="Loading tickets…" /> : null}
          {tickets.isError ? (
            <ErrorState
              message={toErrorMessage(tickets.error)}
              onRetry={() => tickets.refetch()}
            />
          ) : null}
          {tickets.data && tickets.data.items.length === 0 ? (
            <EmptyState title="No tickets" description="This customer has no tickets yet." />
          ) : null}
          {tickets.data && tickets.data.items.length > 0 ? (
            <ul className="divide-y divide-slate-100">
              {tickets.data.items.map((ticket) => (
                <li key={ticket.id} className="flex items-center justify-between py-3">
                  <div className="min-w-0">
                    <Link
                      to={`/tickets/${ticket.id}`}
                      className="block truncate font-medium text-brand-600 hover:underline"
                    >
                      {ticket.subject}
                    </Link>
                    <p className="text-xs text-slate-400">{formatDateTime(ticket.created_at)}</p>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <Badge tone={ticketPriorityTone[ticket.priority]}>
                      {humanize(ticket.priority)}
                    </Badge>
                    <Badge tone={ticketStatusTone[ticket.status]}>
                      {humanize(ticket.status)}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </Card>
      </div>

      <Card className="mt-6 p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-700">Billing</h2>
          <Button
            variant="secondary"
            onClick={() => setCheckoutOpen(true)}
            disabled={checkout.isPending}
          >
            Create checkout session
          </Button>
        </div>

        {billing.isLoading ? <Spinner label="Loading billing…" /> : null}
        {billing.isError ? (
          <ErrorState
            message={toErrorMessage(billing.error)}
            onRetry={() => billing.refetch()}
          />
        ) : null}

        {billing.data ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">Plan</p>
              <p className="mt-1 text-sm text-slate-800">
                {billing.data.plan_name ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">
                Outstanding balance
              </p>
              <p className="mt-1 text-sm text-slate-800">
                {formatMoney(billing.data.outstanding_balance)}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">
                Latest activity
              </p>
              <div className="mt-1 flex flex-wrap gap-2">
                {billing.data.latest_invoice ? (
                  <Badge tone={invoiceStatusTone[billing.data.latest_invoice.status]}>
                    Invoice: {humanize(billing.data.latest_invoice.status)}
                  </Badge>
                ) : null}
                {billing.data.latest_payment ? (
                  <Badge tone={paymentStatusTone[billing.data.latest_payment.status]}>
                    Payment: {humanize(billing.data.latest_payment.status)}
                  </Badge>
                ) : null}
                {!billing.data.latest_invoice && !billing.data.latest_payment ? (
                  <span className="text-sm text-slate-500">No activity yet.</span>
                ) : null}
              </div>
            </div>
          </div>
        ) : null}
      </Card>

      <ConfirmDialog
        open={checkoutOpen}
        title="Create Stripe checkout session?"
        description="This opens a Stripe Checkout page in a new tab for the customer to complete a subscription. Requires Stripe keys to be configured."
        confirmLabel="Create session"
        loading={checkout.isPending}
        onCancel={() => setCheckoutOpen(false)}
        onConfirm={startCheckout}
      >
        {checkout.isError ? (
          <p className="text-sm text-rose-600">{toErrorMessage(checkout.error)}</p>
        ) : null}
      </ConfirmDialog>
    </div>
  );
}
