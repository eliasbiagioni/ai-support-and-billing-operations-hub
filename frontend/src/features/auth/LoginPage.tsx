import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button, Card, Field, Input } from '@/components/ui';
import { useAuth } from '@/features/auth/authState';
import { toErrorMessage } from '@/lib/errors';

export function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    navigate('/dashboard', { replace: true });
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-sm p-6">
        <div className="mb-6 flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 font-bold text-white">
            S
          </span>
          <div>
            <p className="text-sm font-semibold leading-tight">SupportLedger</p>
            <p className="text-xs text-slate-400">AI Operations Hub</p>
          </div>
        </div>
        <h1 className="mb-1 text-lg font-semibold text-slate-900">Sign in</h1>
        <p className="mb-4 text-sm text-slate-500">
          Use your agent account. Accounts are provisioned by an admin.
        </p>
        <form className="space-y-3" onSubmit={onSubmit}>
          <Field label="Email">
            <Input
              type="email"
              value={email}
              autoComplete="username"
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </Field>
          <Field label="Password">
            <Input
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </Field>
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>
      </Card>
    </div>
  );
}
