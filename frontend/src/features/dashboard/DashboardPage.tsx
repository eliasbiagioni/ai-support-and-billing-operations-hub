import { Link } from 'react-router-dom';

import { Card, ErrorState, PageHeader, Spinner } from '@/components/ui';
import { useDashboardSummary } from '@/features/dashboard/dashboardApi';
import { toErrorMessage } from '@/lib/errors';

interface Metric {
  label: string;
  value: number;
  accent: string;
  to: string;
  hint: string;
}

export function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useDashboardSummary();

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Operational overview of support and billing activity."
      />

      {isLoading ? <Spinner /> : null}
      {isError ? <ErrorState message={toErrorMessage(error)} onRetry={() => refetch()} /> : null}

      {data ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {(
            [
              {
                label: 'Open tickets',
                value: data.open_tickets,
                accent: 'text-indigo-600',
                to: '/tickets?status=open',
                hint: 'Currently being worked',
              },
              {
                label: 'High priority',
                value: data.high_priority_tickets,
                accent: 'text-rose-600',
                to: '/tickets?priority=high',
                hint: 'High & urgent tickets',
              },
              {
                label: 'Billing tickets',
                value: data.billing_tickets,
                accent: 'text-amber-600',
                to: '/tickets?category=billing',
                hint: 'Payment & invoice issues',
              },
              {
                label: 'Unresolved',
                value: data.unresolved_tickets,
                accent: 'text-sky-600',
                to: '/tickets',
                hint: 'Not yet resolved or closed',
              },
            ] satisfies Metric[]
          ).map((metric) => (
            <Link key={metric.label} to={metric.to}>
              <Card className="p-5 transition hover:shadow-md">
                <p className="text-sm font-medium text-slate-500">{metric.label}</p>
                <p className={`mt-2 text-3xl font-semibold ${metric.accent}`}>{metric.value}</p>
                <p className="mt-1 text-xs text-slate-400">{metric.hint}</p>
              </Card>
            </Link>
          ))}
        </div>
      ) : null}

      {data ? (
        <Card className="mt-6 p-5">
          <p className="text-sm font-medium text-slate-500">Customers</p>
          <p className="mt-2 text-2xl font-semibold text-slate-800">{data.total_customers}</p>
          <Link to="/customers" className="mt-1 inline-block text-sm text-brand-600 hover:underline">
            View all customers →
          </Link>
        </Card>
      ) : null}
    </div>
  );
}
