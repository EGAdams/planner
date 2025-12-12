-- Create merchants table for storing common merchant names
CREATE TABLE IF NOT EXISTS merchants (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_category (category)
);

-- Insert some common merchants
INSERT INTO merchants (name, category, notes) VALUES
('Meijer', 'Food & Supplies', 'Grocery store chain'),
('Gordon Foods', 'Food & Supplies', 'Bulk food supplier'),
('Walmart', 'Food & Supplies', 'Retail and grocery'),
('Target', 'Food & Supplies', 'Retail and grocery'),
('Costco', 'Food & Supplies', 'Wholesale club'),
('Sams Club', 'Food & Supplies', 'Wholesale club'),
('Kroger', 'Food & Supplies', 'Grocery store'),
('Aldi', 'Food & Supplies', 'Discount grocer'),
('Family Fare', 'Food & Supplies', 'Grocery store'),
('Spartan Stores', 'Food & Supplies', 'Grocery store')
ON DUPLICATE KEY UPDATE name=name;

-- Add merchant_id to expenses table if it doesn't exist
ALTER TABLE expenses
ADD COLUMN IF NOT EXISTS merchant_id BIGINT UNSIGNED,
ADD CONSTRAINT fk_merchant
FOREIGN KEY (merchant_id) REFERENCES merchants(id);
