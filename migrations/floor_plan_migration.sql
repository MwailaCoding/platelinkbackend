-- Floors table
CREATE TABLE IF NOT EXISTS floors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    background_image_url TEXT,
    width INTEGER DEFAULT 1200,
    height INTEGER DEFAULT 800,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Floor elements (walls, doors, windows, bars)
CREATE TABLE IF NOT EXISTS floor_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    floor_id UUID REFERENCES floors(id) ON DELETE CASCADE,
    element_type VARCHAR(50) NOT NULL, -- 'wall', 'door', 'window', 'bar', 'host_stand', 'restroom', 'kitchen'
    element_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add floor_id and position to tables
ALTER TABLE tables ADD COLUMN IF NOT EXISTS floor_id UUID REFERENCES floors(id);
ALTER TABLE tables ADD COLUMN IF NOT EXISTS pos_x INTEGER DEFAULT 0;
ALTER TABLE tables ADD COLUMN IF NOT EXISTS pos_y INTEGER DEFAULT 0;
ALTER TABLE tables ADD COLUMN IF NOT EXISTS shape VARCHAR(20) DEFAULT 'square';
ALTER TABLE tables ADD COLUMN IF NOT EXISTS width INTEGER DEFAULT 80;
ALTER TABLE tables ADD COLUMN IF NOT EXISTS height INTEGER DEFAULT 80;

-- Add floor plan settings to restaurant_settings
INSERT INTO restaurant_settings (restaurant_id, key, value) 
SELECT id, 'floor_plan_grid_size', '20' FROM restaurants
ON CONFLICT DO NOTHING;

INSERT INTO restaurant_settings (restaurant_id, key, value)
SELECT id, 'floor_plan_snap_enabled', 'true' FROM restaurants
ON CONFLICT DO NOTHING;

INSERT INTO restaurant_settings (restaurant_id, key, value)
SELECT id, 'floor_plan_show_grid', 'true' FROM restaurants
ON CONFLICT DO NOTHING;
