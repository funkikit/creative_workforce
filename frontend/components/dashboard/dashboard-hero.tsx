import type { ReactNode } from "react";

type Stat = {
  label: string;
  value: string;
  helper: string;
};

type DashboardHeroProps = {
  headline: string;
  description: string;
  eyebrow?: string;
  stats: Stat[];
  actions?: ReactNode;
};

export function DashboardHero({ headline, description, eyebrow, stats, actions }: DashboardHeroProps) {
  return (
    <div className="relative overflow-hidden border-b border-slate-800 bg-gradient-to-br from-slate-900 via-slate-950 to-black">
      <div className="pointer-events-none absolute -left-10 top-16 h-64 w-64 rounded-full bg-blue-500/20 blur-3xl" />
      <div className="pointer-events-none absolute right-[-6rem] top-32 h-80 w-80 rounded-full bg-indigo-500/10 blur-3xl" />
      <div className="relative mx-auto flex max-w-7xl flex-col gap-6 px-6 py-16">
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-300">{eyebrow}</p>
        ) : null}
        <div className="max-w-3xl space-y-3">
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">{headline}</h1>
          <p className="text-sm text-slate-300 sm:text-base">{description}</p>
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
        <div className="grid gap-4 sm:grid-cols-3">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-2xl border border-slate-800/60 bg-slate-900/40 p-4 shadow-sm backdrop-blur"
            >
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                {stat.label}
              </p>
              <p className="mt-2 text-3xl font-semibold text-white">{stat.value}</p>
              <p className="text-xs text-slate-400">{stat.helper}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
