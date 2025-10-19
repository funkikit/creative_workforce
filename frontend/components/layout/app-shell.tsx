import type { ReactNode } from "react";

type AppShellProps = {
  sidebar: ReactNode;
  mobileSidebar?: ReactNode;
  hero: ReactNode;
  children: ReactNode;
  message?: ReactNode;
  headerActions?: ReactNode;
};

export function AppShell({
  sidebar,
  mobileSidebar,
  hero,
  children,
  message,
  headerActions,
}: AppShellProps) {
  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className="hidden w-80 flex-col border-r border-slate-800/80 bg-slate-950/80 px-6 py-8 backdrop-blur lg:flex">
        <div className="flex items-center gap-2 text-lg font-semibold tracking-tight text-white">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/20 text-brand-200">
            CW
          </span>
          Creative Workforce
        </div>
        <div className="mt-8 flex-1 overflow-y-auto pr-2">{sidebar}</div>
        <p className="mt-6 text-xs text-slate-500">
          © {new Date().getFullYear()} Creative Workforce Labs. All rights reserved.
        </p>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-800 bg-slate-950/70 px-4 py-3 backdrop-blur md:px-8">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-400">
              Console
            </span>
            <span className="hidden text-sm text-slate-500 sm:inline">
              プロダクションフローの統合ハブ
            </span>
          </div>
          <div className="flex items-center gap-2">
            {headerActions}
            <a
              href="https://github.com/"
              target="_blank"
              rel="noreferrer"
              className="hidden items-center gap-2 rounded-full border border-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:border-brand-500/60 hover:text-brand-200 md:flex"
            >
              <span>Docs</span>
            </a>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto pb-16">
          {hero}
          <div className="mx-auto w-full max-w-7xl px-4 md:px-8">
            <div className="lg:hidden">{mobileSidebar ?? sidebar}</div>
            {message}
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
