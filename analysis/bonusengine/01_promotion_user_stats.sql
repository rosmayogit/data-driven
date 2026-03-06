-- ============================================================================
-- PROMOTION USER STATS: Asignados, Apostadores, Ganadores y Redimidos
-- ============================================================================
-- Joins promotion_user con hive_metastore.db_silver_voucher.eventsmaster
-- para obtener el funnel completo por promoción (usuarios únicos).
--
-- Métricas:
--   assigned  → usuarios únicos asignados a la promo
--   wagered   → usuarios únicos que apostaron (ConfirmedGrossAmountStaked > 0)
--   won       → usuarios únicos a quienes se emitió al menos un voucher
--   redeemed  → usuarios únicos que redimieron al menos un voucher
-- ============================================================================

WITH voucher AS (
    SELECT
        CampaignId,
        IssuedToUserId,
        IssuedOnUTC,
        RedeemedOnUTC
    FROM hive_metastore.db_silver_voucher.eventsmaster
),

voucher_agg AS (
    SELECT
        CampaignId,
        IssuedToUserId,
        COUNT(*)                                        AS total_vouchers,
        COUNT(CASE WHEN RedeemedOnUTC IS NOT NULL
                   THEN 1 END)                          AS redeemed_vouchers
    FROM voucher
    GROUP BY CampaignId, IssuedToUserId
)

SELECT
    pu.PromotionId,
    pd.PromotionName,
    pd.PromotionKey,
    pd.BrandId,

    -- Funnel (usuarios únicos)
    COUNT(DISTINCT pu.UserId)                                               AS assigned,
    COUNT(DISTINCT CASE WHEN pu.ConfirmedGrossAmountStaked > 0
                        THEN pu.UserId END)                                 AS wagered,
    COUNT(DISTINCT v.IssuedToUserId)                                        AS won,
    COUNT(DISTINCT CASE WHEN v.redeemed_vouchers > 0
                        THEN v.IssuedToUserId END)                          AS redeemed,

    -- Tasas de conversión
    ROUND(
        COUNT(DISTINCT CASE WHEN pu.ConfirmedGrossAmountStaked > 0
                            THEN pu.UserId END)
        / NULLIF(COUNT(DISTINCT pu.UserId), 0) * 100, 1
    )                                                                       AS wagered_rate_pct,
    ROUND(
        COUNT(DISTINCT v.IssuedToUserId)
        / NULLIF(COUNT(DISTINCT pu.UserId), 0) * 100, 1
    )                                                                       AS win_rate_pct,
    ROUND(
        COUNT(DISTINCT CASE WHEN v.redeemed_vouchers > 0
                            THEN v.IssuedToUserId END)
        / NULLIF(COUNT(DISTINCT v.IssuedToUserId), 0) * 100, 1
    )                                                                       AS redeem_rate_pct

FROM promotion_user  pu

INNER JOIN promotion_detail  pd
    ON pd.PromotionId = pu.PromotionId

LEFT JOIN voucher_agg  v
    ON  v.CampaignId     = pu.PromotionId
    AND v.IssuedToUserId = pu.UserId

WHERE pu.PromotionId IN (1037, 1038, 1039, 1040, 1041)

GROUP BY
    pu.PromotionId,
    pd.PromotionName,
    pd.PromotionKey,
    pd.BrandId

ORDER BY
    pu.PromotionId;
