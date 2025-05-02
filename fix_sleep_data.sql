-- Fix sleep data
-- First, find duplicate records
SELECT DATE(timestamp) as sleep_date, COUNT(*) as record_count FROM sleeps GROUP BY DATE(timestamp) HAVING COUNT(*) > 1 ORDER BY sleep_date;

-- Set correct data source information for each day's sleep records
UPDATE sleeps SET notes = 'Source: Connect (manually tagged)' WHERE notes LIKE '%Connect%' OR notes LIKE '%connect%';
