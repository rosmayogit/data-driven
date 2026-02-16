-- ============================================================================
-- COHORT ANALYSIS: Weekly participation cohorts
-- ============================================================================
-- Groups users by their first promo participation week, then tracks
-- their behavior in subsequent weeks.
-- ============================================================================

-- 1. Define cohorts: first participation week per user
CREATE OR REPLACE TEMP VIEW user_cohorts AS
SELECT
    f.user_id,
    DATE_TRUNC('week', MIN(f.participation_date)) AS cohort_week
FROM funnel f
WHERE f.participated = true
GROUP BY f.user_id;


-- 2. Weekly participation retention by cohort
-- Shows: of users who first participated in week X, how many participated
-- again in week X+1, X+2, etc.
SELECT
    uc.cohort_week,
    COUNT(DISTINCT uc.user_id) AS cohort_size,
    DATE_TRUNC('week', f.participation_date) AS activity_week,
    DATEDIFF(DATE_TRUNC('week', f.participation_date), uc.cohort_week) / 7 AS weeks_since_first,
    COUNT(DISTINCT f.user_id) AS active_users,
    ROUND(COUNT(DISTINCT f.user_id) * 100.0 / COUNT(DISTINCT uc.user_id), 1) AS retention_pct
FROM user_cohorts uc
JOIN funnel f
    ON uc.user_id = f.user_id
    AND f.participated = true
GROUP BY uc.cohort_week, DATE_TRUNC('week', f.participation_date)
ORDER BY uc.cohort_week, activity_week;


-- 3. Cohort retention matrix (pivot-friendly for dashboards)
-- Each row = cohort, each "week_N" = retention % at week N
SELECT
    uc.cohort_week,
    COUNT(DISTINCT uc.user_id) AS cohort_size,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(DATE_TRUNC('week', f.participation_date), uc.cohort_week) / 7 = 0
        THEN f.user_id END) * 100.0 / COUNT(DISTINCT uc.user_id), 1) AS week_0,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(DATE_TRUNC('week', f.participation_date), uc.cohort_week) / 7 = 1
        THEN f.user_id END) * 100.0 / COUNT(DISTINCT uc.user_id), 1) AS week_1,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(DATE_TRUNC('week', f.participation_date), uc.cohort_week) / 7 = 2
        THEN f.user_id END) * 100.0 / COUNT(DISTINCT uc.user_id), 1) AS week_2,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(DATE_TRUNC('week', f.participation_date), uc.cohort_week) / 7 = 3
        THEN f.user_id END) * 100.0 / COUNT(DISTINCT uc.user_id), 1) AS week_3,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(DATE_TRUNC('week', f.participation_date), uc.cohort_week) / 7 = 4
        THEN f.user_id END) * 100.0 / COUNT(DISTINCT uc.user_id), 1) AS week_4,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(DATE_TRUNC('week', f.participation_date), uc.cohort_week) / 7 = 5
        THEN f.user_id END) * 100.0 / COUNT(DISTINCT uc.user_id), 1) AS week_5,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(DATE_TRUNC('week', f.participation_date), uc.cohort_week) / 7 = 6
        THEN f.user_id END) * 100.0 / COUNT(DISTINCT uc.user_id), 1) AS week_6
FROM user_cohorts uc
JOIN funnel f
    ON uc.user_id = f.user_id
    AND f.participated = true
GROUP BY uc.cohort_week
ORDER BY uc.cohort_week;


-- 4. Cohort size evolution: how many new promo users each week
SELECT
    cohort_week,
    COUNT(*) AS new_promo_users,
    SUM(COUNT(*)) OVER (ORDER BY cohort_week) AS cumulative_promo_users
FROM user_cohorts
GROUP BY cohort_week
ORDER BY cohort_week;
