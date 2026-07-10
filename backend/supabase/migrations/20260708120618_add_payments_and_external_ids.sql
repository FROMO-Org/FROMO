alter table events
  add column if not exists external_event_id varchar;

create unique index if not exists events_external_event_id_idx
  on events (external_event_id)
  where external_event_id is not null;

create table if not exists payments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id),
  event_id uuid not null references events(id),
  quantity int not null default 1 check (quantity > 0),
  amount_cents int not null check (amount_cents >= 0),
  currency varchar not null default 'eur',
  status varchar not null default 'pending'
    check (status in ('pending', 'paid', 'failed', 'cancelled', 'expired')),
  stripe_checkout_session_id varchar unique,
  stripe_payment_intent_id varchar unique,
  booking_id uuid unique references bookings(id),
  created_at timestamp default now(),
  updated_at timestamp default now()
);

create index if not exists payments_user_id_idx on payments(user_id);
create index if not exists payments_event_id_idx on payments(event_id);
create index if not exists payments_status_idx on payments(status);