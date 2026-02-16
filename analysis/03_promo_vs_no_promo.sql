-- ============================================================================
-- COMPARATIVE ANALYSIS: Promo users vs Non-promo users
-- ============================================================================
-- Compares key metrics between users who participate in promotions
-- and those who don't, over time.
-- ============================================================================

-- 1. Classify users: promo participant vs non-participant
CREATE OR REPLACE TEMP VIEW user_promo_flag AS
SELECT
    u.user_id,
    u.segment,
    u.country,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM funnel f
            WHERE f.user_id = u.user_id AND f.participated = true
        ) THEN 'promo_user'
        ELSE 'non_promo_user'
    END AS user_type
FROM users u;


-- 2. Weekly KPIs: promo users vs non-promo users
SELECT
    upf.user_type,
    DATE_TRUNC('week', da.activity_date) AS week,
    COUNT(DISTINCT da.user_id) AS unique_users,
    -- Active days
    ROUND(SUM(CASE WHEN da.is_active THEN 1 ELSE 0 END) * 1.0
        / COUNT(DISTINCT da.user_id), 2) AS avg_active_days_per_user,
    -- Stake
    ROUND(SUM(da.total_stake) / COUNT(DISTINCT da.user_id), 2) AS avg_stake_per_user,
    ROUND(SUM(da.total_stake)
        / NULLIF(SUM(CASE WHEN da.is_active THEN 1 ELSE 0 END), 0), 2) AS avg_stake_per_active_day,
    -- Bets
    ROUND(SUM(da.num_bets) * 1.0 / COUNT(DISTINCT da.user_id), 2) AS avg_bets_per_user,
    -- Product diversity
    ROUND(AVG(CASE WHEN da.is_active THEN da.num_products ELSE NULL END), 2) AS avg_products_when_active
FROM daily_activity da
JOIN user_promo_flag upf ON da.user_id = upf.user_id
GROUP BY upf.user_type, DATE_TRUNC('week', da.activity_date)
ORDER BY week, upf.user_type;


-- 3. Same comparison but controlling for segment
-- (important because high_value users are more likely to use promos AND be active)
SELECT
    upf.segment,
    upf.user_type,
    COUNT(DISTINCT da.user_id) AS unique_users,
    ROUND(SUM(CASE WHEN da.is_active THEN 1 ELSE 0 END) * 1.0
        / COUNT(DISTINCT da.user_id), 2) AS avg_active_days_per_user,
    ROUND(SUM(da.total_stake) / COUNT(DISTINCT da.user_id), 2) AS avg_stake_per_user,
    ROUND(SUM(da.num_bets) * 1.0 / COUNT(DISTINCT da.user_id), 2) AS avg_bets_per_user,
    ROUND(AVG(CASE WHEN da.is_active THEN da.num_products ELSE NULL END), 2) AS avg_products_when_active
FROM daily_activity da
JOIN user_promo_flag upf ON da.user_id = upf.user_id
GROUP BY upf.segment, upf.user_type
ORDER BY upf.segment, upf.user_type;


-- 4. Retention comparison: % of users active each week
-- (Did they come back week over week?)
SELECT
    upf.user_type,
    DATE_TRUNC('week', da.activity_date) AS week,
    COUNT(DISTINCT da.user_id) AS total_users_in_group,
    COUNT(DISTINCT CASE WHEN da.is_active THEN da.user_id END) AS active_users,
    ROUND(COUNT(DISTINCT CASE WHEN da.is_active THEN da.user_id END) * 100.0
        / COUNT(DISTINCT da.user_id), 1) AS weekly_active_pct
FROM daily_activity da
JOIN user_promo_flag upf ON da.user_id = upf.user_id
GROUP BY upf.user_type, DATE_TRUNC('week', da.activity_date)
ORDER BY week, upf.user_type;


-- 5. Before vs After first promo: does the user behavior change?
-- Compares the 4 weeks before first participation vs 4 weeks after
WITH first_participation AS (
    SELECT
        user_id,
        MIN(participation_date) AS first_promo_date
    FROM funnel
    WHERE participated = true
    GROUP BY user_id
)
SELECT
    CASE
        WHEN da.activity_date < fp.first_promo_date THEN 'before_promo'
        ELSE 'after_promo'
    END AS period,
    COUNT(DISTINCT da.user_id) AS users,
    ROUND(SUM(CASE WHEN da.is_active THEN 1 ELSE 0 END) * 1.0
        / COUNT(DISTINCT da.user_id), 2) AS avg_active_days,
    ROUND(SUM(da.total_stake) / COUNT(DISTINCT da.user_id), 2) AS avg_stake,
    ROUND(SUM(da.num_bets) * 1.0 / COUNT(DISTINCT da.user_id), 2) AS avg_bets,
    ROUND(AVG(CASE WHEN da.is_active THEN da.num_products ELSE NULL END), 2) AS avg_products
FROM daily_activity da
JOIN first_participation fp ON da.user_id = fp.user_id
WHERE da.activity_date BETWEEN DATE_SUB(fp.first_promo_date, 28)
                           AND DATE_ADD(fp.first_promo_date, 28)
GROUP BY CASE
    WHEN da.activity_date < fp.first_promo_date THEN 'before_promo'
    ELSE 'after_promo'
END
ORDER BY period;


-- 6. Uplift by promo type: how much does each promo type increase stake?
-- Compares user stake in promo weeks vs non-promo weeks
WITH user_promo_weeks AS (
    SELECT DISTINCT
        f.user_id,
        DATE_TRUNC('week', p.start_date) AS promo_week,
        p.promo_type
    FROM funnel f
    JOIN promotions p ON f.promo_id = p.promo_id
    WHERE f.participated = true
)
SELECT
    upw.promo_type,
    ROUND(AVG(CASE WHEN upw.promo_week IS NOT NULL THEN da.total_stake END), 2) AS avg_daily_stake_promo_week,
    ROUND(AVG(CASE WHEN upw.promo_week IS NULL THEN da.total_stake END), 2) AS avg_daily_stake_non_promo_week,
    ROUND(
        (AVG(CASE WHEN upw.promo_week IS NOT NULL THEN da.total_stake END)
        - AVG(CASE WHEN upw.promo_week IS NULL THEN da.total_stake END))
        * 100.0
        / NULLIF(AVG(CASE WHEN upw.promo_week IS NULL THEN da.total_stake END), 0),
    1) AS stake_uplift_pct
FROM daily_activity da
LEFT JOIN user_promo_weeks upw
    ON da.user_id = upw.user_id
    AND DATE_TRUNC('week', da.activity_date) = upw.promo_week
WHERE da.is_active = true
GROUP BY upw.promo_type
ORDER BY stake_uplift_pct DESC;
