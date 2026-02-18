-- ============================================================================
-- QUERY: Users in Promotion 1021 with Confirmed Gross Staked >= 300,000
-- ============================================================================
-- Retrieves user IDs from the silver bonus engine layer for users who:
--   - Participated in promotion 1021
--   - Have a confirmed gross amount staked of at least 300,000
-- ============================================================================

SELECT userId
FROM hive_metastore.db_silver_bonusengine.promotion_user
WHERE PromotionId = 1021
  AND ConfirmedGrossAmountStaked >= 300000;
