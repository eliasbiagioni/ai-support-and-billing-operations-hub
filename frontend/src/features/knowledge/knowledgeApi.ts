import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/apiClient';
import type {
  ArticleCreate,
  ArticleUpdate,
  KnowledgeArticle,
  KnowledgeSearchResult,
  Page,
} from '@/types/api';

export interface ArticleListFilters {
  tag?: string;
  active?: boolean;
  q?: string;
}

const knowledgeKeys = {
  all: ['knowledge'] as const,
  list: (filters: ArticleListFilters) => ['knowledge', 'list', filters] as const,
  detail: (id: string) => ['knowledge', 'detail', id] as const,
  search: (q: string) => ['knowledge', 'search', q] as const,
};

export function useArticles(filters: ArticleListFilters) {
  return useQuery({
    queryKey: knowledgeKeys.list(filters),
    queryFn: ({ signal }) =>
      apiRequest<Page<KnowledgeArticle>>('/api/knowledge/articles', {
        query: { limit: 100, tag: filters.tag, active: filters.active, q: filters.q },
        signal,
      }),
  });
}

export function useKnowledgeSearch(q: string) {
  return useQuery({
    queryKey: knowledgeKeys.search(q),
    queryFn: ({ signal }) =>
      apiRequest<KnowledgeSearchResult[]>('/api/knowledge/search', {
        query: { q },
        signal,
      }),
    enabled: q.trim() !== '',
  });
}

export function useCreateArticle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ArticleCreate) =>
      apiRequest<KnowledgeArticle>('/api/knowledge/articles', {
        method: 'POST',
        body: payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: knowledgeKeys.all });
    },
  });
}

export function useUpdateArticle(articleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ArticleUpdate) =>
      apiRequest<KnowledgeArticle>(`/api/knowledge/articles/${articleId}`, {
        method: 'PATCH',
        body: payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: knowledgeKeys.all });
    },
  });
}
