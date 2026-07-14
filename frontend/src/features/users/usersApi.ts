import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/apiClient';
import type { AuthUser, Page, UserCreate, UserUpdate } from '@/types/api';

const usersKey = ['users'] as const;

export function useUsers() {
  return useQuery({
    queryKey: usersKey,
    queryFn: ({ signal }) =>
      apiRequest<Page<AuthUser>>('/api/users', { query: { limit: 200 }, signal }),
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserCreate) =>
      apiRequest<AuthUser>('/api/users', { method: 'POST', body: payload }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: usersKey });
    },
  });
}

export function useUpdateUser(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserUpdate) =>
      apiRequest<AuthUser>(`/api/users/${userId}`, { method: 'PATCH', body: payload }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: usersKey });
    },
  });
}

export function useResetPassword(userId: string) {
  return useMutation({
    mutationFn: (newPassword: string) =>
      apiRequest<AuthUser>(`/api/users/${userId}/reset-password`, {
        method: 'POST',
        body: { new_password: newPassword },
      }),
  });
}
