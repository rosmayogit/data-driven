-- ============================================================================
-- WEEKLY STAKED TREND: Apuestas por semana con comparativa semana anterior
-- ============================================================================
-- Desglosa ConfirmedGrossAmountStaked por promoción y semana de opt-in,
-- añade la semana anterior via LAG() y calcula el aumento absoluto y
-- porcentual. Útil para medir el impacto de la campaña semana a semana.
--
-- Columnas clave:
--   staked_this_week   → suma de apuestas en la semana actual
--   staked_prev_week   → suma de apuestas en la semana anterior (LAG)
--   staked_increase    → diferencia absoluta (actual - anterior)
--   staked_increase_pct → variación porcentual respecto a la semana anterior
-- ============================================================================

WITH weekly_stakes AS (
    SELECT
        pu.PromotionId,
        DATE_TRUNC('week', pu.OptInDateTimeUtc)  AS week_start,
        COUNT(DISTINCT pu.UserId)                AS users_wagered,
        SUM(pu.ConfirmedGrossAmountStaked)        AS total_staked
    FROM db_silver_bonusengine.promotion_user  pu
    WHERE pu.PromotionId IN (1037, 1038, 1039, 1040, 1041)
      AND pu.OptInDateTimeUtc IS NOT NULL
    GROUP BY
        pu.PromotionId,
        DATE_TRUNC('week', pu.OptInDateTimeUtc)
),

weekly_with_prev AS (
    SELECT
        *,
        LAG(total_staked) OVER (
            PARTITION BY PromotionId
            ORDER BY week_start
        ) AS prev_week_staked
    FROM weekly_stakes
)

SELECT
    wwp.PromotionId,
    pd.PromotionName,
    pd.PromotionKey,
    pd.BrandId,
    wwp.week_start,
    wwp.users_wagered,

    -- Apuestas semana actual y anterior
    ROUND(wwp.total_staked,       2)                        AS staked_this_week,
    ROUND(wwp.prev_week_staked,   2)                        AS staked_prev_week,

    -- Aumento absoluto
    ROUND(wwp.total_staked - wwp.prev_week_staked, 2)       AS staked_increase,

    -- Variación porcentual (NULL en la primera semana de cada promo)
    ROUND(
        (wwp.total_staked - wwp.prev_week_staked)
        / NULLIF(wwp.prev_week_staked, 0) * 100, 1
    )                                                       AS staked_increase_pct

FROM weekly_with_prev  wwp

INNER JOIN db_silver_bonusengine.promotion_detail  pd
    ON pd.PromotionId = wwp.PromotionId

ORDER BY
    wwp.PromotionId,
    wwp.week_start;
