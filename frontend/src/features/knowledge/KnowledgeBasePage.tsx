import { useMemo, useState } from 'react';

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
import {
  useArticles,
  useCreateArticle,
  useKnowledgeSearch,
  useUpdateArticle,
} from '@/features/knowledge/knowledgeApi';
import { toErrorMessage } from '@/lib/errors';
import { formatDateTime, humanize } from '@/lib/format';
import type { ArticleVisibility, KnowledgeArticle } from '@/types/api';

interface ArticleForm {
  title: string;
  content: string;
  tags: string;
  visibility: ArticleVisibility;
  active: boolean;
}

const emptyForm: ArticleForm = {
  title: '',
  content: '',
  tags: '',
  visibility: 'internal',
  active: true,
};

function toForm(article: KnowledgeArticle): ArticleForm {
  return {
    title: article.title,
    content: article.content,
    tags: article.tags.join(', '),
    visibility: article.visibility,
    active: article.active,
  };
}

export function KnowledgeBasePage() {
  const [tag, setTag] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [search, setSearch] = useState('');

  const activeParam =
    activeFilter === 'all' ? undefined : activeFilter === 'active';
  const { data, isLoading, isError, error, refetch } = useArticles({
    tag: tag || undefined,
    active: activeParam,
  });
  const searchQuery = useKnowledgeSearch(search);

  const [editing, setEditing] = useState<KnowledgeArticle | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [form, setForm] = useState<ArticleForm>(emptyForm);
  const [preview, setPreview] = useState<KnowledgeArticle | null>(null);

  const createArticle = useCreateArticle();
  const updateArticle = useUpdateArticle(editing?.id ?? '');
  const mutation = editing ? updateArticle : createArticle;

  const tags = useMemo(() => {
    const set = new Set<string>();
    for (const article of data?.items ?? []) {
      for (const t of article.tags) set.add(t);
    }
    return Array.from(set).sort();
  }, [data]);

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setShowEditor(true);
  }

  function openEdit(article: KnowledgeArticle) {
    setEditing(article);
    setForm(toForm(article));
    setShowEditor(true);
  }

  function closeEditor() {
    setShowEditor(false);
    setEditing(null);
    setForm(emptyForm);
  }

  function handleSubmit() {
    const payload = {
      title: form.title,
      content: form.content,
      tags: form.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
      visibility: form.visibility,
      active: form.active,
    };
    mutation.mutate(payload, { onSuccess: closeEditor });
  }

  const canSubmit = form.title.trim() !== '' && form.content.trim() !== '';

  return (
    <div>
      <PageHeader
        title="Knowledge base"
        subtitle="Reference articles that power support answers and future AI retrieval."
        actions={<Button onClick={openCreate}>New article</Button>}
      />

      <Card className="mb-4 flex flex-wrap items-end gap-3 p-4">
        <Input
          placeholder="Search articles…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="max-w-xs"
        />
        <Select value={tag} onChange={(event) => setTag(event.target.value)}>
          <option value="">All tags</option>
          {tags.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </Select>
        <Select
          value={activeFilter}
          onChange={(event) =>
            setActiveFilter(event.target.value as 'all' | 'active' | 'inactive')
          }
        >
          <option value="all">All states</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </Select>
      </Card>

      {search.trim() !== '' ? (
        <Card className="mb-4 p-4">
          <p className="mb-3 text-sm font-semibold text-slate-700">
            Search results for “{search}”
          </p>
          {searchQuery.isLoading ? <Spinner label="Searching…" /> : null}
          {searchQuery.data && searchQuery.data.length === 0 ? (
            <p className="text-sm text-slate-500">No matching chunks found.</p>
          ) : null}
          <ul className="space-y-3">
            {(searchQuery.data ?? []).map((result) => (
              <li
                key={result.chunk_id ?? result.article_id}
                className="rounded-lg border border-slate-200 p-3"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-800">
                    {result.title}
                  </span>
                  <Badge tone={result.visibility === 'public' ? 'green' : 'slate'}>
                    {humanize(result.visibility)}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-slate-600">{result.snippet}</p>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {isLoading ? <Spinner label="Loading articles…" /> : null}
      {isError ? (
        <ErrorState message={toErrorMessage(error)} onRetry={() => refetch()} />
      ) : null}

      {data && data.items.length === 0 ? (
        <EmptyState
          title="No articles yet"
          description="Create your first knowledge base article to get started."
        />
      ) : null}

      {data && data.items.length > 0 ? (
        <div className="grid gap-3 md:grid-cols-2">
          {data.items.map((article) => (
            <Card key={article.id} className="flex flex-col p-4">
              <div className="flex items-start justify-between gap-2">
                <button
                  type="button"
                  onClick={() => setPreview(article)}
                  className="text-left text-base font-semibold text-brand-600 hover:underline"
                >
                  {article.title}
                </button>
                <Badge tone={article.active ? 'green' : 'slate'}>
                  {article.active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <p className="mt-2 line-clamp-3 text-sm text-slate-600">
                {article.content}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Badge tone={article.visibility === 'public' ? 'green' : 'slate'}>
                  {humanize(article.visibility)}
                </Badge>
                {article.tags.map((t) => (
                  <Badge key={t} tone="blue">
                    {t}
                  </Badge>
                ))}
              </div>
              <div className="mt-4 flex items-center justify-between text-xs text-slate-400">
                <span>{article.chunk_count} chunks</span>
                <Button variant="secondary" onClick={() => openEdit(article)}>
                  Edit
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : null}

      <ConfirmDialog
        open={showEditor}
        title={editing ? 'Edit article' : 'Create article'}
        confirmLabel={editing ? 'Save' : 'Create'}
        loading={mutation.isPending}
        onCancel={closeEditor}
        onConfirm={() => {
          if (canSubmit) handleSubmit();
        }}
      >
        <div className="space-y-3">
          <Field label="Title">
            <Input
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              placeholder="Refund policy"
            />
          </Field>
          <Field label="Content">
            <Textarea
              rows={8}
              value={form.content}
              onChange={(event) => setForm({ ...form, content: event.target.value })}
              placeholder="Separate paragraphs with a blank line for cleaner chunks."
            />
          </Field>
          <Field label="Tags (comma-separated)">
            <Input
              value={form.tags}
              onChange={(event) => setForm({ ...form, tags: event.target.value })}
              placeholder="billing, refund"
            />
          </Field>
          <div className="flex gap-3">
            <Field label="Visibility">
              <Select
                className="w-full"
                value={form.visibility}
                onChange={(event) =>
                  setForm({ ...form, visibility: event.target.value as ArticleVisibility })
                }
              >
                <option value="internal">Internal</option>
                <option value="public">Public</option>
              </Select>
            </Field>
            <Field label="Active">
              <Select
                className="w-full"
                value={form.active ? 'true' : 'false'}
                onChange={(event) =>
                  setForm({ ...form, active: event.target.value === 'true' })
                }
              >
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </Select>
            </Field>
          </div>
          {mutation.isError ? (
            <p className="text-sm text-rose-600">{toErrorMessage(mutation.error)}</p>
          ) : null}
        </div>
      </ConfirmDialog>

      <ConfirmDialog
        open={preview !== null}
        title={preview?.title ?? ''}
        confirmLabel="Close"
        onCancel={() => setPreview(null)}
        onConfirm={() => setPreview(null)}
      >
        {preview ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={preview.visibility === 'public' ? 'green' : 'slate'}>
                {humanize(preview.visibility)}
              </Badge>
              <Badge tone={preview.active ? 'green' : 'slate'}>
                {preview.active ? 'Active' : 'Inactive'}
              </Badge>
              <span className="text-xs text-slate-400">
                {preview.chunk_count} chunks · updated {formatDateTime(preview.updated_at)}
              </span>
            </div>
            <p className="whitespace-pre-wrap text-sm text-slate-700">
              {preview.content}
            </p>
          </div>
        ) : null}
      </ConfirmDialog>
    </div>
  );
}
