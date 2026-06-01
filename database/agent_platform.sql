-- Agent platform schema for Supabase.
-- Designed for a personal multi-agent system that can grow into workflows,
-- integrations, memory, approvals, observability, and cost accounting.
--
-- Run from Supabase SQL Editor.
-- Keep personal data behind backend/service-role access. Do not expose these
-- tables with broad anon policies.

create extension if not exists pgcrypto;
create extension if not exists vector;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  owner_label text,
  settings jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.workspace_members (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  external_user_id text,
  display_name text,
  role text not null default 'owner'
    check (role in ('owner', 'admin', 'operator', 'viewer')),
  settings jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, external_user_id)
);

create table if not exists public.secret_refs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  provider text not null,
  name text not null,
  description text,
  external_ref text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, provider, name)
);

create table if not exists public.integration_accounts (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  provider text not null,
  account_label text not null,
  auth_type text not null default 'api_key'
    check (auth_type in ('api_key', 'oauth', 'smtp', 'webhook', 'service_role', 'none')),
  secret_ref_id uuid references public.secret_refs(id) on delete set null,
  status text not null default 'active'
    check (status in ('active', 'disabled', 'expired', 'error')),
  scopes text[] not null default '{}'::text[],
  config jsonb not null default '{}'::jsonb,
  last_verified_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, provider, account_label)
);

create table if not exists public.agent_versions (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  agent_slug text not null,
  version int not null,
  name text not null,
  description text,
  model_provider text not null default 'gemini',
  model_name text not null default 'gemini-2.5-flash',
  system_prompt text,
  instructions jsonb not null default '{}'::jsonb,
  config jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (workspace_id, agent_slug, version)
);

create table if not exists public.agent_profiles (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  slug text not null,
  name text not null,
  description text,
  active_version_id uuid references public.agent_versions(id) on delete set null,
  default_model_provider text not null default 'gemini',
  default_model_name text not null default 'gemini-2.5-flash',
  default_system_prompt text,
  config jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, slug)
);

alter table public.agent_versions
add column if not exists agent_id uuid references public.agent_profiles(id) on delete cascade;

create table if not exists public.agent_tools (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  slug text not null,
  name text not null,
  description text,
  tool_type text not null
    check (tool_type in ('api', 'database', 'browser', 'code', 'webhook', 'human', 'internal')),
  integration_account_id uuid references public.integration_accounts(id) on delete set null,
  input_schema jsonb not null default '{}'::jsonb,
  output_schema jsonb not null default '{}'::jsonb,
  config jsonb not null default '{}'::jsonb,
  requires_approval boolean not null default false,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, slug)
);

create table if not exists public.agent_tool_permissions (
  agent_id uuid not null references public.agent_profiles(id) on delete cascade,
  tool_id uuid not null references public.agent_tools(id) on delete cascade,
  permission_level text not null default 'execute'
    check (permission_level in ('read', 'execute', 'admin')),
  config jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  primary key (agent_id, tool_id)
);

create table if not exists public.contacts (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  display_name text not null,
  aliases text[] not null default '{}'::text[],
  email_addresses text[] not null default '{}'::text[],
  phone_numbers text[] not null default '{}'::text[],
  relationship text,
  notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  channel text not null,
  external_thread_id text,
  title text,
  status text not null default 'open'
    check (status in ('open', 'closed', 'archived')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, channel, external_thread_id)
);

create table if not exists public.agent_messages (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  conversation_id uuid references public.conversations(id) on delete cascade,
  agent_id uuid references public.agent_profiles(id) on delete set null,
  role text not null check (role in ('user', 'assistant', 'system', 'tool', 'developer')),
  content text not null,
  content_format text not null default 'text',
  raw_payload jsonb not null default '{}'::jsonb,
  token_count int,
  created_at timestamptz not null default now()
);

create table if not exists public.workflow_definitions (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  slug text not null,
  name text not null,
  description text,
  status text not null default 'draft'
    check (status in ('draft', 'active', 'disabled', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, slug)
);

create table if not exists public.workflow_versions (
  id uuid primary key default gen_random_uuid(),
  workflow_id uuid not null references public.workflow_definitions(id) on delete cascade,
  version int not null,
  graph jsonb not null default '{}'::jsonb,
  config jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (workflow_id, version)
);

create table if not exists public.workflow_schedules (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  workflow_id uuid references public.workflow_definitions(id) on delete cascade,
  schedule_type text not null check (schedule_type in ('cron', 'interval', 'manual')),
  schedule_expression text,
  timezone text not null default 'UTC',
  payload jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  next_run_at timestamptz,
  last_run_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_tasks (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  conversation_id uuid references public.conversations(id) on delete set null,
  requested_by_message_id uuid references public.agent_messages(id) on delete set null,
  workflow_id uuid references public.workflow_definitions(id) on delete set null,
  workflow_version_id uuid references public.workflow_versions(id) on delete set null,
  parent_task_id uuid references public.agent_tasks(id) on delete set null,
  assigned_agent_id uuid references public.agent_profiles(id) on delete set null,
  intent text not null,
  title text,
  status text not null default 'queued'
    check (status in ('queued', 'running', 'waiting_approval', 'waiting_external', 'completed', 'failed', 'cancelled')),
  priority int not null default 100,
  input jsonb not null default '{}'::jsonb,
  output jsonb not null default '{}'::jsonb,
  error text,
  total_input_tokens int not null default 0,
  total_output_tokens int not null default 0,
  total_cached_tokens int not null default 0,
  total_reasoning_tokens int not null default 0,
  total_tokens int not null default 0,
  total_cost_usd numeric(14, 8) not null default 0,
  total_duration_ms int not null default 0,
  queued_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_runs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  task_id uuid references public.agent_tasks(id) on delete cascade,
  agent_id uuid references public.agent_profiles(id) on delete set null,
  agent_version_id uuid references public.agent_versions(id) on delete set null,
  status text not null default 'running'
    check (status in ('queued', 'running', 'completed', 'failed', 'cancelled')),
  model_provider text,
  model_name text,
  provider_request_id text,
  input jsonb not null default '{}'::jsonb,
  output jsonb not null default '{}'::jsonb,
  error text,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  duration_ms int,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_run_steps (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  task_id uuid references public.agent_tasks(id) on delete cascade,
  step_index int not null,
  step_type text not null
    check (step_type in ('model_call', 'tool_call', 'memory_read', 'memory_write', 'decision', 'approval', 'handoff', 'error')),
  agent_id uuid references public.agent_profiles(id) on delete set null,
  tool_id uuid references public.agent_tools(id) on delete set null,
  status text not null default 'completed'
    check (status in ('queued', 'running', 'completed', 'failed', 'skipped', 'cancelled')),
  input jsonb not null default '{}'::jsonb,
  output jsonb not null default '{}'::jsonb,
  error text,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  duration_ms int,
  created_at timestamptz not null default now(),
  unique (run_id, step_index)
);

create table if not exists public.agent_usage_events (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  task_id uuid references public.agent_tasks(id) on delete set null,
  run_id uuid references public.agent_runs(id) on delete set null,
  step_id uuid references public.agent_run_steps(id) on delete set null,
  agent_id uuid references public.agent_profiles(id) on delete set null,
  provider text not null,
  model_name text,
  operation text not null default 'model_call',
  provider_request_id text,
  input_tokens int not null default 0,
  output_tokens int not null default 0,
  cached_tokens int not null default 0,
  reasoning_tokens int not null default 0,
  total_tokens int generated always as
    (input_tokens + output_tokens + cached_tokens + reasoning_tokens) stored,
  input_cost_usd numeric(14, 8) not null default 0,
  output_cost_usd numeric(14, 8) not null default 0,
  cached_cost_usd numeric(14, 8) not null default 0,
  reasoning_cost_usd numeric(14, 8) not null default 0,
  total_cost_usd numeric(14, 8) generated always as
    (input_cost_usd + output_cost_usd + cached_cost_usd + reasoning_cost_usd) stored,
  latency_ms int,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_budgets (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  scope_type text not null check (scope_type in ('workspace', 'agent', 'workflow', 'tool')),
  scope_id uuid,
  period text not null check (period in ('daily', 'weekly', 'monthly', 'lifetime')),
  max_cost_usd numeric(14, 4),
  max_tokens int,
  alert_threshold_percent int not null default 80,
  hard_limit boolean not null default false,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_approvals (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  task_id uuid references public.agent_tasks(id) on delete cascade,
  run_id uuid references public.agent_runs(id) on delete set null,
  step_id uuid references public.agent_run_steps(id) on delete set null,
  requested_by_agent_id uuid references public.agent_profiles(id) on delete set null,
  approval_type text not null,
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected', 'expired', 'cancelled')),
  reason text,
  request_payload jsonb not null default '{}'::jsonb,
  response_payload jsonb not null default '{}'::jsonb,
  approved_by text,
  requested_at timestamptz not null default now(),
  decided_at timestamptz,
  expires_at timestamptz
);

create table if not exists public.agent_memory (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  agent_id uuid references public.agent_profiles(id) on delete cascade,
  contact_id uuid references public.contacts(id) on delete set null,
  memory_type text not null,
  scope text not null default 'workspace'
    check (scope in ('workspace', 'agent', 'contact', 'conversation', 'task')),
  subject text,
  content text not null,
  source_task_id uuid references public.agent_tasks(id) on delete set null,
  source_message_id uuid references public.agent_messages(id) on delete set null,
  confidence numeric(4, 3) not null default 1.0,
  importance int not null default 50,
  metadata jsonb not null default '{}'::jsonb,
  last_used_at timestamptz,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_memory_embeddings (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  memory_id uuid not null references public.agent_memory(id) on delete cascade,
  embedding_model text not null,
  embedding vector(1536),
  content_hash text,
  created_at timestamptz not null default now(),
  unique (memory_id, embedding_model)
);

create table if not exists public.agent_artifacts (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  task_id uuid references public.agent_tasks(id) on delete set null,
  run_id uuid references public.agent_runs(id) on delete set null,
  step_id uuid references public.agent_run_steps(id) on delete set null,
  artifact_type text not null,
  title text,
  content text,
  content_format text not null default 'text',
  url text,
  storage_path text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_events (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  event_type text not null,
  severity text not null default 'info'
    check (severity in ('debug', 'info', 'warning', 'error', 'critical')),
  agent_id uuid references public.agent_profiles(id) on delete set null,
  task_id uuid references public.agent_tasks(id) on delete set null,
  run_id uuid references public.agent_runs(id) on delete set null,
  conversation_id uuid references public.conversations(id) on delete set null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_audit_log (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  actor_type text not null check (actor_type in ('user', 'agent', 'system', 'tool')),
  actor_id uuid,
  action text not null,
  resource_type text,
  resource_id uuid,
  before_state jsonb,
  after_state jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.agent_eval_sets (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  slug text not null,
  name text not null,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, slug)
);

create table if not exists public.agent_eval_cases (
  id uuid primary key default gen_random_uuid(),
  eval_set_id uuid not null references public.agent_eval_sets(id) on delete cascade,
  name text not null,
  input jsonb not null,
  expected_output jsonb,
  grading_notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_eval_runs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  eval_set_id uuid references public.agent_eval_sets(id) on delete set null,
  agent_id uuid references public.agent_profiles(id) on delete set null,
  agent_version_id uuid references public.agent_versions(id) on delete set null,
  status text not null default 'running'
    check (status in ('running', 'completed', 'failed', 'cancelled')),
  score numeric(6, 4),
  summary text,
  started_at timestamptz not null default now(),
  finished_at timestamptz
);

create table if not exists public.agent_eval_results (
  id uuid primary key default gen_random_uuid(),
  eval_run_id uuid not null references public.agent_eval_runs(id) on delete cascade,
  eval_case_id uuid references public.agent_eval_cases(id) on delete set null,
  task_id uuid references public.agent_tasks(id) on delete set null,
  score numeric(6, 4),
  passed boolean,
  output jsonb,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.rate_limit_buckets (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  scope text not null,
  bucket_key text not null,
  window_start timestamptz not null,
  window_seconds int not null,
  used_count int not null default 0,
  used_tokens int not null default 0,
  used_cost_usd numeric(14, 8) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, scope, bucket_key, window_start, window_seconds)
);

create index if not exists idx_workspace_members_workspace on public.workspace_members (workspace_id);
create index if not exists idx_secret_refs_workspace_provider on public.secret_refs (workspace_id, provider);
create index if not exists idx_integration_accounts_workspace_provider on public.integration_accounts (workspace_id, provider);
create index if not exists idx_agent_profiles_workspace_slug on public.agent_profiles (workspace_id, slug);
create index if not exists idx_agent_versions_agent on public.agent_versions (agent_id, version);
create index if not exists idx_agent_tools_workspace_slug on public.agent_tools (workspace_id, slug);
create index if not exists idx_contacts_workspace_aliases on public.contacts using gin (aliases);
create index if not exists idx_contacts_workspace_email_addresses on public.contacts using gin (email_addresses);
create index if not exists idx_conversations_workspace_channel_thread on public.conversations (workspace_id, channel, external_thread_id);
create index if not exists idx_agent_messages_conversation_created on public.agent_messages (conversation_id, created_at);
create index if not exists idx_workflow_versions_workflow on public.workflow_versions (workflow_id, version);
create index if not exists idx_workflow_schedules_next_run on public.workflow_schedules (is_active, next_run_at);
create index if not exists idx_agent_tasks_status_created on public.agent_tasks (workspace_id, status, created_at);
create index if not exists idx_agent_tasks_assigned_agent on public.agent_tasks (assigned_agent_id, status);
create index if not exists idx_agent_runs_task on public.agent_runs (task_id, started_at);
create index if not exists idx_agent_run_steps_run on public.agent_run_steps (run_id, step_index);
create index if not exists idx_usage_events_task on public.agent_usage_events (task_id, created_at);
create index if not exists idx_usage_events_provider_model on public.agent_usage_events (provider, model_name, created_at);
create index if not exists idx_agent_approvals_status on public.agent_approvals (workspace_id, status, requested_at);
create index if not exists idx_agent_memory_workspace_type on public.agent_memory (workspace_id, memory_type);
create index if not exists idx_agent_memory_agent_type on public.agent_memory (agent_id, memory_type);
create index if not exists idx_agent_memory_embeddings_vector
  on public.agent_memory_embeddings using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
create index if not exists idx_agent_artifacts_task on public.agent_artifacts (task_id, created_at);
create index if not exists idx_agent_events_type_created on public.agent_events (workspace_id, event_type, created_at);
create index if not exists idx_agent_audit_resource on public.agent_audit_log (resource_type, resource_id, created_at);

create or replace view public.agent_task_cost_summary as
select
  task_id,
  count(*) as usage_event_count,
  coalesce(sum(input_tokens), 0)::int as input_tokens,
  coalesce(sum(output_tokens), 0)::int as output_tokens,
  coalesce(sum(cached_tokens), 0)::int as cached_tokens,
  coalesce(sum(reasoning_tokens), 0)::int as reasoning_tokens,
  coalesce(sum(total_tokens), 0)::int as total_tokens,
  coalesce(sum(total_cost_usd), 0)::numeric(14, 8) as total_cost_usd,
  coalesce(sum(latency_ms), 0)::int as total_latency_ms
from public.agent_usage_events
where task_id is not null
group by task_id;

create or replace view public.agent_daily_cost_summary as
select
  workspace_id,
  date_trunc('day', created_at) as day,
  provider,
  model_name,
  count(*) as usage_event_count,
  coalesce(sum(total_tokens), 0)::int as total_tokens,
  coalesce(sum(total_cost_usd), 0)::numeric(14, 8) as total_cost_usd
from public.agent_usage_events
group by workspace_id, date_trunc('day', created_at), provider, model_name;

drop trigger if exists set_workspaces_updated_at on public.workspaces;
create trigger set_workspaces_updated_at before update on public.workspaces
for each row execute function public.set_updated_at();

drop trigger if exists set_workspace_members_updated_at on public.workspace_members;
create trigger set_workspace_members_updated_at before update on public.workspace_members
for each row execute function public.set_updated_at();

drop trigger if exists set_secret_refs_updated_at on public.secret_refs;
create trigger set_secret_refs_updated_at before update on public.secret_refs
for each row execute function public.set_updated_at();

drop trigger if exists set_integration_accounts_updated_at on public.integration_accounts;
create trigger set_integration_accounts_updated_at before update on public.integration_accounts
for each row execute function public.set_updated_at();

drop trigger if exists set_agent_profiles_updated_at on public.agent_profiles;
create trigger set_agent_profiles_updated_at before update on public.agent_profiles
for each row execute function public.set_updated_at();

drop trigger if exists set_agent_tools_updated_at on public.agent_tools;
create trigger set_agent_tools_updated_at before update on public.agent_tools
for each row execute function public.set_updated_at();

drop trigger if exists set_contacts_updated_at on public.contacts;
create trigger set_contacts_updated_at before update on public.contacts
for each row execute function public.set_updated_at();

drop trigger if exists set_conversations_updated_at on public.conversations;
create trigger set_conversations_updated_at before update on public.conversations
for each row execute function public.set_updated_at();

drop trigger if exists set_workflow_definitions_updated_at on public.workflow_definitions;
create trigger set_workflow_definitions_updated_at before update on public.workflow_definitions
for each row execute function public.set_updated_at();

drop trigger if exists set_workflow_schedules_updated_at on public.workflow_schedules;
create trigger set_workflow_schedules_updated_at before update on public.workflow_schedules
for each row execute function public.set_updated_at();

drop trigger if exists set_agent_tasks_updated_at on public.agent_tasks;
create trigger set_agent_tasks_updated_at before update on public.agent_tasks
for each row execute function public.set_updated_at();

drop trigger if exists set_agent_budgets_updated_at on public.agent_budgets;
create trigger set_agent_budgets_updated_at before update on public.agent_budgets
for each row execute function public.set_updated_at();

drop trigger if exists set_agent_memory_updated_at on public.agent_memory;
create trigger set_agent_memory_updated_at before update on public.agent_memory
for each row execute function public.set_updated_at();

drop trigger if exists set_agent_eval_sets_updated_at on public.agent_eval_sets;
create trigger set_agent_eval_sets_updated_at before update on public.agent_eval_sets
for each row execute function public.set_updated_at();

drop trigger if exists set_agent_eval_cases_updated_at on public.agent_eval_cases;
create trigger set_agent_eval_cases_updated_at before update on public.agent_eval_cases
for each row execute function public.set_updated_at();

drop trigger if exists set_rate_limit_buckets_updated_at on public.rate_limit_buckets;
create trigger set_rate_limit_buckets_updated_at before update on public.rate_limit_buckets
for each row execute function public.set_updated_at();

alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.secret_refs enable row level security;
alter table public.integration_accounts enable row level security;
alter table public.agent_versions enable row level security;
alter table public.agent_profiles enable row level security;
alter table public.agent_tools enable row level security;
alter table public.agent_tool_permissions enable row level security;
alter table public.contacts enable row level security;
alter table public.conversations enable row level security;
alter table public.agent_messages enable row level security;
alter table public.workflow_definitions enable row level security;
alter table public.workflow_versions enable row level security;
alter table public.workflow_schedules enable row level security;
alter table public.agent_tasks enable row level security;
alter table public.agent_runs enable row level security;
alter table public.agent_run_steps enable row level security;
alter table public.agent_usage_events enable row level security;
alter table public.agent_budgets enable row level security;
alter table public.agent_approvals enable row level security;
alter table public.agent_memory enable row level security;
alter table public.agent_memory_embeddings enable row level security;
alter table public.agent_artifacts enable row level security;
alter table public.agent_events enable row level security;
alter table public.agent_audit_log enable row level security;
alter table public.agent_eval_sets enable row level security;
alter table public.agent_eval_cases enable row level security;
alter table public.agent_eval_runs enable row level security;
alter table public.agent_eval_results enable row level security;
alter table public.rate_limit_buckets enable row level security;

-- Seed a personal workspace and first platform agents/tools.
insert into public.workspaces (slug, name, owner_label)
values ('personal', 'Personal Agent Workspace', 'Solomon')
on conflict (slug) do nothing;

with workspace_row as (
  select id from public.workspaces where slug = 'personal'
)
insert into public.agent_profiles (workspace_id, slug, name, description, default_system_prompt)
select
  workspace_row.id,
  agent.slug,
  agent.name,
  agent.description,
  agent.system_prompt
from workspace_row
cross join (
  values
    ('router', 'Router Agent', 'Classifies requests and assigns work.', 'Route each request to the best agent, workflow, or tool.'),
    ('personal_assistant', 'Personal Assistant', 'General-purpose assistant that coordinates everyday requests.', 'Help the user complete practical tasks by using memory, contacts, research, scheduling, and communication tools.'),
    ('research_agent', 'Research Agent', 'Searches, reads, compares, and summarizes information.', 'Research topics carefully, cite useful sources in artifacts, and hand off communication when needed.'),
    ('youtube_researcher', 'YouTube Research Agent', 'Finds and evaluates YouTube videos.', 'Find high-quality videos and explain why they match the request.'),
    ('email_assistant', 'Email Assistant', 'Prepares and sends emails.', 'Write clear emails and send them only through approved tools.'),
    ('scheduler_agent', 'Scheduler Agent', 'Handles reminders, calendar tasks, and timed workflows.', 'Create reminders, schedule tasks, and coordinate calendar-related actions.'),
    ('memory_agent', 'Memory Agent', 'Stores and retrieves durable memory.', 'Save useful facts, preferences, and contact knowledge.'),
    ('workflow_manager', 'Workflow Manager', 'Coordinates multi-step jobs.', 'Break complex requests into ordered tasks and monitor completion.')
) as agent(slug, name, description, system_prompt)
on conflict (workspace_id, slug) do nothing;

with workspace_row as (
  select id from public.workspaces where slug = 'personal'
)
insert into public.agent_tools (workspace_id, slug, name, description, tool_type, requires_approval)
select
  workspace_row.id,
  tool.slug,
  tool.name,
  tool.description,
  tool.tool_type,
  tool.requires_approval
from workspace_row
cross join (
  values
    ('youtube_search', 'YouTube Search', 'Search YouTube for videos.', 'api', false),
    ('youtube_transcript', 'YouTube Transcript', 'Fetch or store video transcripts when available.', 'api', false),
    ('youtube_rank_videos', 'YouTube Rank Videos', 'Compare candidate videos and choose the best match.', 'internal', false),
    ('gmail_send', 'Gmail Send', 'Send email through Gmail SMTP.', 'api', true),
    ('gmail_draft', 'Gmail Draft', 'Prepare an email draft for review before sending.', 'api', false),
    ('gmail_read', 'Gmail Read', 'Read approved mailbox threads for context.', 'api', true),
    ('telegram_send', 'Telegram Send', 'Send Telegram messages back to the user or allowed chats.', 'api', false),
    ('contacts_lookup', 'Contacts Lookup', 'Resolve names and aliases to contact details.', 'database', false),
    ('contacts_write', 'Contacts Write', 'Create or update contact records and aliases.', 'database', true),
    ('memory_search', 'Memory Search', 'Retrieve saved agent memory.', 'database', false),
    ('memory_write', 'Memory Write', 'Save durable agent memory.', 'database', false),
    ('memory_update', 'Memory Update', 'Revise or deprecate saved memories.', 'database', true),
    ('web_search', 'Web Search', 'Search the web for current information.', 'api', false),
    ('web_fetch', 'Web Fetch', 'Fetch a specific URL for reading or summarization.', 'api', false),
    ('url_summarize', 'URL Summarize', 'Summarize a webpage, article, or document URL.', 'internal', false),
    ('calendar_create', 'Calendar Create', 'Create calendar events after approval.', 'api', true),
    ('calendar_list', 'Calendar List', 'Read calendar availability or upcoming events.', 'api', true),
    ('reminder_create', 'Reminder Create', 'Create reminders or scheduled follow-up tasks.', 'database', false),
    ('task_create', 'Task Create', 'Create a tracked agent task or subtask.', 'database', false),
    ('artifact_write', 'Artifact Write', 'Save summaries, reports, emails, links, or files as artifacts.', 'database', false),
    ('workflow_start', 'Workflow Start', 'Start a reusable multi-step workflow.', 'internal', false),
    ('cost_report', 'Cost Report', 'Report token usage, spend, latency, and run history.', 'database', false),
    ('approval_request', 'Approval Request', 'Ask a human to approve sensitive actions.', 'human', false)
) as tool(slug, name, description, tool_type, requires_approval)
on conflict (workspace_id, slug) do nothing;

with workspace_row as (
  select id from public.workspaces where slug = 'personal'
),
permissions as (
  select
    workspace_row.id as workspace_id,
    permission.agent_slug,
    permission.tool_slug,
    permission.permission_level
  from workspace_row
  cross join (
    values
      ('router', 'contacts_lookup', 'read'),
      ('router', 'memory_search', 'read'),
      ('router', 'task_create', 'execute'),
      ('router', 'workflow_start', 'execute'),
      ('router', 'approval_request', 'execute'),
      ('router', 'cost_report', 'read'),

      ('personal_assistant', 'contacts_lookup', 'read'),
      ('personal_assistant', 'contacts_write', 'execute'),
      ('personal_assistant', 'memory_search', 'read'),
      ('personal_assistant', 'memory_write', 'execute'),
      ('personal_assistant', 'web_search', 'execute'),
      ('personal_assistant', 'web_fetch', 'execute'),
      ('personal_assistant', 'url_summarize', 'execute'),
      ('personal_assistant', 'gmail_draft', 'execute'),
      ('personal_assistant', 'telegram_send', 'execute'),
      ('personal_assistant', 'reminder_create', 'execute'),
      ('personal_assistant', 'task_create', 'execute'),
      ('personal_assistant', 'artifact_write', 'execute'),
      ('personal_assistant', 'approval_request', 'execute'),

      ('research_agent', 'web_search', 'execute'),
      ('research_agent', 'web_fetch', 'execute'),
      ('research_agent', 'url_summarize', 'execute'),
      ('research_agent', 'youtube_search', 'execute'),
      ('research_agent', 'youtube_transcript', 'execute'),
      ('research_agent', 'youtube_rank_videos', 'execute'),
      ('research_agent', 'memory_search', 'read'),
      ('research_agent', 'artifact_write', 'execute'),
      ('research_agent', 'cost_report', 'read'),

      ('youtube_researcher', 'youtube_search', 'execute'),
      ('youtube_researcher', 'youtube_transcript', 'execute'),
      ('youtube_researcher', 'youtube_rank_videos', 'execute'),
      ('youtube_researcher', 'memory_search', 'read'),
      ('youtube_researcher', 'artifact_write', 'execute'),

      ('email_assistant', 'contacts_lookup', 'read'),
      ('email_assistant', 'gmail_draft', 'execute'),
      ('email_assistant', 'gmail_send', 'execute'),
      ('email_assistant', 'gmail_read', 'read'),
      ('email_assistant', 'approval_request', 'execute'),
      ('email_assistant', 'artifact_write', 'execute'),

      ('scheduler_agent', 'calendar_list', 'read'),
      ('scheduler_agent', 'calendar_create', 'execute'),
      ('scheduler_agent', 'reminder_create', 'execute'),
      ('scheduler_agent', 'task_create', 'execute'),
      ('scheduler_agent', 'approval_request', 'execute'),

      ('memory_agent', 'contacts_lookup', 'read'),
      ('memory_agent', 'contacts_write', 'execute'),
      ('memory_agent', 'memory_search', 'read'),
      ('memory_agent', 'memory_write', 'execute'),
      ('memory_agent', 'memory_update', 'execute'),
      ('memory_agent', 'artifact_write', 'execute'),

      ('workflow_manager', 'task_create', 'execute'),
      ('workflow_manager', 'workflow_start', 'execute'),
      ('workflow_manager', 'approval_request', 'execute'),
      ('workflow_manager', 'cost_report', 'read'),
      ('workflow_manager', 'artifact_write', 'execute')
  ) as permission(agent_slug, tool_slug, permission_level)
)
insert into public.agent_tool_permissions (agent_id, tool_id, permission_level)
select
  agent_profiles.id,
  agent_tools.id,
  permissions.permission_level
from permissions
join public.agent_profiles
  on agent_profiles.workspace_id = permissions.workspace_id
 and agent_profiles.slug = permissions.agent_slug
join public.agent_tools
  on agent_tools.workspace_id = permissions.workspace_id
 and agent_tools.slug = permissions.tool_slug
on conflict (agent_id, tool_id) do update
set permission_level = excluded.permission_level;
