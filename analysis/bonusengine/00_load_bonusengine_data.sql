-- ============================================================================
-- LOAD BONUSENGINE DATA: Load CSVs into Databricks tables
-- ============================================================================
-- Schema: db_silver_bonusengine
--
-- Generate the CSVs first:
--   python scripts/generate_bonusengine_data.py
--
-- Then upload to DBFS:
--   dbutils.fs.cp("file:/tmp/bonusengine/promotion_detail.csv",
--                  "dbfs:/data-driven/bonusengine/promotion_detail.csv")
--   (repeat for each file)
-- ============================================================================

-- ----- promotion_detail -----
CREATE TABLE IF NOT EXISTS promotion_detail
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/bonusengine/promotion_detail.csv',
    header 'true',
    inferSchema 'true'
);

-- ----- promotion_user -----
CREATE TABLE IF NOT EXISTS promotion_user
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/bonusengine/promotion_user.csv',
    header 'true',
    inferSchema 'true'
);

-- ----- reward_detail -----
CREATE TABLE IF NOT EXISTS reward_detail
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/bonusengine/reward_detail.csv',
    header 'true',
    inferSchema 'true'
);

-- ----- reward_redeem_user -----
CREATE TABLE IF NOT EXISTS reward_redeem_user
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/bonusengine/reward_redeem_user.csv',
    header 'true',
    inferSchema 'true'
);

-- ----- reward_freebet -----
CREATE TABLE IF NOT EXISTS reward_freebet
USING CSV
OPTIONS (
    path 'dbfs:/data-driven/bonusengine/reward_freebet.csv',
    header 'true',
    inferSchema 'true'
);

-- ----- Validation -----
SELECT 'promotion_detail' AS table_name, COUNT(*) AS row_count FROM promotion_detail
UNION ALL
SELECT 'promotion_user', COUNT(*) FROM promotion_user
UNION ALL
SELECT 'reward_detail', COUNT(*) FROM reward_detail
UNION ALL
SELECT 'reward_redeem_user', COUNT(*) FROM reward_redeem_user
UNION ALL
SELECT 'reward_freebet', COUNT(*) FROM reward_freebet;
