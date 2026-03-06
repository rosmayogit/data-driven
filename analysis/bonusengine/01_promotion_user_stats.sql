-- ============================================================================
-- PROMOTION USER STATS: Asignados, Opt-in, Ganadores y Redimidos por Promoción
-- ============================================================================
-- Joins promotion_user con hive_metastore.db_silver_voucher.eventsmaster
-- para obtener el funnel completo por promoción.
--
-- Métricas:
--   assigned  → usuarios asignados a la promo (en promotion_user)
--   opted_in  → usuarios que hicieron opt-in
--   won       → usuarios a quienes se emitió un voucher (IssuedOnUTC IS NOT NULL)
--   redeemed  → usuarios que redimieron el voucher (RedeemedOnUTC IS NOT NULL)
-- ============================================================================

WITH voucher AS (
    SELECT
        CampaignId,
        IssuedToUserId,
        IssuedOnUTC,
        RedeemedOnUTC
    FROM hive_metastore.db_silver_voucher.eventsmaster
    WHERE row_valid_to_ts IS NULL   -- solo registro vigente (SCD2)
)

SELECT
    pu.PromotionId,
    pd.PromotionName,
    pd.PromotionKey,
    pd.BrandId,

    -- Funnel
    COUNT(DISTINCT pu.UserId)                                               AS assigned,
    COUNT(DISTINCT CASE WHEN pu.OptInDateTimeUtc IS NOT NULL
                        THEN pu.UserId END)                                 AS opted_in,
    COUNT(v.IssuedToUserId)                                                 AS won,
    COUNT(CASE WHEN v.RedeemedOnUTC IS NOT NULL
               THEN v.IssuedToUserId END)                                   AS redeemed,

    -- Tasas de conversión
    ROUND(
        COUNT(DISTINCT CASE WHEN pu.OptInDateTimeUtc IS NOT NULL
                            THEN pu.UserId END)
        / NULLIF(COUNT(DISTINCT pu.UserId), 0) * 100, 1
    )                                                                       AS optin_rate_pct,
    ROUND(
        COUNT(v.IssuedToUserId)
        / NULLIF(COUNT(DISTINCT pu.UserId), 0) * 100, 1
    )                                                                       AS win_rate_pct,
    ROUND(
        COUNT(CASE WHEN v.RedeemedOnUTC IS NOT NULL THEN v.IssuedToUserId END)
        / NULLIF(COUNT(v.IssuedToUserId), 0) * 100, 1
    )                                                                       AS redeem_rate_pct

FROM promotion_user  pu

INNER JOIN promotion_detail  pd
    ON pd.PromotionId = pu.PromotionId

LEFT JOIN voucher  v
    ON  v.CampaignId     = pu.PromotionId
    AND v.IssuedToUserId = pu.UserId

GROUP BY
    pu.PromotionId,
    pd.PromotionName,
    pd.PromotionKey,
    pd.BrandId

ORDER BY
    pu.PromotionId;
