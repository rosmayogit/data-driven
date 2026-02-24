-- =============================================================================
-- CAMPAIGN FUNNEL ANALYSIS — New Users per Day
-- =============================================================================
-- Funnel stages:
--   1. Registered   — new users who joined the platform during the campaign
--   2. Opt-In       — registered users who opted in to this promotion
--   3. Reward       — opted-in users who obtained (were issued) the reward
--   4. Redeemed     — users who redeemed the reward
--
-- Grouped by: registration_date (usuarios nuevos al día)
--
-- Tables:
--   hive_metastore.db_silver_bonusengine.promotion_detail
--   hive_metastore.db_silver_bonusengine.promotion_user
--   hive_metastore.db_silver_bonusengine.reward_redeem_user
--   hive_metastore.db_bronze_tps.users_userdetail
--
-- Widget setup (run once in a %python cell before this query):
--   dbutils.widgets.text("campaign_id", "980", "Campaign ID")
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Campaign metadata
-- ---------------------------------------------------------------------------
WITH campaign AS (
  SELECT
    PromotionId,
    PromotionName,
    CAST(StartDateUtc AS DATE) AS start_date,
    CAST(EndDateUtc   AS DATE) AS end_date
  FROM hive_metastore.db_silver_bonusengine.promotion_detail
  WHERE PromotionId = CAST(${campaign_id} AS INT)
),

-- ---------------------------------------------------------------------------
-- 1. Registered — users in the campaign with their registration date
--    Join promotion_user → users_userdetail via UserId
-- ---------------------------------------------------------------------------
registered AS (
  SELECT
    pu.UserId,
    CAST(u.registration_date AS DATE) AS reg_day
  FROM hive_metastore.db_silver_bonusengine.promotion_user pu
  INNER JOIN hive_metastore.db_bronze_tps.users_userdetail u
    ON pu.UserId = u.userId
  WHERE pu.PromotionId = CAST(${campaign_id} AS INT)
),

-- ---------------------------------------------------------------------------
-- 2. Opt-In — users who explicitly opted in to this campaign
-- ---------------------------------------------------------------------------
opted_in AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.promotion_user
  WHERE PromotionId = CAST(${campaign_id} AS INT)
    AND UserIsOptIn = TRUE
),

-- ---------------------------------------------------------------------------
-- 3. Reward obtained — users who were issued a reward for this campaign
-- ---------------------------------------------------------------------------
reward_obtained AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.reward_redeem_user
  WHERE PromotionId = CAST(${campaign_id} AS INT)
),

-- ---------------------------------------------------------------------------
-- 4. Reward redeemed — users who actually redeemed their reward
-- ---------------------------------------------------------------------------
reward_redeemed AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.reward_redeem_user
  WHERE PromotionId = CAST(${campaign_id} AS INT)
    AND RedeemedOnUtc IS NOT NULL
),

-- ---------------------------------------------------------------------------
-- 5. Funnel aggregated by registration day
-- ---------------------------------------------------------------------------
funnel_daily AS (
  SELECT
    r.reg_day,
    COUNT(DISTINCT r.UserId)    AS new_users,
    COUNT(DISTINCT oi.UserId)   AS opted_in,
    COUNT(DISTINCT ro.UserId)   AS reward_obtained,
    COUNT(DISTINCT rr.UserId)   AS reward_redeemed
  FROM registered r
  LEFT JOIN opted_in      oi ON r.UserId = oi.UserId
  LEFT JOIN reward_obtained ro ON r.UserId = ro.UserId
  LEFT JOIN reward_redeemed rr ON r.UserId = rr.UserId
  GROUP BY r.reg_day
)

-- ---------------------------------------------------------------------------
-- Final output: daily funnel with step-over-step conversion rates
-- ---------------------------------------------------------------------------
SELECT
  c.PromotionId,
  c.PromotionName,
  c.start_date                                                        AS campaign_start,
  c.end_date                                                          AS campaign_end,
  f.reg_day,
  f.new_users,
  f.opted_in,
  ROUND(100.0 * f.opted_in        / NULLIF(f.new_users, 0),      1)  AS pct_optin,
  f.reward_obtained,
  ROUND(100.0 * f.reward_obtained / NULLIF(f.opted_in, 0),       1)  AS pct_reward,
  f.reward_redeemed,
  ROUND(100.0 * f.reward_redeemed / NULLIF(f.reward_obtained, 0), 1) AS pct_redeemed,
  ROUND(100.0 * f.reward_redeemed / NULLIF(f.new_users, 0),       1) AS pct_overall
FROM funnel_daily f
CROSS JOIN campaign c
ORDER BY f.reg_day;


-- =============================================================================
-- TOTALS — Overall campaign funnel (all days combined)
-- =============================================================================
WITH campaign AS (
  SELECT
    PromotionId,
    PromotionName,
    CAST(StartDateUtc AS DATE) AS start_date,
    CAST(EndDateUtc   AS DATE) AS end_date
  FROM hive_metastore.db_silver_bonusengine.promotion_detail
  WHERE PromotionId = CAST(${campaign_id} AS INT)
),

registered AS (
  SELECT
    pu.UserId
  FROM hive_metastore.db_silver_bonusengine.promotion_user pu
  INNER JOIN hive_metastore.db_bronze_tps.users_userdetail u
    ON pu.UserId = u.userId
  WHERE pu.PromotionId = CAST(${campaign_id} AS INT)
),

opted_in AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.promotion_user
  WHERE PromotionId = CAST(${campaign_id} AS INT)
    AND UserIsOptIn = TRUE
),

reward_obtained AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.reward_redeem_user
  WHERE PromotionId = CAST(${campaign_id} AS INT)
),

reward_redeemed AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.reward_redeem_user
  WHERE PromotionId = CAST(${campaign_id} AS INT)
    AND RedeemedOnUtc IS NOT NULL
)

SELECT
  c.PromotionId,
  c.PromotionName,
  c.start_date                                                        AS campaign_start,
  c.end_date                                                          AS campaign_end,
  COUNT(DISTINCT r.UserId)                                            AS new_users,
  COUNT(DISTINCT oi.UserId)                                           AS opted_in,
  ROUND(100.0 * COUNT(DISTINCT oi.UserId) / NULLIF(COUNT(DISTINCT r.UserId), 0), 1) AS pct_optin,
  COUNT(DISTINCT ro.UserId)                                           AS reward_obtained,
  ROUND(100.0 * COUNT(DISTINCT ro.UserId) / NULLIF(COUNT(DISTINCT oi.UserId), 0), 1) AS pct_reward,
  COUNT(DISTINCT rr.UserId)                                           AS reward_redeemed,
  ROUND(100.0 * COUNT(DISTINCT rr.UserId) / NULLIF(COUNT(DISTINCT ro.UserId), 0), 1) AS pct_redeemed,
  ROUND(100.0 * COUNT(DISTINCT rr.UserId) / NULLIF(COUNT(DISTINCT r.UserId), 0), 1)  AS pct_overall
FROM registered r
CROSS JOIN campaign c
LEFT JOIN opted_in      oi ON r.UserId = oi.UserId
LEFT JOIN reward_obtained ro ON r.UserId = ro.UserId
LEFT JOIN reward_redeemed rr ON r.UserId = rr.UserId
GROUP BY c.PromotionId, c.PromotionName, c.start_date, c.end_date;
