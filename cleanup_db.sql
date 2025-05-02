-- SQLite script to clean all imported health data
-- This script can be run directly with: sqlite3 instance/app.db < cleanup_db.sql

-- Start transaction
BEGIN TRANSACTION;

-- Temporarily disable foreign key constraints
PRAGMA foreign_keys = OFF;

-- Delete all health data records
DELETE FROM sleeps;
DELETE FROM weights;
DELETE FROM heart_rates;
DELETE FROM activities;

-- Delete import logs
DELETE FROM import_logs;

-- Reset auto-increment counters
DELETE FROM sqlite_sequence WHERE name IN ('sleeps', 'weights', 'heart_rates', 'activities', 'import_logs');

-- Re-enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Commit changes
COMMIT;

-- Vacuum database to reclaim space
VACUUM;

-- Verify deletion (comment these out if you just want to run the deletion)
SELECT 'Remaining sleeps: ' || COUNT(*) FROM sleeps;
SELECT 'Remaining weights: ' || COUNT(*) FROM weights;
SELECT 'Remaining heart_rates: ' || COUNT(*) FROM heart_rates;
SELECT 'Remaining activities: ' || COUNT(*) FROM activities;
SELECT 'Remaining import_logs: ' || COUNT(*) FROM import_logs;

-- Add admin user (only if it doesn't exist)
INSERT OR IGNORE INTO users (username, email, password_hash, created_at, is_active, is_admin, updated_at)
VALUES ('admin', 'admin@example.com', 'pbkdf2:sha256:260000$xZzH0v8CqXrOhSi0$b5575ac50f4a41e3d21166b28fccac94ab9a03a5cdd197764c5a80ff8fcb9172', 
        CURRENT_TIMESTAMP, 1, 1, CURRENT_TIMESTAMP);

-- If admin user already exists but is not an administrator, update to administrator
UPDATE users SET is_admin = 1 WHERE username = 'admin' AND is_admin = 0;

-- Note: The password hash above corresponds to the password 'admin123'
-- To change the password, use the following Python command to generate a new hash:
-- from werkzeug.security import generate_password_hash
-- print(generate_password_hash('your_password_here'))

