-- Create branches table
CREATE TABLE IF NOT EXISTS branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add branch_id to existing tables
ALTER TABLE staff ADD COLUMN IF NOT EXISTS branch_id UUID REFERENCES branches(id);
ALTER TABLE tables ADD COLUMN IF NOT EXISTS branch_id UUID REFERENCES branches(id);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS branch_id UUID REFERENCES branches(id);
ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS branch_id UUID REFERENCES branches(id);
-- The prompt said menu_categories, but models.py says categories
ALTER TABLE categories ADD COLUMN IF NOT EXISTS branch_id UUID REFERENCES branches(id);
ALTER TABLE customer_sessions ADD COLUMN IF NOT EXISTS branch_id UUID REFERENCES branches(id);

-- Add role_type to staff (owner, branch_manager, waiter, kitchen, cashier)
-- We also have a 'role' column based on StaffRole enum, but prompt says add 'role_type'
ALTER TABLE staff ADD COLUMN IF NOT EXISTS role_type VARCHAR(50) DEFAULT 'waiter';

-- Add parent_restaurant_id for grouping branches
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS parent_restaurant_id UUID REFERENCES restaurants(id);
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS is_multi_branch BOOLEAN DEFAULT FALSE;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_branches_restaurant_id ON branches(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_orders_branch_id ON orders(branch_id);
CREATE INDEX IF NOT EXISTS idx_tables_branch_id ON tables(branch_id);
CREATE INDEX IF NOT EXISTS idx_staff_branch_id ON staff(branch_id);
