-- =============================================================================
-- CAMPAIGN FUNNEL ANALYSIS — New Users per Day
-- =============================================================================
-- Funnel stages:
--   1. Registered   — ALL new users who registered during the campaign period
--   2. Opt-In       — registered users who opted in to this promotion
--   3. Reward       — users who were issued a reward for this campaign
--   4. Redeemed     — users who redeemed their reward
--
-- Base: hive_metastore.db_bronze_tps.users_user (RegistrationDate)
-- Bonus tables joined via UserId
-- Grouped by: RegistrationDate (usuarios nuevos al día)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- QUERY 1 — Daily funnel grouped by registration date
-- ---------------------------------------------------------------------------
WITH campaign AS (
  SELECT
    PromotionId,
    PromotionName,
    CAST(StartDateUtc AS DATE) AS start_date,
    CAST(EndDateUtc   AS DATE) AS end_date
  FROM hive_metastore.db_silver_bonusengine.promotion_detail
  WHERE PromotionId = 980
),

-- Base: all users who registered during the campaign window
new_users AS (
  SELECT
    u.UserId,
    CAST(u.RegistrationDate AS DATE) AS reg_day
  FROM hive_metastore.db_bronze_tps.users_user u
  CROSS JOIN campaign c
  WHERE CAST(u.RegistrationDate AS DATE) BETWEEN c.start_date AND c.end_date
),

opted_in AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.promotion_user
  WHERE PromotionId = 980
    AND UserIsOptIn = TRUE
),

reward_obtained AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.reward_redeem_user
  WHERE PromotionId = 980
),

reward_redeemed AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.reward_redeem_user
  WHERE PromotionId = 980
    AND RedeemedOnUtc IS NOT NULL
),

funnel_daily AS (
  SELECT
    n.reg_day,
    COUNT(DISTINCT n.UserId)    AS new_users,
    COUNT(DISTINCT oi.UserId)   AS opted_in,
    COUNT(DISTINCT ro.UserId)   AS reward_obtained,
    COUNT(DISTINCT rr.UserId)   AS reward_redeemed
  FROM new_users n
  LEFT JOIN opted_in        oi ON n.UserId = oi.UserId
  LEFT JOIN reward_obtained ro ON n.UserId = ro.UserId
  LEFT JOIN reward_redeemed rr ON n.UserId = rr.UserId
  GROUP BY n.reg_day
)

SELECT
  c.PromotionId,
  c.PromotionName,
  c.start_date                                                         AS campaign_start,
  c.end_date                                                           AS campaign_end,
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


-- ---------------------------------------------------------------------------
-- QUERY 2 — Overall totals (all days combined)
-- ---------------------------------------------------------------------------
WITH campaign AS (
  SELECT
    PromotionId,
    PromotionName,
    CAST(StartDateUtc AS DATE) AS start_date,
    CAST(EndDateUtc   AS DATE) AS end_date
  FROM hive_metastore.db_silver_bonusengine.promotion_detail
  WHERE PromotionId = 980
),

new_users AS (
  SELECT u.UserId
  FROM hive_metastore.db_bronze_tps.users_user u
  CROSS JOIN campaign c
  WHERE CAST(u.RegistrationDate AS DATE) BETWEEN c.start_date AND c.end_date
),

opted_in AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.promotion_user
  WHERE PromotionId = 980
    AND UserIsOptIn = TRUE
),

reward_obtained AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.reward_redeem_user
  WHERE PromotionId = 980
),

reward_redeemed AS (
  SELECT DISTINCT UserId
  FROM hive_metastore.db_silver_bonusengine.reward_redeem_user
  WHERE PromotionId = 980
    AND RedeemedOnUtc IS NOT NULL
)

SELECT
  c.PromotionId,
  c.PromotionName,
  c.start_date                                                                          AS campaign_start,
  c.end_date                                                                            AS campaign_end,
  COUNT(DISTINCT n.UserId)                                                              AS new_users,
  COUNT(DISTINCT oi.UserId)                                                             AS opted_in,
  ROUND(100.0 * COUNT(DISTINCT oi.UserId) / NULLIF(COUNT(DISTINCT n.UserId),  0), 1)  AS pct_optin,
  COUNT(DISTINCT ro.UserId)                                                             AS reward_obtained,
  ROUND(100.0 * COUNT(DISTINCT ro.UserId) / NULLIF(COUNT(DISTINCT oi.UserId), 0), 1)  AS pct_reward,
  COUNT(DISTINCT rr.UserId)                                                             AS reward_redeemed,
  ROUND(100.0 * COUNT(DISTINCT rr.UserId) / NULLIF(COUNT(DISTINCT ro.UserId), 0), 1)  AS pct_redeemed,
  ROUND(100.0 * COUNT(DISTINCT rr.UserId) / NULLIF(COUNT(DISTINCT n.UserId),  0), 1)  AS pct_overall
FROM new_users n
CROSS JOIN campaign c
LEFT JOIN opted_in        oi ON n.UserId = oi.UserId
LEFT JOIN reward_obtained ro ON n.UserId = ro.UserId
LEFT JOIN reward_redeemed rr ON n.UserId = rr.UserId
GROUP BY c.PromotionId, c.PromotionName, c.start_date, c.end_date;
