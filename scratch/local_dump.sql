--
-- PostgreSQL database dump
--

-- Dumped from database version 15.3
-- Dumped by pg_dump version 15.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: order_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.order_status_enum AS ENUM (
    'received',
    'pending',
    'preparing',
    'ready',
    'served',
    'completed',
    'cancelled'
);


--
-- Name: payment_method_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.payment_method_enum AS ENUM (
    'cash',
    'mpesa',
    'card',
    'bank_transfer'
);


--
-- Name: payment_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.payment_status_enum AS ENUM (
    'pending',
    'paid',
    'failed',
    'refunded',
    'partially_paid'
);


--
-- Name: session_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.session_status_enum AS ENUM (
    'active',
    'closed',
    'expired'
);


--
-- Name: shift_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.shift_type_enum AS ENUM (
    'morning',
    'afternoon',
    'evening',
    'night',
    'full'
);


--
-- Name: staff_role_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.staff_role_enum AS ENUM (
    'owner',
    'manager',
    'waiter',
    'chef',
    'cashier'
);


--
-- Name: subscription_plan_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.subscription_plan_enum AS ENUM (
    'starter',
    'pro',
    'enterprise'
);


--
-- Name: subscription_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.subscription_status_enum AS ENUM (
    'active',
    'expired',
    'trial'
);


--
-- Name: table_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.table_status_enum AS ENUM (
    'available',
    'occupied',
    'cleaning',
    'reserved',
    'ordering',
    'ordered',
    'ready',
    'eating',
    'bill_requested',
    'held'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activity_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activity_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    staff_id uuid,
    action text NOT NULL,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: branches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.branches (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid,
    name character varying(255) NOT NULL,
    address text,
    city character varying(100),
    phone character varying(20),
    email character varying(255),
    is_active boolean DEFAULT true,
    settings jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    name text NOT NULL,
    display_order integer NOT NULL,
    is_active boolean NOT NULL,
    branch_id uuid
);


--
-- Name: customer_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    table_id uuid NOT NULL,
    session_token text NOT NULL,
    customer_phone text,
    status public.session_status_enum NOT NULL,
    closed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    order_number character varying(50),
    device_fingerprint text,
    branch_id uuid
);


--
-- Name: floor_elements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.floor_elements (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    floor_id uuid,
    element_type character varying(50) NOT NULL,
    element_data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: floors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.floors (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid,
    name character varying(50) NOT NULL,
    display_order integer DEFAULT 0,
    is_active boolean DEFAULT true,
    background_image_url text,
    width integer DEFAULT 1200,
    height integer DEFAULT 800,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: item_transfers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.item_transfers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid,
    order_item_id uuid,
    from_session_id uuid,
    to_session_id uuid,
    transferred_by uuid,
    transferred_at timestamp with time zone DEFAULT now()
);


--
-- Name: kitchen_display_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kitchen_display_settings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    station_id uuid NOT NULL,
    sound_alerts_enabled boolean DEFAULT true NOT NULL,
    new_order_volume integer DEFAULT 70 NOT NULL,
    ready_order_volume integer DEFAULT 80 NOT NULL,
    theme character varying(20) DEFAULT 'dark'::character varying NOT NULL,
    font_size character varying(10) DEFAULT 'large'::character varying NOT NULL,
    show_timer boolean DEFAULT true NOT NULL,
    show_modifiers boolean DEFAULT true NOT NULL,
    auto_accept boolean DEFAULT false NOT NULL,
    prep_time_buffer_percent integer DEFAULT 10 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: kitchen_routing_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kitchen_routing_rules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    source_station_id uuid,
    target_station_id uuid NOT NULL,
    item_keyword character varying(100) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: kitchen_stations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kitchen_stations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(100),
    station_type character varying(50),
    display_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: menu_item_modifiers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_item_modifiers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    menu_item_id uuid NOT NULL,
    name text NOT NULL,
    price numeric(10,2) NOT NULL,
    is_available boolean NOT NULL
);


--
-- Name: menu_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu_items (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    category_id uuid NOT NULL,
    name text NOT NULL,
    description text,
    price numeric(10,2) NOT NULL,
    image_url text,
    is_available boolean NOT NULL,
    stock_quantity integer,
    low_stock_threshold integer NOT NULL,
    preparation_time integer DEFAULT 15 NOT NULL,
    is_popular boolean NOT NULL,
    calories integer,
    dietary_info jsonb,
    is_active boolean NOT NULL,
    display_order integer NOT NULL,
    station_id uuid,
    branch_id uuid,
    CONSTRAINT menu_items_price_check CHECK ((price >= (0)::numeric))
);


--
-- Name: mpesa_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mpesa_transactions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    checkout_request_id text NOT NULL,
    merchant_request_id text NOT NULL,
    phone_number text NOT NULL,
    amount numeric(10,2) NOT NULL,
    result_code integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    mpesa_receipt_number text,
    result_desc text
);


--
-- Name: order_item_modifiers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_item_modifiers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    order_item_id uuid NOT NULL,
    modifier_id uuid NOT NULL,
    price numeric(10,2) NOT NULL
);


--
-- Name: order_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_items (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    order_id uuid NOT NULL,
    menu_item_id uuid NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric(10,2) NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    special_instructions text,
    status public.order_status_enum NOT NULL,
    started_at timestamp with time zone,
    ready_at timestamp with time zone,
    estimated_start_at timestamp with time zone,
    estimated_ready_at timestamp with time zone,
    start_delay_seconds integer DEFAULT 0,
    is_held boolean DEFAULT false,
    hold_reason character varying(255),
    hold_resume_at timestamp with time zone,
    hold_started_at timestamp with time zone,
    is_paid boolean DEFAULT false,
    paid_at timestamp with time zone,
    course_number integer DEFAULT 1,
    is_fired boolean DEFAULT false,
    fired_at timestamp with time zone,
    course_name character varying(50)
);


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    table_id uuid,
    session_id uuid,
    staff_id uuid,
    order_number text NOT NULL,
    status public.order_status_enum NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    tax numeric(10,2) NOT NULL,
    total numeric(10,2) NOT NULL,
    payment_status public.payment_status_enum NOT NULL,
    payment_method public.payment_method_enum,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    waiter_notes text,
    customer_phone character varying(20),
    pacing_preference character varying(20) DEFAULT 'all_together'::character varying,
    branch_id uuid
);


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    order_id uuid NOT NULL,
    amount numeric(10,2) NOT NULL,
    payment_method public.payment_method_enum NOT NULL,
    status public.payment_status_enum NOT NULL,
    mpesa_receipt_number text,
    transaction_id text,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    mpesa_result_code integer,
    mpesa_result_description text,
    cash_received numeric(10,2),
    change_given numeric(10,2),
    cashier_id uuid,
    CONSTRAINT payments_amount_check CHECK ((amount > (0)::numeric))
);


--
-- Name: restaurant_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurant_settings (
    restaurant_id uuid NOT NULL,
    key text NOT NULL,
    value jsonb NOT NULL,
    auto_clear_ready_minutes integer DEFAULT 5,
    default_pacing character varying(20) DEFAULT 'let_customer_choose'::character varying,
    auto_fire_delay_minutes integer DEFAULT 15
);


--
-- Name: restaurants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restaurants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    subdomain text NOT NULL,
    phone text,
    email text,
    address text,
    logo_url text,
    prefix text NOT NULL,
    is_active boolean NOT NULL,
    is_onboarded boolean NOT NULL,
    status public.subscription_status_enum NOT NULL,
    subscription_plan public.subscription_plan_enum NOT NULL,
    trial_ends_at timestamp with time zone,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    parent_restaurant_id uuid,
    is_multi_branch boolean DEFAULT false
);


--
-- Name: staff; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.staff (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    full_name text NOT NULL,
    email text,
    phone text,
    role public.staff_role_enum NOT NULL,
    shift public.shift_type_enum NOT NULL,
    pin_code text NOT NULL,
    assigned_tables jsonb,
    is_active boolean NOT NULL,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    is_verified boolean DEFAULT false,
    kitchen_station character varying(50),
    kitchen_station_id uuid,
    branch_id uuid,
    role_type character varying(50) DEFAULT 'waiter'::character varying
);


--
-- Name: staff_activity_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.staff_activity_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    staff_id uuid NOT NULL,
    restaurant_id uuid NOT NULL,
    clock_in_at timestamp with time zone NOT NULL,
    clock_out_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: station_prep_times; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.station_prep_times (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    station_id uuid NOT NULL,
    item_category character varying(50) NOT NULL,
    default_seconds integer DEFAULT 600 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: table_transfer_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.table_transfer_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid,
    original_table_id uuid,
    new_table_id uuid,
    order_id uuid,
    transferred_by uuid,
    transferred_at timestamp with time zone DEFAULT now()
);


--
-- Name: table_transfers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.table_transfers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid,
    original_table_id uuid,
    new_table_id uuid,
    order_id uuid,
    transferred_by uuid,
    transferred_at timestamp with time zone DEFAULT now()
);


--
-- Name: tables; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tables (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    table_number integer NOT NULL,
    capacity integer NOT NULL,
    location text,
    status public.table_status_enum NOT NULL,
    current_session_id uuid,
    qr_code_url text,
    qr_code_token text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    occupied_since timestamp with time zone,
    last_status_change timestamp with time zone,
    status_history jsonb DEFAULT '[]'::jsonb,
    floor_id uuid,
    pos_x integer DEFAULT 0,
    pos_y integer DEFAULT 0,
    shape character varying(20) DEFAULT 'square'::character varying,
    width integer DEFAULT 80,
    height integer DEFAULT 80,
    branch_id uuid,
    CONSTRAINT tables_capacity_check CHECK ((capacity > 0))
);


--
-- Name: waiter_calls; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.waiter_calls (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    restaurant_id uuid NOT NULL,
    table_id uuid NOT NULL,
    message text,
    status text NOT NULL,
    acknowledged_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Data for Name: activity_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.activity_logs (id, restaurant_id, staff_id, action, metadata, created_at) FROM stdin;
d5d93600-8c21-4be2-9fa0-c48a054aee91	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	d73e0182-4322-444a-8199-a8861e545f72	login	\N	2026-05-07 23:16:39.068065+03
06fef8ca-0c88-452a-b7b1-4a3fbc6a80ca	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	d73e0182-4322-444a-8199-a8861e545f72	created_item_Cold Soda	\N	2026-05-07 23:16:40.959313+03
8219d457-968d-4999-9ee2-b2bd421eaefa	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	5b028260-312c-4319-9ab0-d9682841bda3	login	\N	2026-05-07 23:17:17.372771+03
9a88d536-7907-4ce0-9cc7-1755664a20d2	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	5b028260-312c-4319-9ab0-d9682841bda3	created_item_Cold Soda	\N	2026-05-07 23:17:19.045004+03
1941de08-8e77-465a-a83b-c06cac6b1159	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	c36a00c0-6800-4ba1-84c8-e660e76da3e6	login	\N	2026-05-07 23:18:26.429988+03
b95622d5-6e31-4f17-8f42-8a375a00b869	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	c36a00c0-6800-4ba1-84c8-e660e76da3e6	created_item_Cold Soda	\N	2026-05-07 23:18:28.091522+03
81dc318e-9640-4205-befa-86e5583d95ff	02de8b85-bc5b-4651-a33d-b8985011a099	29c3e073-3e91-469e-b1ab-de8f7ae6eaf5	login	\N	2026-05-07 23:19:26.807578+03
c60f2d1a-0dad-4120-87bd-8ebcba30917d	02de8b85-bc5b-4651-a33d-b8985011a099	29c3e073-3e91-469e-b1ab-de8f7ae6eaf5	created_item_Cold Soda	\N	2026-05-07 23:19:28.72455+03
b175445a-7459-4397-922b-e3d0043629a4	bf7d7043-ce4a-40a5-beed-c2789606f922	44f4430f-0b11-49df-a996-95bb6e770752	login	\N	2026-05-08 00:03:05.46526+03
860f4df3-5b89-4628-9a9c-b34f4083842f	bf7d7043-ce4a-40a5-beed-c2789606f922	44f4430f-0b11-49df-a996-95bb6e770752	created_item_Cold Soda	\N	2026-05-08 00:03:06.889884+03
bbecabd0-bf26-4f9a-9fa3-bb733082f4ca	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	54cbf982-7615-439c-91de-1b8a3a462e91	login	\N	2026-05-25 22:44:50.462946+03
571ae8a7-16e7-40be-ac5d-cee37b9c3500	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	54cbf982-7615-439c-91de-1b8a3a462e91	created_item_Cold Soda	\N	2026-05-25 22:44:52.752655+03
35c48091-8f21-4ec5-bd97-7710ba0e8a33	8bbc1483-4e02-4b06-a59d-d08b34b795b3	ba87634e-fdb6-424e-855b-26d431320ec1	login	\N	2026-05-25 22:58:05.015202+03
d4148f7f-9d73-48e6-b262-27b9cc142a78	85d9b191-1dbb-4245-aa75-8e2fff19766f	586efd0f-85ea-466d-bd23-9db0c79f53e0	login	\N	2026-05-25 23:33:20.626095+03
42b29e72-a836-4750-a63f-ec9e2f993f9a	85d9b191-1dbb-4245-aa75-8e2fff19766f	586efd0f-85ea-466d-bd23-9db0c79f53e0	created_item_Cold Soda	\N	2026-05-25 23:33:22.513241+03
37c38f10-d0f4-4f45-b4b5-49dbada4aaea	4be5e95a-46ec-4d3b-b57e-c3a08aeffb9c	8eff54df-99fd-4103-868f-5620966e316d	login	\N	2026-05-25 23:34:37.657425+03
1761b1ee-f472-4d8c-a550-029a84fbc2fd	8c436214-34b0-490d-b798-51349dce3728	39e9908f-d24d-44de-a009-23d5936e2443	login	\N	2026-05-26 00:28:19.838102+03
501933a2-cf36-40f8-b599-1576b339beb9	8c436214-34b0-490d-b798-51349dce3728	39e9908f-d24d-44de-a009-23d5936e2443	restaurant_updated	\N	2026-05-26 00:31:11.127602+03
d0c2804f-5cb1-41c1-be58-7bfdd0e79f3c	8c436214-34b0-490d-b798-51349dce3728	39e9908f-d24d-44de-a009-23d5936e2443	settings_updated	\N	2026-05-26 00:43:10.968635+03
1f63a807-6eee-46aa-9590-d502de9a9f11	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	4e1a5f19-c2a6-4477-a60b-b5d42a0a12db	login	\N	2026-05-26 23:40:41.002089+03
a0556bd6-6e67-4089-bffe-8d06fe3d0ea3	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	4e1a5f19-c2a6-4477-a60b-b5d42a0a12db	created_item_Cold Soda	\N	2026-05-26 23:40:43.038019+03
c4b8655e-fde8-444d-809b-28197a9dbefc	b39c5777-e4db-4d70-962e-1a92220ec9e9	1badbf86-e4d0-4da9-bede-8fd74062ac3d	login	\N	2026-05-26 23:45:05.378987+03
ccd34115-8053-433b-a897-75cb18b527c5	b39c5777-e4db-4d70-962e-1a92220ec9e9	1badbf86-e4d0-4da9-bede-8fd74062ac3d	created_item_Cold Soda	\N	2026-05-26 23:45:06.931791+03
29fc0ef2-085e-438a-a2f1-77ee30201559	7d13a11b-9373-4669-8d53-d2a041014c93	b63280b5-0253-4c82-a007-28d38a4dd10f	login	\N	2026-05-26 23:46:26.092797+03
be83df29-1220-4b68-a1dc-e85b62638993	7d13a11b-9373-4669-8d53-d2a041014c93	b63280b5-0253-4c82-a007-28d38a4dd10f	restaurant_updated	\N	2026-05-26 23:47:02.004151+03
e9bcab16-e40b-4757-83cf-e2b066aa43ba	5b7a69ce-beec-47b7-b006-f4151e77a7f3	7316a18c-92da-4bda-917b-6936359d8833	login	\N	2026-05-27 00:11:08.521341+03
3b04bac0-b166-4df0-a1c4-96d4bda9cae2	5b7a69ce-beec-47b7-b006-f4151e77a7f3	7316a18c-92da-4bda-917b-6936359d8833	created_item_Cold Soda	\N	2026-05-27 00:11:10.166126+03
851b6dd1-2a64-47c1-9042-61e975f28205	d7fc9094-3c1d-4eca-864d-6cf3009dea92	670136cd-e10e-4e9a-84d9-135180d7ea38	login	\N	2026-05-27 00:58:52.185271+03
a283acd2-1679-4e20-9fc2-3eb611ec1f73	d7fc9094-3c1d-4eca-864d-6cf3009dea92	670136cd-e10e-4e9a-84d9-135180d7ea38	created_item_Cold Soda	\N	2026-05-27 00:58:55.372328+03
e6f7e999-dac4-4fd3-b4ce-79a2771f1006	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	login	\N	2026-06-07 17:23:35.071221+03
a3554db1-58ec-492c-a33c-e055d70b67b1	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	restaurant_updated	\N	2026-06-07 17:25:00.035206+03
4bbf9bb1-8de2-419b-ba52-71b4b9ae4644	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	ai_menu_extraction_confirmed	{"categories_count": 4}	2026-06-07 21:44:43.005534+03
9813f984-dd06-4161-b1f1-b2838b1a2fe8	e50d5aac-c374-490a-8040-ae3ff526a264	d1a41c28-a376-4ba7-9591-fbff1d42dd56	staff_login	\N	2026-06-10 23:21:12.419681+03
7a5e90b4-5692-4a33-bab9-5512e50b698a	e50d5aac-c374-490a-8040-ae3ff526a264	7cdfc9d4-16f3-4b0d-801a-aa0d559a8a42	staff_login	\N	2026-06-10 23:22:11.685126+03
b7296848-a034-413e-af1f-f70f32a173e9	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-06-10 23:29:25.684248+03
3c1e11a0-8f20-4e79-86c6-95186bac5b95	e50d5aac-c374-490a-8040-ae3ff526a264	7cdfc9d4-16f3-4b0d-801a-aa0d559a8a42	staff_login	\N	2026-06-10 23:33:20.595761+03
0ccd7806-2419-492c-b728-41499b8ed1b3	e50d5aac-c374-490a-8040-ae3ff526a264	7cdfc9d4-16f3-4b0d-801a-aa0d559a8a42	order_status_ready	\N	2026-06-10 23:36:23.16479+03
80ef577d-a57c-43ae-aa9a-132995132f6c	e50d5aac-c374-490a-8040-ae3ff526a264	7cdfc9d4-16f3-4b0d-801a-aa0d559a8a42	order_status_ready	\N	2026-06-10 23:36:24.818844+03
702a60e9-4c62-424f-a055-91d04f346486	e50d5aac-c374-490a-8040-ae3ff526a264	7cdfc9d4-16f3-4b0d-801a-aa0d559a8a42	order_status_ready	\N	2026-06-10 23:36:26.687779+03
6889fa3c-9303-4bbd-b8d9-198e6f995d7e	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	83e4689d-2fb3-4e82-bc30-31c700ce5724	staff_login	\N	2026-06-10 23:37:58.765202+03
cd6bb27d-784b-4e35-88ed-a120c5a54214	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	54cbf982-7615-439c-91de-1b8a3a462e91	login	\N	2026-06-10 23:41:01.455443+03
36541cc3-5ffb-4043-bb0f-8523961167c5	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	login	\N	2026-06-10 23:44:46.253328+03
7380895a-b935-4871-8fbe-951fa64ddd6f	e50d5aac-c374-490a-8040-ae3ff526a264	596898c8-4980-4cce-97b6-bea366173065	staff_login	\N	2026-06-10 23:53:11.445689+03
b37febab-9723-4bfe-a131-a7316bb0e286	e50d5aac-c374-490a-8040-ae3ff526a264	596898c8-4980-4cce-97b6-bea366173065	staff_login	\N	2026-06-11 00:00:24.394222+03
d367298b-13bd-4c6a-8547-05cbd12050d7	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-06-11 00:03:18.048482+03
5c1da837-059c-4a08-ae1b-487969b3f506	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	d70b42c1-c748-4adb-ba03-9b40560ed749	login	\N	2026-06-11 00:03:38.618449+03
13500505-72e8-4584-9ab8-6e110af9b7f5	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	d70b42c1-c748-4adb-ba03-9b40560ed749	created_item_Cold Soda	\N	2026-06-11 00:03:42.78937+03
512f33b6-9e3b-4623-8ef8-7de32db8b3e3	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	54cbf982-7615-439c-91de-1b8a3a462e91	login	\N	2026-06-11 01:51:16.017825+03
306efa54-bcca-4492-85e6-16728f234e50	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	8fc1873c-546f-427f-9fe4-43ee8460f9f7	login	\N	2026-06-11 01:57:43.906046+03
58fc89cb-81ea-4f21-bcc4-e340efd56445	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	8fc1873c-546f-427f-9fe4-43ee8460f9f7	created_item_Cold Soda	\N	2026-06-11 01:57:48.276635+03
07329d30-eeb2-490f-a1ee-e1876877fd41	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-06-13 16:41:05.516025+03
908d994f-c4d7-406d-8b39-dd66c98b8fb1	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	login	\N	2026-06-13 16:41:15.42152+03
f699ea91-0b0c-4ee0-930c-2ee7d8f7b22b	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-06-13 16:42:35.112765+03
73c247d1-a703-4316-84d2-f9650d5a441b	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	order_status_ready	\N	2026-06-13 16:42:40.877616+03
d5d64ede-5de3-4032-ac9d-8c812f0545dd	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	order_status_ready	\N	2026-06-13 16:42:42.862171+03
ab86433c-a683-4253-b6dd-0d5475ece48d	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-06-13 22:32:05.554842+03
bf6f6467-0a39-403e-9ec7-3a48e1750b9a	c77f442c-89eb-4f66-b360-73270ea0e2ec	8931e935-7550-42b2-a020-44ce19284e8a	login	\N	2026-06-13 23:24:59.733194+03
e91215b5-cfce-4da1-98fa-bf13b6a3b6ba	a2c491c9-ead9-443d-8099-843e2901a3e9	03a6de53-568b-46e1-80fe-5d163bd2ecd2	login	\N	2026-06-13 23:27:08.735923+03
fbe2794a-f324-4c91-8f8f-59fa18706b0c	a2c491c9-ead9-443d-8099-843e2901a3e9	03a6de53-568b-46e1-80fe-5d163bd2ecd2	created_item_Cold Soda	\N	2026-06-13 23:27:11.194658+03
134719f3-2186-40e6-875b-83a6c06f6182	c79080f9-500d-4a40-893c-491e10860cc7	4fe63ccb-986e-4f39-8ddb-5f1bc9f0b919	login	\N	2026-06-13 23:28:48.096073+03
6ed4c830-1c72-4d77-9e00-e4bfc9a5de8d	c79080f9-500d-4a40-893c-491e10860cc7	4fe63ccb-986e-4f39-8ddb-5f1bc9f0b919	created_item_Cold Soda	\N	2026-06-13 23:28:49.83533+03
d6ac9815-ed5e-44a8-8042-ef43361b1d6a	c79080f9-500d-4a40-893c-491e10860cc7	4fe63ccb-986e-4f39-8ddb-5f1bc9f0b919	cash_payment_confirmed	{"order_id": "94b446c7-cf4f-40e0-a536-17a76a7de343", "payment_id": "1fad6e68-4d8c-490a-a5ee-6e7b1c873010", "change_given": 50.0, "amount_received": 224.0}	2026-06-13 23:28:51.48164+03
a83eb34a-5570-47fb-8722-e8348875bc7d	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	login	\N	2026-06-14 17:25:42.478259+03
81024ec9-df6e-4c3a-a89e-0ca887558fca	e50d5aac-c374-490a-8040-ae3ff526a264	596898c8-4980-4cce-97b6-bea366173065	staff_login	\N	2026-06-14 17:49:39.662773+03
2ce2ea66-bed4-4b8d-b1e2-69fb119c79b9	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-06-14 20:20:12.672872+03
b6c9001e-f60e-4acc-973f-174a70b2defa	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-06-14 21:52:47.998888+03
0c086902-fcee-4352-b7be-9be4f93f8449	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	login	\N	2026-06-15 22:49:13.997317+03
28f40fc8-1b7f-41be-b9bf-4592233117ff	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-06-15 23:06:21.442342+03
a3ee817b-b034-4a0a-9a66-e039dc891f11	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	login	\N	2026-07-13 18:51:27.630929+03
5aca1293-d536-4619-91f6-1e0f45e7fbbc	e50d5aac-c374-490a-8040-ae3ff526a264	75deb9da-d112-4945-90e1-4ed1462ef8a9	login	\N	2026-07-13 18:51:34.046956+03
afa746cd-50f2-4a5e-9e95-769500d8e4ea	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-07-13 18:56:06.183304+03
cb36b495-7142-4a6c-a2b3-b7621d289980	e50d5aac-c374-490a-8040-ae3ff526a264	\N	payment_received_pesapal_simulated	{"amount": 0.01, "order_id": "4370786a-411b-486a-a48b-52d4d18422c4"}	2026-07-13 20:48:10.302443+03
dee267b9-c23d-4773-8183-d4b17c311e02	e50d5aac-c374-490a-8040-ae3ff526a264	\N	payment_received_mpesa_simulated	{"amount": 0.0, "order_id": "0f248511-7816-4a61-a420-23fc6f656946"}	2026-07-13 22:58:33.840523+03
da2bfb91-75d8-4919-bc57-790541a6747c	e50d5aac-c374-490a-8040-ae3ff526a264	\N	payment_received_mpesa_simulated	{"amount": 0.0, "order_id": "005d115d-c13f-4a3a-b66c-23bd24256178"}	2026-07-13 23:18:14.239988+03
0ecbb6cd-dd59-46b0-8102-6fdc36b3e9ce	e50d5aac-c374-490a-8040-ae3ff526a264	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	staff_login	\N	2026-07-13 23:30:19.497481+03
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
8ee6ea06d509
\.


--
-- Data for Name: branches; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.branches (id, restaurant_id, name, address, city, phone, email, is_active, settings, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.categories (id, restaurant_id, name, display_order, is_active, branch_id) FROM stdin;
e26bd126-550a-40b0-8304-2110ee3e1489	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	Drinks	1	t	\N
5ef9b355-e536-42a8-9969-4d73dd359cf4	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	Drinks	1	t	\N
c7547459-bb75-4b4d-8351-c03296560b1d	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	Drinks	1	t	\N
8bf04362-cea2-4552-a5fb-beac237ea6ec	02de8b85-bc5b-4651-a33d-b8985011a099	Drinks	1	t	\N
bd5034b7-db63-4772-b389-6ffe0bc9d075	bf7d7043-ce4a-40a5-beed-c2789606f922	Drinks	1	t	\N
a5245619-8277-4be0-8009-aaf17c9064d1	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	Drinks	1	t	\N
c675b3e3-0829-43ff-a6d8-114164300547	85d9b191-1dbb-4245-aa75-8e2fff19766f	Drinks	1	t	\N
e627a04e-9a55-4e59-8760-892a05b37256	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	Drinks	1	t	\N
b55ffa38-4e29-43c0-9531-9b8c227c1405	b39c5777-e4db-4d70-962e-1a92220ec9e9	Drinks	1	t	\N
ef0dd6d8-3cd1-451c-a642-c8a817332aca	5b7a69ce-beec-47b7-b006-f4151e77a7f3	Drinks	1	t	\N
3d8a66be-768c-4a51-9dcb-518ccb1c728f	8c436214-34b0-490d-b798-51349dce3728	Drinks	1	t	\N
39902d17-378f-471c-93df-24a03e51074d	7d13a11b-9373-4669-8d53-d2a041014c93	Drinks	1	t	\N
6b818397-cb18-4660-b90e-2f17bb24d5cd	623d31eb-f986-4676-a38b-fca9c15a4636	Drinks	1	t	\N
d89d020c-77e9-4699-a5c4-82adfef7f43d	8bbc1483-4e02-4b06-a59d-d08b34b795b3	Drinks	1	t	\N
ff4812e5-f6c8-4820-9ab5-5b1e643b293c	d7fc9094-3c1d-4eca-864d-6cf3009dea92	Drinks	1	t	\N
6f9f0638-5e77-47ca-b6f7-528d0cdfb03f	e50d5aac-c374-490a-8040-ae3ff526a264	Burgers	0	t	\N
9c508f63-b140-4c13-ac6b-c2f2ad6cdc8a	e50d5aac-c374-490a-8040-ae3ff526a264	Snacks	0	t	\N
f903c4f3-40ff-4815-8d81-e48cde8ca9be	e50d5aac-c374-490a-8040-ae3ff526a264	Shakes	0	t	\N
9c7d09bb-86fc-4985-836f-8829d44ff6fc	e50d5aac-c374-490a-8040-ae3ff526a264	Desserts	0	t	\N
e06c9bad-3d26-4823-af44-2b27f5bb032f	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	Drinks	1	t	\N
92f2b446-bfd5-4da4-b236-532c785582e1	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	Drinks	1	t	\N
eb2dd113-4aed-41b1-9a0d-4cfb31ee24dd	c77f442c-89eb-4f66-b360-73270ea0e2ec	Drinks	1	t	\N
ca62c671-e366-4c15-9e6b-13c3ed6a9f55	a2c491c9-ead9-443d-8099-843e2901a3e9	Drinks	1	t	\N
3a9d25ef-7f74-4bd9-9325-41d0320b9830	c79080f9-500d-4a40-893c-491e10860cc7	Drinks	1	t	\N
\.


--
-- Data for Name: customer_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.customer_sessions (id, restaurant_id, table_id, session_token, customer_phone, status, closed_at, created_at, order_number, device_fingerprint, branch_id) FROM stdin;
7b4a3f6e-cc23-467c-8f67-1c9c88ac99d9	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	b0e986eb-86e7-434d-96ed-761a3956fb36	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzgxOTk0MDEsInN1YiI6ImIwZTk4NmViLTg2ZTctNDM0ZC05NmVkLTc2MWEzOTU2ZmIzNiIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6Ijg1NzhkYjA1LTYwZTgtNDllMy1hOWM1LTBjNWViOWY1YzUyOCJ9.JYZPIRB6exVC9os72im3uOfV5EemBqQcKiFVw7R71gI	\N	active	\N	2026-05-07 23:16:41.070644+03	\N	\N	\N
f0bb844b-dce8-487a-8159-10cd37c61340	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	3b8bd374-3146-4d16-af12-aaac148d91b6	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzgxOTk0MzksInN1YiI6IjNiOGJkMzc0LTMxNDYtNGQxNi1hZjEyLWFhYWMxNDhkOTFiNiIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImJmZDAyYWJiLTQwYmUtNDVlNi05ZmIwLWI1N2FhN2U3M2I5OCJ9.Bb_MnO7oxE_UGPJbHY46jcgzNYdXzA26yjQfRdjnN6s	\N	active	\N	2026-05-07 23:17:19.138018+03	\N	\N	\N
c10265a3-b32b-46e8-8475-6a14f5511ae0	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	11b74d86-c2ec-4f0a-8ac6-5c577e37c5c7	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzgxOTk1MDgsInN1YiI6IjExYjc0ZDg2LWMyZWMtNGYwYS04YWM2LTVjNTc3ZTM3YzVjNyIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6IjZkMTdlODdhLTRhNGItNDg2My1hOWE3LTdhZTFiNzA0M2JhNCJ9.2eHMMphfEjJfXBcIdI5X-SdBdl2bpjquAVYSHT3_t3g	\N	active	\N	2026-05-07 23:18:28.176157+03	\N	\N	\N
eb68be03-2c42-4afc-8cd0-7806e4ad3b00	02de8b85-bc5b-4651-a33d-b8985011a099	c6c1e5cd-26d7-46cf-8f2f-c12f50beba14	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzgxOTk1NjgsInN1YiI6ImM2YzFlNWNkLTI2ZDctNDZjZi04ZjJmLWMxMmY1MGJlYmExNCIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6IjAyZGU4Yjg1LWJjNWItNDY1MS1hMzNkLWI4OTg1MDExYTA5OSJ9.MZvh4QbhV6EpIlRKPDWaz1kq4BByj8xrxRdnlL5Esu8	\N	active	\N	2026-05-07 23:19:28.820452+03	\N	\N	\N
674b3ffe-d46e-4b80-b1af-1809c250f5e1	bf7d7043-ce4a-40a5-beed-c2789606f922	342ca64a-4456-4d4c-92a3-12cc454f17ed	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzgyMDIxODYsInN1YiI6IjM0MmNhNjRhLTQ0NTYtNGQ0Yy05MmEzLTEyY2M0NTRmMTdlZCIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImJmN2Q3MDQzLWNlNGEtNDBhNS1iZWVkLWMyNzg5NjA2ZjkyMiJ9.ULG1eBWZNoFLw1xQV8rruGa0AnbSfnUHYov2E6YcthM	\N	active	\N	2026-05-08 00:03:06.97958+03	\N	\N	\N
1bee3ad9-47b6-4337-a9e3-e0d821950b93	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	08f9a1ae-07fd-46ed-96be-a76a3b39c83c	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk3NTI2OTIsInN1YiI6IjA4ZjlhMWFlLTA3ZmQtNDZlZC05NmJlLWE3NmEzYjM5YzgzYyIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6IjAwZjRjM2Q0LTc5NTQtNGUzZS05ZDVkLWMwODZhMzFlYWIyYSJ9.Eh8ReACydyCl3aHxetBLjXLeD5Oo7on8OAEnT563AO4	\N	active	\N	2026-05-25 22:44:52.862829+03	\N	\N	\N
9545d1f4-be0c-41de-b8f1-de3cb6b2ae0b	85d9b191-1dbb-4245-aa75-8e2fff19766f	f67b44b5-d9a9-44e5-b766-b6bef06d6db0	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk3NTU2MDIsInN1YiI6ImY2N2I0NGI1LWQ5YTktNDRlNS1iNzY2LWI2YmVmMDZkNmRiMCIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6Ijg1ZDliMTkxLTFkYmItNDI0NS1hYTc1LThlMmZmZjE5NzY2ZiJ9.71YxryPGhDUcVlMA56fq92NzDf6E3fWKK9F8AYp00gY	\N	active	\N	2026-05-25 23:33:22.620283+03	\N	\N	\N
4a555c37-870a-4362-b712-e23b8c0e15ab	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	83f5ef90-d42e-4e74-8265-890137ef12f9	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk4NDI0NDMsInN1YiI6IjgzZjVlZjkwLWQ0MmUtNGU3NC04MjY1LTg5MDEzN2VmMTJmOSIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6IjNlYTU2N2FhLTRjZmMtNDY5Ny05ZWM5LWNmNGViMjNlZWM3NCJ9.bS-E5x_sPob8drtpUFTwi0VsRl907T1h16hwCj-wdF4	\N	active	\N	2026-05-26 23:40:43.134937+03	\N	\N	\N
5025765e-6da6-48db-9735-6ea5e9c8d696	b39c5777-e4db-4d70-962e-1a92220ec9e9	12691e11-36ca-48c1-9b4d-ae251a2511e0	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk4NDI3MDcsInN1YiI6IjEyNjkxZTExLTM2Y2EtNDhjMS05YjRkLWFlMjUxYTI1MTFlMCIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImIzOWM1Nzc3LWU0ZGItNGQ3MC05NjJlLTFhOTIyMjBlYzllOSJ9.GvoDxC_iFIrgLQIuSdX2wbg1G74GS-Zp_f0Dbw6YAbA	\N	active	\N	2026-05-26 23:45:07.018451+03	\N	\N	\N
2f5152fd-76f7-4dae-9c66-a33fd3ce5868	5b7a69ce-beec-47b7-b006-f4151e77a7f3	7b88cab2-7513-440a-b740-3bdca4cc03b8	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk4NDQyNzAsInN1YiI6IjdiODhjYWIyLTc1MTMtNDQwYS1iNzQwLTNiZGNhNGNjMDNiOCIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6IjViN2E2OWNlLWJlZWMtNDdiNy1iMDA2LWY0MTUxZTc3YTdmMyJ9.bCZg7oXF14Qw1JKrJp92aEfnFpuJbi2yGwXFfmETz2k	\N	active	\N	2026-05-27 00:11:10.239399+03	\N	\N	\N
9dafbef7-df1a-491c-aa96-5e6aaf7653ff	623d31eb-f986-4676-a38b-fca9c15a4636	58713c50-8732-4dd3-9d46-90513a52dbab	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk4NDY4MzcsInN1YiI6IjU4NzEzYzUwLTg3MzItNGRkMy05ZDQ2LTkwNTEzYTUyZGJhYiIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6IjYyM2QzMWViLWY5ODYtNDY3Ni1hMzhiLWZjYTljMTVhNDYzNiJ9.UVLgdeW2gqTc6c9ugXwcVvPTJ9xH5BEUgcD1zCn1KbU	\N	active	\N	2026-05-27 00:53:56.855986+03	\N	\N	\N
e2b44ef9-24b9-49e3-b564-82013b3dc9ae	7d13a11b-9373-4669-8d53-d2a041014c93	c94499b8-a67b-428f-b6ab-8434f56c60b7	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk4NDY4NTMsInN1YiI6ImM5NDQ5OWI4LWE2N2ItNDI4Zi1iNmFiLTg0MzRmNTZjNjBiNyIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6IjdkMTNhMTFiLTkzNzMtNDY2OS04ZDUzLWQyYTA0MTAxNGM5MyJ9.IDOKK2LSBGYSqmPkHNk1BTmz40u0IxBfuXJwp6YBvoU	\N	active	\N	2026-05-27 00:54:13.491655+03	\N	\N	\N
62a007a4-f63b-49f9-a133-ddd138bc77c4	d7fc9094-3c1d-4eca-864d-6cf3009dea92	8570fb78-0f53-4ca3-891b-9300fe00face	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzk4NDcxMzUsInN1YiI6Ijg1NzBmYjc4LTBmNTMtNGNhMy04OTFiLTkzMDBmZTAwZmFjZSIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImQ3ZmM5MDk0LTNjMWQtNGVjYS04NjRkLTZjZjMwMDlkZWE5MiJ9.M_nz7TuqG4gGR5o4wmtrxPp_X29b5anJv6Qag-DKBuc	\N	active	\N	2026-05-27 00:58:55.506119+03	\N	\N	\N
6e4d1d2f-6eb6-4767-acd1-abbd6720651a	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	3c43d5c8-4428-430b-ad01-ad9c2184108c	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODExMzk4MjIsInN1YiI6IjNjNDNkNWM4LTQ0MjgtNDMwYi1hZDAxLWFkOWMyMTg0MTA4YyIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImZjM2M3ZDczLTA2OTEtNGMyYi05OGE2LTNkMWZjMzlhMTdlMSJ9.PH4tyG9aWXLF68TD3wOooCxX1Ls1hQcWMdm5YeTRxnE	\N	active	\N	2026-06-11 00:03:42.961089+03	\N	\N	\N
07b6e885-1c97-4c65-989d-f9939659a49b	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	d3b9720d-9874-45c8-ba25-31f43bbd4fc7	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODExNDY2NjgsInN1YiI6ImQzYjk3MjBkLTk4NzQtNDVjOC1iYTI1LTMxZjQzYmJkNGZjNyIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImU4YjdlNDM0LWRhYjUtNDYyYi1hNmM1LWU1MWIxNzZiYjZjMCJ9.S-TPQO2dkBLy5msah7B_81W9b5I0v-6Avt8reShyTPE	\N	active	\N	2026-06-11 01:57:48.669927+03	\N	\N	\N
f34f0681-1aef-473b-9255-8fa87511e157	a2c491c9-ead9-443d-8099-843e2901a3e9	de8ea456-ea0a-467d-8a0e-01dddaaafef1	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODEzOTY4MzEsInN1YiI6ImRlOGVhNDU2LWVhMGEtNDY3ZC04YTBlLTAxZGRkYWFhZmVmMSIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImEyYzQ5MWM5LWVhZDktNDQzZC04MDk5LTg0M2UyOTAxYTNlOSJ9.OgN7ZRGhatzkyJdS9mSNRKdE8nsiFkK9k4w4fLkmzTo	\N	active	\N	2026-06-13 23:27:11.310599+03	\N	\N	\N
39c26be3-8d32-494f-a65c-2a9c1fba3651	c79080f9-500d-4a40-893c-491e10860cc7	8acb8e7e-d8a5-4c32-900c-dbcdaefc06a2	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODEzOTY5MjksInN1YiI6IjUzODVmMzVkLTY0NjAtNDhkNS05Mjk5LThlYjdkMmI1NmFkOSIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImM3OTA4MGY5LTUwMGQtNGE0MC04OTNjLTQ5MWUxMDg2MGNjNyJ9.lFuFnd8784DCVpnJTXtp7vPL_sMXXLzgf9yMLoWE8Zk	\N	active	\N	2026-06-13 23:28:49.921073+03	\N	\N	\N
0e6ca96d-c4cb-4551-9179-a2979fb452d0	e50d5aac-c374-490a-8040-ae3ff526a264	e31c0877-63fa-4613-9b0f-6d9e0a67bdd8	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODA5NjI4MzEsInN1YiI6IjU1OTYzNDc4LTI4OGEtNDBmYy1iYmRkLWVmMDk2Yzk4N2FiZiIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImU1MGQ1YWFjLWMzNzQtNDkwYS04MDQwLWFlM2ZmNTI2YTI2NCJ9.4yicrcFYmshwYBrIkK6qdJi0I4jFagjAIhah8XJEyoQ	\N	active	\N	2026-06-08 22:53:51.628377+03	\N	\N	\N
5199b9ab-d91a-4dad-8df9-138066187c7f	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODM5NzcyOTIsInN1YiI6IjU1OTYzNDc4LTI4OGEtNDBmYy1iYmRkLWVmMDk2Yzk4N2FiZiIsInR5cGUiOiJzZXNzaW9uIiwicmVzdGF1cmFudF9pZCI6ImU1MGQ1YWFjLWMzNzQtNDkwYS04MDQwLWFlM2ZmNTI2YTI2NCJ9.j2J0HGvhLWnVzNNFF_fIW1ClYrSVbdPhrsrvs3FktRg	0769491949	active	\N	2026-07-13 20:14:52.626738+03	\N	\N	\N
\.


--
-- Data for Name: floor_elements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.floor_elements (id, floor_id, element_type, element_data, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: floors; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.floors (id, restaurant_id, name, display_order, is_active, background_image_url, width, height, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: item_transfers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.item_transfers (id, restaurant_id, order_item_id, from_session_id, to_session_id, transferred_by, transferred_at) FROM stdin;
\.


--
-- Data for Name: kitchen_display_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.kitchen_display_settings (id, restaurant_id, station_id, sound_alerts_enabled, new_order_volume, ready_order_volume, theme, font_size, show_timer, show_modifiers, auto_accept, prep_time_buffer_percent, created_at, updated_at) FROM stdin;
dfda3497-5c3f-4c96-aa05-71ac132cc452	e50d5aac-c374-490a-8040-ae3ff526a264	bb3c6bb9-172a-42aa-99b4-23230caf29ec	t	70	89	light	large	t	t	t	10	2026-06-13 18:04:27.055401+03	2026-06-13 18:06:35.195649+03
d1d00136-19f8-43f0-b73a-74ed8ae9c9cf	e50d5aac-c374-490a-8040-ae3ff526a264	d7f50300-730d-478a-9441-de8273050b02	t	70	80	dark	large	t	t	f	10	2026-06-13 18:07:48.680555+03	2026-06-13 18:07:48.680555+03
2b3c418d-5f7e-47a2-82de-9514ba15d67f	e50d5aac-c374-490a-8040-ae3ff526a264	18a60cb5-aa25-41b3-9c13-c6541dba0a4d	t	70	80	dark	large	t	t	f	10	2026-06-13 18:08:54.022797+03	2026-06-13 18:08:54.022797+03
9102a004-4d9c-441b-a0f9-58cd16ccef45	e50d5aac-c374-490a-8040-ae3ff526a264	b07f8936-1908-4a67-8414-1d8dd4f99979	t	70	80	dark	large	t	t	f	10	2026-06-13 18:09:58.378792+03	2026-06-13 18:09:58.378792+03
f66dfb20-215f-4225-a6fc-596f731ab848	e50d5aac-c374-490a-8040-ae3ff526a264	179d55c4-1493-4d6f-ace1-d9f5d64ddcf2	t	70	80	dark	large	t	t	f	10	2026-06-13 18:11:15.92641+03	2026-06-13 18:11:15.92641+03
21fb52ff-6bf9-495c-8435-0b8430821e6c	e50d5aac-c374-490a-8040-ae3ff526a264	9974007d-b0f3-4bf3-8fd0-a7e06fd599c7	t	70	80	dark	large	t	t	f	10	2026-06-13 18:12:02.876661+03	2026-06-13 18:12:02.876661+03
18008208-d069-4284-b39e-14b8ac3b5c9d	e50d5aac-c374-490a-8040-ae3ff526a264	4b2c6bec-b0b7-4b98-8f0f-52d050f121cd	t	70	80	dark	large	t	t	f	10	2026-06-13 18:12:46.386707+03	2026-06-13 18:12:46.386707+03
\.


--
-- Data for Name: kitchen_routing_rules; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.kitchen_routing_rules (id, restaurant_id, source_station_id, target_station_id, item_keyword, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: kitchen_stations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.kitchen_stations (id, restaurant_id, name, display_name, station_type, display_order, is_active, created_at, updated_at) FROM stdin;
b07f8936-1908-4a67-8414-1d8dd4f99979	e50d5aac-c374-490a-8040-ae3ff526a264	Pastry Station	Bakery	pastry	3	t	2026-06-13 18:09:58.364042+03	2026-06-13 18:09:58.364042+03
18a60cb5-aa25-41b3-9c13-c6541dba0a4d	e50d5aac-c374-490a-8040-ae3ff526a264	Espresso Bar	Barista & Juice	drinks	2	t	2026-06-13 18:08:54.014429+03	2026-06-13 18:10:08.130911+03
179d55c4-1493-4d6f-ace1-d9f5d64ddcf2	e50d5aac-c374-490a-8040-ae3ff526a264	Dessert	Dessert	dessert	4	t	2026-06-13 18:11:15.918812+03	2026-06-13 18:11:15.918812+03
9974007d-b0f3-4bf3-8fd0-a7e06fd599c7	e50d5aac-c374-490a-8040-ae3ff526a264	Fry  Station	Fry Station	fry	4	t	2026-06-13 18:12:02.863892+03	2026-06-13 18:12:02.863892+03
4b2c6bec-b0b7-4b98-8f0f-52d050f121cd	e50d5aac-c374-490a-8040-ae3ff526a264	Grill Station	Nyama Choma	grill	7	t	2026-06-13 18:12:46.366729+03	2026-06-13 18:12:46.366729+03
bb3c6bb9-172a-42aa-99b4-23230caf29ec	e50d5aac-c374-490a-8040-ae3ff526a264	Main Kitchen	Main Kitchen	hot	0	t	2026-06-13 18:04:26.955622+03	2026-06-13 20:12:46.548535+03
d7f50300-730d-478a-9441-de8273050b02	e50d5aac-c374-490a-8040-ae3ff526a264	Cold Kitchen	Salads & Wraps	cold	1	t	2026-06-13 18:07:48.655429+03	2026-06-13 20:12:46.551286+03
\.


--
-- Data for Name: menu_item_modifiers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_item_modifiers (id, restaurant_id, menu_item_id, name, price, is_available) FROM stdin;
\.


--
-- Data for Name: menu_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu_items (id, restaurant_id, category_id, name, description, price, image_url, is_available, stock_quantity, low_stock_threshold, preparation_time, is_popular, calories, dietary_info, is_active, display_order, station_id, branch_id) FROM stdin;
5c385bbc-728a-4721-be86-3908714e48e8	8c436214-34b0-490d-b798-51349dce3728	3d8a66be-768c-4a51-9dcb-518ccb1c728f	KES 1.00 Live Test Payment	Simulated Live Test payment item for PlateLink Africa verification.	1.00	\N	t	1000	5	5	t	\N	\N	t	1	\N	\N
af33adb7-fdf7-4949-9887-e0820232fe71	7d13a11b-9373-4669-8d53-d2a041014c93	39902d17-378f-471c-93df-24a03e51074d	KES 1.00 Live Test Payment	Simulated Live Test payment item for PlateLink Africa verification.	1.00	\N	t	1000	5	5	t	\N	\N	t	1	\N	\N
54947ced-5984-4042-bf0c-b504b23487fb	623d31eb-f986-4676-a38b-fca9c15a4636	6b818397-cb18-4660-b90e-2f17bb24d5cd	KES 1.00 Live Test Payment	Simulated Live Test payment item for PlateLink Africa verification.	1.00	\N	t	1000	5	5	t	\N	\N	t	1	\N	\N
93525e8d-2f5d-45f0-a8f3-8283fb8961a1	8bbc1483-4e02-4b06-a59d-d08b34b795b3	d89d020c-77e9-4699-a5c4-82adfef7f43d	KES 1.00 Live Test Payment	Simulated Live Test payment item for PlateLink Africa verification.	1.00	\N	t	1000	5	5	t	\N	\N	t	1	\N	\N
80f7a912-d3f0-468f-b26e-b710da52ea05	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	e26bd126-550a-40b0-8304-2110ee3e1489	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
3598d88d-2444-4163-9a0d-ced08691f3fc	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	5ef9b355-e536-42a8-9969-4d73dd359cf4	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
ba167465-06cc-4504-941b-5d10f96fee17	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	c7547459-bb75-4b4d-8351-c03296560b1d	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
14e039e1-99bd-4444-a3f1-7c6950f3aa1d	02de8b85-bc5b-4651-a33d-b8985011a099	8bf04362-cea2-4552-a5fb-beac237ea6ec	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
29b1f28f-62fd-48de-a80c-fb9100fe30b6	bf7d7043-ce4a-40a5-beed-c2789606f922	bd5034b7-db63-4772-b389-6ffe0bc9d075	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
e94acc88-e3e5-4f20-9b49-eae47ddfbd79	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	a5245619-8277-4be0-8009-aaf17c9064d1	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
fe7b7071-4893-4088-b49e-51da0d099620	85d9b191-1dbb-4245-aa75-8e2fff19766f	c675b3e3-0829-43ff-a6d8-114164300547	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
44ead896-bd08-4b4f-b16c-934f259cdf58	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	e627a04e-9a55-4e59-8760-892a05b37256	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
8e57c010-d8f3-4e91-9cf7-a1ce581a6619	b39c5777-e4db-4d70-962e-1a92220ec9e9	b55ffa38-4e29-43c0-9531-9b8c227c1405	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
1984d18c-af15-45f3-a3af-58617959444c	5b7a69ce-beec-47b7-b006-f4151e77a7f3	ef0dd6d8-3cd1-451c-a642-c8a817332aca	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
5ac1001f-8203-4da9-bb63-89bca61893aa	d7fc9094-3c1d-4eca-864d-6cf3009dea92	ff4812e5-f6c8-4820-9ab5-5b1e643b293c	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
9bed665e-c0ca-4412-9f5b-065bd532cc24	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	e06c9bad-3d26-4823-af44-2b27f5bb032f	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
3e5ca84d-3a0c-4ad0-91dd-7bb6bb537a17	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	92f2b446-bfd5-4da4-b236-532c785582e1	Cold Soda	\N	150.00	\N	t	\N	5	15	f	\N	null	t	0	\N	\N
19698748-4474-4fc3-b9c3-0294de3f65e3	e50d5aac-c374-490a-8040-ae3ff526a264	6f9f0638-5e77-47ca-b6f7-528d0cdfb03f	Big Arch	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	bb3c6bb9-172a-42aa-99b4-23230caf29ec	\N
f7e53e0c-1cd5-4716-bf71-6db968bfdbb8	e50d5aac-c374-490a-8040-ae3ff526a264	6f9f0638-5e77-47ca-b6f7-528d0cdfb03f	Surf 'N' Turf	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	bb3c6bb9-172a-42aa-99b4-23230caf29ec	\N
f03211af-137a-482d-b1e3-6cdad9a69722	e50d5aac-c374-490a-8040-ae3ff526a264	6f9f0638-5e77-47ca-b6f7-528d0cdfb03f	Chicken Big Mac	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	4b2c6bec-b0b7-4b98-8f0f-52d050f121cd	\N
a9e4d90d-c380-45f5-b91b-661b328424e8	e50d5aac-c374-490a-8040-ae3ff526a264	9c508f63-b140-4c13-ac6b-c2f2ad6cdc8a	Chili Cheese Bites	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	bb3c6bb9-172a-42aa-99b4-23230caf29ec	\N
07e6e4d1-92d3-46b5-a936-b5c0b58dfeb4	e50d5aac-c374-490a-8040-ae3ff526a264	6f9f0638-5e77-47ca-b6f7-528d0cdfb03f	Chicken Cheeseburger	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	4b2c6bec-b0b7-4b98-8f0f-52d050f121cd	\N
0b7e6757-89d4-47bc-b003-b302cc2f3f0e	e50d5aac-c374-490a-8040-ae3ff526a264	9c7d09bb-86fc-4985-836f-8829d44ff6fc	Apple Pie Mini McFlurry	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	b07f8936-1908-4a67-8414-1d8dd4f99979	\N
74e39b8c-eb89-4da9-a0e5-c413aa96caca	e50d5aac-c374-490a-8040-ae3ff526a264	f903c4f3-40ff-4815-8d81-e48cde8ca9be	Eraser Milkshake	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	18a60cb5-aa25-41b3-9c13-c6541dba0a4d	\N
f1418e33-71ee-4892-8740-987005611a39	e50d5aac-c374-490a-8040-ae3ff526a264	9c7d09bb-86fc-4985-836f-8829d44ff6fc	Galaxy Stretch Caramel McFlurry	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	bb3c6bb9-172a-42aa-99b4-23230caf29ec	\N
b93fd2d0-a1fb-4110-b2f7-214f7c693651	e50d5aac-c374-490a-8040-ae3ff526a264	9c7d09bb-86fc-4985-836f-8829d44ff6fc	Big Mac® Sauce Dip	\N	0.00	\N	t	\N	5	15	f	\N	\N	t	0	bb3c6bb9-172a-42aa-99b4-23230caf29ec	\N
7a3accd8-ebb3-4d07-9644-8968705627ea	a2c491c9-ead9-443d-8099-843e2901a3e9	ca62c671-e366-4c15-9e6b-13c3ed6a9f55	Cold Soda	\N	150.00	\N	t	\N	5	10	f	\N	null	t	0	\N	\N
4f2edd42-70ce-44ad-b92d-dd71276e28cf	c79080f9-500d-4a40-893c-491e10860cc7	3a9d25ef-7f74-4bd9-9325-41d0320b9830	Cold Soda	\N	150.00	\N	t	\N	5	10	f	\N	null	t	0	\N	\N
\.


--
-- Data for Name: mpesa_transactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.mpesa_transactions (id, restaurant_id, checkout_request_id, merchant_request_id, phone_number, amount, result_code, created_at, mpesa_receipt_number, result_desc) FROM stdin;
c21cd6ae-fde9-4d94-a3a8-b4b324ff0003	e50d5aac-c374-490a-8040-ae3ff526a264	ws_CO_MOCK_692af7bc6095	MR_MOCK_7278b9ce66df	254769491949	0.00	0	2026-07-13 22:58:29.930895+03	MOCK275DDB	The service request is processed successfully. (SIMULATED)
f3d20ff5-dcac-4b64-a6af-58bbee0865ea	e50d5aac-c374-490a-8040-ae3ff526a264	ws_CO_MOCK_87af1c76ab59	MR_MOCK_ad75e0bf7982	254769491949	0.00	0	2026-07-13 23:18:11.119253+03	MOCKFF732F	The service request is processed successfully. (SIMULATED)
\.


--
-- Data for Name: order_item_modifiers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_item_modifiers (id, restaurant_id, order_item_id, modifier_id, price) FROM stdin;
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.order_items (id, order_id, menu_item_id, quantity, unit_price, subtotal, special_instructions, status, started_at, ready_at, estimated_start_at, estimated_ready_at, start_delay_seconds, is_held, hold_reason, hold_resume_at, hold_started_at, is_paid, paid_at, course_number, is_fired, fired_at, course_name) FROM stdin;
aaf0546b-2565-40e7-b322-50717309c384	2d3b8834-5fdb-47af-8876-1cb53ae97011	3598d88d-2444-4163-9a0d-ced08691f3fc	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
d4b79a09-640e-43df-9be5-6c17ba5e4a2b	e82eabd0-a12f-4838-9bc8-e1b3226ebaec	ba167465-06cc-4504-941b-5d10f96fee17	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
57ec4c44-093b-4806-8385-b28dc933815a	a8985a05-eb00-4001-a204-3459d655e1f9	14e039e1-99bd-4444-a3f1-7c6950f3aa1d	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
d351aaeb-9404-4280-8283-6462fd347a78	871cdc34-b279-4541-a072-e01b57a52730	29b1f28f-62fd-48de-a80c-fb9100fe30b6	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
af6ab57a-74ef-4dae-b82b-5243f437608e	80d9c7aa-3f97-498b-a221-bb7aebe69fb1	e94acc88-e3e5-4f20-9b49-eae47ddfbd79	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
405833a8-615f-4e6c-a7c8-414ebf1d63e7	641eb46e-2c3c-4826-8385-c89881028ec8	fe7b7071-4893-4088-b49e-51da0d099620	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
802bb2ee-3498-412e-8344-a987770bb8ea	184e6d5e-92c5-4fda-bcf4-dc769ee448c3	44ead896-bd08-4b4f-b16c-934f259cdf58	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
fa2aae4b-d882-4c10-a893-29dee2b59ee3	379d40a3-8aef-45c1-bbbc-2420a4894249	8e57c010-d8f3-4e91-9cf7-a1ce581a6619	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
a1f1a8d4-7a9d-4448-b1c5-2d8f15d0d5e7	785ef853-67d3-4657-b93c-eca2ffd089a4	1984d18c-af15-45f3-a3af-58617959444c	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
b25f2751-b832-4513-b043-3516f7b42e1f	662c4e94-7752-489f-b48b-10027358d5b7	5ac1001f-8203-4da9-bb63-89bca61893aa	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
da79db6e-0f07-444c-9a03-ef0efee55558	32f159d8-84cf-4103-921a-8a25c7bc0f4b	54947ced-5984-4042-bf0c-b504b23487fb	1	1.00	1.00	njnnbjbnhjgbhgbyygvb	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
1ac6f3ab-aaa0-4059-80dd-6df3e838e65f	bfe05c8a-4ed6-41cd-94df-84435c0246b9	54947ced-5984-4042-bf0c-b504b23487fb	1	1.00	1.00	njnnbjbnhjgbhgbyygvb	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
cd150dad-c0a8-4c25-83f4-8be14296d186	d1eb85e2-c65e-4398-810d-8584b5afd2df	54947ced-5984-4042-bf0c-b504b23487fb	1	1.00	1.00	njnnbjbnhjgbhgbyygvb	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
59a152b8-03ef-4191-b69d-6f4d14d9543b	ef62c4c0-2e61-420a-9ba1-a478f456eb61	9bed665e-c0ca-4412-9f5b-065bd532cc24	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
d5ebab35-e499-4e19-98a1-44a25ab20c98	e086235f-0fa1-494a-b2a6-57f315a4cac6	3e5ca84d-3a0c-4ad0-91dd-7bb6bb537a17	2	150.00	300.00	Very cold	received	\N	\N	\N	\N	0	f	\N	\N	\N	f	\N	1	f	\N	\N
4a1ff844-a356-4dd7-9d14-0b86663c47ad	2695b4ca-6d13-43ea-9e71-d01d64894153	7a3accd8-ebb3-4d07-9644-8968705627ea	2	150.00	300.00	Very cold	received	\N	\N	2026-06-13 23:27:11.368171+03	2026-06-13 23:37:11.368171+03	0	f	\N	\N	\N	f	\N	1	f	\N	\N
7579ba0d-626f-4d41-b84c-231d240b62c8	94b446c7-cf4f-40e0-a536-17a76a7de343	4f2edd42-70ce-44ad-b92d-dd71276e28cf	2	150.00	300.00	Very cold	received	\N	\N	2026-06-13 23:28:49.969718+03	2026-06-13 23:38:49.969718+03	0	f	\N	\N	\N	f	\N	1	f	\N	\N
e41f8e71-8ee6-48fa-8f94-0907996bef58	005d115d-c13f-4a3a-b66c-23bd24256178	f03211af-137a-482d-b1e3-6cdad9a69722	1	0.00	0.00		received	\N	\N	2026-07-13 23:18:09.453396+03	2026-07-13 23:33:09.453396+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 20:18:09.557399+03	Mains
a1947607-366e-4c43-9b44-a15e98641e12	005d115d-c13f-4a3a-b66c-23bd24256178	0b7e6757-89d4-47bc-b003-b302cc2f3f0e	1	0.00	0.00		received	\N	\N	2026-07-13 23:18:09.453396+03	2026-07-13 23:33:09.453396+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 20:18:09.568399+03	Desserts
b8b81e47-307a-4816-b38a-9fc1c76c0f8d	005d115d-c13f-4a3a-b66c-23bd24256178	07e6e4d1-92d3-46b5-a936-b5c0b58dfeb4	1	0.00	0.00		received	\N	\N	2026-07-13 23:18:09.453396+03	2026-07-13 23:33:09.453396+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 20:18:09.579443+03	Mains
c38a7cf1-f374-42a2-abfc-4b35c3a6c4af	29960d21-48fc-496b-8f8e-a6d4b4bef89f	b93fd2d0-a1fb-4110-b2f7-214f7c693651	1	0.00	0.00		ready	\N	2026-07-13 20:32:56.401681+03	2026-07-13 20:35:55.083493+03	2026-07-13 20:50:55.083493+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 17:35:55.125493+03	Desserts
3c9d827d-6080-49c6-82a1-d8cb40d063ce	9978d447-4470-4546-888a-8d2b153b6574	f7e53e0c-1cd5-4716-bf71-6db968bfdbb8	1	0.00	0.00		ready	\N	2026-07-13 20:30:41.110214+03	2026-07-13 20:21:00.905724+03	2026-07-13 20:36:00.905724+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 17:21:00.97102+03	Mains
273db3b0-6aba-4b4e-9039-1a2a06e206f9	9978d447-4470-4546-888a-8d2b153b6574	b93fd2d0-a1fb-4110-b2f7-214f7c693651	1	0.00	0.00		ready	\N	2026-07-13 20:30:43.298438+03	2026-07-13 20:21:00.905724+03	2026-07-13 20:36:00.905724+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 17:21:00.981022+03	Desserts
5d1e9819-913c-428e-96f4-7045dd1ecc0b	9978d447-4470-4546-888a-8d2b153b6574	19698748-4474-4fc3-b9c3-0294de3f65e3	1	0.00	0.00		ready	\N	2026-07-13 20:32:48.160248+03	2026-07-13 20:21:00.905724+03	2026-07-13 20:36:00.905724+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 17:21:00.951737+03	Mains
93aac657-7ea0-4ffc-98c9-a91d74767ac5	48d5cdfc-b185-4857-89a5-4e960ebf9c0b	19698748-4474-4fc3-b9c3-0294de3f65e3	1	0.00	0.00		ready	\N	2026-07-13 20:32:51.925977+03	2026-07-13 20:21:27.322561+03	2026-07-13 20:36:27.322561+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 17:21:27.330561+03	Mains
ad91a162-376b-4292-802f-4abfe7f859ae	48d5cdfc-b185-4857-89a5-4e960ebf9c0b	f7e53e0c-1cd5-4716-bf71-6db968bfdbb8	1	0.00	0.00		ready	\N	2026-07-13 20:32:53.052458+03	2026-07-13 20:21:27.322561+03	2026-07-13 20:36:27.322561+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 17:21:27.338565+03	Mains
f2b79334-d6fa-4f0a-a676-05d71ae90bb8	48d5cdfc-b185-4857-89a5-4e960ebf9c0b	b93fd2d0-a1fb-4110-b2f7-214f7c693651	1	0.00	0.00		ready	\N	2026-07-13 20:32:53.759232+03	2026-07-13 20:21:27.322561+03	2026-07-13 20:36:27.322561+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 17:21:27.346562+03	Desserts
fb27c0cd-e78e-4fd0-a547-5de31f9743cc	48d5cdfc-b185-4857-89a5-4e960ebf9c0b	f1418e33-71ee-4892-8740-987005611a39	1	0.00	0.00		ready	\N	2026-07-13 20:32:54.30465+03	2026-07-13 20:21:27.322561+03	2026-07-13 20:36:27.322561+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 17:21:27.354584+03	Desserts
5a078fde-ca66-4bb6-a6d8-f7b48ebd9bcc	29960d21-48fc-496b-8f8e-a6d4b4bef89f	19698748-4474-4fc3-b9c3-0294de3f65e3	1	0.00	0.00		ready	\N	2026-07-13 20:32:55.157851+03	2026-07-13 20:35:55.083493+03	2026-07-13 20:50:55.083493+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 17:35:55.106492+03	Mains
81ee0a15-40f8-4003-a170-46459244d75d	29960d21-48fc-496b-8f8e-a6d4b4bef89f	f7e53e0c-1cd5-4716-bf71-6db968bfdbb8	1	0.00	0.00		ready	\N	2026-07-13 20:32:55.874503+03	2026-07-13 20:35:55.083493+03	2026-07-13 20:50:55.083493+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 17:35:55.120495+03	Mains
952558ef-d504-48c8-9372-51554b94edd1	29960d21-48fc-496b-8f8e-a6d4b4bef89f	f1418e33-71ee-4892-8740-987005611a39	1	0.00	0.00		ready	\N	2026-07-13 20:32:56.878339+03	2026-07-13 20:35:55.083493+03	2026-07-13 20:50:55.083493+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 17:35:55.131514+03	Desserts
02beda97-9677-40b3-b012-e6d0e6feedef	4370786a-411b-486a-a48b-52d4d18422c4	19698748-4474-4fc3-b9c3-0294de3f65e3	1	0.00	0.00		ready	\N	2026-07-13 20:32:57.862705+03	2026-07-13 20:44:50.823235+03	2026-07-13 20:59:50.823235+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 17:44:50.879982+03	Mains
83fc59c6-f321-4ca7-a574-c8fa8fcc2491	0f248511-7816-4a61-a420-23fc6f656946	a9e4d90d-c380-45f5-b91b-661b328424e8	1	0.00	0.00		ready	\N	2026-07-13 20:33:03.117123+03	2026-07-13 22:58:28.071813+03	2026-07-13 23:13:28.071813+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 19:58:28.205645+03	Mains
609bf469-737b-42bf-a8c9-0b2cc57d24fd	4370786a-411b-486a-a48b-52d4d18422c4	f7e53e0c-1cd5-4716-bf71-6db968bfdbb8	1	0.00	0.00		ready	\N	2026-07-13 20:32:58.796088+03	2026-07-13 20:44:50.823235+03	2026-07-13 20:59:50.823235+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 17:44:50.897977+03	Mains
42aa187a-ee45-4c6b-b17e-810b854b066c	4370786a-411b-486a-a48b-52d4d18422c4	b93fd2d0-a1fb-4110-b2f7-214f7c693651	1	0.00	0.00		ready	\N	2026-07-13 20:33:00.297011+03	2026-07-13 20:44:50.823235+03	2026-07-13 20:59:50.823235+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 17:44:50.905978+03	Desserts
0ccf0f49-bda5-4398-b1ce-2e491f31c87b	0f248511-7816-4a61-a420-23fc6f656946	f1418e33-71ee-4892-8740-987005611a39	2	0.00	0.00		ready	\N	2026-07-13 20:33:03.890488+03	2026-07-13 22:58:28.071813+03	2026-07-13 23:13:28.071813+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 19:58:28.196645+03	Desserts
1586dff7-be5c-41fe-9cbe-93547a54ef39	0f248511-7816-4a61-a420-23fc6f656946	b93fd2d0-a1fb-4110-b2f7-214f7c693651	1	0.00	0.00		ready	\N	2026-07-13 20:33:04.390326+03	2026-07-13 22:58:28.071813+03	2026-07-13 23:13:28.071813+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 19:58:28.19233+03	Desserts
d95c53e9-7899-44bd-8046-697d701bb44c	0f248511-7816-4a61-a420-23fc6f656946	f7e53e0c-1cd5-4716-bf71-6db968bfdbb8	1	0.00	0.00		ready	\N	2026-07-13 20:33:04.956019+03	2026-07-13 22:58:28.071813+03	2026-07-13 23:13:28.071813+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 19:58:28.184333+03	Mains
03ddae25-dd8c-44de-b947-2b63f0f0a4c7	9978d447-4470-4546-888a-8d2b153b6574	f1418e33-71ee-4892-8740-987005611a39	1	0.00	0.00		ready	\N	2026-07-13 20:33:07.036639+03	2026-07-13 20:21:00.905724+03	2026-07-13 20:36:00.905724+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 17:21:00.98702+03	Desserts
d3f64b14-af20-499b-96e9-bcb5d3cf6bb9	005d115d-c13f-4a3a-b66c-23bd24256178	a9e4d90d-c380-45f5-b91b-661b328424e8	1	0.00	0.00		ready	\N	2026-07-13 20:33:08.760657+03	2026-07-13 23:18:09.453396+03	2026-07-13 23:33:09.453396+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 20:18:09.588398+03	Mains
8161b107-5755-48ca-aaaf-5ce99f479eaf	005d115d-c13f-4a3a-b66c-23bd24256178	19698748-4474-4fc3-b9c3-0294de3f65e3	1	0.00	0.00		ready	\N	2026-07-13 20:33:09.271406+03	2026-07-13 23:18:09.453396+03	2026-07-13 23:33:09.453396+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 20:18:09.543412+03	Mains
e684c3ac-8a8e-4060-86f6-22212e283a14	4370786a-411b-486a-a48b-52d4d18422c4	f1418e33-71ee-4892-8740-987005611a39	1	0.00	0.00		ready	\N	2026-07-13 20:33:01.655728+03	2026-07-13 20:44:50.823235+03	2026-07-13 20:59:50.823235+03	0	f	\N	\N	\N	f	\N	3	t	2026-07-13 17:44:50.91398+03	Desserts
6fe88f3f-707b-4c39-8e46-32d2ea587823	0f248511-7816-4a61-a420-23fc6f656946	19698748-4474-4fc3-b9c3-0294de3f65e3	1	0.00	0.00		ready	\N	2026-07-13 20:33:14.37068+03	2026-07-13 22:58:28.071813+03	2026-07-13 23:13:28.071813+03	0	f	\N	\N	\N	f	\N	2	t	2026-07-13 19:58:28.164809+03	Mains
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orders (id, restaurant_id, table_id, session_id, staff_id, order_number, status, subtotal, tax, total, payment_status, payment_method, completed_at, created_at, waiter_notes, customer_phone, pacing_preference, branch_id) FROM stdin;
2d3b8834-5fdb-47af-8876-1cb53ae97011	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	3b8bd374-3146-4d16-af12-aaac148d91b6	f0bb844b-dce8-487a-8159-10cd37c61340	\N	EFD0507231719	received	300.00	48.00	348.00	pending	mpesa	\N	2026-05-07 23:17:19.172675+03	\N	\N	all_together	\N
e82eabd0-a12f-4838-9bc8-e1b3226ebaec	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	11b74d86-c2ec-4f0a-8ac6-5c577e37c5c7	c10265a3-b32b-46e8-8475-6a14f5511ae0	\N	ACA0507231828	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-07 23:18:28.21298+03	\N	\N	all_together	\N
a8985a05-eb00-4001-a204-3459d655e1f9	02de8b85-bc5b-4651-a33d-b8985011a099	c6c1e5cd-26d7-46cf-8f2f-c12f50beba14	eb68be03-2c42-4afc-8cd0-7806e4ad3b00	\N	A780507231928	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-07 23:19:28.861074+03	\N	\N	all_together	\N
871cdc34-b279-4541-a072-e01b57a52730	bf7d7043-ce4a-40a5-beed-c2789606f922	342ca64a-4456-4d4c-92a3-12cc454f17ed	674b3ffe-d46e-4b80-b1af-1809c250f5e1	\N	F200508000307	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-08 00:03:07.015888+03	\N	\N	all_together	\N
80d9c7aa-3f97-498b-a221-bb7aebe69fb1	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	08f9a1ae-07fd-46ed-96be-a76a3b39c83c	1bee3ad9-47b6-4337-a9e3-e0d821950b93	\N	E560525224452	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-25 22:44:52.907668+03	\N	\N	all_together	\N
641eb46e-2c3c-4826-8385-c89881028ec8	85d9b191-1dbb-4245-aa75-8e2fff19766f	f67b44b5-d9a9-44e5-b766-b6bef06d6db0	9545d1f4-be0c-41de-b8f1-de3cb6b2ae0b	\N	8CA0525233322	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-25 23:33:22.669689+03	\N	\N	all_together	\N
184e6d5e-92c5-4fda-bcf4-dc769ee448c3	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	83f5ef90-d42e-4e74-8265-890137ef12f9	4a555c37-870a-4362-b712-e23b8c0e15ab	\N	6E20526234043	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-26 23:40:43.221377+03	\N	\N	all_together	\N
379d40a3-8aef-45c1-bbbc-2420a4894249	b39c5777-e4db-4d70-962e-1a92220ec9e9	12691e11-36ca-48c1-9b4d-ae251a2511e0	5025765e-6da6-48db-9735-6ea5e9c8d696	\N	5FA0526234507	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-26 23:45:07.061516+03	\N	\N	all_together	\N
785ef853-67d3-4657-b93c-eca2ffd089a4	5b7a69ce-beec-47b7-b006-f4151e77a7f3	7b88cab2-7513-440a-b740-3bdca4cc03b8	2f5152fd-76f7-4dae-9c66-a33fd3ce5868	\N	1950527001110	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-27 00:11:10.274209+03	\N	\N	all_together	\N
662c4e94-7752-489f-b48b-10027358d5b7	d7fc9094-3c1d-4eca-864d-6cf3009dea92	8570fb78-0f53-4ca3-891b-9300fe00face	62a007a4-f63b-49f9-a133-ddd138bc77c4	\N	41B0527005855	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-05-27 00:58:55.577298+03	\N	\N	all_together	\N
29960d21-48fc-496b-8f8e-a6d4b4bef89f	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	5199b9ab-d91a-4dad-8df9-138066187c7f	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	5D60713203555	served	0.00	0.00	0.00	pending	card	\N	2026-07-13 20:35:55.032077+03	\N	\N	all_together	\N
bfe05c8a-4ed6-41cd-94df-84435c0246b9	e50d5aac-c374-490a-8040-ae3ff526a264	e31c0877-63fa-4613-9b0f-6d9e0a67bdd8	0e6ca96d-c4cb-4551-9179-a2979fb452d0	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	5D60609014054	completed	1.00	0.16	1.16	paid	cash	2026-06-15 20:09:48.833795+03	2026-06-09 01:40:54.586792+03	\N	\N	all_together	\N
32f159d8-84cf-4103-921a-8a25c7bc0f4b	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	0e6ca96d-c4cb-4551-9179-a2979fb452d0	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	5D60609000827	completed	1.00	0.16	1.16	paid	cash	2026-06-15 20:11:26.917866+03	2026-06-09 00:08:27.606299+03	\N	\N	all_together	\N
ef62c4c0-2e61-420a-9ba1-a478f456eb61	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	3c43d5c8-4428-430b-ad01-ad9c2184108c	6e4d1d2f-6eb6-4767-acd1-abbd6720651a	\N	5780611000343	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-06-11 00:03:43.03675+03	\N	\N	all_together	\N
e086235f-0fa1-494a-b2a6-57f315a4cac6	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	d3b9720d-9874-45c8-ba25-31f43bbd4fc7	07b6e885-1c97-4c65-989d-f9939659a49b	\N	A400611015748	preparing	300.00	48.00	348.00	pending	mpesa	\N	2026-06-11 01:57:48.865009+03	\N	\N	all_together	\N
2695b4ca-6d13-43ea-9e71-d01d64894153	a2c491c9-ead9-443d-8099-843e2901a3e9	de8ea456-ea0a-467d-8a0e-01dddaaafef1	f34f0681-1aef-473b-9255-8fa87511e157	\N	2630613232711	received	300.00	48.00	348.00	pending	mpesa	\N	2026-06-13 23:27:11.356345+03	\N	\N	all_together	\N
94b446c7-cf4f-40e0-a536-17a76a7de343	c79080f9-500d-4a40-893c-491e10860cc7	8acb8e7e-d8a5-4c32-900c-dbcdaefc06a2	39c26be3-8d32-494f-a65c-2a9c1fba3651	\N	5510613232849	preparing	300.00	48.00	348.00	partially_paid	mpesa	\N	2026-06-13 23:28:49.959663+03	Extra cold soda please	\N	all_together	\N
d1eb85e2-c65e-4398-810d-8584b5afd2df	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	0e6ca96d-c4cb-4551-9179-a2979fb452d0	\N	5D60609014911	completed	1.00	0.16	1.16	paid	cash	2026-06-14 18:53:25.425715+03	2026-06-09 01:49:11.036992+03	\N	\N	all_together	\N
005d115d-c13f-4a3a-b66c-23bd24256178	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	5199b9ab-d91a-4dad-8df9-138066187c7f	\N	5D60713231809	preparing	0.00	0.00	0.00	paid	mpesa	\N	2026-07-13 23:18:09.359497+03	\N	\N	all_together	\N
0f248511-7816-4a61-a420-23fc6f656946	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	5199b9ab-d91a-4dad-8df9-138066187c7f	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	5D60713225828	served	0.00	0.00	0.00	paid	mpesa	\N	2026-07-13 22:58:27.895251+03	\N	\N	all_together	\N
4370786a-411b-486a-a48b-52d4d18422c4	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	5199b9ab-d91a-4dad-8df9-138066187c7f	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	5D60713204450	served	0.00	0.00	0.00	paid	card	\N	2026-07-13 20:44:50.744991+03	\N	\N	all_together	\N
9978d447-4470-4546-888a-8d2b153b6574	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	5199b9ab-d91a-4dad-8df9-138066187c7f	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	5D60713202100	served	0.00	0.00	0.00	pending	card	\N	2026-07-13 20:21:00.869456+03	\N	\N	all_together	\N
48d5cdfc-b185-4857-89a5-4e960ebf9c0b	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	5199b9ab-d91a-4dad-8df9-138066187c7f	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	5D60713202127	served	0.00	0.00	0.00	pending	card	\N	2026-07-13 20:21:27.299597+03	\N	\N	all_together	\N
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payments (id, restaurant_id, order_id, amount, payment_method, status, mpesa_receipt_number, transaction_id, completed_at, created_at, mpesa_result_code, mpesa_result_description, cash_received, change_given, cashier_id) FROM stdin;
8d4b4c4c-2010-4b40-b5f9-da27d24c5f92	e50d5aac-c374-490a-8040-ae3ff526a264	32f159d8-84cf-4103-921a-8a25c7bc0f4b	1.16	card	pending	\N	115c759e-3b1a-4f7c-9038-da4856e966f2	\N	2026-06-09 01:36:52.217656+03	\N	\N	\N	\N	\N
c09e3f4b-50cc-4adf-96ae-5d8e8e90019b	e50d5aac-c374-490a-8040-ae3ff526a264	bfe05c8a-4ed6-41cd-94df-84435c0246b9	1.16	card	pending	\N	b1221c12-afff-4d5d-ace3-da487b54a211	\N	2026-06-09 01:40:54.650405+03	\N	\N	\N	\N	\N
e4c38306-de97-4bf0-9de8-b3c8a9f770ea	e50d5aac-c374-490a-8040-ae3ff526a264	d1eb85e2-c65e-4398-810d-8584b5afd2df	1.16	card	pending	\N	04fcf0b8-864a-43b6-936a-da48ff22d5ec	\N	2026-06-09 01:49:11.233272+03	\N	\N	\N	\N	\N
c3868b90-abfd-415a-a4f6-381d8e80ac08	e50d5aac-c374-490a-8040-ae3ff526a264	d1eb85e2-c65e-4398-810d-8584b5afd2df	1.16	card	pending	\N	04fcf0b8-864a-43b6-936a-da48ff22d5ec	\N	2026-06-09 01:49:12.822625+03	\N	\N	\N	\N	\N
42551e2f-5178-4d0f-908a-4e4c2cd23e5c	c79080f9-500d-4a40-893c-491e10860cc7	94b446c7-cf4f-40e0-a536-17a76a7de343	174.00	cash	pending	\N	SPLIT-5510613232849-2-5736A3	\N	2026-06-13 23:28:51.43154+03	\N	\N	\N	\N	\N
1fad6e68-4d8c-490a-a5ee-6e7b1c873010	c79080f9-500d-4a40-893c-491e10860cc7	94b446c7-cf4f-40e0-a536-17a76a7de343	174.00	cash	paid	\N	SPLIT-5510613232849-1-4F71BE	2026-06-13 20:28:51.496491+03	2026-06-13 23:28:51.43154+03	\N	\N	224.00	50.00	4fe63ccb-986e-4f39-8ddb-5f1bc9f0b919
03487705-e08b-4bad-ac8e-e7f4c638ddb6	e50d5aac-c374-490a-8040-ae3ff526a264	d1eb85e2-c65e-4398-810d-8584b5afd2df	1.16	cash	paid	\N	CASH-8f30e73b-1d3f-4f7f-984c-4a64a661d8ed-20260614185325	\N	2026-06-14 21:53:25.401615+03	\N	\N	2.00	0.84	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed
ed6adcf9-9325-4b17-9191-a4cd574fe78b	e50d5aac-c374-490a-8040-ae3ff526a264	bfe05c8a-4ed6-41cd-94df-84435c0246b9	1.16	cash	paid	\N	CASH-8f30e73b-1d3f-4f7f-984c-4a64a661d8ed-20260615200948	\N	2026-06-15 23:09:48.800744+03	\N	\N	177.00	175.84	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed
6e3429eb-94f5-4f00-bdc7-aea911ad365a	e50d5aac-c374-490a-8040-ae3ff526a264	32f159d8-84cf-4103-921a-8a25c7bc0f4b	1.16	cash	paid	\N	CASH-8f30e73b-1d3f-4f7f-984c-4a64a661d8ed-20260615201126	\N	2026-06-15 23:11:26.889035+03	\N	\N	177.00	175.84	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed
f9017910-55ca-4598-93f8-a973028512e7	e50d5aac-c374-490a-8040-ae3ff526a264	4370786a-411b-486a-a48b-52d4d18422c4	0.01	card	paid	MOCK89545C	pesapal_mock_1046276c9e04	2026-07-13 17:48:10.32189+03	2026-07-13 20:48:07.239381+03	\N	\N	\N	\N	\N
40701cde-ed74-4496-8ac0-64004db47267	e50d5aac-c374-490a-8040-ae3ff526a264	0f248511-7816-4a61-a420-23fc6f656946	0.01	mpesa	paid	MOCK275DDB	ws_CO_MOCK_692af7bc6095	2026-07-13 19:58:33.882053+03	2026-07-13 22:58:29.930895+03	\N	\N	\N	\N	\N
4bba3063-1374-4b82-b296-8eeacc37ac34	e50d5aac-c374-490a-8040-ae3ff526a264	005d115d-c13f-4a3a-b66c-23bd24256178	0.01	mpesa	paid	MOCKFF732F	ws_CO_MOCK_87af1c76ab59	2026-07-13 20:18:15.375742+03	2026-07-13 23:18:11.119253+03	\N	\N	\N	\N	\N
\.


--
-- Data for Name: restaurant_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.restaurant_settings (restaurant_id, key, value, auto_clear_ready_minutes, default_pacing, auto_fire_delay_minutes) FROM stdin;
8c436214-34b0-490d-b798-51349dce3728	paybill_number	"174379"	5	let_customer_choose	15
8c436214-34b0-490d-b798-51349dce3728	consumer_key	"gA848yAwAAdG4g1K7783u167gAaG8A1g"	5	let_customer_choose	15
8c436214-34b0-490d-b798-51349dce3728	consumer_secret	"A123456789ABCDEF"	5	let_customer_choose	15
8c436214-34b0-490d-b798-51349dce3728	passkey	"bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"	5	let_customer_choose	15
7d13a11b-9373-4669-8d53-d2a041014c93	certificate_url	"https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=platelink"	5	let_customer_choose	15
e50d5aac-c374-490a-8040-ae3ff526a264	kds_settings	{"enable_alarms": true, "alert_threshold_minutes": 10}	5	let_customer_choose	15
8578db05-60e8-49e3-a9c5-0c5eb9f5c528	floor_plan_grid_size	20	5	let_customer_choose	15
bfd02abb-40be-45e6-9fb0-b57aa7e73b98	floor_plan_grid_size	20	5	let_customer_choose	15
6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	floor_plan_grid_size	20	5	let_customer_choose	15
02de8b85-bc5b-4651-a33d-b8985011a099	floor_plan_grid_size	20	5	let_customer_choose	15
bf7d7043-ce4a-40a5-beed-c2789606f922	floor_plan_grid_size	20	5	let_customer_choose	15
00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	floor_plan_grid_size	20	5	let_customer_choose	15
85d9b191-1dbb-4245-aa75-8e2fff19766f	floor_plan_grid_size	20	5	let_customer_choose	15
4be5e95a-46ec-4d3b-b57e-c3a08aeffb9c	floor_plan_grid_size	20	5	let_customer_choose	15
8c436214-34b0-490d-b798-51349dce3728	floor_plan_grid_size	20	5	let_customer_choose	15
3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	floor_plan_grid_size	20	5	let_customer_choose	15
b39c5777-e4db-4d70-962e-1a92220ec9e9	floor_plan_grid_size	20	5	let_customer_choose	15
5b7a69ce-beec-47b7-b006-f4151e77a7f3	floor_plan_grid_size	20	5	let_customer_choose	15
8bbc1483-4e02-4b06-a59d-d08b34b795b3	floor_plan_grid_size	20	5	let_customer_choose	15
623d31eb-f986-4676-a38b-fca9c15a4636	floor_plan_grid_size	20	5	let_customer_choose	15
7d13a11b-9373-4669-8d53-d2a041014c93	floor_plan_grid_size	20	5	let_customer_choose	15
d7fc9094-3c1d-4eca-864d-6cf3009dea92	floor_plan_grid_size	20	5	let_customer_choose	15
e50d5aac-c374-490a-8040-ae3ff526a264	floor_plan_grid_size	20	5	let_customer_choose	15
fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	floor_plan_grid_size	20	5	let_customer_choose	15
e8b7e434-dab5-462b-a6c5-e51b176bb6c0	floor_plan_grid_size	20	5	let_customer_choose	15
c77f442c-89eb-4f66-b360-73270ea0e2ec	floor_plan_grid_size	20	5	let_customer_choose	15
a2c491c9-ead9-443d-8099-843e2901a3e9	floor_plan_grid_size	20	5	let_customer_choose	15
c79080f9-500d-4a40-893c-491e10860cc7	floor_plan_grid_size	20	5	let_customer_choose	15
f215eb25-4250-4483-9d6f-30bc2adf475e	floor_plan_grid_size	20	5	let_customer_choose	15
8578db05-60e8-49e3-a9c5-0c5eb9f5c528	floor_plan_snap_enabled	true	5	let_customer_choose	15
bfd02abb-40be-45e6-9fb0-b57aa7e73b98	floor_plan_snap_enabled	true	5	let_customer_choose	15
6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	floor_plan_snap_enabled	true	5	let_customer_choose	15
02de8b85-bc5b-4651-a33d-b8985011a099	floor_plan_snap_enabled	true	5	let_customer_choose	15
bf7d7043-ce4a-40a5-beed-c2789606f922	floor_plan_snap_enabled	true	5	let_customer_choose	15
00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	floor_plan_snap_enabled	true	5	let_customer_choose	15
85d9b191-1dbb-4245-aa75-8e2fff19766f	floor_plan_snap_enabled	true	5	let_customer_choose	15
4be5e95a-46ec-4d3b-b57e-c3a08aeffb9c	floor_plan_snap_enabled	true	5	let_customer_choose	15
8c436214-34b0-490d-b798-51349dce3728	floor_plan_snap_enabled	true	5	let_customer_choose	15
3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	floor_plan_snap_enabled	true	5	let_customer_choose	15
b39c5777-e4db-4d70-962e-1a92220ec9e9	floor_plan_snap_enabled	true	5	let_customer_choose	15
5b7a69ce-beec-47b7-b006-f4151e77a7f3	floor_plan_snap_enabled	true	5	let_customer_choose	15
8bbc1483-4e02-4b06-a59d-d08b34b795b3	floor_plan_snap_enabled	true	5	let_customer_choose	15
623d31eb-f986-4676-a38b-fca9c15a4636	floor_plan_snap_enabled	true	5	let_customer_choose	15
7d13a11b-9373-4669-8d53-d2a041014c93	floor_plan_snap_enabled	true	5	let_customer_choose	15
d7fc9094-3c1d-4eca-864d-6cf3009dea92	floor_plan_snap_enabled	true	5	let_customer_choose	15
e50d5aac-c374-490a-8040-ae3ff526a264	floor_plan_snap_enabled	true	5	let_customer_choose	15
fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	floor_plan_snap_enabled	true	5	let_customer_choose	15
e8b7e434-dab5-462b-a6c5-e51b176bb6c0	floor_plan_snap_enabled	true	5	let_customer_choose	15
c77f442c-89eb-4f66-b360-73270ea0e2ec	floor_plan_snap_enabled	true	5	let_customer_choose	15
a2c491c9-ead9-443d-8099-843e2901a3e9	floor_plan_snap_enabled	true	5	let_customer_choose	15
c79080f9-500d-4a40-893c-491e10860cc7	floor_plan_snap_enabled	true	5	let_customer_choose	15
f215eb25-4250-4483-9d6f-30bc2adf475e	floor_plan_snap_enabled	true	5	let_customer_choose	15
8578db05-60e8-49e3-a9c5-0c5eb9f5c528	floor_plan_show_grid	true	5	let_customer_choose	15
bfd02abb-40be-45e6-9fb0-b57aa7e73b98	floor_plan_show_grid	true	5	let_customer_choose	15
6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	floor_plan_show_grid	true	5	let_customer_choose	15
02de8b85-bc5b-4651-a33d-b8985011a099	floor_plan_show_grid	true	5	let_customer_choose	15
bf7d7043-ce4a-40a5-beed-c2789606f922	floor_plan_show_grid	true	5	let_customer_choose	15
00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	floor_plan_show_grid	true	5	let_customer_choose	15
85d9b191-1dbb-4245-aa75-8e2fff19766f	floor_plan_show_grid	true	5	let_customer_choose	15
4be5e95a-46ec-4d3b-b57e-c3a08aeffb9c	floor_plan_show_grid	true	5	let_customer_choose	15
8c436214-34b0-490d-b798-51349dce3728	floor_plan_show_grid	true	5	let_customer_choose	15
3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	floor_plan_show_grid	true	5	let_customer_choose	15
b39c5777-e4db-4d70-962e-1a92220ec9e9	floor_plan_show_grid	true	5	let_customer_choose	15
5b7a69ce-beec-47b7-b006-f4151e77a7f3	floor_plan_show_grid	true	5	let_customer_choose	15
8bbc1483-4e02-4b06-a59d-d08b34b795b3	floor_plan_show_grid	true	5	let_customer_choose	15
623d31eb-f986-4676-a38b-fca9c15a4636	floor_plan_show_grid	true	5	let_customer_choose	15
7d13a11b-9373-4669-8d53-d2a041014c93	floor_plan_show_grid	true	5	let_customer_choose	15
d7fc9094-3c1d-4eca-864d-6cf3009dea92	floor_plan_show_grid	true	5	let_customer_choose	15
e50d5aac-c374-490a-8040-ae3ff526a264	floor_plan_show_grid	true	5	let_customer_choose	15
fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	floor_plan_show_grid	true	5	let_customer_choose	15
e8b7e434-dab5-462b-a6c5-e51b176bb6c0	floor_plan_show_grid	true	5	let_customer_choose	15
c77f442c-89eb-4f66-b360-73270ea0e2ec	floor_plan_show_grid	true	5	let_customer_choose	15
a2c491c9-ead9-443d-8099-843e2901a3e9	floor_plan_show_grid	true	5	let_customer_choose	15
c79080f9-500d-4a40-893c-491e10860cc7	floor_plan_show_grid	true	5	let_customer_choose	15
f215eb25-4250-4483-9d6f-30bc2adf475e	floor_plan_show_grid	true	5	let_customer_choose	15
\.


--
-- Data for Name: restaurants; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.restaurants (id, name, slug, subdomain, phone, email, address, logo_url, prefix, is_active, is_onboarded, status, subscription_plan, trial_ends_at, deleted_at, created_at, updated_at, parent_restaurant_id, is_multi_branch) FROM stdin;
8578db05-60e8-49e3-a9c5-0c5eb9f5c528	Test Restaurant	testrest6074	testrest6074	\N	\N	\N	\N	B49	t	f	trial	starter	2026-05-21 20:16:38.381791+03	\N	2026-05-07 23:16:38.345723+03	2026-05-07 23:16:39.040305+03	\N	f
bfd02abb-40be-45e6-9fb0-b57aa7e73b98	Test Restaurant	testrest2575	testrest2575	\N	\N	\N	\N	EFD	t	f	trial	starter	2026-05-21 20:17:16.689434+03	\N	2026-05-07 23:17:16.653959+03	2026-05-07 23:17:17.340895+03	\N	f
6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	Test Restaurant	testrest4173	testrest4173	\N	\N	\N	\N	ACA	t	f	trial	starter	2026-05-21 20:18:25.737808+03	\N	2026-05-07 23:18:25.7006+03	2026-05-07 23:18:26.396511+03	\N	f
02de8b85-bc5b-4651-a33d-b8985011a099	Test Restaurant	testrest1740	testrest1740	\N	\N	\N	\N	A78	t	f	trial	starter	2026-05-21 20:19:26.084601+03	\N	2026-05-07 23:19:26.043674+03	2026-05-07 23:19:26.773521+03	\N	f
bf7d7043-ce4a-40a5-beed-c2789606f922	Test Restaurant	testrest8716	testrest8716	\N	\N	\N	\N	F20	t	f	trial	starter	2026-05-21 21:03:04.818585+03	\N	2026-05-08 00:03:04.756731+03	2026-05-08 00:03:05.44123+03	\N	f
00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	Test Restaurant	testrest7808	testrest7808	\N	\N	\N	\N	E56	t	f	trial	starter	2026-06-08 19:44:49.639433+03	\N	2026-05-25 22:44:49.593035+03	2026-05-25 22:44:50.413274+03	\N	f
85d9b191-1dbb-4245-aa75-8e2fff19766f	Test Restaurant	testrest5247	testrest5247	\N	\N	\N	\N	8CA	t	f	trial	starter	2026-06-08 20:33:17.348225+03	\N	2026-05-25 23:33:17.251322+03	2026-05-25 23:33:19.490161+03	\N	f
4be5e95a-46ec-4d3b-b57e-c3a08aeffb9c	Verification Test Restaurant	verifytest8578	verifytest8578	\N	\N	\N	\N	B5E	t	f	trial	starter	2026-06-08 20:34:30.568837+03	\N	2026-05-25 23:34:30.567442+03	2026-05-25 23:34:36.371737+03	\N	f
8c436214-34b0-490d-b798-51349dce3728	riverside	riverside	riverside	\N	\N	KENYA,NAIROBI	\N	EEF	t	f	trial	starter	2026-06-08 21:13:49.608883+03	\N	2026-05-26 00:13:49.591805+03	2026-05-26 00:31:11.127602+03	\N	f
3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	Test Restaurant	testrest9632	testrest9632	\N	\N	\N	\N	6E2	t	f	trial	starter	2026-06-09 20:40:34.69701+03	\N	2026-05-26 23:40:34.645543+03	2026-05-26 23:40:37.958941+03	\N	f
b39c5777-e4db-4d70-962e-1a92220ec9e9	Test Restaurant	testrest2914	testrest2914	\N	\N	\N	\N	5FA	t	f	trial	starter	2026-06-09 20:44:59.312337+03	\N	2026-05-26 23:44:59.223538+03	2026-05-26 23:45:02.551791+03	\N	f
5b7a69ce-beec-47b7-b006-f4151e77a7f3	Test Restaurant	testrest6877	testrest6877	\N	\N	\N	\N	195	t	f	trial	starter	2026-06-09 21:11:01.096772+03	\N	2026-05-27 00:11:01.008126+03	2026-05-27 00:11:05.11259+03	\N	f
8bbc1483-4e02-4b06-a59d-d08b34b795b3	asxasdasdasda	asxasdasdasda	asxasdasdasda	\N	\N	\N	\N	208	t	f	trial	starter	2026-06-08 19:58:04.05322+03	\N	2026-05-25 22:58:03.943797+03	2026-05-25 22:58:03.943797+03	\N	f
623d31eb-f986-4676-a38b-fca9c15a4636	Primetech	primetech	primetech	\N	\N	\N	\N	350	t	f	trial	starter	2026-06-08 21:03:59.759232+03	\N	2026-05-26 00:03:59.673246+03	2026-05-26 00:03:59.673246+03	\N	f
7d13a11b-9373-4669-8d53-d2a041014c93	Primetech	primetechmwaila	primetechmwaila	\N	\N	Ruiru Wilbet Apartment House No 5	\N	75D	t	f	trial	starter	2026-06-09 20:36:26.275797+03	\N	2026-05-26 23:36:26.267813+03	2026-05-26 23:47:02.004151+03	\N	f
d7fc9094-3c1d-4eca-864d-6cf3009dea92	Test Restaurant	testrest3024	testrest3024	\N	\N	\N	\N	41B	t	f	trial	starter	2026-06-09 21:58:41.527814+03	\N	2026-05-27 00:58:41.008354+03	2026-05-27 00:58:48.835903+03	\N	f
e50d5aac-c374-490a-8040-ae3ff526a264	Hamiltons cafe	hamiltons-cafe	hamiltons-cafe	\N	\N	Ruiru Wilbet Apartment House No 5	\N	5D6	t	t	trial	starter	2026-06-21 14:10:40.166234+03	\N	2026-06-07 17:10:39.862526+03	2026-06-07 22:34:21.310078+03	\N	f
fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	Test Restaurant	testrest7011	testrest7011	\N	\N	\N	\N	578	t	f	trial	starter	2026-06-24 21:03:32.210853+03	\N	2026-06-11 00:03:32.200503+03	2026-06-11 00:03:35.783149+03	\N	f
e8b7e434-dab5-462b-a6c5-e51b176bb6c0	Test Restaurant	testrest8717	testrest8717	\N	\N	\N	\N	A40	t	f	trial	starter	2026-06-24 22:57:34.563269+03	\N	2026-06-11 01:57:34.407036+03	2026-06-11 01:57:40.79871+03	\N	f
c77f442c-89eb-4f66-b360-73270ea0e2ec	Test Restaurant	testrest4454	testrest4454	\N	\N	\N	\N	FAA	t	f	trial	starter	2026-06-27 20:24:54.608143+03	\N	2026-06-13 23:24:54.596537+03	2026-06-13 23:24:57.11559+03	\N	f
a2c491c9-ead9-443d-8099-843e2901a3e9	Test Restaurant	testrest6754	testrest6754	\N	\N	\N	\N	263	t	f	trial	starter	2026-06-27 20:27:03.796277+03	\N	2026-06-13 23:27:03.731189+03	2026-06-13 23:27:06.237901+03	\N	f
c79080f9-500d-4a40-893c-491e10860cc7	Test Restaurant	testrest7036	testrest7036	\N	\N	\N	\N	551	t	f	trial	starter	2026-06-27 20:28:32.515936+03	\N	2026-06-13 23:28:32.45872+03	2026-06-13 23:28:34.937156+03	\N	f
f215eb25-4250-4483-9d6f-30bc2adf475e	Test Restaurant	testrest2252	testrest2252	\N	\N	\N	\N	4BD	f	f	trial	starter	2026-06-28 14:25:41.997517+03	\N	2026-06-14 17:25:41.218135+03	2026-06-14 17:25:41.218135+03	\N	f
\.


--
-- Data for Name: staff; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.staff (id, restaurant_id, full_name, email, phone, role, shift, pin_code, assigned_tables, is_active, last_login_at, created_at, is_verified, kitchen_station, kitchen_station_id, branch_id, role_type) FROM stdin;
35b81453-5899-4b54-8bf8-2ed56229cd41	5b7a69ce-beec-47b7-b006-f4151e77a7f3	Test Waiter	\N	\N	waiter	morning	$2b$12$q.3pS04grcfyoNGKEkDaN.kq6FTmD/ggw5PU3TkUWMA9CIvrwtVNa	null	t	\N	2026-05-27 00:11:08.922119+03	f	\N	\N	\N	waiter
8eff54df-99fd-4103-868f-5620966e316d	4be5e95a-46ec-4d3b-b57e-c3a08aeffb9c	Verify Test Owner	owner@verifytest8578.com	254711111111	owner	full	$2b$12$9qRnuj/VG.V0FX1eckvuDOmgxugvukJERCTGd8wDn5.f8NQqnseVK	\N	t	2026-05-25 20:34:38.051884+03	2026-05-25 23:34:30.567442+03	t	\N	\N	\N	waiter
ef15dbb4-657a-4a72-86d9-f7dfcf32494a	623d31eb-f986-4676-a38b-fca9c15a4636	HAMILTON JANUARY MWAILA	hamiltonmwaila06@gmail.com	0116811764	owner	full	$2b$12$JklTy0lAOk585mRbFgWPh.xFLkaCdj8FOa6sjsI/0zmnNnrgcwGwu	\N	t	\N	2026-05-26 00:03:59.673246+03	t	\N	\N	\N	waiter
39e9908f-d24d-44de-a009-23d5936e2443	8c436214-34b0-490d-b798-51349dce3728	primetech.company69@gmail.com	primetech.company69@gmail.com	0769491949	owner	full	$2b$12$Sgqa6PE.GJtkYnQ2fk344.EHzKG1mRI73c0nthVSNCl/dJWT09DYq	\N	t	2026-05-25 21:28:20.280582+03	2026-05-26 00:13:49.591805+03	t	\N	\N	\N	waiter
d73e0182-4322-444a-8199-a8861e545f72	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	Test Owner	owner@testrest6074.com	254700000000	owner	full	$2b$12$Jx3LcyJfZgEFFyIpMFHi/.rOEgS21UUOQhdnEhpoz6cgIaQZa.KHy	\N	t	2026-05-07 20:16:39.434604+03	2026-05-07 23:16:38.345723+03	t	\N	\N	\N	waiter
8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	e50d5aac-c374-490a-8040-ae3ff526a264	peter ken	\N	\N	waiter	full	$2b$12$D7ltp9//3.Dp6QNUvu77X.A0pyxZqjWJRMq7/uzrbHbRIZ0JQxx.q	[1, 2]	t	2026-07-13 20:30:20.797171+03	2026-06-07 22:34:00.422533+03	f	\N	\N	\N	waiter
5b028260-312c-4319-9ab0-d9682841bda3	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	Test Owner	owner@testrest2575.com	254700000000	owner	full	$2b$12$Uk8LscJlZGC.2nj4cW2A9emSXmCmpTm4F4MseDXEg/oNTdrJKMeM2	\N	t	2026-05-07 20:17:17.728067+03	2026-05-07 23:17:16.653959+03	t	\N	\N	\N	waiter
33a0b50e-36ba-4284-9faa-98a21e932f32	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	Test Waiter	\N	\N	waiter	morning	$2b$12$MDta8P/aTIQywANNV52sXO.cFpQD2Ac5Ekkn68NuCqnu4qoDS24AG	null	t	\N	2026-05-07 23:17:17.774941+03	t	\N	\N	\N	waiter
c36a00c0-6800-4ba1-84c8-e660e76da3e6	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	Test Owner	owner@testrest4173.com	254700000000	owner	full	$2b$12$R19DWJpxWD2lFGD8/7KX..eA1nnPU2A4l4bn/kL.u.aLo4L1tbBJi	\N	t	2026-05-07 20:18:26.81002+03	2026-05-07 23:18:25.7006+03	t	\N	\N	\N	waiter
c82fde3e-d2c9-40ad-a7af-f51e6a8670b3	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	Test Waiter	\N	\N	waiter	morning	$2b$12$kDgFUQ40wCTHafljCG.4bORDe/fVhJ8lSnOOXHjls64cZVz3DJeWK	null	t	\N	2026-05-07 23:18:26.845802+03	t	\N	\N	\N	waiter
29c3e073-3e91-469e-b1ab-de8f7ae6eaf5	02de8b85-bc5b-4651-a33d-b8985011a099	Test Owner	owner@testrest1740.com	254700000000	owner	full	$2b$12$4tZW/D5nqKrYaEzIkbnd0.QqcoB139FjpxCSgeCOTjQ6bMcCRkUdu	\N	t	2026-05-07 20:19:27.184591+03	2026-05-07 23:19:26.043674+03	t	\N	\N	\N	waiter
89a76149-1d6d-4d49-b45d-90689686459e	02de8b85-bc5b-4651-a33d-b8985011a099	Test Waiter	\N	\N	waiter	morning	$2b$12$RaIDTkIvh2n76Uwgd7HExe.y9B1DzsPOfj.XoF4V/nRjZmNWx.ToS	null	t	\N	2026-05-07 23:19:27.220433+03	t	\N	\N	\N	waiter
44f4430f-0b11-49df-a996-95bb6e770752	bf7d7043-ce4a-40a5-beed-c2789606f922	Test Owner	owner@testrest8716.com	254700000000	owner	full	$2b$12$96bB5XtH8TgUAqZxL.iZCOm6ok9gmGbu/7nAEtAsUaggbhjCDGCGC	\N	t	2026-05-07 21:03:05.807576+03	2026-05-08 00:03:04.756731+03	t	\N	\N	\N	waiter
a5afdc44-3d69-411b-b80b-6b0df7071c2a	bf7d7043-ce4a-40a5-beed-c2789606f922	Test Waiter	\N	\N	waiter	morning	$2b$12$Ku/hYPn91iKCekhL4vzOjehPNN3hjwg1CJHEW27/6MDS8.cw3j5Cy	null	t	\N	2026-05-08 00:03:05.846563+03	t	\N	\N	\N	waiter
5da9d502-7dc1-4275-86cc-9232d23c7d2e	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	Test Waiter	\N	\N	waiter	morning	$2b$12$y5o7uWE5hUnRW8tbmULmoedaMGCjlAS6bvfppDjuuRSbctvYqvYSu	null	t	\N	2026-05-25 22:44:51.075468+03	t	\N	\N	\N	waiter
586efd0f-85ea-466d-bd23-9db0c79f53e0	85d9b191-1dbb-4245-aa75-8e2fff19766f	Test Owner	owner@testrest5247.com	254700000000	owner	full	$2b$12$I9biSoUXwigAp9PEge24A.ayGyV8Hv5itlvkLI5YrPbvx6KKOaOGy	\N	t	2026-05-25 20:33:21.004823+03	2026-05-25 23:33:17.251322+03	t	\N	\N	\N	waiter
c55047e0-3566-4046-b106-bdc909599e5b	85d9b191-1dbb-4245-aa75-8e2fff19766f	Test Waiter	\N	\N	waiter	morning	$2b$12$ZECo69.nZU1lURujTIZXYOSyhBrP5ByQvhHGMibNYYxiJhToTeIH.	null	t	\N	2026-05-25 23:33:21.088835+03	f	\N	\N	\N	waiter
ba87634e-fdb6-424e-855b-26d431320ec1	8bbc1483-4e02-4b06-a59d-d08b34b795b3	FLIRTY CODING TONN	hamiltonmwaila06@gmail.com	0769491949	owner	full	$2b$12$E2GLa/Se/hqh66G826mMVOkKjEFYaIMfWStmy7Qs6TiIxKPR8p6IO	\N	t	2026-05-25 19:58:05.474028+03	2026-05-25 22:58:03.943797+03	t	\N	\N	\N	waiter
4e1a5f19-c2a6-4477-a60b-b5d42a0a12db	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	Test Owner	owner@testrest9632.com	254700000000	owner	full	$2b$12$XjgnbC2HoZ.bdGi15VdFzOjJwQbxg0aUH6Tx0F.olzRr42mddKTxu	\N	t	2026-05-26 20:40:41.45266+03	2026-05-26 23:40:34.645543+03	t	\N	\N	\N	waiter
1dd6edde-8d43-443b-91ac-1cdd0b4b7854	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	Test Waiter	\N	\N	waiter	morning	$2b$12$2rlZcyrgIAGQIIz/.A2Tl.MSfWch5rEIrM7XaUpTiKBm.bpnkktS.	null	t	\N	2026-05-26 23:40:41.518979+03	f	\N	\N	\N	waiter
b63280b5-0253-4c82-a007-28d38a4dd10f	7d13a11b-9373-4669-8d53-d2a041014c93	HAMILTON JANUARY MWAILA	hamiltonmwaila06@gmail.com	0116811764	owner	full	$2b$12$KlpGl6xMzbDUgILsZEOVBuZrgOaXdVmszsrqqVoTnNl7qSGIqTMcm	\N	t	2026-05-26 20:46:27.093791+03	2026-05-26 23:36:26.267813+03	t	\N	\N	\N	waiter
1badbf86-e4d0-4da9-bede-8fd74062ac3d	b39c5777-e4db-4d70-962e-1a92220ec9e9	Test Owner	owner@testrest2914.com	254700000000	owner	full	$2b$12$pawxAS8mCpxBwpebfPl5eeejRBAJUhMWQBLthI5AltgCluAsm28PO	\N	t	2026-05-26 20:45:05.739753+03	2026-05-26 23:44:59.223538+03	t	\N	\N	\N	waiter
9cdf8ac7-200d-4c52-be21-6e97ab8a0a12	b39c5777-e4db-4d70-962e-1a92220ec9e9	Test Waiter	\N	\N	waiter	morning	$2b$12$.7AqSW7HKZD7EW9ovtDzyOCwJmYJevgI/MWrwMoBnG1yO5u8QauHW	null	t	\N	2026-05-26 23:45:05.775259+03	f	\N	\N	\N	waiter
3c1cb2f9-e8f2-41c2-9a32-c24caf7d8adf	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
7316a18c-92da-4bda-917b-6936359d8833	5b7a69ce-beec-47b7-b006-f4151e77a7f3	Test Owner	owner@testrest6877.com	254700000000	owner	full	$2b$12$C0wM6Ts48JFvZB/qdFzlR.fycAmFhjzlPRnZJgjR6BLPYg6VfliZu	\N	t	2026-05-26 21:11:08.887423+03	2026-05-27 00:11:01.008126+03	t	\N	\N	\N	waiter
670136cd-e10e-4e9a-84d9-135180d7ea38	d7fc9094-3c1d-4eca-864d-6cf3009dea92	Test Owner	owner@testrest3024.com	254700000000	owner	full	$2b$12$xI1VdETuaD60gPu8FoZv6uzo3FnvhDZKZnSaApANUA677hPWDtQee	\N	t	2026-05-26 21:58:53.104625+03	2026-05-27 00:58:41.008354+03	t	\N	\N	\N	waiter
b7b915e0-e8a8-4fa6-9539-1be4efc38e0f	d7fc9094-3c1d-4eca-864d-6cf3009dea92	Test Waiter	\N	\N	waiter	morning	$2b$12$x9xp/veuBozVv.0LP9ejQeNt9IvkrBCFFm/BfTvubLbShw3I2kGiG	null	t	\N	2026-05-27 00:58:53.221551+03	f	\N	\N	\N	waiter
9ebf6195-af6e-45d6-acd5-63b7fef2c058	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
75deb9da-d112-4945-90e1-4ed1462ef8a9	e50d5aac-c374-490a-8040-ae3ff526a264	Hamilton Peter 	hamilton@primetechkenya.co.ke	0769491949	owner	full	$2b$12$ENtymy/AsqdzUrcGE1MBsu0E..gv1OwotxgA35ifPdYDxPut.FWw6	\N	t	2026-07-13 15:51:35.358421+03	2026-06-07 17:10:39.862526+03	t	\N	\N	\N	waiter
957f7a37-4909-41af-a716-b91476faaf5b	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
289db48e-d4cb-48cc-8b52-c254b3416ca3	02de8b85-bc5b-4651-a33d-b8985011a099	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
0169062b-7f59-4c5a-951a-c81a05776715	bf7d7043-ce4a-40a5-beed-c2789606f922	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
d8502349-273e-4ab5-b3fb-d2b083e80837	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
7cc7b957-5b8b-4108-bd19-e8b0bfd613b7	85d9b191-1dbb-4245-aa75-8e2fff19766f	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
4cb61f92-cf23-40b6-ae08-208c902bac2c	4be5e95a-46ec-4d3b-b57e-c3a08aeffb9c	Chef for Verification Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
c2f7da73-4e97-4e16-b8aa-78e7a0a5998b	8c436214-34b0-490d-b798-51349dce3728	Chef for riverside	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
83e4689d-2fb3-4e82-bc30-31c700ce5724	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	Test Waiter	\N	\N	waiter	morning	$2b$12$t.c7z2XnDaqAf2yUxoqoh.3OTdBMKyCk0wYFhCZS5IG7nKcg6spCG	null	t	2026-06-10 20:38:00.480937+03	2026-05-07 23:16:39.47448+03	t	\N	\N	\N	waiter
54cbf982-7615-439c-91de-1b8a3a462e91	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	Test Owner	owner@testrest7808.com	254700000000	owner	full	$2b$12$22dRup2DrZREcBEuYDn2zuRhFLVSLZu711f9B6Haa4jGZOakhnrwq	\N	t	2026-06-10 22:51:17.539833+03	2026-05-25 22:44:49.593035+03	t	\N	\N	\N	waiter
596898c8-4980-4cce-97b6-bea366173065	e50d5aac-c374-490a-8040-ae3ff526a264	John Kamau	\N	\N	waiter	full	$2b$12$WauFYzaNPYwxxj5dJutSSOCUuO/z9mqLkYDCApAy89ukkFOUBDeLm	[9, 10]	t	2026-06-14 14:49:41.016162+03	2026-06-07 22:34:00.422533+03	f	\N	\N	\N	waiter
e647a586-0c7b-47e8-a8c4-0058d90de5f9	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
188b5b32-6cc6-40be-9bae-858783908959	b39c5777-e4db-4d70-962e-1a92220ec9e9	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
a62f631f-5dc0-41f2-87b3-146dedc1412d	5b7a69ce-beec-47b7-b006-f4151e77a7f3	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
bf26e4b5-ffec-47f7-a858-c509bebbc7ed	8bbc1483-4e02-4b06-a59d-d08b34b795b3	Chef for asxasdasdasda	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
2cd3f20b-e216-4779-b5cd-ebc5e8bc67f2	623d31eb-f986-4676-a38b-fca9c15a4636	Chef for Primetech	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
ec37e216-d9d6-431d-86a0-1c318332a4e9	7d13a11b-9373-4669-8d53-d2a041014c93	Chef for Primetech	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
987c9b8b-e726-4a95-b1dd-e0b1c55acc58	d7fc9094-3c1d-4eca-864d-6cf3009dea92	Chef for Test Restaurant	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
7cdfc9d4-16f3-4b0d-801a-aa0d559a8a42	e50d5aac-c374-490a-8040-ae3ff526a264	peter ken	\N	\N	waiter	full	$2b$12$.r.VI/oH0TGoUEYtihfdNePip5NoXxQrG2aFTHzbrJXHlM53RXLDK	[]	t	2026-06-10 20:33:21.666216+03	2026-06-07 22:34:11.26636+03	f	\N	\N	\N	waiter
d70b42c1-c748-4adb-ba03-9b40560ed749	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	Test Owner	owner@testrest7011.com	254700000000	owner	full	$2b$12$kZEdcOTbhygF21r3GL93BOItNw94Qolv4e9RcHg84mV8sWUFaB6WC	\N	t	2026-06-10 21:03:39.165777+03	2026-06-11 00:03:32.200503+03	t	\N	\N	\N	waiter
980532fb-768b-4f90-b5c3-80664ce995a9	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	Test Waiter	\N	\N	waiter	morning	$2b$12$ZoOHRtdmOLB04tfM5q0wDeur6TcXvwQ4kkeQXKGnemF9FlAEvBRRO	null	t	\N	2026-06-11 00:03:39.217325+03	f	\N	\N	\N	waiter
8fc1873c-546f-427f-9fe4-43ee8460f9f7	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	Test Owner	owner@testrest8717.com	254700000000	owner	full	$2b$12$MJ8sQjsJ133OcFAYk8kWVeobi59yrU/f86stFFs9MTNIZWtN/qt6.	\N	t	2026-06-10 22:57:44.75918+03	2026-06-11 01:57:34.407036+03	t	\N	\N	\N	waiter
44fb646a-f0d7-4596-9bf5-36ba4c234c97	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	Test Waiter	\N	\N	waiter	morning	$2b$12$Czhl2p0dzhlEW.x4wt.8l.8abXSE8E38jDSdKwP66B/iC1f15yqtC	null	t	\N	2026-06-11 01:57:44.94689+03	f	\N	\N	\N	waiter
2b5c312b-e3a4-4f5c-afa9-264f22f53df2	e50d5aac-c374-490a-8040-ae3ff526a264	Chef for Hamiltons cafe	\N	\N	chef	full	$2b$12$9lvIByyoSU5WDoV6j7RpTu5OFz/PLUgwIIXpKtpoLq0HyxboKaKQq	\N	t	\N	2026-06-10 19:52:17.528333+03	t	\N	\N	\N	waiter
8931e935-7550-42b2-a020-44ce19284e8a	c77f442c-89eb-4f66-b360-73270ea0e2ec	Test Owner	owner@testrest4454.com	254700000000	owner	full	$2b$12$UJ6s3V/2EJtiyHzhOjacweAaOqcqh3SCPBUpkI5vlQY9l9Eu/GpES	\N	t	2026-06-13 20:25:00.103338+03	2026-06-13 23:24:54.596537+03	t	\N	\N	\N	waiter
ba22d3f8-3bc8-4861-9b6c-ffc39ab236fa	c77f442c-89eb-4f66-b360-73270ea0e2ec	Test Waiter	\N	\N	waiter	morning	$2b$12$/hZyIHoI502zqXF9o0Ma5OMOv0m9D/YoYYoKt4Ifdfxon67P2RL5S	null	t	\N	2026-06-13 23:25:00.152746+03	f	\N	\N	\N	waiter
03a6de53-568b-46e1-80fe-5d163bd2ecd2	a2c491c9-ead9-443d-8099-843e2901a3e9	Test Owner	owner@testrest6754.com	254700000000	owner	full	$2b$12$C5WvN6Qn89VEGQ4qwa.FC.vLk9gcU.LWS0X3zEyLDN8gaAG0WGJwy	\N	t	2026-06-13 20:27:09.148064+03	2026-06-13 23:27:03.731189+03	t	\N	\N	\N	waiter
5be3654d-2cb3-4dab-9727-2101f7d6e4d1	a2c491c9-ead9-443d-8099-843e2901a3e9	Test Waiter	\N	\N	waiter	morning	$2b$12$5QlEbVbhinEAcbu8/pwpseb2UjG3vBh4wICo32zIDe4I3bzUzvlW.	null	t	\N	2026-06-13 23:27:09.191447+03	f	\N	\N	\N	waiter
4fe63ccb-986e-4f39-8ddb-5f1bc9f0b919	c79080f9-500d-4a40-893c-491e10860cc7	Test Owner	owner@testrest7036.com	254700000000	owner	full	$2b$12$xerftOQ0e9wfeQ8XZUgOr.PsTP40RfNCAJbY6TbgUyZJhfRwCKyWm	\N	t	2026-06-13 20:28:48.521713+03	2026-06-13 23:28:32.45872+03	t	\N	\N	\N	waiter
fadaaab5-dae3-433c-b639-5d0c712204cc	c79080f9-500d-4a40-893c-491e10860cc7	Test Waiter	\N	\N	waiter	morning	$2b$12$DpSKepbTgaD21T1ojLgbWOxd..WzvrEoBR9lV6KowGK3sEU2UrpxC	null	t	\N	2026-06-13 23:28:48.565949+03	f	\N	\N	\N	waiter
e2c04751-81c3-4838-8d10-d4b1193e06d9	f215eb25-4250-4483-9d6f-30bc2adf475e	Test Owner	owner@testrest2252.com	254700000000	owner	full	$2b$12$V4QMhc9kTciz4nyW1QS8MuaxElbETMNCFSW1CzMa1XAzh7MAbQbwO	\N	t	\N	2026-06-14 17:25:41.218135+03	f	\N	\N	\N	waiter
d1a41c28-a376-4ba7-9591-fbff1d42dd56	e50d5aac-c374-490a-8040-ae3ff526a264	John Kamau	\N	\N	waiter	full	$2b$12$IfhntEwN1IZYsPlPKsza3OvWyp26AyGa1uzY1du2M3HfWrKVRPJOG	[11, 12]	t	2026-06-10 20:21:13.983912+03	2026-06-07 22:34:11.26636+03	f	\N	\N	\N	waiter
\.


--
-- Data for Name: staff_activity_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.staff_activity_logs (id, staff_id, restaurant_id, clock_in_at, clock_out_at, created_at) FROM stdin;
\.


--
-- Data for Name: station_prep_times; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.station_prep_times (id, restaurant_id, station_id, item_category, default_seconds, created_at, updated_at) FROM stdin;
be327b0f-b707-4115-b258-b89543198df5	e50d5aac-c374-490a-8040-ae3ff526a264	d7f50300-730d-478a-9441-de8273050b02	appetizer	300	2026-06-13 18:07:48.680555+03	2026-06-13 18:07:48.680555+03
706a5fa1-5776-4b85-b154-b32111c4e22a	e50d5aac-c374-490a-8040-ae3ff526a264	d7f50300-730d-478a-9441-de8273050b02	main	600	2026-06-13 18:07:48.680555+03	2026-06-13 18:07:48.680555+03
08a94a80-aa92-4558-a306-58060e105fc8	e50d5aac-c374-490a-8040-ae3ff526a264	d7f50300-730d-478a-9441-de8273050b02	dessert	600	2026-06-13 18:07:48.680555+03	2026-06-13 18:07:48.680555+03
5ee7a973-a114-418d-9856-fe5d53da9e97	e50d5aac-c374-490a-8040-ae3ff526a264	d7f50300-730d-478a-9441-de8273050b02	beverage	300	2026-06-13 18:07:48.680555+03	2026-06-13 18:07:48.680555+03
81474c1c-9f39-40bf-85ad-835dd0aab97a	e50d5aac-c374-490a-8040-ae3ff526a264	18a60cb5-aa25-41b3-9c13-c6541dba0a4d	appetizer	300	2026-06-13 18:08:54.022797+03	2026-06-13 18:08:54.022797+03
ca3828be-cece-4f2a-b902-6976ba86e031	e50d5aac-c374-490a-8040-ae3ff526a264	18a60cb5-aa25-41b3-9c13-c6541dba0a4d	main	600	2026-06-13 18:08:54.022797+03	2026-06-13 18:08:54.022797+03
d3549bae-bd11-4754-98df-7653d20dea00	e50d5aac-c374-490a-8040-ae3ff526a264	18a60cb5-aa25-41b3-9c13-c6541dba0a4d	dessert	600	2026-06-13 18:08:54.022797+03	2026-06-13 18:08:54.022797+03
f1919f48-9825-403a-8b58-23fcd01f5d6f	e50d5aac-c374-490a-8040-ae3ff526a264	18a60cb5-aa25-41b3-9c13-c6541dba0a4d	beverage	300	2026-06-13 18:08:54.022797+03	2026-06-13 18:08:54.022797+03
a59797a0-517d-4b82-bb49-a53a460095b0	e50d5aac-c374-490a-8040-ae3ff526a264	b07f8936-1908-4a67-8414-1d8dd4f99979	appetizer	300	2026-06-13 18:09:58.378792+03	2026-06-13 18:09:58.378792+03
cd96bb2d-e91a-4a7a-9d50-cd756dffeff9	e50d5aac-c374-490a-8040-ae3ff526a264	b07f8936-1908-4a67-8414-1d8dd4f99979	main	600	2026-06-13 18:09:58.378792+03	2026-06-13 18:09:58.378792+03
aa02bee7-9249-4d3f-be15-c85ce250fd94	e50d5aac-c374-490a-8040-ae3ff526a264	b07f8936-1908-4a67-8414-1d8dd4f99979	dessert	600	2026-06-13 18:09:58.378792+03	2026-06-13 18:09:58.378792+03
26db3b23-fbb5-4d04-b574-3f0139646a23	e50d5aac-c374-490a-8040-ae3ff526a264	b07f8936-1908-4a67-8414-1d8dd4f99979	beverage	300	2026-06-13 18:09:58.378792+03	2026-06-13 18:09:58.378792+03
ec89dce7-bd4f-4776-a05b-0596a33c4bb1	e50d5aac-c374-490a-8040-ae3ff526a264	179d55c4-1493-4d6f-ace1-d9f5d64ddcf2	appetizer	300	2026-06-13 18:11:15.92641+03	2026-06-13 18:11:15.92641+03
e20c49cb-5579-49b5-96d7-c4da000c58a5	e50d5aac-c374-490a-8040-ae3ff526a264	179d55c4-1493-4d6f-ace1-d9f5d64ddcf2	main	600	2026-06-13 18:11:15.92641+03	2026-06-13 18:11:15.92641+03
5ece2f4b-7850-465f-b169-855f14a1f3cf	e50d5aac-c374-490a-8040-ae3ff526a264	179d55c4-1493-4d6f-ace1-d9f5d64ddcf2	dessert	600	2026-06-13 18:11:15.92641+03	2026-06-13 18:11:15.92641+03
6744b5f1-470a-4dea-b533-06db40a42e42	e50d5aac-c374-490a-8040-ae3ff526a264	179d55c4-1493-4d6f-ace1-d9f5d64ddcf2	beverage	300	2026-06-13 18:11:15.92641+03	2026-06-13 18:11:15.92641+03
f95ed7c4-3aea-4e8f-a251-5248243140e1	e50d5aac-c374-490a-8040-ae3ff526a264	9974007d-b0f3-4bf3-8fd0-a7e06fd599c7	appetizer	300	2026-06-13 18:12:02.876661+03	2026-06-13 18:12:02.876661+03
bd47c666-6dda-4176-bd0f-60fc0b86df30	e50d5aac-c374-490a-8040-ae3ff526a264	9974007d-b0f3-4bf3-8fd0-a7e06fd599c7	main	600	2026-06-13 18:12:02.876661+03	2026-06-13 18:12:02.876661+03
b031c051-83cf-48eb-a412-4152998b2b85	e50d5aac-c374-490a-8040-ae3ff526a264	9974007d-b0f3-4bf3-8fd0-a7e06fd599c7	dessert	600	2026-06-13 18:12:02.876661+03	2026-06-13 18:12:02.876661+03
b05c72cc-36e6-4423-b3ef-8f34d929f341	e50d5aac-c374-490a-8040-ae3ff526a264	9974007d-b0f3-4bf3-8fd0-a7e06fd599c7	beverage	300	2026-06-13 18:12:02.876661+03	2026-06-13 18:12:02.876661+03
e071feed-d8b2-473e-b782-0f58989ffd7a	e50d5aac-c374-490a-8040-ae3ff526a264	4b2c6bec-b0b7-4b98-8f0f-52d050f121cd	appetizer	300	2026-06-13 18:12:46.386707+03	2026-06-13 18:12:46.386707+03
32ba5930-c877-47ba-bc57-a0152d342b46	e50d5aac-c374-490a-8040-ae3ff526a264	4b2c6bec-b0b7-4b98-8f0f-52d050f121cd	main	600	2026-06-13 18:12:46.386707+03	2026-06-13 18:12:46.386707+03
08541a2a-d05d-4ad5-b8f6-b52844962bde	e50d5aac-c374-490a-8040-ae3ff526a264	4b2c6bec-b0b7-4b98-8f0f-52d050f121cd	dessert	600	2026-06-13 18:12:46.386707+03	2026-06-13 18:12:46.386707+03
b2c9b1dc-0747-46e2-bf2f-f76a50d1731a	e50d5aac-c374-490a-8040-ae3ff526a264	4b2c6bec-b0b7-4b98-8f0f-52d050f121cd	beverage	300	2026-06-13 18:12:46.386707+03	2026-06-13 18:12:46.386707+03
\.


--
-- Data for Name: table_transfer_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.table_transfer_logs (id, restaurant_id, original_table_id, new_table_id, order_id, transferred_by, transferred_at) FROM stdin;
15a6b5e8-b6e2-416a-ae8e-d35291b14dcb	c79080f9-500d-4a40-893c-491e10860cc7	5385f35d-6460-48d5-9299-8eb7d2b56ad9	8acb8e7e-d8a5-4c32-900c-dbcdaefc06a2	94b446c7-cf4f-40e0-a536-17a76a7de343	4fe63ccb-986e-4f39-8ddb-5f1bc9f0b919	2026-06-13 23:28:51.337781+03
85e52539-979d-4549-8b81-d4ec455cfa6f	e50d5aac-c374-490a-8040-ae3ff526a264	55963478-288a-40fc-bbdd-ef096c987abf	e31c0877-63fa-4613-9b0f-6d9e0a67bdd8	bfe05c8a-4ed6-41cd-94df-84435c0246b9	8f30e73b-1d3f-4f7f-984c-4a64a661d8ed	2026-06-15 23:09:27.588451+03
\.


--
-- Data for Name: table_transfers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.table_transfers (id, restaurant_id, original_table_id, new_table_id, order_id, transferred_by, transferred_at) FROM stdin;
\.


--
-- Data for Name: tables; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tables (id, restaurant_id, table_number, capacity, location, status, current_session_id, qr_code_url, qr_code_token, created_at, occupied_since, last_status_change, status_history, floor_id, pos_x, pos_y, shape, width, height, branch_id) FROM stdin;
55963478-288a-40fc-bbdd-ef096c987abf	e50d5aac-c374-490a-8040-ae3ff526a264	1	4	\N	occupied	5199b9ab-d91a-4dad-8df9-138066187c7f	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjU1OTYzNDc4LTI4OGEtNDBmYy1iYmRkLWVmMDk2Yzk4N2FiZiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjF9.VKhPS6VIN3nHeg3Q9Imxev8byq7HPVlduW6CRnEjb48	2026-06-07 21:45:03.101325+03	2026-07-13 17:14:52.715639+03	\N	[]	\N	0	0	square	80	80	\N
e9da988f-de6b-46ec-a218-b7d2c736661a	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0ODU0MjEsInN1YiI6ImU5ZGE5ODhmLWRlNmItNDZlYy1hMjE4LWI3ZDJjNzM2NjYxYSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJmYzNjN2Q3My0wNjkxLTRjMmItOThhNi0zZDFmYzM5YTE3ZTEiLCJ0YWJsZV9udW1iZXIiOjJ9.YCBQkayaJNutjbaf9NCEqAMwU0be6ABmmNO2CSg_pOM	2026-06-11 00:03:40.583209+03	\N	\N	[]	\N	0	0	square	80	80	\N
c8e05475-0170-4e77-ae1e-53ace6a510ea	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0ODU0MjIsInN1YiI6ImM4ZTA1NDc1LTAxNzAtNGU3Ny1hZTFlLTUzYWNlNmE1MTBlYSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJmYzNjN2Q3My0wNjkxLTRjMmItOThhNi0zZDFmYzM5YTE3ZTEiLCJ0YWJsZV9udW1iZXIiOjN9.GEDtE03vfjsbFyMntzZlelwVsjIbMuMMILEtaX3LU34	2026-06-11 00:03:40.583209+03	\N	\N	[]	\N	0	0	square	80	80	\N
a96acc58-d3b4-4d9a-b177-b30e9060daae	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0ODU0MjIsInN1YiI6ImE5NmFjYzU4LWQzYjQtNGQ5YS1iMTc3LWIzMGU5MDYwZGFhZSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJmYzNjN2Q3My0wNjkxLTRjMmItOThhNi0zZDFmYzM5YTE3ZTEiLCJ0YWJsZV9udW1iZXIiOjR9.fLL_2v-5eQoLHjxoP-qXmGCIMEImI-l8HQJrah7Ejmw	2026-06-11 00:03:40.583209+03	\N	\N	[]	\N	0	0	square	80	80	\N
dd877a74-086b-407a-a270-eded572da72c	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0ODU0MjIsInN1YiI6ImRkODc3YTc0LTA4NmItNDA3YS1hMjcwLWVkZWQ1NzJkYTcyYyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJmYzNjN2Q3My0wNjkxLTRjMmItOThhNi0zZDFmYzM5YTE3ZTEiLCJ0YWJsZV9udW1iZXIiOjV9.am59-tiFhJ3qPD_MbZnpdM5e2PGu7h8g9r41662I4O0	2026-06-11 00:03:40.583209+03	\N	\N	[]	\N	0	0	square	80	80	\N
3c43d5c8-4428-430b-ad01-ad9c2184108c	fc3c7d73-0691-4c2b-98a6-3d1fc39a17e1	1	4	Main Hall	occupied	6e4d1d2f-6eb6-4767-acd1-abbd6720651a	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0ODU0MjAsInN1YiI6IjNjNDNkNWM4LTQ0MjgtNDMwYi1hZDAxLWFkOWMyMTg0MTA4YyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJmYzNjN2Q3My0wNjkxLTRjMmItOThhNi0zZDFmYzM5YTE3ZTEiLCJ0YWJsZV9udW1iZXIiOjF9.S44dJBdjEc2SdkZcbo_DaqO_bhn__1Hl2HL_NnJBkuM	2026-06-11 00:03:40.583209+03	\N	\N	[]	\N	0	0	square	80	80	\N
7f8c2989-f978-4826-941f-d5e8a43911a3	c77f442c-89eb-4f66-b360-73270ea0e2ec	1	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDIzMDEsInN1YiI6IjdmOGMyOTg5LWY5NzgtNDgyNi05NDFmLWQ1ZThhNDM5MTFhMyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzdmNDQyYy04OWViLTRmNjYtYjM2MC03MzI3MGVhMGUyZWMiLCJ0YWJsZV9udW1iZXIiOjF9.KZG9PTc421RuiUJBNufAqE78-YH-XQAjsD6B12po-U4	2026-06-13 23:25:01.022049+03	\N	\N	[]	\N	0	0	square	80	80	\N
5699ebce-5425-44a5-a2af-36a1cd4e8d29	c77f442c-89eb-4f66-b360-73270ea0e2ec	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDIzMDEsInN1YiI6IjU2OTllYmNlLTU0MjUtNDRhNS1hMmFmLTM2YTFjZDRlOGQyOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzdmNDQyYy04OWViLTRmNjYtYjM2MC03MzI3MGVhMGUyZWMiLCJ0YWJsZV9udW1iZXIiOjJ9.3LQ4Uy9yhdQ-Kc5j_1DnGt_em9rUuiqahODbLNz8HYU	2026-06-13 23:25:01.022049+03	\N	\N	[]	\N	0	0	square	80	80	\N
e2984258-163c-414b-90b9-86fcb6351a37	c77f442c-89eb-4f66-b360-73270ea0e2ec	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDIzMDIsInN1YiI6ImUyOTg0MjU4LTE2M2MtNDE0Yi05MGI5LTg2ZmNiNjM1MWEzNyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzdmNDQyYy04OWViLTRmNjYtYjM2MC03MzI3MGVhMGUyZWMiLCJ0YWJsZV9udW1iZXIiOjN9.y9xcRwhrQWdLZs9Lc_2mUty4Y1WXxRLoDXRQJnapwvk	2026-06-13 23:25:01.022049+03	\N	\N	[]	\N	0	0	square	80	80	\N
c5f9e5e2-5bb9-4b82-8a2e-f433044aa46f	c77f442c-89eb-4f66-b360-73270ea0e2ec	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDIzMDIsInN1YiI6ImM1ZjllNWUyLTViYjktNGI4Mi04YTJlLWY0MzMwNDRhYTQ2ZiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzdmNDQyYy04OWViLTRmNjYtYjM2MC03MzI3MGVhMGUyZWMiLCJ0YWJsZV9udW1iZXIiOjR9.VaqY4eQ4D96yHC1KIRv1cOjezBNCmO5j29e4xH3q9eY	2026-06-13 23:25:01.022049+03	\N	\N	[]	\N	0	0	square	80	80	\N
1e116988-7ac6-41d4-8fe3-6b6189f91826	c77f442c-89eb-4f66-b360-73270ea0e2ec	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDIzMDIsInN1YiI6IjFlMTE2OTg4LTdhYzYtNDFkNC04ZmUzLTZiNjE4OWY5MTgyNiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzdmNDQyYy04OWViLTRmNjYtYjM2MC03MzI3MGVhMGUyZWMiLCJ0YWJsZV9udW1iZXIiOjV9.co6rX4A1DY2zbuO4p3Qk-lghieb4mGCAjQc0VBbIStQ	2026-06-13 23:25:01.022049+03	\N	\N	[]	\N	0	0	square	80	80	\N
e8753e5a-4b03-48cb-815e-9c6c57e0f312	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImU4NzUzZTVhLTRiMDMtNDhjYi04MTVlLTljNmM1N2UwZjMxMiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI2ZDE3ZTg3YS00YTRiLTQ4NjMtYTlhNy03YWUxYjcwNDNiYTQiLCJ0YWJsZV9udW1iZXIiOjN9.GoynT5mA83SSJM02JME3jf3j9IgKM73M0CHrdDnOIRM	2026-05-07 23:18:27.622415+03	\N	\N	[]	\N	0	0	square	80	80	\N
d4636d4a-a04d-4a8f-95c0-80f35592dd70	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0OTIyNjcsInN1YiI6ImQ0NjM2ZDRhLWEwNGQtNGE4Zi05NWMwLTgwZjM1NTkyZGQ3MCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlOGI3ZTQzNC1kYWI1LTQ2MmItYTZjNS1lNTFiMTc2YmI2YzAiLCJ0YWJsZV9udW1iZXIiOjJ9.TsqJTZlF0QkwJKJIlOuMtmjJOz0yznDsFhyPcqqLrXw	2026-06-11 01:57:46.516275+03	\N	\N	[]	\N	0	0	square	80	80	\N
9eaf192f-52bc-432d-bf82-1ed626759d3a	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0OTIyNjcsInN1YiI6IjllYWYxOTJmLTUyYmMtNDMyZC1iZjgyLTFlZDYyNjc1OWQzYSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlOGI3ZTQzNC1kYWI1LTQ2MmItYTZjNS1lNTFiMTc2YmI2YzAiLCJ0YWJsZV9udW1iZXIiOjN9.I7jOJw_1qKzNNOWdbMqmmS6BiVr8PymitohuWAziyfk	2026-06-11 01:57:46.516275+03	\N	\N	[]	\N	0	0	square	80	80	\N
f9d4ed5f-c41a-484c-ba8a-d9e8b43650d9	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0OTIyNjcsInN1YiI6ImY5ZDRlZDVmLWM0MWEtNDg0Yy1iYThhLWQ5ZThiNDM2NTBkOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlOGI3ZTQzNC1kYWI1LTQ2MmItYTZjNS1lNTFiMTc2YmI2YzAiLCJ0YWJsZV9udW1iZXIiOjR9.6BYWl1acvjPbwng67l7SB-74QdioImxTCMDXFSnFMNs	2026-06-11 01:57:46.516275+03	\N	\N	[]	\N	0	0	square	80	80	\N
0a27f15e-44fe-456f-808f-62fe05126bf8	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0OTIyNjcsInN1YiI6IjBhMjdmMTVlLTQ0ZmUtNDU2Zi04MDhmLTYyZmUwNTEyNmJmOCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlOGI3ZTQzNC1kYWI1LTQ2MmItYTZjNS1lNTFiMTc2YmI2YzAiLCJ0YWJsZV9udW1iZXIiOjV9.KTQgcycKG_4ntXYOAWZ5Snr1LJtg433zZKJjD0-ed5E	2026-06-11 01:57:46.516275+03	\N	\N	[]	\N	0	0	square	80	80	\N
d3b9720d-9874-45c8-ba25-31f43bbd4fc7	e8b7e434-dab5-462b-a6c5-e51b176bb6c0	1	4	Main Hall	occupied	07b6e885-1c97-4c65-989d-f9939659a49b	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY0OTIyNjYsInN1YiI6ImQzYjk3MjBkLTk4NzQtNDVjOC1iYTI1LTMxZjQzYmJkNGZjNyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlOGI3ZTQzNC1kYWI1LTQ2MmItYTZjNS1lNTFiMTc2YmI2YzAiLCJ0YWJsZV9udW1iZXIiOjF9.DTfzpHRk97FNYkGsxz00KVCsOnpwogmQ07daxLJlIX8	2026-06-11 01:57:46.516275+03	\N	\N	[]	\N	0	0	square	80	80	\N
a914f841-be80-4a07-870f-6f7b24edcd61	a2c491c9-ead9-443d-8099-843e2901a3e9	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI0MzAsInN1YiI6ImE5MTRmODQxLWJlODAtNGEwNy04NzBmLTZmN2IyNGVkY2Q2MSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJhMmM0OTFjOS1lYWQ5LTQ0M2QtODA5OS04NDNlMjkwMWEzZTkiLCJ0YWJsZV9udW1iZXIiOjJ9.D8rNdNEYrY9GV6iqmnbtZRR_232P-b2ttVaDCDeYT7Q	2026-06-13 23:27:10.348417+03	\N	\N	[]	\N	0	0	square	80	80	\N
e27b2f28-763a-41a3-9ca4-84d5ded3765a	a2c491c9-ead9-443d-8099-843e2901a3e9	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI0MzAsInN1YiI6ImUyN2IyZjI4LTc2M2EtNDFhMy05Y2E0LTg0ZDVkZWQzNzY1YSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJhMmM0OTFjOS1lYWQ5LTQ0M2QtODA5OS04NDNlMjkwMWEzZTkiLCJ0YWJsZV9udW1iZXIiOjN9.SXOFGaw3AzK0mFO-H3fShKO1Z9HTvgxhi0GSmT-Q7gY	2026-06-13 23:27:10.348417+03	\N	\N	[]	\N	0	0	square	80	80	\N
a5f4a0ea-fcf4-4eca-a784-9a8b93327fec	a2c491c9-ead9-443d-8099-843e2901a3e9	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI0MzAsInN1YiI6ImE1ZjRhMGVhLWZjZjQtNGVjYS1hNzg0LTlhOGI5MzMyN2ZlYyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJhMmM0OTFjOS1lYWQ5LTQ0M2QtODA5OS04NDNlMjkwMWEzZTkiLCJ0YWJsZV9udW1iZXIiOjR9.mqNiVgEZQ8y5rql9wWkeeWENnf0GESr7j0Kgk7RpShU	2026-06-13 23:27:10.348417+03	\N	\N	[]	\N	0	0	square	80	80	\N
78710447-009c-47ce-96da-51bf6c907ab4	a2c491c9-ead9-443d-8099-843e2901a3e9	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI0MzAsInN1YiI6Ijc4NzEwNDQ3LTAwOWMtNDdjZS05NmRhLTUxYmY2YzkwN2FiNCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJhMmM0OTFjOS1lYWQ5LTQ0M2QtODA5OS04NDNlMjkwMWEzZTkiLCJ0YWJsZV9udW1iZXIiOjV9.3EjwlVboWlkadWFk31KXCGWN2aV-4R2a24RZyjIIsws	2026-06-13 23:27:10.348417+03	\N	\N	[]	\N	0	0	square	80	80	\N
de8ea456-ea0a-467d-8a0e-01dddaaafef1	a2c491c9-ead9-443d-8099-843e2901a3e9	1	4	Main Hall	occupied	f34f0681-1aef-473b-9255-8fa87511e157	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI0MzAsInN1YiI6ImRlOGVhNDU2LWVhMGEtNDY3ZC04YTBlLTAxZGRkYWFhZmVmMSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJhMmM0OTFjOS1lYWQ5LTQ0M2QtODA5OS04NDNlMjkwMWEzZTkiLCJ0YWJsZV9udW1iZXIiOjF9.LcfX0Ys9diZyYJl4mppbvgljvcsJCwJMx0qLN6qh9PU	2026-06-13 23:27:10.348417+03	2026-06-13 20:27:11.338193+03	\N	[]	\N	0	0	square	80	80	\N
51d523d6-6ccf-4d40-ad61-09bdb21c5547	02de8b85-bc5b-4651-a33d-b8985011a099	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjUxZDUyM2Q2LTZjY2YtNGQ0MC1hZDYxLTA5YmRiMjFjNTU0NyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMmRlOGI4NS1iYzViLTQ2NTEtYTMzZC1iODk4NTAxMWEwOTkiLCJ0YWJsZV9udW1iZXIiOjJ9.eAvFuzbcAn0XQzELzddMXm9FxN-1Bj2DqIQ55YZKgtI	2026-05-07 23:19:27.988187+03	\N	\N	[]	\N	0	0	square	80	80	\N
24e02d43-9a5a-424e-b733-e22a43abe246	c79080f9-500d-4a40-893c-491e10860cc7	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI1MjksInN1YiI6IjI0ZTAyZDQzLTlhNWEtNDI0ZS1iNzMzLWUyMmE0M2FiZTI0NiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzkwODBmOS01MDBkLTRhNDAtODkzYy00OTFlMTA4NjBjYzciLCJ0YWJsZV9udW1iZXIiOjN9.6Uhqd50BK4Sy_OzbB4niwL6ByvqEPBrApR26bqFav74	2026-06-13 23:28:49.366944+03	\N	\N	[]	\N	0	0	square	80	80	\N
c5080360-7a43-4bc5-a71c-81e6f00f3906	c79080f9-500d-4a40-893c-491e10860cc7	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI1MjksInN1YiI6ImM1MDgwMzYwLTdhNDMtNGJjNS1hNzFjLTgxZTZmMDBmMzkwNiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzkwODBmOS01MDBkLTRhNDAtODkzYy00OTFlMTA4NjBjYzciLCJ0YWJsZV9udW1iZXIiOjR9.rGSiyycx_ZM2MUNyVNLO2jjUL31BNFse8eVcTKNfbFQ	2026-06-13 23:28:49.366944+03	\N	\N	[]	\N	0	0	square	80	80	\N
4ef04f8e-5ad8-4bd1-b1d5-bfc6bdeb5351	c79080f9-500d-4a40-893c-491e10860cc7	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI1MjksInN1YiI6IjRlZjA0ZjhlLTVhZDgtNGJkMS1iMWQ1LWJmYzZiZGViNTM1MSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzkwODBmOS01MDBkLTRhNDAtODkzYy00OTFlMTA4NjBjYzciLCJ0YWJsZV9udW1iZXIiOjV9.aSGzFcqS8oKKblhm0W6DH6nZRcpnhdDZ5lcGJdIOipI	2026-06-13 23:28:49.366944+03	\N	\N	[]	\N	0	0	square	80	80	\N
5385f35d-6460-48d5-9299-8eb7d2b56ad9	c79080f9-500d-4a40-893c-491e10860cc7	1	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI1MjksInN1YiI6IjUzODVmMzVkLTY0NjAtNDhkNS05Mjk5LThlYjdkMmI1NmFkOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzkwODBmOS01MDBkLTRhNDAtODkzYy00OTFlMTA4NjBjYzciLCJ0YWJsZV9udW1iZXIiOjF9.RhmzEgs-uOxeSmBu8Jv4u6zYH6sZ2auPdZm2hFVNmPQ	2026-06-13 23:28:49.366944+03	\N	\N	[]	\N	0	0	square	80	80	\N
8acb8e7e-d8a5-4c32-900c-dbcdaefc06a2	c79080f9-500d-4a40-893c-491e10860cc7	2	4	Main Hall	occupied	39c26be3-8d32-494f-a65c-2a9c1fba3651	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTY3NDI1MjksInN1YiI6IjhhY2I4ZTdlLWQ4YTUtNGMzMi05MDBjLWRiY2RhZWZjMDZhMiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJjNzkwODBmOS01MDBkLTRhNDAtODkzYy00OTFlMTA4NjBjYzciLCJ0YWJsZV9udW1iZXIiOjJ9.AlJjqJd2cNB2MdIEpHKSWfOrlM0YDN3O6ON3thp70T4	2026-06-13 23:28:49.366944+03	2026-06-13 20:28:51.360491+03	\N	[]	\N	0	0	square	80	80	\N
2764dc8b-4b3b-43cd-8dde-eb4adef44d68	85d9b191-1dbb-4245-aa75-8e2fff19766f	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjI3NjRkYzhiLTRiM2ItNDNjZC04ZGRlLWViNGFkZWY0NGQ2OCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NWQ5YjE5MS0xZGJiLTQyNDUtYWE3NS04ZTJmZmYxOTc2NmYiLCJ0YWJsZV9udW1iZXIiOjN9.6VeSqzq0Q94C4nJ89AVKLaHT_qRLd3dwsT8bbpNAPW8	2026-05-25 23:33:21.891987+03	\N	\N	[]	\N	0	0	square	80	80	\N
deff9d38-4c21-423f-934a-2bfbfbddb014	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImRlZmY5ZDM4LTRjMjEtNDIzZi05MzRhLTJiZmJmYmRkYjAxNCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIzZWE1NjdhYS00Y2ZjLTQ2OTctOWVjOS1jZjRlYjIzZWVjNzQiLCJ0YWJsZV9udW1iZXIiOjR9.9iuW0Z_AozP0On_J16ARs8QNDAYIncOZrexn0BUIhkA	2026-05-26 23:40:42.387022+03	\N	\N	[]	\N	0	0	square	80	80	\N
82b17efd-8f54-43de-9319-ee16719c0a9e	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjgyYjE3ZWZkLThmNTQtNDNkZS05MzE5LWVlMTY3MTljMGE5ZSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIzZWE1NjdhYS00Y2ZjLTQ2OTctOWVjOS1jZjRlYjIzZWVjNzQiLCJ0YWJsZV9udW1iZXIiOjV9.p5T-LwNBP8Z6GDXn3CXnpLao0Xi-be_Swj3BqF8jKbI	2026-05-26 23:40:42.387022+03	\N	\N	[]	\N	0	0	square	80	80	\N
4628c3a2-7eff-4cb2-bda7-0c8839839723	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjQ2MjhjM2EyLTdlZmYtNGNiMi1iZGE3LTBjODgzOTgzOTcyMyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NTc4ZGIwNS02MGU4LTQ5ZTMtYTljNS0wYzVlYjlmNWM1MjgiLCJ0YWJsZV9udW1iZXIiOjJ9.1Deq9J2LwRh3xZukxcO3hHGiXuoHwwgtc-nGWjl0d5I	2026-05-07 23:16:40.331015+03	\N	\N	[]	\N	0	0	square	80	80	\N
5c3d6f5b-b0e8-4828-8cf7-504ddb226d41	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjVjM2Q2ZjViLWIwZTgtNDgyOC04Y2Y3LTUwNGRkYjIyNmQ0MSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NTc4ZGIwNS02MGU4LTQ5ZTMtYTljNS0wYzVlYjlmNWM1MjgiLCJ0YWJsZV9udW1iZXIiOjN9.kzdKfdcMBWGvcYA5Md6GxMwh1HUXIaP8eyJHVnTT62U	2026-05-07 23:16:40.331015+03	\N	\N	[]	\N	0	0	square	80	80	\N
3a1cd853-e4a7-4078-9dcf-85524d5267fe	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjNhMWNkODUzLWU0YTctNDA3OC05ZGNmLTg1NTI0ZDUyNjdmZSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NTc4ZGIwNS02MGU4LTQ5ZTMtYTljNS0wYzVlYjlmNWM1MjgiLCJ0YWJsZV9udW1iZXIiOjR9.URHyDJxF-5MVXEoL-w9Ek1EyazrvppvxKfwi-b98CXU	2026-05-07 23:16:40.331015+03	\N	\N	[]	\N	0	0	square	80	80	\N
0373f19e-aa06-432a-8fef-907d60e2e5e3	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjAzNzNmMTllLWFhMDYtNDMyYS04ZmVmLTkwN2Q2MGUyZTVlMyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NTc4ZGIwNS02MGU4LTQ5ZTMtYTljNS0wYzVlYjlmNWM1MjgiLCJ0YWJsZV9udW1iZXIiOjV9.hyfC6zT0dL2tWAr_nct-EaTw5DzuzzwE7BQH4Lwz1dc	2026-05-07 23:16:40.331015+03	\N	\N	[]	\N	0	0	square	80	80	\N
b0e986eb-86e7-434d-96ed-761a3956fb36	8578db05-60e8-49e3-a9c5-0c5eb9f5c528	1	4	Main Hall	occupied	7b4a3f6e-cc23-467c-8f67-1c9c88ac99d9	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImIwZTk4NmViLTg2ZTctNDM0ZC05NmVkLTc2MWEzOTU2ZmIzNiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NTc4ZGIwNS02MGU4LTQ5ZTMtYTljNS0wYzVlYjlmNWM1MjgiLCJ0YWJsZV9udW1iZXIiOjF9.6fdY6ZZabWTCkiC6YtJ59lgrmx_x4BK0HFr5jq6C93A	2026-05-07 23:16:40.331015+03	\N	\N	[]	\N	0	0	square	80	80	\N
c56e43f2-8df3-4bb7-b329-235ffc5c905e	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImM1NmU0M2YyLThkZjMtNGJiNy1iMzI5LTIzNWZmYzVjOTA1ZSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZmQwMmFiYi00MGJlLTQ1ZTYtOWZiMC1iNTdhYTdlNzNiOTgiLCJ0YWJsZV9udW1iZXIiOjJ9.XpLcOHVLLf4OTfPJcpLoTR1nRnEa6PJ3NGR0MfuAgBA	2026-05-07 23:17:18.537046+03	\N	\N	[]	\N	0	0	square	80	80	\N
1756511e-b627-4754-85e6-7751609d0d9d	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjE3NTY1MTFlLWI2MjctNDc1NC04NWU2LTc3NTE2MDlkMGQ5ZCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZmQwMmFiYi00MGJlLTQ1ZTYtOWZiMC1iNTdhYTdlNzNiOTgiLCJ0YWJsZV9udW1iZXIiOjN9.gO6-oV6T4h6_2Dch2wokWkf4Arh3DFUatS9WA2x4U_A	2026-05-07 23:17:18.537046+03	\N	\N	[]	\N	0	0	square	80	80	\N
84af7c28-d58f-4571-9f6c-d3d1f40b6c9c	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6Ijg0YWY3YzI4LWQ1OGYtNDU3MS05ZjZjLWQzZDFmNDBiNmM5YyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZmQwMmFiYi00MGJlLTQ1ZTYtOWZiMC1iNTdhYTdlNzNiOTgiLCJ0YWJsZV9udW1iZXIiOjR9.I-_o7xgmDYdehRHrFWO1w3yq01MsRjuk2Uk6vFIxgCw	2026-05-07 23:17:18.537046+03	\N	\N	[]	\N	0	0	square	80	80	\N
d24fdc82-29d2-46b9-ac3c-f141511b212f	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImQyNGZkYzgyLTI5ZDItNDZiOS1hYzNjLWYxNDE1MTFiMjEyZiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZmQwMmFiYi00MGJlLTQ1ZTYtOWZiMC1iNTdhYTdlNzNiOTgiLCJ0YWJsZV9udW1iZXIiOjV9.MoppjZjk63Xc8jhTB42pGOGg7UxY082lbyHjOScoTng	2026-05-07 23:17:18.537046+03	\N	\N	[]	\N	0	0	square	80	80	\N
3b8bd374-3146-4d16-af12-aaac148d91b6	bfd02abb-40be-45e6-9fb0-b57aa7e73b98	1	4	Main Hall	occupied	f0bb844b-dce8-487a-8159-10cd37c61340	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjNiOGJkMzc0LTMxNDYtNGQxNi1hZjEyLWFhYWMxNDhkOTFiNiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZmQwMmFiYi00MGJlLTQ1ZTYtOWZiMC1iNTdhYTdlNzNiOTgiLCJ0YWJsZV9udW1iZXIiOjF9.DV-7McA6rAYwUNIujnYwWDuAeuxlnDnkzyO2rCCLtJ4	2026-05-07 23:17:18.537046+03	\N	\N	[]	\N	0	0	square	80	80	\N
7e789848-5dc4-49fb-bf2f-096075ad3f77	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	1	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjdlNzg5ODQ4LTVkYzQtNDlmYi1iZjJmLTA5NjA3NWFkM2Y3NyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI2ZDE3ZTg3YS00YTRiLTQ4NjMtYTlhNy03YWUxYjcwNDNiYTQiLCJ0YWJsZV9udW1iZXIiOjF9.dpnOD-SkNJnkt4-1M4v9JtB8aTofe1Q2crVoxMwdBZ4	2026-05-07 23:18:27.622415+03	\N	\N	[]	\N	0	0	square	80	80	\N
69aa03b4-8dba-4022-9b4b-f8091ec9a06c	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjY5YWEwM2I0LThkYmEtNDAyMi05YjRiLWY4MDkxZWM5YTA2YyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI2ZDE3ZTg3YS00YTRiLTQ4NjMtYTlhNy03YWUxYjcwNDNiYTQiLCJ0YWJsZV9udW1iZXIiOjJ9.Sib5yBa7GkZudoMBfnGdr21qkXERDcNCKvi98z1PZ6M	2026-05-07 23:18:27.622415+03	\N	\N	[]	\N	0	0	square	80	80	\N
cc513c8f-bcf1-4002-b175-2888fd73f1d9	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImNjNTEzYzhmLWJjZjEtNDAwMi1iMTc1LTI4ODhmZDczZjFkOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI2ZDE3ZTg3YS00YTRiLTQ4NjMtYTlhNy03YWUxYjcwNDNiYTQiLCJ0YWJsZV9udW1iZXIiOjV9.sSggk9qe45LMp6jJWNX5Lt__hrnSsdzhcC42vz-YrTA	2026-05-07 23:18:27.622415+03	\N	\N	[]	\N	0	0	square	80	80	\N
11b74d86-c2ec-4f0a-8ac6-5c577e37c5c7	6d17e87a-4a4b-4863-a9a7-7ae1b7043ba4	4	4	Main Hall	occupied	c10265a3-b32b-46e8-8475-6a14f5511ae0	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjExYjc0ZDg2LWMyZWMtNGYwYS04YWM2LTVjNTc3ZTM3YzVjNyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI2ZDE3ZTg3YS00YTRiLTQ4NjMtYTlhNy03YWUxYjcwNDNiYTQiLCJ0YWJsZV9udW1iZXIiOjR9.FplZWu3mt61hq8XYTT0y1RJ3j1XBVKmb_1e3rIxdqtM	2026-05-07 23:18:27.622415+03	\N	\N	[]	\N	0	0	square	80	80	\N
c6c1e5cd-26d7-46cf-8f2f-c12f50beba14	02de8b85-bc5b-4651-a33d-b8985011a099	1	4	Main Hall	occupied	eb68be03-2c42-4afc-8cd0-7806e4ad3b00	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImM2YzFlNWNkLTI2ZDctNDZjZi04ZjJmLWMxMmY1MGJlYmExNCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMmRlOGI4NS1iYzViLTQ2NTEtYTMzZC1iODk4NTAxMWEwOTkiLCJ0YWJsZV9udW1iZXIiOjF9.O5J4c7lKo8xUG2gb3pLYQNtvQoM5FR6Gt5Z-suQSGgg	2026-05-07 23:19:27.988187+03	\N	\N	[]	\N	0	0	square	80	80	\N
98483ac4-4505-4c7e-b369-de6f656a16bb	02de8b85-bc5b-4651-a33d-b8985011a099	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6Ijk4NDgzYWM0LTQ1MDUtNGM3ZS1iMzY5LWRlNmY2NTZhMTZiYiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMmRlOGI4NS1iYzViLTQ2NTEtYTMzZC1iODk4NTAxMWEwOTkiLCJ0YWJsZV9udW1iZXIiOjN9.swu5quYP_dUxyL4wLlbU1xK1yR3l5uziKZDtAn4IsXs	2026-05-07 23:19:27.988187+03	\N	\N	[]	\N	0	0	square	80	80	\N
2c1c5cb3-7fd7-4fc3-95ea-1b1c7b16deff	02de8b85-bc5b-4651-a33d-b8985011a099	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjJjMWM1Y2IzLTdmZDctNGZjMy05NWVhLTFiMWM3YjE2ZGVmZiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMmRlOGI4NS1iYzViLTQ2NTEtYTMzZC1iODk4NTAxMWEwOTkiLCJ0YWJsZV9udW1iZXIiOjR9.CMEaYmsXndTGzOqDfBu6QNhF0cb8flLhyT060AXxqSU	2026-05-07 23:19:27.988187+03	\N	\N	[]	\N	0	0	square	80	80	\N
9953c875-6c6d-4b8a-aff9-7083df86ea2b	02de8b85-bc5b-4651-a33d-b8985011a099	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6Ijk5NTNjODc1LTZjNmQtNGI4YS1hZmY5LTcwODNkZjg2ZWEyYiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMmRlOGI4NS1iYzViLTQ2NTEtYTMzZC1iODk4NTAxMWEwOTkiLCJ0YWJsZV9udW1iZXIiOjV9.pjtqUWF_4hfQMe4iqerGnTj-3eZHkIoi8qKLWvQLaKo	2026-05-07 23:19:27.988187+03	\N	\N	[]	\N	0	0	square	80	80	\N
3d3d88ff-1bde-4a77-8c1f-102c175f7049	bf7d7043-ce4a-40a5-beed-c2789606f922	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjNkM2Q4OGZmLTFiZGUtNGE3Ny04YzFmLTEwMmMxNzVmNzA0OSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZjdkNzA0My1jZTRhLTQwYTUtYmVlZC1jMjc4OTYwNmY5MjIiLCJ0YWJsZV9udW1iZXIiOjJ9.ZIw0e2esQGKy9X0A2x3euRAWYK_19duKPELDoTnILf4	2026-05-08 00:03:06.516245+03	\N	\N	[]	\N	0	0	square	80	80	\N
f2070d2d-2acf-48c8-9052-278d05f4be7d	bf7d7043-ce4a-40a5-beed-c2789606f922	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImYyMDcwZDJkLTJhY2YtNDhjOC05MDUyLTI3OGQwNWY0YmU3ZCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZjdkNzA0My1jZTRhLTQwYTUtYmVlZC1jMjc4OTYwNmY5MjIiLCJ0YWJsZV9udW1iZXIiOjN9.qvEHC439O0dhhlA8IdADkvnnk4lztyzDm5grdrDUXhI	2026-05-08 00:03:06.516245+03	\N	\N	[]	\N	0	0	square	80	80	\N
7fef9f9d-2f78-47ae-95d5-688f16a37174	bf7d7043-ce4a-40a5-beed-c2789606f922	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjdmZWY5ZjlkLTJmNzgtNDdhZS05NWQ1LTY4OGYxNmEzNzE3NCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZjdkNzA0My1jZTRhLTQwYTUtYmVlZC1jMjc4OTYwNmY5MjIiLCJ0YWJsZV9udW1iZXIiOjR9.ZmZ-LNzufj8n_9If6ZGhTJxAUR7LXg-HjQ7lCzrdnmk	2026-05-08 00:03:06.516245+03	\N	\N	[]	\N	0	0	square	80	80	\N
e719bd38-5f7c-45cb-819c-d9b68a4ef634	bf7d7043-ce4a-40a5-beed-c2789606f922	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImU3MTliZDM4LTVmN2MtNDVjYi04MTljLWQ5YjY4YTRlZjYzNCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZjdkNzA0My1jZTRhLTQwYTUtYmVlZC1jMjc4OTYwNmY5MjIiLCJ0YWJsZV9udW1iZXIiOjV9.LUmELvFWFlEDvehBNaqdLP-xhaveBojIAjYXwOItib8	2026-05-08 00:03:06.516245+03	\N	\N	[]	\N	0	0	square	80	80	\N
342ca64a-4456-4d4c-92a3-12cc454f17ed	bf7d7043-ce4a-40a5-beed-c2789606f922	1	4	Main Hall	occupied	674b3ffe-d46e-4b80-b1af-1809c250f5e1	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjM0MmNhNjRhLTQ0NTYtNGQ0Yy05MmEzLTEyY2M0NTRmMTdlZCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiZjdkNzA0My1jZTRhLTQwYTUtYmVlZC1jMjc4OTYwNmY5MjIiLCJ0YWJsZV9udW1iZXIiOjF9.9604YFibCmCKZ0ev7ah6hGr7vJmfXFdJ0q_UmrvrznI	2026-05-08 00:03:06.516245+03	\N	\N	[]	\N	0	0	square	80	80	\N
5e0ac086-033a-47d0-b5c4-607418773627	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjVlMGFjMDg2LTAzM2EtNDdkMC1iNWM0LTYwNzQxODc3MzYyNyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMGY0YzNkNC03OTU0LTRlM2UtOWQ1ZC1jMDg2YTMxZWFiMmEiLCJ0YWJsZV9udW1iZXIiOjJ9.lut3NpTrVaqwuWaUvFW4G8mrmTAjBUu1Y5AXCZopdqA	2026-05-25 22:44:51.962247+03	\N	\N	[]	\N	0	0	square	80	80	\N
1978fcec-18d6-4bfa-a8bc-99f3bf3bc18f	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjE5NzhmY2VjLTE4ZDYtNGJmYS1hOGJjLTk5ZjNiZjNiYzE4ZiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMGY0YzNkNC03OTU0LTRlM2UtOWQ1ZC1jMDg2YTMxZWFiMmEiLCJ0YWJsZV9udW1iZXIiOjN9.dqO9D0AXSL9DM0QROGNy8jt5iAABaM5N9BCdC3_6aeI	2026-05-25 22:44:51.962247+03	\N	\N	[]	\N	0	0	square	80	80	\N
dd290aaf-b62f-4ebf-8dd3-df6c1a49d539	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImRkMjkwYWFmLWI2MmYtNGViZi04ZGQzLWRmNmMxYTQ5ZDUzOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMGY0YzNkNC03OTU0LTRlM2UtOWQ1ZC1jMDg2YTMxZWFiMmEiLCJ0YWJsZV9udW1iZXIiOjR9.SplSyveaxey1iDrub1pRuvEcOAO-3CJof9FOAf46nhs	2026-05-25 22:44:51.962247+03	\N	\N	[]	\N	0	0	square	80	80	\N
0cf921ec-fa96-439d-a8e6-ab325247ce5c	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjBjZjkyMWVjLWZhOTYtNDM5ZC1hOGU2LWFiMzI1MjQ3Y2U1YyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMGY0YzNkNC03OTU0LTRlM2UtOWQ1ZC1jMDg2YTMxZWFiMmEiLCJ0YWJsZV9udW1iZXIiOjV9.eH4BbgVwkx3xWJBz44H_973BpEk0ukSrSPYiRJKqCyM	2026-05-25 22:44:51.962247+03	\N	\N	[]	\N	0	0	square	80	80	\N
08f9a1ae-07fd-46ed-96be-a76a3b39c83c	00f4c3d4-7954-4e3e-9d5d-c086a31eab2a	1	4	Main Hall	occupied	1bee3ad9-47b6-4337-a9e3-e0d821950b93	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjA4ZjlhMWFlLTA3ZmQtNDZlZC05NmJlLWE3NmEzYjM5YzgzYyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIwMGY0YzNkNC03OTU0LTRlM2UtOWQ1ZC1jMDg2YTMxZWFiMmEiLCJ0YWJsZV9udW1iZXIiOjF9.JpkMJcCWFxl19AjiJIxZ4qFo1CFCbQv-_swEH49Zrrc	2026-05-25 22:44:51.962247+03	\N	\N	[]	\N	0	0	square	80	80	\N
4eadfd72-9597-4359-9f57-f3839ab8fc87	85d9b191-1dbb-4245-aa75-8e2fff19766f	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjRlYWRmZDcyLTk1OTctNDM1OS05ZjU3LWYzODM5YWI4ZmM4NyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NWQ5YjE5MS0xZGJiLTQyNDUtYWE3NS04ZTJmZmYxOTc2NmYiLCJ0YWJsZV9udW1iZXIiOjJ9.DFF7Uo5Bl0I9vv_Zd1cxO2u8QVZJUBjwBeejl7wsop0	2026-05-25 23:33:21.891987+03	\N	\N	[]	\N	0	0	square	80	80	\N
f67b44b5-d9a9-44e5-b766-b6bef06d6db0	85d9b191-1dbb-4245-aa75-8e2fff19766f	1	4	Main Hall	occupied	9545d1f4-be0c-41de-b8f1-de3cb6b2ae0b	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImY2N2I0NGI1LWQ5YTktNDRlNS1iNzY2LWI2YmVmMDZkNmRiMCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NWQ5YjE5MS0xZGJiLTQyNDUtYWE3NS04ZTJmZmYxOTc2NmYiLCJ0YWJsZV9udW1iZXIiOjF9.S6Ibnj--xAgvdef5VZ3_QNyLSVFWSnv2kqzxLkBfalM	2026-05-25 23:33:21.891987+03	\N	\N	[]	\N	0	0	square	80	80	\N
2e5f81e7-558c-4b67-b4d1-95dfc85e2746	85d9b191-1dbb-4245-aa75-8e2fff19766f	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjJlNWY4MWU3LTU1OGMtNGI2Ny1iNGQxLTk1ZGZjODVlMjc0NiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NWQ5YjE5MS0xZGJiLTQyNDUtYWE3NS04ZTJmZmYxOTc2NmYiLCJ0YWJsZV9udW1iZXIiOjR9.uymP8CpHetOgLxRScTJIzjSvdpK046_PyDQZhSAIBAc	2026-05-25 23:33:21.891987+03	\N	\N	[]	\N	0	0	square	80	80	\N
431c185b-f9d8-42ec-ba43-18396c5b6c43	85d9b191-1dbb-4245-aa75-8e2fff19766f	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjQzMWMxODViLWY5ZDgtNDJlYy1iYTQzLTE4Mzk2YzViNmM0MyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4NWQ5YjE5MS0xZGJiLTQyNDUtYWE3NS04ZTJmZmYxOTc2NmYiLCJ0YWJsZV9udW1iZXIiOjV9.5PozAjCs4stAcZ1_dgI6KODhdpxDFmY9z01vuh8lTlc	2026-05-25 23:33:21.891987+03	\N	\N	[]	\N	0	0	square	80	80	\N
4b8e94d3-db11-4508-84e5-1cb1029ca005	8c436214-34b0-490d-b798-51349dce3728	1	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjRiOGU5NGQzLWRiMTEtNDUwOC04NGU1LTFjYjEwMjljYTAwNSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjF9.k3FtzzGQTPBD8aA1rYlj9s3IbjSBZYASrFxAhROvKWk	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
9dc02e6f-9c12-4160-ac53-774ee2abc5d1	8c436214-34b0-490d-b798-51349dce3728	2	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjlkYzAyZTZmLTljMTItNDE2MC1hYzUzLTc3NGVlMmFiYzVkMSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjJ9.HS3XdjNT0YTCmewFmeoN_o4rxvC40obRqUDjUaKV6SI	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
bc50caeb-7488-4b7d-857c-c1c34b194cad	8c436214-34b0-490d-b798-51349dce3728	3	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImJjNTBjYWViLTc0ODgtNGI3ZC04NTdjLWMxYzM0YjE5NGNhZCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjN9.MyZZ5LDaqN6qPAUIlJrIhym-kSB4VzTno6KZuJjMip0	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
d251ca58-215b-4e37-9485-607e1999c844	8c436214-34b0-490d-b798-51349dce3728	4	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImQyNTFjYTU4LTIxNWItNGUzNy05NDg1LTYwN2UxOTk5Yzg0NCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjR9.XDXTiItPj6ICUmd7ogT8n_YiWkVP9V5Bo7c6AhEcK1Q	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
aefb70fa-58e4-4529-b814-2884d68578eb	8c436214-34b0-490d-b798-51349dce3728	5	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImFlZmI3MGZhLTU4ZTQtNDUyOS1iODE0LTI4ODRkNjg1NzhlYiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjV9.ri035IFvgozfiIYtq_wfC1NeJDvscBbXSQkRzelG7Jc	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
ef245f00-b29f-479c-b56d-7a3d2b916262	8c436214-34b0-490d-b798-51349dce3728	6	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImVmMjQ1ZjAwLWIyOWYtNDc5Yy1iNTZkLTdhM2QyYjkxNjI2MiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjZ9.kET0CK-m8r0ciyB41uJEvlK8ld9ecD4FKaxcoGB9Usw	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
339c717c-e0fc-49e3-9790-d8b67cad0d94	8c436214-34b0-490d-b798-51349dce3728	7	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjMzOWM3MTdjLWUwZmMtNDllMy05NzkwLWQ4YjY3Y2FkMGQ5NCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjd9.Va_5CoFLTTZNrMW6OVscx4ZhxUf8rrlwIrG5sljrE78	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
14d9b377-7d02-4a0d-ba94-e861c6dec188	8c436214-34b0-490d-b798-51349dce3728	8	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjE0ZDliMzc3LTdkMDItNGEwZC1iYTk0LWU4NjFjNmRlYzE4OCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjh9.pkvBiBLSWaDOmYsKJSIA7uCHT7LArWsLxGDWjfToCWA	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
d5a5b1cd-760e-4283-b6ea-0c4e92139311	8c436214-34b0-490d-b798-51349dce3728	9	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImQ1YTViMWNkLTc2MGUtNDI4My1iNmVhLTBjNGU5MjEzOTMxMSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjl9.7F55quHzAG6GpxSn40yWVI9X1Yx1vrwx_EXRSfA3Ep4	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
c04554b4-cb1e-426b-8f9e-d673369bb3d0	8c436214-34b0-490d-b798-51349dce3728	10	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImMwNDU1NGI0LWNiMWUtNDI2Yi04ZjllLWQ2NzMzNjliYjNkMCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YzQzNjIxNC0zNGIwLTQ5MGQtYjc5OC01MTM0OWRjZTM3MjgiLCJ0YWJsZV9udW1iZXIiOjEwfQ.o3jHLjTrMs2XdjQDHlME9uhFzwxLhcO9jvsAoG86JE4	2026-05-26 00:43:29.010367+03	\N	\N	[]	\N	0	0	square	80	80	\N
dcd81a8e-f3c8-4469-8646-cf00a5581199	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImRjZDgxYThlLWYzYzgtNDQ2OS04NjQ2LWNmMDBhNTU4MTE5OSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIzZWE1NjdhYS00Y2ZjLTQ2OTctOWVjOS1jZjRlYjIzZWVjNzQiLCJ0YWJsZV9udW1iZXIiOjJ9.RmQNn2PavC4TCPCz4JdiXoGWMEqM75w91UNwIYVkPD0	2026-05-26 23:40:42.387022+03	\N	\N	[]	\N	0	0	square	80	80	\N
cc41a8d8-360f-4257-982a-63b743675b37	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImNjNDFhOGQ4LTM2MGYtNDI1Ny05ODJhLTYzYjc0MzY3NWIzNyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIzZWE1NjdhYS00Y2ZjLTQ2OTctOWVjOS1jZjRlYjIzZWVjNzQiLCJ0YWJsZV9udW1iZXIiOjN9.s6kZYRNcQMZui8X3XcXb_mukTJyerafcQgqOLA0hi-0	2026-05-26 23:40:42.387022+03	\N	\N	[]	\N	0	0	square	80	80	\N
83f5ef90-d42e-4e74-8265-890137ef12f9	3ea567aa-4cfc-4697-9ec9-cf4eb23eec74	1	4	Main Hall	occupied	4a555c37-870a-4362-b712-e23b8c0e15ab	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjgzZjVlZjkwLWQ0MmUtNGU3NC04MjY1LTg5MDEzN2VmMTJmOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiIzZWE1NjdhYS00Y2ZjLTQ2OTctOWVjOS1jZjRlYjIzZWVjNzQiLCJ0YWJsZV9udW1iZXIiOjF9._MbE2BeyczKGRHJw21kN1akAi7j5PVvUhnnHum3V620	2026-05-26 23:40:42.387022+03	\N	\N	[]	\N	0	0	square	80	80	\N
4f6553e1-6ea3-426a-8c37-f34f52d5bfef	b39c5777-e4db-4d70-962e-1a92220ec9e9	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjRmNjU1M2UxLTZlYTMtNDI2YS04YzM3LWYzNGY1MmQ1YmZlZiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiMzljNTc3Ny1lNGRiLTRkNzAtOTYyZS0xYTkyMjIwZWM5ZTkiLCJ0YWJsZV9udW1iZXIiOjJ9.XKVuHP4xwvLZWiKvvSej1fZqT3gt_dnhiA9lWNjY3VE	2026-05-26 23:45:06.495353+03	\N	\N	[]	\N	0	0	square	80	80	\N
1d1505c7-5715-4750-bf40-3115836ab7b5	b39c5777-e4db-4d70-962e-1a92220ec9e9	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjFkMTUwNWM3LTU3MTUtNDc1MC1iZjQwLTMxMTU4MzZhYjdiNSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiMzljNTc3Ny1lNGRiLTRkNzAtOTYyZS0xYTkyMjIwZWM5ZTkiLCJ0YWJsZV9udW1iZXIiOjN9.Tc7ivOJVsWw_JTxSXkqnJ23Nx-nSswQWGhMz1IPDnXQ	2026-05-26 23:45:06.495353+03	\N	\N	[]	\N	0	0	square	80	80	\N
a034eb18-4bce-4971-b3a9-3637834b6b16	b39c5777-e4db-4d70-962e-1a92220ec9e9	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImEwMzRlYjE4LTRiY2UtNDk3MS1iM2E5LTM2Mzc4MzRiNmIxNiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiMzljNTc3Ny1lNGRiLTRkNzAtOTYyZS0xYTkyMjIwZWM5ZTkiLCJ0YWJsZV9udW1iZXIiOjR9.KuBPBKQhhu7XJEDS5ngXDcJLi0JSNZd4_1AgHpXbLAE	2026-05-26 23:45:06.495353+03	\N	\N	[]	\N	0	0	square	80	80	\N
4686a55f-e84b-478b-b746-188af0709a55	b39c5777-e4db-4d70-962e-1a92220ec9e9	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjQ2ODZhNTVmLWU4NGItNDc4Yi1iNzQ2LTE4OGFmMDcwOWE1NSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiMzljNTc3Ny1lNGRiLTRkNzAtOTYyZS0xYTkyMjIwZWM5ZTkiLCJ0YWJsZV9udW1iZXIiOjV9.njvM4vqwZsh24mYp3974U4vs6-7nvCT7jkMul5WATl8	2026-05-26 23:45:06.495353+03	\N	\N	[]	\N	0	0	square	80	80	\N
12691e11-36ca-48c1-9b4d-ae251a2511e0	b39c5777-e4db-4d70-962e-1a92220ec9e9	1	4	Main Hall	occupied	5025765e-6da6-48db-9735-6ea5e9c8d696	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjEyNjkxZTExLTM2Y2EtNDhjMS05YjRkLWFlMjUxYTI1MTFlMCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJiMzljNTc3Ny1lNGRiLTRkNzAtOTYyZS0xYTkyMjIwZWM5ZTkiLCJ0YWJsZV9udW1iZXIiOjF9.D1GcOUHLV86OheiOgILB4GZp1IOSN_3-cIXTKiPIbE4	2026-05-26 23:45:06.495353+03	\N	\N	[]	\N	0	0	square	80	80	\N
89c95dfd-1c80-48fc-a0b8-8296e9fd8ea9	7d13a11b-9373-4669-8d53-d2a041014c93	2	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6Ijg5Yzk1ZGZkLTFjODAtNDhmYy1hMGI4LTgyOTZlOWZkOGVhOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjJ9.5WL8RvNUbJYZMy0axIqsubCI3wKPUt2YOXzUPBGF6m8	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
929f931f-4d80-4b61-bea3-d47caa573d4f	7d13a11b-9373-4669-8d53-d2a041014c93	3	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjkyOWY5MzFmLTRkODAtNGI2MS1iZWEzLWQ0N2NhYTU3M2Q0ZiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjN9.Ioa8D0_cZ-M-hF7twnfqCtVqO4OzQ3_a4hU85IPE0LQ	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
bd24467b-4ee2-4b6a-a7ac-827f33838140	7d13a11b-9373-4669-8d53-d2a041014c93	4	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImJkMjQ0NjdiLTRlZTItNGI2YS1hN2FjLTgyN2YzMzgzODE0MCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjR9.myWXmvKn0GxRwnyCC_bRbKtATsVaA8p122JU-LP_Nqs	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
c2aa4363-1ef5-4914-ba91-8e28ab67e325	7d13a11b-9373-4669-8d53-d2a041014c93	5	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImMyYWE0MzYzLTFlZjUtNDkxNC1iYTkxLThlMjhhYjY3ZTMyNSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjV9.FFv9iLxtacFM2oQkCOs1kZNEZRtBrD-cXv34A_jb9hw	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
b379351b-5901-46dd-bbfa-c5dc5181be57	7d13a11b-9373-4669-8d53-d2a041014c93	6	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImIzNzkzNTFiLTU5MDEtNDZkZC1iYmZhLWM1ZGM1MTgxYmU1NyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjZ9.wf0zcdX6IXWK5g7M9SQOE_TcuXOfShksFsM21ANXyu8	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
9bbd19c8-179e-4c64-bd83-d9a317299f60	7d13a11b-9373-4669-8d53-d2a041014c93	7	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjliYmQxOWM4LTE3OWUtNGM2NC1iZDgzLWQ5YTMxNzI5OWY2MCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjd9.tfW5vsosq76lNq9_QU45hjNkJtdTzqyf3zeQ5lThrqI	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
e9c8ec2c-9c18-4bdc-ac64-fdc0db93f1e3	7d13a11b-9373-4669-8d53-d2a041014c93	8	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImU5YzhlYzJjLTljMTgtNGJkYy1hYzY0LWZkYzBkYjkzZjFlMyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjh9.-QbpJlWomXCMQUuE6nU4O1jqjrHlJsndAgheXuj1AAI	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
c94499b8-a67b-428f-b6ab-8434f56c60b7	7d13a11b-9373-4669-8d53-d2a041014c93	1	4	\N	occupied	e2b44ef9-24b9-49e3-b564-82013b3dc9ae	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImM5NDQ5OWI4LWE2N2ItNDI4Zi1iNmFiLTg0MzRmNTZjNjBiNyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjF9.Cu6YQRY-B5oBEQh8NwsKB17IQeHJH4kJ682SGUYdhCs	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
ca928dab-67a3-4512-a484-2adc0af721d0	7d13a11b-9373-4669-8d53-d2a041014c93	9	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImNhOTI4ZGFiLTY3YTMtNDUxMi1hNDg0LTJhZGMwYWY3MjFkMCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjl9.nV8emJOgOFVpZkfbbsAiWK3c0hnekptmr5subaNYJhA	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
db9dd40c-d554-427b-93ec-9091d18eba18	7d13a11b-9373-4669-8d53-d2a041014c93	10	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImRiOWRkNDBjLWQ1NTQtNDI3Yi05M2VjLTkwOTFkMThlYmExOCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI3ZDEzYTExYi05MzczLTQ2NjktOGQ1My1kMmEwNDEwMTRjOTMiLCJ0YWJsZV9udW1iZXIiOjEwfQ.Yk-FNEtd9MHmoGiZgqk2u_VCbCfwhEdTVz_vhA1vlVQ	2026-05-26 23:47:39.718759+03	\N	\N	[]	\N	0	0	square	80	80	\N
fee5429d-62cd-4ccb-b7a9-62285eabca5c	5b7a69ce-beec-47b7-b006-f4151e77a7f3	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImZlZTU0MjlkLTYyY2QtNGNjYi1iN2E5LTYyMjg1ZWFiY2E1YyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI1YjdhNjljZS1iZWVjLTQ3YjctYjAwNi1mNDE1MWU3N2E3ZjMiLCJ0YWJsZV9udW1iZXIiOjJ9.7lCUErdYAJxZCRQvlTIsC_HJl9G0QXIrG1GP1Yh_ztw	2026-05-27 00:11:09.657961+03	\N	\N	[]	\N	0	0	square	80	80	\N
6903a65d-d4f9-4c7b-865d-4c17f6c771b5	5b7a69ce-beec-47b7-b006-f4151e77a7f3	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjY5MDNhNjVkLWQ0ZjktNGM3Yi04NjVkLTRjMTdmNmM3NzFiNSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI1YjdhNjljZS1iZWVjLTQ3YjctYjAwNi1mNDE1MWU3N2E3ZjMiLCJ0YWJsZV9udW1iZXIiOjN9.7avjvyM18UUl0pKIg-WizTcylYVCUWdGx6y6_QF2G50	2026-05-27 00:11:09.657961+03	\N	\N	[]	\N	0	0	square	80	80	\N
a5e5884e-2548-4955-be0e-acddb9521c87	5b7a69ce-beec-47b7-b006-f4151e77a7f3	4	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImE1ZTU4ODRlLTI1NDgtNDk1NS1iZTBlLWFjZGRiOTUyMWM4NyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI1YjdhNjljZS1iZWVjLTQ3YjctYjAwNi1mNDE1MWU3N2E3ZjMiLCJ0YWJsZV9udW1iZXIiOjR9.Jz7WTM73domPbBCWJvfOZnwk_-9K1sQ-4PmF28GtNF4	2026-05-27 00:11:09.657961+03	\N	\N	[]	\N	0	0	square	80	80	\N
4d247b2a-2f9b-480e-9e0f-f3651199b42c	5b7a69ce-beec-47b7-b006-f4151e77a7f3	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjRkMjQ3YjJhLTJmOWItNDgwZS05ZTBmLWYzNjUxMTk5YjQyYyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI1YjdhNjljZS1iZWVjLTQ3YjctYjAwNi1mNDE1MWU3N2E3ZjMiLCJ0YWJsZV9udW1iZXIiOjV9.IIXBD04XFVX0MPBCdTuhRG0lSmjhtNztCmGoXjuPhBc	2026-05-27 00:11:09.657961+03	\N	\N	[]	\N	0	0	square	80	80	\N
7b88cab2-7513-440a-b740-3bdca4cc03b8	5b7a69ce-beec-47b7-b006-f4151e77a7f3	1	4	Main Hall	occupied	2f5152fd-76f7-4dae-9c66-a33fd3ce5868	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjdiODhjYWIyLTc1MTMtNDQwYS1iNzQwLTNiZGNhNGNjMDNiOCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI1YjdhNjljZS1iZWVjLTQ3YjctYjAwNi1mNDE1MWU3N2E3ZjMiLCJ0YWJsZV9udW1iZXIiOjF9.1_HTiYRDJc4DJNanrCWmYRlFwKS_L9IUwl1P_yGOq6c	2026-05-27 00:11:09.657961+03	\N	\N	[]	\N	0	0	square	80	80	\N
8162b206-3fd0-4a48-934a-8f7093b0fb28	8bbc1483-4e02-4b06-a59d-d08b34b795b3	1	4	Main Hall	available	\N	\N	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjgxNjJiMjA2LTNmZDAtNGE0OC05MzRhLThmNzA5M2IwZmIyOCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI4YmJjMTQ4My00ZTAyLTRiMDYtYTU5ZC1kMDhiMzRiNzk1YjMiLCJ0YWJsZV9udW1iZXIiOjF9.oyYaFaE_imhdlNW6oAwg3uC3TtzY9lrOByKv4Qil_NI	2026-05-27 00:38:04.747108+03	\N	\N	[]	\N	0	0	square	80	80	\N
58713c50-8732-4dd3-9d46-90513a52dbab	623d31eb-f986-4676-a38b-fca9c15a4636	1	4	Main Hall	occupied	9dafbef7-df1a-491c-aa96-5e6aaf7653ff	\N	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjU4NzEzYzUwLTg3MzItNGRkMy05ZDQ2LTkwNTEzYTUyZGJhYiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiI2MjNkMzFlYi1mOTg2LTQ2NzYtYTM4Yi1mY2E5YzE1YTQ2MzYiLCJ0YWJsZV9udW1iZXIiOjF9.jcbjo9mxFYk618E2ERoI4UklUpH4-jejNMP_ED6Kaa4	2026-05-27 00:38:04.747108+03	\N	\N	[]	\N	0	0	square	80	80	\N
bc5c90b5-57ab-4764-ba94-67d2f46b9958	d7fc9094-3c1d-4eca-864d-6cf3009dea92	1	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImJjNWM5MGI1LTU3YWItNDc2NC1iYTk0LTY3ZDJmNDZiOTk1OCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJkN2ZjOTA5NC0zYzFkLTRlY2EtODY0ZC02Y2YzMDA5ZGVhOTIiLCJ0YWJsZV9udW1iZXIiOjF9.ZjeVPOuvI28EcX350sHGQWryp03FB92XzzxpMpjN9BU	2026-05-27 00:58:54.205299+03	\N	\N	[]	\N	0	0	square	80	80	\N
f7bfd26a-b80b-4c7c-beac-7b82611b2ab7	d7fc9094-3c1d-4eca-864d-6cf3009dea92	2	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImY3YmZkMjZhLWI4MGItNGM3Yy1iZWFjLTdiODI2MTFiMmFiNyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJkN2ZjOTA5NC0zYzFkLTRlY2EtODY0ZC02Y2YzMDA5ZGVhOTIiLCJ0YWJsZV9udW1iZXIiOjJ9.2ZJLb1pBANKryBaoNeN4ANFiG37gJnakkFUMdMJDxio	2026-05-27 00:58:54.205299+03	\N	\N	[]	\N	0	0	square	80	80	\N
15a3fe9f-27af-4287-908c-8b2ad9ffe9e9	d7fc9094-3c1d-4eca-864d-6cf3009dea92	3	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjE1YTNmZTlmLTI3YWYtNDI4Ny05MDhjLThiMmFkOWZmZTllOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJkN2ZjOTA5NC0zYzFkLTRlY2EtODY0ZC02Y2YzMDA5ZGVhOTIiLCJ0YWJsZV9udW1iZXIiOjN9.BnpG2dMVLM1hflNHZYN_0SMQKZw5TRZ7SGeXjzxSbxk	2026-05-27 00:58:54.205299+03	\N	\N	[]	\N	0	0	square	80	80	\N
100c930f-1a59-43df-8548-74b8fab8583d	d7fc9094-3c1d-4eca-864d-6cf3009dea92	5	4	Main Hall	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjEwMGM5MzBmLTFhNTktNDNkZi04NTQ4LTc0YjhmYWI4NTgzZCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJkN2ZjOTA5NC0zYzFkLTRlY2EtODY0ZC02Y2YzMDA5ZGVhOTIiLCJ0YWJsZV9udW1iZXIiOjV9.qVyQqpvNtDMz6E7ii668jyqPhhUu-whLOFt--a4g-e8	2026-05-27 00:58:54.205299+03	\N	\N	[]	\N	0	0	square	80	80	\N
8570fb78-0f53-4ca3-891b-9300fe00face	d7fc9094-3c1d-4eca-864d-6cf3009dea92	4	4	Main Hall	occupied	62a007a4-f63b-49f9-a133-ddd138bc77c4	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6Ijg1NzBmYjc4LTBmNTMtNGNhMy04OTFiLTkzMDBmZTAwZmFjZSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJkN2ZjOTA5NC0zYzFkLTRlY2EtODY0ZC02Y2YzMDA5ZGVhOTIiLCJ0YWJsZV9udW1iZXIiOjR9.bpV4ffGUkqo1DUVfeYUcxIUEhTwP3bYa2Npq_ZJCblY	2026-05-27 00:58:54.205299+03	\N	\N	[]	\N	0	0	square	80	80	\N
c937980d-a04b-469b-9a91-96e9866b546e	e50d5aac-c374-490a-8040-ae3ff526a264	3	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImM5Mzc5ODBkLWEwNGItNDY5Yi05YTkxLTk2ZTk4NjZiNTQ2ZSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjN9.2vnU_EYFy4le-9vKGolxdsHLCfX5tfH-Vi92hoTYM7g	2026-06-07 21:45:03.101325+03	\N	\N	[]	\N	0	0	square	80	80	\N
f61c2599-b647-4a50-a301-f61163fd9e70	e50d5aac-c374-490a-8040-ae3ff526a264	4	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImY2MWMyNTk5LWI2NDctNGE1MC1hMzAxLWY2MTE2M2ZkOWU3MCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjR9.a5MfuOahRfM0hBybDv4eU7wkrYymCIl9Gy3MMIE7FTs	2026-06-07 21:45:03.101325+03	\N	\N	[]	\N	0	0	square	80	80	\N
353c5e8f-7e64-4bc0-a8b4-af0fef8ad78d	e50d5aac-c374-490a-8040-ae3ff526a264	5	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjM1M2M1ZThmLTdlNjQtNGJjMC1hOGI0LWFmMGZlZjhhZDc4ZCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjV9.G1TPpxxSIPlGOZzAe8g63MM0wrxaATjeEpwM2D-wWEU	2026-06-07 21:45:03.101325+03	\N	\N	[]	\N	0	0	square	80	80	\N
9b7d7ca6-f2e7-45aa-a0fa-8e2e0ff331d9	e50d5aac-c374-490a-8040-ae3ff526a264	6	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjliN2Q3Y2E2LWYyZTctNDVhYS1hMGZhLThlMmUwZmYzMzFkOSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjZ9.G54DHgXAoGpch5_v-S8_yUDIS6FQJYRuJDL_iOQl1Ns	2026-06-07 21:45:03.101325+03	\N	\N	[]	\N	0	0	square	80	80	\N
e31c0877-63fa-4613-9b0f-6d9e0a67bdd8	e50d5aac-c374-490a-8040-ae3ff526a264	2	4	\N	occupied	0e6ca96d-c4cb-4551-9179-a2979fb452d0	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImUzMWMwODc3LTYzZmEtNDYxMy05YjBmLTZkOWUwYTY3YmRkOCIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjJ9.UuxEVhB8joFDs9DKNILsxu275bqkMh4VkZ2vk2dscyo	2026-06-07 21:45:03.101325+03	2026-06-15 20:09:27.650883+03	\N	[]	\N	0	0	square	80	80	\N
499c74ba-f24a-449b-b832-912ff5889b7a	e50d5aac-c374-490a-8040-ae3ff526a264	7	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjQ5OWM3NGJhLWYyNGEtNDQ5Yi1iODMyLTkxMmZmNTg4OWI3YSIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjd9.FTMEuf1rIjoEolTeBqwXXhSb4c5C6i5uEo54u7i-_uo	2026-06-07 21:45:03.101325+03	\N	\N	[]	\N	0	0	square	80	80	\N
46cdbf27-75c4-4c4e-83f7-ce7f218e0c0c	e50d5aac-c374-490a-8040-ae3ff526a264	8	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjQ2Y2RiZjI3LTc1YzQtNGM0ZS04M2Y3LWNlN2YyMThlMGMwYyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjh9.1zZBdQcyVgJKHI_9EV-y7l1UpU6F6eNRZU0mLXOphRA	2026-06-07 21:45:03.101325+03	\N	\N	[]	\N	0	0	square	80	80	\N
22fa3f75-8057-4e29-ade9-fb47a41c71df	e50d5aac-c374-490a-8040-ae3ff526a264	9	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6IjIyZmEzZjc1LTgwNTctNGUyOS1hZGU5LWZiNDdhNDFjNzFkZiIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjl9.xBzrI9WTLcpGRUrLTKNVyqr9X4B1okhG--stTWGtiw0	2026-06-07 21:45:03.101325+03	\N	\N	[]	\N	0	0	square	80	80	\N
b8abb7fd-de5f-4fd2-a03e-c87a9d55c863	e50d5aac-c374-490a-8040-ae3ff526a264	10	4	\N	available	\N	https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder=qr_codes	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwOTYzMDc1MDgsInN1YiI6ImI4YWJiN2ZkLWRlNWYtNGZkMi1hMDNlLWM4N2E5ZDU1Yzg2MyIsInR5cGUiOiJ0YWJsZSIsInJlc3RhdXJhbnRfaWQiOiJlNTBkNWFhYy1jMzc0LTQ5MGEtODA0MC1hZTNmZjUyNmEyNjQiLCJ0YWJsZV9udW1iZXIiOjEwfQ.DTHONyf0olPN67Pb_48GX07X5L15FaTQ3EJ1uAC60bc	2026-06-07 21:45:03.101325+03	\N	\N	[]	\N	0	0	square	80	80	\N
\.


--
-- Data for Name: waiter_calls; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.waiter_calls (id, restaurant_id, table_id, message, status, acknowledged_by, created_at) FROM stdin;
\.


--
-- Name: activity_logs activity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: branches branches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branches
    ADD CONSTRAINT branches_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: customer_sessions customer_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_sessions
    ADD CONSTRAINT customer_sessions_pkey PRIMARY KEY (id);


--
-- Name: customer_sessions customer_sessions_session_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_sessions
    ADD CONSTRAINT customer_sessions_session_token_key UNIQUE (session_token);


--
-- Name: floor_elements floor_elements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floor_elements
    ADD CONSTRAINT floor_elements_pkey PRIMARY KEY (id);


--
-- Name: floors floors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floors
    ADD CONSTRAINT floors_pkey PRIMARY KEY (id);


--
-- Name: item_transfers item_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_transfers
    ADD CONSTRAINT item_transfers_pkey PRIMARY KEY (id);


--
-- Name: kitchen_display_settings kitchen_display_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_display_settings
    ADD CONSTRAINT kitchen_display_settings_pkey PRIMARY KEY (id);


--
-- Name: kitchen_routing_rules kitchen_routing_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_routing_rules
    ADD CONSTRAINT kitchen_routing_rules_pkey PRIMARY KEY (id);


--
-- Name: kitchen_stations kitchen_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_stations
    ADD CONSTRAINT kitchen_stations_pkey PRIMARY KEY (id);


--
-- Name: menu_item_modifiers menu_item_modifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_modifiers
    ADD CONSTRAINT menu_item_modifiers_pkey PRIMARY KEY (id);


--
-- Name: menu_items menu_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_pkey PRIMARY KEY (id);


--
-- Name: mpesa_transactions mpesa_transactions_checkout_request_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mpesa_transactions
    ADD CONSTRAINT mpesa_transactions_checkout_request_id_key UNIQUE (checkout_request_id);


--
-- Name: mpesa_transactions mpesa_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mpesa_transactions
    ADD CONSTRAINT mpesa_transactions_pkey PRIMARY KEY (id);


--
-- Name: order_item_modifiers order_item_modifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT order_item_modifiers_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_order_number_key UNIQUE (order_number);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: restaurant_settings restaurant_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_settings
    ADD CONSTRAINT restaurant_settings_pkey PRIMARY KEY (restaurant_id, key);


--
-- Name: restaurants restaurants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_pkey PRIMARY KEY (id);


--
-- Name: restaurants restaurants_prefix_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_prefix_key UNIQUE (prefix);


--
-- Name: restaurants restaurants_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_slug_key UNIQUE (slug);


--
-- Name: restaurants restaurants_subdomain_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_subdomain_key UNIQUE (subdomain);


--
-- Name: staff_activity_logs staff_activity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_activity_logs
    ADD CONSTRAINT staff_activity_logs_pkey PRIMARY KEY (id);


--
-- Name: staff staff_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (id);


--
-- Name: station_prep_times station_prep_times_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.station_prep_times
    ADD CONSTRAINT station_prep_times_pkey PRIMARY KEY (id);


--
-- Name: table_transfer_logs table_transfer_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfer_logs
    ADD CONSTRAINT table_transfer_logs_pkey PRIMARY KEY (id);


--
-- Name: table_transfers table_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfers
    ADD CONSTRAINT table_transfers_pkey PRIMARY KEY (id);


--
-- Name: tables tables_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT tables_pkey PRIMARY KEY (id);


--
-- Name: tables tables_restaurant_id_table_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT tables_restaurant_id_table_number_key UNIQUE (restaurant_id, table_number);


--
-- Name: waiter_calls waiter_calls_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.waiter_calls
    ADD CONSTRAINT waiter_calls_pkey PRIMARY KEY (id);


--
-- Name: idx_branches_restaurant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_branches_restaurant_id ON public.branches USING btree (restaurant_id);


--
-- Name: idx_orders_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_orders_branch_id ON public.orders USING btree (branch_id);


--
-- Name: idx_staff_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_branch_id ON public.staff USING btree (branch_id);


--
-- Name: idx_tables_branch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tables_branch_id ON public.tables USING btree (branch_id);


--
-- Name: activity_logs activity_logs_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: activity_logs activity_logs_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: branches branches_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branches
    ADD CONSTRAINT branches_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: categories categories_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: categories categories_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: customer_sessions customer_sessions_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_sessions
    ADD CONSTRAINT customer_sessions_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: customer_sessions customer_sessions_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_sessions
    ADD CONSTRAINT customer_sessions_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: customer_sessions customer_sessions_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_sessions
    ADD CONSTRAINT customer_sessions_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.tables(id) ON DELETE CASCADE;


--
-- Name: menu_items fk_menu_items_station_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT fk_menu_items_station_id FOREIGN KEY (station_id) REFERENCES public.kitchen_stations(id) ON DELETE SET NULL;


--
-- Name: staff fk_staff_kitchen_station_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT fk_staff_kitchen_station_id FOREIGN KEY (kitchen_station_id) REFERENCES public.kitchen_stations(id) ON DELETE SET NULL;


--
-- Name: floor_elements floor_elements_floor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floor_elements
    ADD CONSTRAINT floor_elements_floor_id_fkey FOREIGN KEY (floor_id) REFERENCES public.floors(id) ON DELETE CASCADE;


--
-- Name: floors floors_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floors
    ADD CONSTRAINT floors_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: item_transfers item_transfers_from_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_transfers
    ADD CONSTRAINT item_transfers_from_session_id_fkey FOREIGN KEY (from_session_id) REFERENCES public.customer_sessions(id) ON DELETE SET NULL;


--
-- Name: item_transfers item_transfers_order_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_transfers
    ADD CONSTRAINT item_transfers_order_item_id_fkey FOREIGN KEY (order_item_id) REFERENCES public.order_items(id) ON DELETE SET NULL;


--
-- Name: item_transfers item_transfers_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_transfers
    ADD CONSTRAINT item_transfers_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE SET NULL;


--
-- Name: item_transfers item_transfers_to_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_transfers
    ADD CONSTRAINT item_transfers_to_session_id_fkey FOREIGN KEY (to_session_id) REFERENCES public.customer_sessions(id) ON DELETE SET NULL;


--
-- Name: item_transfers item_transfers_transferred_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_transfers
    ADD CONSTRAINT item_transfers_transferred_by_fkey FOREIGN KEY (transferred_by) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: kitchen_display_settings kitchen_display_settings_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_display_settings
    ADD CONSTRAINT kitchen_display_settings_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: kitchen_display_settings kitchen_display_settings_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_display_settings
    ADD CONSTRAINT kitchen_display_settings_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.kitchen_stations(id) ON DELETE CASCADE;


--
-- Name: kitchen_routing_rules kitchen_routing_rules_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_routing_rules
    ADD CONSTRAINT kitchen_routing_rules_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: kitchen_routing_rules kitchen_routing_rules_source_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_routing_rules
    ADD CONSTRAINT kitchen_routing_rules_source_station_id_fkey FOREIGN KEY (source_station_id) REFERENCES public.kitchen_stations(id) ON DELETE SET NULL;


--
-- Name: kitchen_routing_rules kitchen_routing_rules_target_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_routing_rules
    ADD CONSTRAINT kitchen_routing_rules_target_station_id_fkey FOREIGN KEY (target_station_id) REFERENCES public.kitchen_stations(id) ON DELETE CASCADE;


--
-- Name: kitchen_stations kitchen_stations_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kitchen_stations
    ADD CONSTRAINT kitchen_stations_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: menu_item_modifiers menu_item_modifiers_menu_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_modifiers
    ADD CONSTRAINT menu_item_modifiers_menu_item_id_fkey FOREIGN KEY (menu_item_id) REFERENCES public.menu_items(id) ON DELETE CASCADE;


--
-- Name: menu_item_modifiers menu_item_modifiers_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_item_modifiers
    ADD CONSTRAINT menu_item_modifiers_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: menu_items menu_items_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: menu_items menu_items_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;


--
-- Name: menu_items menu_items_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: mpesa_transactions mpesa_transactions_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mpesa_transactions
    ADD CONSTRAINT mpesa_transactions_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: order_item_modifiers order_item_modifiers_modifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT order_item_modifiers_modifier_id_fkey FOREIGN KEY (modifier_id) REFERENCES public.menu_item_modifiers(id) ON DELETE RESTRICT;


--
-- Name: order_item_modifiers order_item_modifiers_order_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT order_item_modifiers_order_item_id_fkey FOREIGN KEY (order_item_id) REFERENCES public.order_items(id) ON DELETE CASCADE;


--
-- Name: order_item_modifiers order_item_modifiers_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT order_item_modifiers_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: order_items order_items_menu_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_menu_item_id_fkey FOREIGN KEY (menu_item_id) REFERENCES public.menu_items(id) ON DELETE RESTRICT;


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: orders orders_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: orders orders_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: orders orders_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.customer_sessions(id) ON DELETE CASCADE;


--
-- Name: orders orders_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: orders orders_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.tables(id) ON DELETE SET NULL;


--
-- Name: payments payments_cashier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_cashier_id_fkey FOREIGN KEY (cashier_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: payments payments_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: payments payments_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: restaurant_settings restaurant_settings_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurant_settings
    ADD CONSTRAINT restaurant_settings_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: restaurants restaurants_parent_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_parent_restaurant_id_fkey FOREIGN KEY (parent_restaurant_id) REFERENCES public.restaurants(id);


--
-- Name: staff_activity_logs staff_activity_logs_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_activity_logs
    ADD CONSTRAINT staff_activity_logs_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: staff_activity_logs staff_activity_logs_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_activity_logs
    ADD CONSTRAINT staff_activity_logs_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(id) ON DELETE CASCADE;


--
-- Name: staff staff_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: staff staff_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: station_prep_times station_prep_times_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.station_prep_times
    ADD CONSTRAINT station_prep_times_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: station_prep_times station_prep_times_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.station_prep_times
    ADD CONSTRAINT station_prep_times_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.kitchen_stations(id) ON DELETE CASCADE;


--
-- Name: table_transfer_logs table_transfer_logs_new_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfer_logs
    ADD CONSTRAINT table_transfer_logs_new_table_id_fkey FOREIGN KEY (new_table_id) REFERENCES public.tables(id) ON DELETE CASCADE;


--
-- Name: table_transfer_logs table_transfer_logs_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfer_logs
    ADD CONSTRAINT table_transfer_logs_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: table_transfer_logs table_transfer_logs_original_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfer_logs
    ADD CONSTRAINT table_transfer_logs_original_table_id_fkey FOREIGN KEY (original_table_id) REFERENCES public.tables(id) ON DELETE CASCADE;


--
-- Name: table_transfer_logs table_transfer_logs_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfer_logs
    ADD CONSTRAINT table_transfer_logs_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: table_transfer_logs table_transfer_logs_transferred_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfer_logs
    ADD CONSTRAINT table_transfer_logs_transferred_by_fkey FOREIGN KEY (transferred_by) REFERENCES public.staff(id) ON DELETE CASCADE;


--
-- Name: table_transfers table_transfers_new_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfers
    ADD CONSTRAINT table_transfers_new_table_id_fkey FOREIGN KEY (new_table_id) REFERENCES public.tables(id) ON DELETE SET NULL;


--
-- Name: table_transfers table_transfers_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfers
    ADD CONSTRAINT table_transfers_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE SET NULL;


--
-- Name: table_transfers table_transfers_original_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfers
    ADD CONSTRAINT table_transfers_original_table_id_fkey FOREIGN KEY (original_table_id) REFERENCES public.tables(id) ON DELETE SET NULL;


--
-- Name: table_transfers table_transfers_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfers
    ADD CONSTRAINT table_transfers_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE SET NULL;


--
-- Name: table_transfers table_transfers_transferred_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_transfers
    ADD CONSTRAINT table_transfers_transferred_by_fkey FOREIGN KEY (transferred_by) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: tables tables_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT tables_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branches(id);


--
-- Name: tables tables_floor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT tables_floor_id_fkey FOREIGN KEY (floor_id) REFERENCES public.floors(id);


--
-- Name: tables tables_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT tables_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: waiter_calls waiter_calls_acknowledged_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.waiter_calls
    ADD CONSTRAINT waiter_calls_acknowledged_by_fkey FOREIGN KEY (acknowledged_by) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: waiter_calls waiter_calls_restaurant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.waiter_calls
    ADD CONSTRAINT waiter_calls_restaurant_id_fkey FOREIGN KEY (restaurant_id) REFERENCES public.restaurants(id) ON DELETE CASCADE;


--
-- Name: waiter_calls waiter_calls_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.waiter_calls
    ADD CONSTRAINT waiter_calls_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.tables(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

