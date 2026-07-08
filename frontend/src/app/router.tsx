import { createBrowserRouter, Navigate } from 'react-router-dom';

import { AppLayout } from '@/components/layout/AppLayout';
import { CustomerDetailPage } from '@/features/customers/CustomerDetailPage';
import { CustomersPage } from '@/features/customers/CustomersPage';
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { TicketDetailPage } from '@/features/tickets/TicketDetailPage';
import { TicketsPage } from '@/features/tickets/TicketsPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'customers', element: <CustomersPage /> },
      { path: 'customers/:customerId', element: <CustomerDetailPage /> },
      { path: 'tickets', element: <TicketsPage /> },
      { path: 'tickets/:ticketId', element: <TicketDetailPage /> },
      { path: '*', element: <Navigate to="/dashboard" replace /> },
    ],
  },
]);
