import { useState } from 'react';
import { Link } from 'react-router-dom';

import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  PageHeader,
  Select,
  Spinner,
} from '@/components/ui';
import { useAiAuditLogs } from '@/features/ai/aiApi';
import { toErrorMessage } from '@/lib/errors';
import { formatDateTime, humanize } from '@/lib/format';

const ACTION_TYPES = ['classify', 'summarize', 'suggest_reply'];

function summarizeOutput(output: unknown): string {
  if (output == null) return '—';
  if (typeof output === 'string') return output;
  try {
    return JSON.stringify(output);
  } catch {
    return String(output);
  }
}

export function AiAuditLogsPage() {
  const [actionType, setActionType] = useState('');
  const { data, isLoading, isError, error, refetch } = useAiAuditLogs(
    actionType || undefined,
  );

  return (
    <div>
      <PageHeader
        title="AI audit logs"
        subtitle="Every AI action is recorded here for transparency and review."
      />

      <Card className="mb-4 flex flex-wrap gap-3 p-4">
        <Select value={actionType} onChange={(event) => setActionType(event.target.value)}>
          <option value="">All actions</option>
          {ACTION_TYPES.map((type) => (
            <option key={type} value={type}>
              {humanize(type)}
            </option>
          ))}
        </Select>
      </Card>

      {isLoading ? <Spinner label="Loading audit logs…" /> : null}
      {isError ? (
        <ErrorState message={toErrorMessage(error)} onRetry={() => refetch()} />
      ) : null}

      {data && data.items.length === 0 ? (
        <EmptyState
          title="No AI activity yet"
          description="Run classify, summarize, or suggest reply on a ticket to see logs here."
        />
      ) : null}

      {data && data.items.length > 0 ? (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">When</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">Input</th>
                <th className="px-4 py-3 font-medium">Output</th>
                <th className="px-4 py-3 font-medium">Risk flags</th>
                <th className="px-4 py-3 font-medium">Ticket</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((log) => (
                <tr key={log.id} className="align-top hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-500">
                    {formatDateTime(log.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone="indigo">{humanize(log.action_type)}</Badge>
                  </td>
                  <td className="max-w-xs px-4 py-3 text-slate-600">{log.input_summary}</td>
                  <td className="max-w-sm px-4 py-3 text-slate-600">
                    <span className="line-clamp-3 block">{summarizeOutput(log.output)}</span>
                  </td>
                  <td className="px-4 py-3">
                    {log.risk_flags.length === 0 ? (
                      <span className="text-slate-400">—</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {log.risk_flags.map((flag) => (
                          <Badge key={flag} tone="red">
                            {humanize(flag)}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {log.ticket_id ? (
                      <Link
                        to={`/tickets/${log.ticket_id}`}
                        className="text-brand-600 hover:underline"
                      >
                        View
                      </Link>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}
