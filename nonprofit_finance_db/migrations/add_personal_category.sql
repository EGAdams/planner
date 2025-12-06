-- Add "Personal" as a third top-level category
-- This migration adds Personal (id=3) alongside Church (id=1) and Housing (id=2)

USE nonprofit_finance;

-- Check if Personal category already exists, and insert if not
INSERT INTO categories (id, parent_id, name, kind, is_active)
SELECT 3, NULL, 'Personal', 'EXPENSE', 1
WHERE NOT EXISTS (
    SELECT 1 FROM categories WHERE id = 3
);

-- Verify the three top-level categories
SELECT id, name, parent_id
FROM categories
WHERE parent_id IS NULL
ORDER BY id;
