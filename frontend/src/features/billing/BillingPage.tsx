import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  PageHeader,
  Spinner,
} from '@/components/ui';
import {
  useInvoices,
  usePayments,
  useWebhookEvents,
} from '@/features/billing/billingApi';
import { toErrorMessage } from '@/lib/errors';
import {
  formatDateTime,
  formatMoney,
  humanize,
  invoiceStatusTone,
  paymentStatusTone,
} from '@/lib/format';

export function BillingPage() {
  const invoices = useInvoices();
  const payments = usePayments();
  const events = useWebhookEvents();

  const failedPayments = (payments.data?.items ?? []).filter(
    (payment) => payment.status === 'failed',
  );

  return (
    <div>
      <PageHeader
        title="Billing"
        subtitle="Invoices, payments, and recent Stripe activity across all customers."
      />

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <Card className="p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">Invoices</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {invoices.data?.total ?? '—'}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">Payments</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {payments.data?.total ?? '—'}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">Failed payments</p>
          <p className="mt-1 text-2xl font-semibold text-rose-600">
            {failedPayments.length}
          </p>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="overflow-hidden">
          <div className="border-b border-slate-100 px-4 py-3 text-sm font-semibold text-slate-700">
            Invoices
          </div>
          {invoices.isLoading ? <Spinner label="Loading invoices…" /> : null}
          {invoices.isError ? (
            <ErrorState
              message={toErrorMessage(invoices.error)}
              onRetry={() => invoices.refetch()}
            />
          ) : null}
          {invoices.data && invoices.data.items.length === 0 ? (
            <EmptyState title="No invoices yet" />
          ) : null}
          {invoices.data && invoices.data.items.length > 0 ? (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-2 font-medium">Description</th>
                  <th className="px-4 py-2 font-medium">Amount</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {invoices.data.items.map((invoice) => (
                  <tr key={invoice.id}>
                    <td className="px-4 py-2 text-slate-600">
                      {invoice.description ?? '—'}
                    </td>
                    <td className="px-4 py-2 text-slate-700">
                      {formatMoney(invoice.amount_due, invoice.currency)}
                    </td>
                    <td className="px-4 py-2">
                      <Badge tone={invoiceStatusTone[invoice.status]}>
                        {humanize(invoice.status)}
                      </Badge>
                    </td>
                    <td className="px-4 py-2 text-slate-500">
                      {formatDateTime(invoice.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </Card>

        <Card className="overflow-hidden">
          <div className="border-b border-slate-100 px-4 py-3 text-sm font-semibold text-slate-700">
            Payments
          </div>
          {payments.isLoading ? <Spinner label="Loading payments…" /> : null}
          {payments.isError ? (
            <ErrorState
              message={toErrorMessage(payments.error)}
              onRetry={() => payments.refetch()}
            />
          ) : null}
          {payments.data && payments.data.items.length === 0 ? (
            <EmptyState title="No payments yet" />
          ) : null}
          {payments.data && payments.data.items.length > 0 ? (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-2 font-medium">Amount</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Reason</th>
                  <th className="px-4 py-2 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {payments.data.items.map((payment) => (
                  <tr key={payment.id}>
                    <td className="px-4 py-2 text-slate-700">
                      {formatMoney(payment.amount, payment.currency)}
                    </td>
                    <td className="px-4 py-2">
                      <Badge tone={paymentStatusTone[payment.status]}>
                        {humanize(payment.status)}
                      </Badge>
                    </td>
                    <td className="px-4 py-2 text-slate-500">
                      {payment.failure_reason ?? '—'}
                    </td>
                    <td className="px-4 py-2 text-slate-500">
                      {formatDateTime(payment.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </Card>
      </div>

      <Card className="mt-6 overflow-hidden">
        <div className="border-b border-slate-100 px-4 py-3 text-sm font-semibold text-slate-700">
          Recent Stripe events
        </div>
        {events.isLoading ? <Spinner label="Loading events…" /> : null}
        {events.data && events.data.items.length === 0 ? (
          <EmptyState
            title="No webhook events yet"
            description="Stripe events appear here once your webhook is receiving traffic."
          />
        ) : null}
        {events.data && events.data.items.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">Event type</th>
                <th className="px-4 py-2 font-medium">Event ID</th>
                <th className="px-4 py-2 font-medium">Processed</th>
                <th className="px-4 py-2 font-medium">Received</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {events.data.items.map((event) => (
                <tr key={event.id}>
                  <td className="px-4 py-2 text-slate-700">{event.event_type}</td>
                  <td className="px-4 py-2 font-mono text-xs text-slate-500">
                    {event.event_id}
                  </td>
                  <td className="px-4 py-2">
                    <Badge tone={event.processed ? 'green' : 'amber'}>
                      {event.processed ? 'Processed' : 'Pending'}
                    </Badge>
                  </td>
                  <td className="px-4 py-2 text-slate-500">
                    {formatDateTime(event.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </Card>
    </div>
  );
}
