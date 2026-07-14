import { useState } from 'react';

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
import {
  useCreateUser,
  useResetPassword,
  useUpdateUser,
  useUsers,
} from '@/features/users/usersApi';
import { toErrorMessage } from '@/lib/errors';
import { formatDateTime, humanize } from '@/lib/format';
import type { AuthUser, UserRole } from '@/types/api';

const ROLES: UserRole[] = ['admin', 'support_agent', 'billing_agent', 'viewer'];

function UserRow({ user }: { user: AuthUser }) {
  const updateUser = useUpdateUser(user.id);
  const resetPassword = useResetPassword(user.id);
  const [resetOpen, setResetOpen] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [resetDone, setResetDone] = useState(false);

  function submitReset() {
    resetPassword.mutate(newPassword, {
      onSuccess: () => {
        setResetDone(true);
        setNewPassword('');
      },
    });
  }

  return (
    <tr className="align-middle hover:bg-slate-50">
      <td className="px-4 py-3">
        <p className="font-medium text-slate-800">{user.name}</p>
        <p className="text-xs text-slate-500">{user.email}</p>
      </td>
      <td className="px-4 py-3">
        <Select
          value={user.role}
          disabled={updateUser.isPending}
          onChange={(event) =>
            updateUser.mutate({ role: event.target.value as UserRole })
          }
        >
          {ROLES.map((role) => (
            <option key={role} value={role}>
              {humanize(role)}
            </option>
          ))}
        </Select>
      </td>
      <td className="px-4 py-3">
        <button
          type="button"
          onClick={() => updateUser.mutate({ active: !user.active })}
          disabled={updateUser.isPending}
        >
          <Badge tone={user.active ? 'green' : 'slate'}>
            {user.active ? 'Active' : 'Disabled'}
          </Badge>
        </button>
      </td>
      <td className="px-4 py-3 text-xs text-slate-500">
        {formatDateTime(user.created_at)}
      </td>
      <td className="px-4 py-3 text-right">
        <Button
          variant="secondary"
          onClick={() => {
            setResetOpen(true);
            setResetDone(false);
          }}
        >
          Reset password
        </Button>
      </td>

      <td>
        <ConfirmDialog
          open={resetOpen}
          title={`Reset password for ${user.name}`}
          description="Set a new password for this user. Share it with them securely."
          confirmLabel={resetDone ? 'Done' : 'Reset password'}
          loading={resetPassword.isPending}
          onCancel={() => setResetOpen(false)}
          onConfirm={resetDone ? () => setResetOpen(false) : submitReset}
        >
          {resetDone ? (
            <p className="text-sm text-emerald-700">Password updated.</p>
          ) : (
            <Field label="New password (min 8 characters)">
              <Input
                type="text"
                value={newPassword}
                minLength={8}
                onChange={(event) => setNewPassword(event.target.value)}
              />
            </Field>
          )}
          {resetPassword.isError ? (
            <p className="mt-2 text-sm text-rose-600">
              {toErrorMessage(resetPassword.error)}
            </p>
          ) : null}
        </ConfirmDialog>
      </td>
    </tr>
  );
}

const emptyForm = {
  name: '',
  email: '',
  password: '',
  role: 'support_agent' as UserRole,
};

export function UsersPage() {
  const { data, isLoading, isError, error, refetch } = useUsers();
  const createUser = useCreateUser();
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const canSubmit =
    form.name.trim() !== '' &&
    form.email.trim() !== '' &&
    form.password.length >= 8;

  function submitCreate() {
    createUser.mutate(form, {
      onSuccess: () => {
        setCreateOpen(false);
        setForm(emptyForm);
      },
    });
  }

  return (
    <div>
      <PageHeader
        title="Users"
        subtitle="Provision and manage agent accounts. There is no public sign-up."
        actions={
          <Button onClick={() => setCreateOpen(true)}>Add user</Button>
        }
      />

      {isLoading ? <Spinner label="Loading users…" /> : null}
      {isError ? (
        <ErrorState message={toErrorMessage(error)} onRetry={() => refetch()} />
      ) : null}

      {data && data.items.length === 0 ? (
        <EmptyState title="No users yet" description="Add the first agent account." />
      ) : null}

      {data && data.items.length > 0 ? (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">User</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((user) => (
                <UserRow key={user.id} user={user} />
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}

      <ConfirmDialog
        open={createOpen}
        title="Add user"
        description="Create a new agent account with an initial password."
        confirmLabel="Create user"
        loading={createUser.isPending}
        onCancel={() => setCreateOpen(false)}
        onConfirm={() => {
          if (canSubmit) submitCreate();
        }}
      >
        <div className="space-y-3">
          <Field label="Name">
            <Input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </Field>
          <Field label="Email">
            <Input
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
            />
          </Field>
          <Field label="Initial password (min 8 characters)">
            <Input
              type="text"
              value={form.password}
              minLength={8}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
            />
          </Field>
          <Field label="Role">
            <Select
              className="w-full"
              value={form.role}
              onChange={(event) =>
                setForm({ ...form, role: event.target.value as UserRole })
              }
            >
              {ROLES.map((role) => (
                <option key={role} value={role}>
                  {humanize(role)}
                </option>
              ))}
            </Select>
          </Field>
          {createUser.isError ? (
            <p className="text-sm text-rose-600">{toErrorMessage(createUser.error)}</p>
          ) : null}
        </div>
      </ConfirmDialog>
    </div>
  );
}
