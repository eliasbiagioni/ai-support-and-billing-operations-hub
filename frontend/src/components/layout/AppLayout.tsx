import { NavLink, Outlet } from 'react-router-dom';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: 'grid' },
  { to: '/tickets', label: 'Tickets', icon: 'ticket' },
  { to: '/customers', label: 'Customers', icon: 'users' },
];

function NavIcon({ name }: { name: string }) {
  const paths: Record<string, string> = {
    grid: 'M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z',
    ticket:
      'M4 7a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 000 4v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2a2 2 0 000-4V7z',
    users:
      'M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-1.13a4 4 0 10-4-4 4 4 0 004 4z',
  };
  return (
    <svg
      className="h-5 w-5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={paths[name] ?? paths.grid} />
    </svg>
  );
}

export function AppLayout() {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white px-4 py-6 md:flex">
        <div className="mb-8 flex items-center gap-2 px-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white font-bold">
            S
          </span>
          <div>
            <p className="text-sm font-semibold leading-tight">SupportLedger</p>
            <p className="text-xs text-slate-400">AI Operations Hub</p>
          </div>
        </div>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-slate-600 hover:bg-slate-100'
                }`
              }
            >
              <NavIcon name={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-400">
          Phase 0-1 MVP. Auth is mocked; AI &amp; Stripe arrive in later phases.
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center gap-3 border-b border-slate-200 bg-white px-6 md:hidden">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white font-bold">
            S
          </span>
          <span className="text-sm font-semibold">SupportLedger AI</span>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
