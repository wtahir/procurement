create table if not exists orders (
    order_id text primary key,
    tenant_id text not null,
    status text not null,
    material_code text,
    qty numeric,
    region text,
    total_value numeric
);

create table if not exists audit_log (
    id bigserial primary key,
    order_id text not null,
    agent text not null,
    action text not null,
    reason text,
    ts timestamptz not null default now()
);

create table if not exists suppliers (
    supplier_id text primary key,
    name text not null,
    channel text not null,
    min_order numeric not null,
    reliability_score numeric not null default 1.0
);
