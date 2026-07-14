import { createBrowserRouter, Navigate } from 'react-router-dom';

import { AppLayout } from '@/components/layout/AppLayout';
import { AiAuditLogsPage } from '@/features/ai/AiAuditLogsPage';
import { CopilotPage } from '@/features/ai/CopilotPage';
import { RequireAuth, RequireRole } from '@/features/auth/AuthContext';
import { LoginPage } from '@/features/auth/LoginPage';
import { BillingPage } from '@/features/billing/BillingPage';
import { CustomerDetailPage } from '@/features/customers/CustomerDetailPage';
import { CustomersPage } from '@/features/customers/CustomersPage';
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { KnowledgeBasePage } from '@/features/knowledge/KnowledgeBasePage';
import { TicketDetailPage } from '@/features/tickets/TicketDetailPage';
import { TicketsPage } from '@/features/tickets/TicketsPage';
import { UsersPage } from '@/features/users/UsersPage';

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'customers', element: <CustomersPage /> },
      { path: 'customers/:customerId', element: <CustomerDetailPage /> },
      { path: 'tickets', element: <TicketsPage /> },
      { path: 'tickets/:ticketId', element: <TicketDetailPage /> },
      { path: 'knowledge', element: <KnowledgeBasePage /> },
      { path: 'billing', element: <BillingPage /> },
      { path: 'copilot', element: <CopilotPage /> },
      { path: 'ai-audit', element: <AiAuditLogsPage /> },
      {
        path: 'users',
        element: (
          <RequireRole roles={['admin']}>
            <UsersPage />
          </RequireRole>
        ),
      },
      { path: '*', element: <Navigate to="/dashboard" replace /> },
    ],
  },
]);
