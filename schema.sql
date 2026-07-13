BEGIN;

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. ENUM TYPES
CREATE TYPE subscription_plan_enum AS ENUM ('starter', 'pro', 'enterprise');
CREATE TYPE staff_role_enum AS ENUM ('owner', 'manager', 'waiter', 'chef', 'cashier');
CREATE TYPE shift_type_enum AS ENUM ('morning', 'afternoon', 'evening', 'night', 'full');
CREATE TYPE table_status_enum AS ENUM ('available', 'occupied', 'cleaning', 'reserved');
CREATE TYPE order_status_enum AS ENUM ('received', 'pending', 'preparing', 'ready', 'served', 'completed', 'cancelled');
CREATE TYPE payment_status_enum AS ENUM ('pending', 'paid', 'failed', 'refunded', 'partially_paid');
CREATE TYPE payment_method_enum AS ENUM ('cash', 'mpesa', 'card', 'bank_transfer', 'wallet');

-- 3. SEQUENCES
CREATE SEQUENCE order_number_seq START 1 INCREMENT 1;

-- 4. TABLES
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    subdomain TEXT UNIQUE NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    logo_url TEXT,
    subscription_plan subscription_plan_enum DEFAULT 'starter',
    trial_ends_at TIMESTAMPTZ,
    subscription_ends_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    prefix TEXT UNIQUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role staff_role_enum NOT NULL,
    shift shift_type_enum DEFAULT 'full',
    pin_code TEXT NOT NULL,
    assigned_tables JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_active_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT staff_pin_format CHECK (pin_code ~ '^[0-9]{4}$')
);

-- Circular FK for deleted_by
ALTER TABLE restaurants ADD CONSTRAINT fk_restaurants_deleted_by FOREIGN KEY (deleted_by) REFERENCES staff(id) ON DELETE SET NULL;

CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    image_url TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER,
    low_stock_threshold INTEGER DEFAULT 5,
    dietary_info TEXT,
    display_order INTEGER DEFAULT 0,
    preparation_time INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT menu_items_prep_time_check CHECK (preparation_time > 0)
);

CREATE TABLE menu_item_modifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    price DECIMAL(10,2) DEFAULT 0.00,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    table_number INTEGER NOT NULL,
    capacity INTEGER DEFAULT 1,
    location TEXT,
    status table_status_enum DEFAULT 'available',
    current_session_id UUID,
    qr_code_url TEXT,
    qr_code_token TEXT,
    qr_code_printed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(restaurant_id, table_number),
    CONSTRAINT tables_capacity_check CHECK (capacity > 0)
);

CREATE TABLE customer_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    table_id UUID NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    customer_phone TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PARTITIONED TABLE: orders
CREATE TABLE orders (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    table_id UUID REFERENCES tables(id) ON DELETE SET NULL,
    session_id UUID REFERENCES customer_sessions(id) ON DELETE CASCADE,
    staff_id UUID REFERENCES staff(id) ON DELETE SET NULL,
    order_number TEXT,
    notes TEXT,
    status order_status_enum DEFAULT 'received',
    subtotal DECIMAL(10,2) DEFAULT 0,
    tax DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) DEFAULT 0,
    payment_status payment_status_enum DEFAULT 'pending',
    payment_method payment_method_enum,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, created_at),
    CONSTRAINT orders_total_check CHECK (total >= 0)
) PARTITION BY RANGE (created_at);

-- Initial partitions
CREATE TABLE orders_y2026m05 PARTITION OF orders FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE orders_y2026m06 PARTITION OF orders FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE orders_y2026m07 PARTITION OF orders FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    order_created_at TIMESTAMPTZ NOT NULL,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    special_instructions TEXT,
    status order_status_enum DEFAULT 'received',
    started_at TIMESTAMPTZ,
    ready_at TIMESTAMPTZ,
    served_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (order_id, order_created_at) REFERENCES orders(id, created_at) ON DELETE CASCADE,
    CONSTRAINT order_items_qty_check CHECK (quantity > 0)
);

CREATE TABLE order_item_modifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    order_item_id UUID NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    modifier_id UUID NOT NULL REFERENCES menu_item_modifiers(id) ON DELETE RESTRICT,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    order_id UUID NOT NULL,
    order_created_at TIMESTAMPTZ NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method payment_method_enum NOT NULL,
    status payment_status_enum DEFAULT 'pending',
    transaction_id TEXT,
    mpesa_receipt_number TEXT,
    mpesa_result_code INTEGER,
    mpesa_result_description TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (order_id, order_created_at) REFERENCES orders(id, created_at) ON DELETE CASCADE,
    CONSTRAINT payments_amount_check CHECK (amount > 0)
);

CREATE TABLE waiter_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    table_id UUID NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
    message TEXT,
    status TEXT DEFAULT 'pending',
    acknowledged_by UUID REFERENCES staff(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE occasion_menus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT occasion_date_check CHECK (end_at > start_at)
);

CREATE TABLE occasion_menu_items (
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    occasion_menu_id UUID NOT NULL REFERENCES occasion_menus(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    special_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (occasion_menu_id, menu_item_id)
);

CREATE TABLE restaurant_settings (
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    PRIMARY KEY (restaurant_id, key)
);

CREATE TABLE inventory_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    change_amount INTEGER NOT NULL,
    reason TEXT,
    staff_id UUID REFERENCES staff(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    staff_id UUID REFERENCES staff(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE qr_code_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    table_id UUID NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
    session_id UUID REFERENCES customer_sessions(id) ON DELETE SET NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE mpesa_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    checkout_request_id TEXT UNIQUE NOT NULL,
    merchant_request_id TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    mpesa_receipt_number TEXT,
    result_code INTEGER,
    result_desc TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. FUNCTIONS
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION auto_create_monthly_partitions()
RETURNS void AS $$
DECLARE
    next_month DATE;
    table_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    next_month := date_trunc('month', NOW() + INTERVAL '1 month');
    FOR i IN 1..3 LOOP
        table_name := 'orders_y' || to_char(next_month, 'YYYY') || 'm' || to_char(next_month, 'MM');
        start_date := to_char(next_month, 'YYYY-MM-01');
        end_date := to_char(next_month + INTERVAL '1 month', 'YYYY-MM-01');
        IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = table_name) THEN
            EXECUTE format('CREATE TABLE %I PARTITION OF orders FOR VALUES FROM (%L) TO (%L)', table_name, start_date, end_date);
        END IF;
        next_month := next_month + INTERVAL '1 month';
    END LOOP;
END;
$$ language 'plpgsql';

-- 6. TRIGGERS
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
        AND table_name != 'orders'
    LOOP
        EXECUTE format('CREATE TRIGGER trigger_update_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t);
    END LOOP;
END;
$$;

-- 7. INDEXES
CREATE INDEX idx_orders_rest_status_created ON orders (restaurant_id, status, created_at);
CREATE INDEX idx_orders_table_status ON orders (table_id, status);
CREATE INDEX idx_order_items_order_id ON order_items (order_id);
CREATE INDEX idx_payments_order_id ON payments (order_id);
CREATE INDEX idx_menu_items_category ON menu_items (category_id);
CREATE INDEX idx_tables_restaurant ON tables (restaurant_id);
CREATE INDEX idx_customer_sessions_token ON customer_sessions (session_token);
CREATE INDEX idx_mpesa_checkout ON mpesa_transactions (checkout_request_id);

-- 8. VIEWS
CREATE VIEW active_tables_view AS
SELECT restaurant_id, id, table_number, capacity, location
FROM tables
WHERE status = 'occupied';

CREATE VIEW pending_calls_view AS
SELECT restaurant_id, id, table_id, message, created_at
FROM waiter_calls
WHERE status = 'pending';

-- 9. ROW LEVEL SECURITY (RLS)
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name NOT IN ('restaurants', 'orders') 
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = t AND column_name = 'restaurant_id') THEN
            EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
            EXECUTE format('CREATE POLICY tenant_select ON %I FOR SELECT USING (restaurant_id = current_setting(''app.current_restaurant_id'', true)::UUID)', t);
            EXECUTE format('CREATE POLICY tenant_all ON %I FOR ALL USING (restaurant_id = current_setting(''app.current_restaurant_id'', true)::UUID)', t);
        END IF;
    END LOOP;
    -- RLS for orders parent applies to partitions
    ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
    CREATE POLICY tenant_select_orders ON orders FOR SELECT USING (restaurant_id = current_setting('app.current_restaurant_id', true)::UUID);
    CREATE POLICY tenant_all_orders ON orders FOR ALL USING (restaurant_id = current_setting('app.current_restaurant_id', true)::UUID);
END;
$$;

COMMIT;

-- P0 AUDIT FIXES - 2026-05-07
BEGIN;

-- 1. MISSING ENUMS
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscription_status_enum') THEN
        CREATE TYPE subscription_status_enum AS ENUM ('trial', 'active', 'suspended', 'cancelled');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'call_type_enum') THEN
        CREATE TYPE call_type_enum AS ENUM ('assistance', 'water', 'bill', 'other');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'call_status_enum') THEN
        CREATE TYPE call_status_enum AS ENUM ('pending', 'acknowledged', 'completed');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_status_enum') THEN
        CREATE TYPE session_status_enum AS ENUM ('active', 'closed', 'expired');
    END IF;
END $$;

-- 2. MISSING TABLES
CREATE TABLE IF NOT EXISTS staff_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    clock_in_at TIMESTAMPTZ NOT NULL,
    clock_out_at TIMESTAMPTZ,
    shift_type_actual shift_type_enum,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS table_transfer_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    original_table_id UUID NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
    new_table_id UUID NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES customer_sessions(id) ON DELETE CASCADE,
    transferred_by_staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    transferred_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. MISSING FUNCTIONS
CREATE OR REPLACE FUNCTION generate_order_number(res_id UUID)
RETURNS TEXT AS $$
DECLARE
    res_prefix TEXT;
    seq_val BIGINT;
BEGIN
    SELECT prefix INTO res_prefix FROM restaurants WHERE id = res_id;
    seq_val := nextval('order_number_seq');
    RETURN res_prefix || LPAD(seq_val::TEXT, 6, '0');
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION calculate_order_totals(o_id UUID, o_created_at TIMESTAMPTZ)
RETURNS void AS $$
DECLARE
    v_subtotal DECIMAL(10,2);
    v_tax DECIMAL(10,2);
    v_total DECIMAL(10,2);
BEGIN
    SELECT COALESCE(SUM(quantity * unit_price), 0) INTO v_subtotal
    FROM order_items
    WHERE order_id = o_id AND order_created_at = o_created_at;

    v_tax := v_subtotal * 0.16;
    v_total := v_subtotal + v_tax;

    UPDATE orders
    SET subtotal = v_subtotal,
        tax = v_tax,
        total = v_total
    WHERE id = o_id AND created_at = o_created_at;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION get_restaurant_daily_sales(res_id UUID, target_date DATE)
RETURNS TABLE (total_sales DECIMAL, order_count BIGINT, avg_order_value DECIMAL) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(total), 0),
        COUNT(id),
        CASE WHEN COUNT(id) > 0 THEN COALESCE(SUM(total), 0) / COUNT(id) ELSE 0 END
    FROM orders
    WHERE restaurant_id = res_id 
    AND created_at::DATE = target_date
    AND status = 'completed';
END;
$$ language 'plpgsql';

-- 4. FIX customer_sessions.status COLUMN
ALTER TABLE customer_sessions 
    ALTER COLUMN status TYPE session_status_enum 
    USING status::session_status_enum;
ALTER TABLE customer_sessions 
    ALTER COLUMN status SET DEFAULT 'active';

-- 5. ADD MISSING COLUMNS
ALTER TABLE customer_sessions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;

ALTER TABLE categories ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS image_url TEXT;

ALTER TABLE waiter_calls ADD COLUMN IF NOT EXISTS call_type call_type_enum NOT NULL DEFAULT 'assistance';
ALTER TABLE waiter_calls ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ;
ALTER TABLE waiter_calls ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS calories INTEGER CHECK (calories >= 0);
ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS is_vegetarian BOOLEAN DEFAULT FALSE;
ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS is_spicy BOOLEAN DEFAULT FALSE;

ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_fee DECIMAL(10,2) DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_rating INTEGER CHECK (customer_rating BETWEEN 1 AND 5);

ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS business_registration TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS kra_pin TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS subscription_status subscription_status_enum DEFAULT 'trial';

-- 6. ADD MISSING INDEXES
CREATE INDEX IF NOT EXISTS idx_orders_rest_created_v3 ON orders (restaurant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_rest_pay_status ON orders (restaurant_id, payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_rest_pay_method ON orders (restaurant_id, payment_method);
CREATE INDEX IF NOT EXISTS idx_order_items_order_status_v2 ON order_items (order_id, status);
CREATE INDEX IF NOT EXISTS idx_order_items_menu_created_v2 ON order_items (menu_item_id, created_at);
CREATE INDEX IF NOT EXISTS idx_menu_items_rest_avail_display_v2 ON menu_items (restaurant_id, is_available, display_order);
CREATE INDEX IF NOT EXISTS idx_staff_rest_pin_v2 ON staff (restaurant_id, pin_code);
CREATE INDEX IF NOT EXISTS idx_staff_rest_role_v2 ON staff (restaurant_id, role);
CREATE INDEX IF NOT EXISTS idx_sessions_rest_status_created_v2 ON customer_sessions (restaurant_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_calls_rest_status_created_v2 ON waiter_calls (restaurant_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_staff_activity_staff_clockin_v2 ON staff_activity_logs (staff_id, clock_in_at);
CREATE INDEX IF NOT EXISTS idx_staff_activity_rest_clockin_v2 ON staff_activity_logs (restaurant_id, clock_in_at);
CREATE INDEX IF NOT EXISTS idx_payments_rest_created_v3 ON payments (restaurant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_mpesa_rest_created_v2 ON mpesa_transactions (restaurant_id, created_at);

-- 7. ADD MISSING CHECK CONSTRAINTS
ALTER TABLE menu_items ADD CONSTRAINT menu_items_price_check_v2 CHECK (price >= 0);
ALTER TABLE menu_items ADD CONSTRAINT menu_items_stock_check_v2 CHECK (stock_quantity >= 0 OR stock_quantity IS NULL);
ALTER TABLE order_items ADD CONSTRAINT order_items_price_check_v2 CHECK (unit_price >= 0);
ALTER TABLE order_items ADD CONSTRAINT order_items_subtotal_check_v2 CHECK (subtotal >= 0);
ALTER TABLE menu_item_modifiers ADD CONSTRAINT modifiers_price_check_v2 CHECK (price >= 0);
ALTER TABLE occasion_menu_items ADD CONSTRAINT occasion_price_check_v2 CHECK (special_price >= 0);

-- 8. ADD ROW LEVEL SECURITY (RLS)
ALTER TABLE mpesa_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE qr_code_scans ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_select_mpesa_v2') THEN
        CREATE POLICY tenant_select_mpesa_v2 ON mpesa_transactions FOR SELECT USING (restaurant_id = current_setting('app.current_restaurant_id', true)::UUID);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_all_mpesa_v2') THEN
        CREATE POLICY tenant_all_mpesa_v2 ON mpesa_transactions FOR ALL USING (restaurant_id = current_setting('app.current_restaurant_id', true)::UUID);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_select_qr_v2') THEN
        CREATE POLICY tenant_select_qr_v2 ON qr_code_scans FOR SELECT USING (restaurant_id = current_setting('app.current_restaurant_id', true)::UUID);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_all_qr_v2') THEN
        CREATE POLICY tenant_all_qr_v2 ON qr_code_scans FOR ALL USING (restaurant_id = current_setting('app.current_restaurant_id', true)::UUID);
    END IF;
END $$;

-- 9. CREATE MISSING VIEWS
CREATE OR REPLACE VIEW active_restaurants_view AS
SELECT id, name, subdomain, city
FROM restaurants
WHERE deleted_at IS NULL AND is_active = TRUE;

CREATE OR REPLACE VIEW daily_sales_summary_view AS
SELECT restaurant_id, created_at::DATE AS sale_date, SUM(total) AS total_sales, COUNT(id) AS order_count
FROM orders
WHERE status = 'completed'
GROUP BY restaurant_id, created_at::DATE;

-- 10. RESERVATION SYSTEM
CREATE TABLE IF NOT EXISTS reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    table_id UUID REFERENCES tables(id) ON DELETE SET NULL,
    
    -- Guest information
    guest_name VARCHAR(100) NOT NULL,
    guest_phone VARCHAR(20) NOT NULL,
    guest_email VARCHAR(255),
    party_size INTEGER NOT NULL CHECK (party_size > 0),
    
    -- Reservation details
    reservation_time TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER DEFAULT 90,
    status VARCHAR(20) DEFAULT 'confirmed', -- confirmed, seated, cancelled, no_show, completed
    
    -- Special requests
    special_requests TEXT,
    occasion VARCHAR(50), -- birthday, anniversary, etc.
    
    -- Deposit information
    deposit_amount DECIMAL(10,2) DEFAULT 0,
    deposit_paid BOOLEAN DEFAULT FALSE,
    deposit_payment_id UUID REFERENCES payments(id),
    
    -- Tracking
    confirmed_at TIMESTAMPTZ DEFAULT NOW(),
    cancelled_at TIMESTAMPTZ,
    seated_at TIMESTAMPTZ,
    no_show_at TIMESTAMPTZ,
    
    -- Recurring reservations
    recurring_id UUID, -- for linking recurring reservations
    recurring_frequency VARCHAR(20), -- weekly, monthly
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Waitlist table
CREATE TABLE IF NOT EXISTS waitlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    
    -- Guest information
    guest_name VARCHAR(100) NOT NULL,
    guest_phone VARCHAR(20) NOT NULL,
    party_size INTEGER NOT NULL CHECK (party_size > 0),
    
    -- Waitlist status
    status VARCHAR(20) DEFAULT 'waiting', -- waiting, seated, cancelled, notified
    position INTEGER,
    estimated_wait_minutes INTEGER,
    
    -- Timing
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    seated_at TIMESTAMPTZ,
    notified_at TIMESTAMPTZ,
    
    -- SMS tracking
    sms_sent BOOLEAN DEFAULT FALSE,
    sms_sent_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Restaurant reservation settings
ALTER TABLE restaurant_settings ADD COLUMN reservation_settings JSONB DEFAULT '{
    "auto_release_minutes": 15,
    "require_deposit_for_party_size": 6,
    "deposit_amount": 1000,
    "max_reservation_days_ahead": 30,
    "min_cancel_hours": 2,
    "no_show_penalty": 500
}';

-- Reservation time slots (configurable)
CREATE TABLE IF NOT EXISTS reservation_time_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Sunday, 6=Saturday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    interval_minutes INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMIT;
