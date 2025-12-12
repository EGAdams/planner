-- Script to add more ministry partners and mission organizations
-- Usage: source this in MySQL or run via Python script

-- Ministry Partners (Local)
INSERT INTO merchants (name, category) VALUES
('Guiding Light', 'Ministry Partners'),
('Mel Trotter Ministries', 'Ministry Partners'),
('Salvation Army', 'Ministry Partners'),
('Samaritan Center', 'Ministry Partners'),
('Degage Ministries', 'Ministry Partners'),
('Heartside Ministry', 'Ministry Partners'),
('Kids Hope USA', 'Ministry Partners'),
('Kids Food Basket', 'Ministry Partners'),
('Love INC', 'Ministry Partners')
ON DUPLICATE KEY UPDATE name=name;

-- Global Missions
INSERT INTO merchants (name, category) VALUES
('Mission India', 'Global Missions'),
('Compassion International', 'Global Missions'),
('World Vision', 'Global Missions')
ON DUPLICATE KEY UPDATE name=name;

-- Add more as needed:
-- INSERT INTO merchants (name, category) VALUES
-- ('New Ministry Name', 'Ministry Partners'),
-- ('Another Mission Org', 'Global Missions')
-- ON DUPLICATE KEY UPDATE name=name;
