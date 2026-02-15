-- ============================================================================
-- LOAD DATA: Instructions to load CSVs into Databricks
-- ============================================================================
-- Run this first to create the tables used by all other analysis queries.
--
-- Option A: Upload CSVs via Databricks UI (Data > Create Table > Upload File)
-- Option B: Upload to DBFS and load with the commands below
-- ============================================================================

-- Step 1: Upload your CSV files to DBFS, e.g.:
--   dbutils.fs.cp("file:/tmp/users.csv", "dbfs:/data-driven/users.csv")
--   (repeat for each file)

-- Step 2: Create tables from CSV

CREATE TABLE IF NOT EXISTS users
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/users.csv',
    header 'true',
    inferSchema 'true'
);

CREATE TABLE IF NOT EXISTS promotions
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/promotions.csv',
    header 'true',
    inferSchema 'true'
);

CREATE TABLE IF NOT EXISTS funnel
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/funnel.csv',
    header 'true',
    inferSchema 'true'
);

CREATE TABLE IF NOT EXISTS bets
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/bets.csv',
    header 'true',
    inferSchema 'true'
);

CREATE TABLE IF NOT EXISTS daily_activity
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/daily_activity.csv',
    header 'true',
    inferSchema 'true'
);

-- Step 3: Quick validation
SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'promotions', COUNT(*) FROM promotions
UNION ALL
SELECT 'funnel', COUNT(*) FROM funnel
UNION ALL
SELECT 'bets', COUNT(*) FROM bets
UNION ALL
SELECT 'daily_activity', COUNT(*) FROM daily_activity;
