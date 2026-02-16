-- ============================================================================
-- FUNNEL ANALYSIS: Promotion conversion funnel
-- ============================================================================
-- Tracks: Eligible → Opt-in → Participate → Win → Redeem
-- Run after loading CSVs as tables: funnel, promotions, users
-- ============================================================================

-- 1. Overall funnel by promo type
SELECT
    p.promo_type,
    COUNT(DISTINCT f.user_id) AS total_users,
    SUM(CASE WHEN f.eligible THEN 1 ELSE 0 END) AS eligible,
    SUM(CASE WHEN f.opted_in THEN 1 ELSE 0 END) AS opted_in,
    SUM(CASE WHEN f.participated THEN 1 ELSE 0 END) AS participated,
    SUM(CASE WHEN f.won THEN 1 ELSE 0 END) AS won,
    SUM(CASE WHEN f.reward_redeemed THEN 1 ELSE 0 END) AS redeemed,
    -- Conversion rates
    ROUND(SUM(CASE WHEN f.opted_in THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN f.eligible THEN 1 ELSE 0 END), 0), 1) AS eligible_to_optin_pct,
    ROUND(SUM(CASE WHEN f.participated THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN f.opted_in THEN 1 ELSE 0 END), 0), 1) AS optin_to_participate_pct,
    ROUND(SUM(CASE WHEN f.won THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN f.participated THEN 1 ELSE 0 END), 0), 1) AS participate_to_win_pct,
    ROUND(SUM(CASE WHEN f.reward_redeemed THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN f.won THEN 1 ELSE 0 END), 0), 1) AS win_to_redeem_pct
FROM funnel f
JOIN promotions p ON f.promo_id = p.promo_id
GROUP BY p.promo_type
ORDER BY eligible DESC;


-- 2. Funnel by promo type AND user segment
SELECT
    u.segment,
    p.promo_type,
    COUNT(*) AS total_records,
    SUM(CASE WHEN f.eligible THEN 1 ELSE 0 END) AS eligible,
    SUM(CASE WHEN f.opted_in THEN 1 ELSE 0 END) AS opted_in,
    SUM(CASE WHEN f.participated THEN 1 ELSE 0 END) AS participated,
    SUM(CASE WHEN f.won THEN 1 ELSE 0 END) AS won,
    SUM(CASE WHEN f.reward_redeemed THEN 1 ELSE 0 END) AS redeemed,
    ROUND(SUM(CASE WHEN f.participated THEN 1 ELSE 0 END) * 100.0
        / NULLIF(SUM(CASE WHEN f.eligible THEN 1 ELSE 0 END), 0), 1) AS eligible_to_participation_pct
FROM funnel f
JOIN promotions p ON f.promo_id = p.promo_id
JOIN users u ON f.user_id = u.user_id
GROUP BY u.segment, p.promo_type
ORDER BY u.segment, p.promo_type;


-- 3. Weekly funnel trend (good for dashboards)
SELECT
    DATE_TRUNC('week', p.start_date) AS promo_week,
    p.promo_type,
    SUM(CASE WHEN f.eligible THEN 1 ELSE 0 END) AS eligible,
    SUM(CASE WHEN f.opted_in THEN 1 ELSE 0 END) AS opted_in,
    SUM(CASE WHEN f.participated THEN 1 ELSE 0 END) AS participated,
    SUM(CASE WHEN f.won THEN 1 ELSE 0 END) AS won,
    SUM(CASE WHEN f.reward_redeemed THEN 1 ELSE 0 END) AS redeemed,
    ROUND(SUM(f.reward_amount), 2) AS total_rewards_given
FROM funnel f
JOIN promotions p ON f.promo_id = p.promo_id
GROUP BY DATE_TRUNC('week', p.start_date), p.promo_type
ORDER BY promo_week, p.promo_type;


-- 4. Reward cost analysis
SELECT
    p.promo_type,
    COUNT(CASE WHEN f.won THEN 1 END) AS winners,
    ROUND(SUM(f.reward_amount), 2) AS total_reward_cost,
    ROUND(AVG(CASE WHEN f.won THEN f.reward_amount END), 2) AS avg_reward,
    COUNT(CASE WHEN f.reward_redeemed THEN 1 END) AS rewards_used,
    ROUND(SUM(CASE WHEN f.reward_redeemed THEN f.reward_amount ELSE 0 END), 2) AS cost_of_used_rewards
FROM funnel f
JOIN promotions p ON f.promo_id = p.promo_id
GROUP BY p.promo_type
ORDER BY total_reward_cost DESC;
