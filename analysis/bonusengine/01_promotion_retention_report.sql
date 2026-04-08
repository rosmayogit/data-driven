-- ============================================================================
-- PROMOTION RETENTION REPORT
-- ============================================================================
-- Analyses how well promotions retain users over time.
--
-- Sections:
--   1. Monthly Active Promotion Users   — baseline participation trend
--   2. Cohort Retention                 — month-0 cohorts tracked forward
--   3. Retention by Promotion Type      — which types drive repeat engagement
--   4. Reward Redemption Impact         — redeeming vs non-redeeming retention
--   5. Summary KPIs                     — top-level headline numbers
--
-- Prerequisites: run 00_load_bonusengine_data.sql first.
-- ============================================================================

-- ============================================================================
-- 1. MONTHLY ACTIVE PROMOTION USERS
-- ============================================================================
-- Count distinct users who opted in to at least one promotion per month.

WITH monthly_active AS (
    SELECT
        DATE_TRUNC('month', pu.OptInDateTimeUtc) AS activity_month,
        COUNT(DISTINCT pu.UserId)                AS active_users
    FROM promotion_user pu
    WHERE pu.UserIsOptIn = TRUE
      AND pu.OptInDateTimeUtc IS NOT NULL
    GROUP BY 1
)
SELECT
    activity_month,
    active_users,
    LAG(active_users) OVER (ORDER BY activity_month) AS prev_month_users,
    ROUND(
        100.0 * (active_users - LAG(active_users) OVER (ORDER BY activity_month))
              / NULLIF(LAG(active_users) OVER (ORDER BY activity_month), 0),
        1
    ) AS mom_growth_pct
FROM monthly_active
ORDER BY activity_month;


-- ============================================================================
-- 2. COHORT RETENTION
-- ============================================================================
-- For each cohort (month of a user's FIRST ever opt-in), calculate what
-- percentage of those users returned and opted in again in month N+1,
-- N+2, … up to 5 months later.

WITH first_optin AS (
    -- Cohort month: earliest opt-in per user
    SELECT
        UserId,
        DATE_TRUNC('month', MIN(OptInDateTimeUtc)) AS cohort_month
    FROM promotion_user
    WHERE UserIsOptIn = TRUE
      AND OptInDateTimeUtc IS NOT NULL
    GROUP BY UserId
),
user_activity AS (
    -- All months in which a user was active (opted in to any promo)
    SELECT DISTINCT
        UserId,
        DATE_TRUNC('month', OptInDateTimeUtc) AS active_month
    FROM promotion_user
    WHERE UserIsOptIn = TRUE
      AND OptInDateTimeUtc IS NOT NULL
),
cohort_activity AS (
    SELECT
        f.cohort_month,
        DATEDIFF(MONTH, f.cohort_month, a.active_month) AS months_since_cohort,
        COUNT(DISTINCT a.UserId)                          AS retained_users
    FROM first_optin     f
    JOIN user_activity   a ON a.UserId = f.UserId
    WHERE a.active_month >= f.cohort_month
    GROUP BY 1, 2
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT UserId) AS cohort_size
    FROM first_optin
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    cs.cohort_size,
    ca.months_since_cohort,
    ca.retained_users,
    ROUND(100.0 * ca.retained_users / cs.cohort_size, 1) AS retention_pct
FROM cohort_activity ca
JOIN cohort_sizes     cs ON cs.cohort_month = ca.cohort_month
WHERE ca.months_since_cohort BETWEEN 0 AND 5
ORDER BY ca.cohort_month, ca.months_since_cohort;


-- ============================================================================
-- 3. RETENTION BY PROMOTION TYPE
-- ============================================================================
-- Of users who participated in a promotion of a given type in month M,
-- what fraction returned to ANY promotion the following month?

WITH promo_type_activity AS (
    SELECT
        pu.UserId,
        pd.PromotionName,
        -- Extract the promotion type from the template name
        CASE
            WHEN pd.PromotionName LIKE '%Freebet%'          THEN 'Freebet'
            WHEN pd.PromotionName LIKE '%Cashback%'         THEN 'Cashback'
            WHEN pd.PromotionName LIKE '%Acumulador%'       THEN 'Accumulator'
            WHEN pd.PromotionName LIKE '%Reto%'             THEN 'Challenge'
            WHEN pd.PromotionName LIKE '%Bienvenida%'       THEN 'Welcome'
            WHEN pd.PromotionName LIKE '%Casino Bonus%'     THEN 'Casino Bonus'
            WHEN pd.PromotionName LIKE '%Tiradas%'          THEN 'Free Spins'
            WHEN pd.PromotionName LIKE '%Sin Riesgo%'       THEN 'Risk-Free Bet'
            ELSE 'Other'
        END                                                     AS promo_type,
        DATE_TRUNC('month', pu.OptInDateTimeUtc)               AS activity_month
    FROM promotion_user pu
    JOIN promotion_detail pd ON pd.PromotionId = pu.PromotionId
    WHERE pu.UserIsOptIn = TRUE
      AND pu.OptInDateTimeUtc IS NOT NULL
),
any_next_month AS (
    -- Did the user appear in any promotion the following month?
    SELECT DISTINCT UserId, activity_month
    FROM promo_type_activity
),
retention_by_type AS (
    SELECT
        pt.promo_type,
        pt.activity_month,
        COUNT(DISTINCT pt.UserId)                              AS users_this_month,
        COUNT(DISTINCT nm.UserId)                              AS returned_next_month
    FROM promo_type_activity pt
    LEFT JOIN any_next_month nm
           ON nm.UserId        = pt.UserId
          AND nm.activity_month = ADD_MONTHS(pt.activity_month, 1)
    GROUP BY 1, 2
)
SELECT
    promo_type,
    activity_month,
    users_this_month,
    returned_next_month,
    ROUND(100.0 * returned_next_month / NULLIF(users_this_month, 0), 1) AS next_month_retention_pct
FROM retention_by_type
ORDER BY promo_type, activity_month;


-- ============================================================================
-- 4. REWARD REDEMPTION IMPACT ON RETENTION
-- ============================================================================
-- Compare next-month return rates for users who redeemed their reward
-- versus those who were issued a reward but did not redeem it.

WITH issued AS (
    SELECT
        rru.UserId,
        rru.PromotionId,
        DATE_TRUNC('month', rru.IssuedOnUtc)                   AS issued_month,
        CASE WHEN rru.RedeemedOnUtc IS NOT NULL THEN 1 ELSE 0 END AS redeemed
    FROM reward_redeem_user rru
    WHERE rru.IssuedOnUtc IS NOT NULL
),
user_next_month AS (
    -- Did the user opt in to any promotion in the month after reward issuance?
    SELECT DISTINCT
        pu.UserId,
        DATE_TRUNC('month', pu.OptInDateTimeUtc) AS optin_month
    FROM promotion_user pu
    WHERE pu.UserIsOptIn = TRUE
      AND pu.OptInDateTimeUtc IS NOT NULL
)
SELECT
    i.redeemed,
    CASE WHEN i.redeemed = 1 THEN 'Redeemed' ELSE 'Not Redeemed' END AS redemption_status,
    COUNT(DISTINCT i.UserId)                                           AS total_users,
    COUNT(DISTINCT nm.UserId)                                          AS returned_next_month,
    ROUND(
        100.0 * COUNT(DISTINCT nm.UserId)
              / NULLIF(COUNT(DISTINCT i.UserId), 0),
        1
    )                                                                  AS retention_pct
FROM issued i
LEFT JOIN user_next_month nm
       ON nm.UserId      = i.UserId
      AND nm.optin_month = ADD_MONTHS(i.issued_month, 1)
GROUP BY 1, 2
ORDER BY 1 DESC;


-- ============================================================================
-- 5. SUMMARY KPIs
-- ============================================================================
-- Single-row headline metrics for the full data period.

WITH opted_in AS (
    SELECT
        UserId,
        DATE_TRUNC('month', OptInDateTimeUtc) AS activity_month
    FROM promotion_user
    WHERE UserIsOptIn = TRUE
      AND OptInDateTimeUtc IS NOT NULL
),
first_optin AS (
    SELECT UserId, MIN(activity_month) AS cohort_month
    FROM opted_in
    GROUP BY UserId
),
multi_month AS (
    SELECT oi.UserId
    FROM opted_in oi
    JOIN first_optin fi ON fi.UserId = oi.UserId
    WHERE oi.activity_month > fi.cohort_month
    GROUP BY oi.UserId
)
SELECT
    (SELECT COUNT(DISTINCT UserId) FROM opted_in)                      AS total_unique_promo_users,
    (SELECT COUNT(DISTINCT UserId) FROM multi_month)                   AS users_returned_after_first_month,
    ROUND(
        100.0 * (SELECT COUNT(DISTINCT UserId) FROM multi_month)
              / NULLIF((SELECT COUNT(DISTINCT UserId) FROM first_optin), 0),
        1
    )                                                                  AS overall_retention_pct,
    (SELECT ROUND(AVG(cnt), 1)
     FROM (
         SELECT UserId, COUNT(DISTINCT activity_month) AS cnt
         FROM opted_in
         GROUP BY UserId
     ) t)                                                              AS avg_active_months_per_user,
    (SELECT MAX(activity_month) FROM opted_in)                         AS latest_data_month,
    (SELECT MIN(activity_month) FROM opted_in)                         AS earliest_data_month;
