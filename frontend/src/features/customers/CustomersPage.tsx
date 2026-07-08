import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

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
} from '@/components/ui';
import { ConfirmDialog } from '@/components/ui/Modal';
import { useCreateCustomer, useCustomers } from '@/features/customers/customerApi';
import { toErrorMessage } from '@/lib/errors';
import { CUSTOMER_STATUSES, customerStatusTone, humanize } from '@/lib/format';
import type { CustomerCreate, CustomerStatus } from '@/types/api';

const emptyForm: CustomerCreate = {
  company_name: '',
  contact_name: '',
  email: '',
  status: 'active',
};

export function CustomersPage() {
  const { data, isLoading, isError, error, refetch } = useCustomers();
  const createCustomer = useCreateCustomer();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<CustomerStatus | ''>('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CustomerCreate>(emptyForm);

  const filtered = useMemo(() => {
    const items = data?.items ?? [];
    return items.filter((customer) => {
      const matchesSearch =
        !search ||
        customer.company_name.toLowerCase().includes(search.toLowerCase()) ||
        customer.email.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = !statusFilter || customer.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [data, search, statusFilter]);

  function resetAndClose() {
    setForm(emptyForm);
    setShowCreate(false);
  }

  function handleCreate() {
    createCustomer.mutate(
      { ...form, contact_name: form.contact_name || null },
      { onSuccess: resetAndClose },
    );
  }

  const canSubmit = form.company_name.trim() !== '' && form.email.trim() !== '';

  return (
    <div>
      <PageHeader
        title="Customers"
        subtitle="Search and manage the accounts your team supports."
        actions={<Button onClick={() => setShowCreate(true)}>New customer</Button>}
      />

      <Card className="mb-4 flex flex-wrap gap-3 p-4">
        <Input
          placeholder="Search by company or email…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="max-w-xs"
        />
        <Select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as CustomerStatus | '')}
        >
          <option value="">All statuses</option>
          {CUSTOMER_STATUSES.map((status) => (
            <option key={status} value={status}>
              {humanize(status)}
            </option>
          ))}
        </Select>
      </Card>

      {isLoading ? <Spinner label="Loading customers…" /> : null}
      {isError ? <ErrorState message={toErrorMessage(error)} onRetry={() => refetch()} /> : null}

      {data && filtered.length === 0 ? (
        <EmptyState
          title="No customers found"
          description="Try adjusting your filters or create a new customer."
        />
      ) : null}

      {data && filtered.length > 0 ? (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Contact</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Plan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((customer) => (
                <tr key={customer.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/customers/${customer.id}`}
                      className="font-medium text-brand-600 hover:underline"
                    >
                      {customer.company_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{customer.contact_name ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600">{customer.email}</td>
                  <td className="px-4 py-3">
                    <Badge tone={customerStatusTone[customer.status]}>
                      {humanize(customer.status)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{customer.plan?.name ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}

      <ConfirmDialog
        open={showCreate}
        title="Create customer"
        confirmLabel="Create"
        loading={createCustomer.isPending}
        onCancel={resetAndClose}
        onConfirm={() => {
          if (canSubmit) handleCreate();
        }}
      >
        <div className="space-y-3">
          <Field label="Company name">
            <Input
              value={form.company_name}
              onChange={(event) => setForm({ ...form, company_name: event.target.value })}
              placeholder="Acme Inc"
            />
          </Field>
          <Field label="Contact name">
            <Input
              value={form.contact_name ?? ''}
              onChange={(event) => setForm({ ...form, contact_name: event.target.value })}
              placeholder="Jane Doe"
            />
          </Field>
          <Field label="Email">
            <Input
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              placeholder="ops@acme.com"
            />
          </Field>
          <Field label="Status">
            <Select
              className="w-full"
              value={form.status}
              onChange={(event) =>
                setForm({ ...form, status: event.target.value as CustomerStatus })
              }
            >
              {CUSTOMER_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {humanize(status)}
                </option>
              ))}
            </Select>
          </Field>
          {createCustomer.isError ? (
            <p className="text-sm text-rose-600">{toErrorMessage(createCustomer.error)}</p>
          ) : null}
        </div>
      </ConfirmDialog>
    </div>
  );
}
