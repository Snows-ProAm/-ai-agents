create table if not exists public.agent_logs (
  id uuid primary key default gen_random_uuid(),
  message text not null,
  created_at timestamptz not null default now()
);

alter table public.agent_logs enable row level security;

drop policy if exists "Allow anon inserts into agent_logs" on public.agent_logs;
create policy "Allow anon inserts into agent_logs"
on public.agent_logs
for insert
to anon
with check (true);

drop policy if exists "Allow anon reads from agent_logs" on public.agent_logs;
create policy "Allow anon reads from agent_logs"
on public.agent_logs
for select
to anon
using (true);
