-- Clinic Booking System — Schema
-- Run this once in Supabase: Dashboard -> SQL Editor -> New query -> paste -> Run

-- pgcrypto gives us gen_random_uuid(), used as the default value for every id column
create extension if not exists pgcrypto;


-- 1. DOCTORS
create table doctors (
    id          uuid primary key default gen_random_uuid(),
    name        text not null,
    specialty   text,
    created_at  timestamptz not null default now()
);


-- 2. WORKING_HOURS
-- One row per doctor per weekday. day_of_week: 0 = Monday ... 6 = Sunday.
create table working_hours (
    id           uuid primary key default gen_random_uuid(),
    doctor_id    uuid not null references doctors(id) on delete cascade,
    day_of_week  smallint not null check (day_of_week between 0 and 6),
    start_time   time not null,
    end_time     time not null,
    check (end_time > start_time),
    unique (doctor_id, day_of_week)  -- a doctor can't have two working-hour blocks on the same weekday
);


-- 3. PATIENTS
create table patients (
    id          uuid primary key default gen_random_uuid(),
    name        text not null,
    email       text unique,
    created_at  timestamptz not null default now()
);


-- 4. APPOINTMENTS
create table appointments (
    id                   uuid primary key default gen_random_uuid(),
    doctor_id            uuid not null references doctors(id) on delete restrict,
    patient_id           uuid not null references patients(id) on delete restrict,
    start_time           timestamptz not null,
    end_time             timestamptz not null,
    status               text not null default 'booked' check (status in ('booked', 'cancelled')),
    cancellation_reason  text,
    created_at           timestamptz not null default now(),
    updated_at           timestamptz not null default now(),
    check (end_time > start_time)
);

-- THE CORE RULE: prevents two BOOKED appointments for the same doctor at the same start_time.
-- "where status = 'booked'" means cancelled appointments don't count toward the uniqueness check,
-- so a freed-up slot can be rebooked.
create unique index uq_doctor_slot_booked
    on appointments (doctor_id, start_time)
    where status = 'booked';

-- Speeds up the two queries we'll run constantly: availability lookups and a patient's appointment list
create index idx_appointments_doctor_date on appointments (doctor_id, start_time);
create index idx_appointments_patient on appointments (patient_id);
