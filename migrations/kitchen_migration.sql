-- migrations/kitchen_migration.sql
ALTER TABLE staff ADD COLUMN IF NOT EXISTS kitchen_station VARCHAR(50);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS ready_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS estimated_start_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS estimated_ready_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS start_delay_seconds INTEGER DEFAULT 0;

-- Add hold columns to order_items
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS is_held BOOLEAN DEFAULT FALSE;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS hold_reason VARCHAR(255);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS hold_resume_at TIMESTAMPTZ;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS hold_started_at TIMESTAMPTZ;

-- Add auto-clear setting column to restaurant_settings table
ALTER TABLE restaurant_settings ADD COLUMN IF NOT EXISTS auto_clear_ready_minutes INTEGER DEFAULT 5;

-- Make preparation_time NOT NULL (for new items, existing items get default 15 minutes)
UPDATE menu_items SET preparation_time = 15 WHERE preparation_time IS NULL;
ALTER TABLE menu_items ALTER COLUMN preparation_time SET DEFAULT 15;
ALTER TABLE menu_items ALTER COLUMN preparation_time SET NOT NULL;


