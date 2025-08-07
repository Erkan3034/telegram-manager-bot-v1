-- Supabase SQL örnek şema (PostgreSQL)

create table if not exists public.users (
  telegram_user_id bigint primary key,
  username text,
  created_at timestamp with time zone default now()
);

create table if not exists public.questions (
  id uuid primary key default gen_random_uuid(),
  text text not null,
  order_index int not null
);

create unique index if not exists uq_questions_order on public.questions(order_index);

create table if not exists public.answers (
  id uuid primary key default gen_random_uuid(),
  telegram_user_id bigint not null references public.users(telegram_user_id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete cascade,
  answer_text text not null,
  created_at timestamp with time zone default now()
);

create table if not exists public.user_states (
  telegram_user_id bigint primary key references public.users(telegram_user_id) on delete cascade,
  current_order_index int
);

create table if not exists public.payments (
  telegram_user_id bigint primary key references public.users(telegram_user_id) on delete cascade,
  status text not null check (status in ('pending','approved','rejected')),
  receipt_url text,
  updated_at timestamp with time zone default now()
);

create table if not exists public.admin_states (
  admin_user_id bigint primary key,
  state text
);

create table if not exists public.members (
  telegram_user_id bigint primary key references public.users(telegram_user_id) on delete cascade,
  joined_at timestamp with time zone default now()
);

-- Storage: receipts bucket (UI'dan oluşturun) public olmalı.


