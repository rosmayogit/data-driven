# PRD — Promotions Analytics Dashboard

**Target audience:** Data Analyst
**Platform:** Databricks (SQL + Python notebooks)
**Status:** In progress — S1–S3 available with BonusEngine data; S4–S6 pending `db_silver.bets`
**Last updated:** 2026-03-17

---

## 1. Purpose

Provide a single analytical dashboard that allows the promotions team and data analysts to measure the effectiveness of the BonusEngine promotions across three dimensions:

1. **Campaign performance** — volume, cost, and redemption rates per campaign
2. **User acquisition** — new vs. returning participants per promotion
3. **Retention & engagement** — cohort retention, active days, and stake behaviour
4. **Revenue impact** — ARPU uplift for promo participants vs. a same-segment control group

---

## 2. Data Sources

### 2.1 BonusEngine tables (available now)

Loaded via `analysis/bonusengine/00_load_bonusengine_data.sql`.

| Table | Description | Key columns |
|-------|-------------|-------------|
| `promotion_detail` | One row per promotion (campaign definition) | `PromotionId`, `PromotionName`, `BrandId`, `IsSegmented`, `StartDateUtc`, `EndDateUtc`, `ValidationTargetBetsPlaced`, `ValidationTargetAmountStaked`, `MaxRedemptions` |
| `promotion_user` | One row per (user × promotion) participation | `PromotionId`, `UserId`, `QualificationCount`, `ConfirmedBetsPlaced`, `ConfirmedGrossAmountStaked`, `UserIsOptIn`, `OptInDateTimeUtc` |
| `reward_detail` | Reward catalogue | `RewardId`, `BrandId`, `RewardName`, `ExpirationDays` |
| `reward_redeem_user` | Reward issuance + redemption per user | `RewardItemId`, `PromotionId`, `UserId`, `RewardId`, `IssuedOnUtc`, `RedeemedOnUtc` |
| `reward_freebet` | Freebet amounts and types per issued reward | `RewardItemId`, `RewardId`, `Amount`, `FreebetTypeName`, `ProductCode` |

> **Qualified user:** `QualificationCount > 0` in `promotion_user`.
> **Redeemed reward:** `RedeemedOnUtc IS NOT NULL` in `reward_redeem_user`.

### 2.2 External tables (required for S4–S6, pending)

| Table | Minimum columns |
|-------|----------------|
| `db_silver.bets` | `user_id`, `bet_date`, `stake`, `odds`, `result` (`'won'` / `'lost'`) |
| `db_silver.users` | `user_id`, `segment` |

**GGR formula per bet:**
```sql
stake - CASE WHEN result = 'won' THEN stake * odds ELSE 0 END
```

> Note: Until `db_silver.bets` is available, `ConfirmedGrossAmountStaked` from `promotion_user` is used as a volume proxy (not a revenue proxy).

---

## 3. Configuration Parameters

The notebook (`notebooks/01_bonusengine_analysis.py` / `.sql`) accepts the following parameters before execution:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `START_DATE` | `2025-08-01` | Start of the analysis period |
| `END_DATE` | `2026-02-28` | End of the analysis period |
| `WINDOW_DAYS` | `28` | Before/after window in days for ARPU uplift (S6) |
| `BRAND_ID_FILTER` | `None` (all brands) | Filter to a specific brand (`BrandId`: 1=ES, 2=MX, 3=CO) |
| `WEEKLY_MAX_DURATION_DAYS` | `7` | Max duration (days) for a campaign to be classified as "weekly" |

---

## 4. Campaign Type Classification

Derived in the base view `v_campaign_types` from `promotion_detail`:

| Type | Duration |
|------|----------|
| `Semanal` | ≤ 7 days |
| `Quincenal` | 8–14 days |
| `Mensual` | 15–31 days |
| `Otro` | > 31 days |

---

## 5. Dashboard Sections

### S1 — Monthly Campaign Summary

**Goal:** Monitor campaign volume, bonus spend, and redemption rate month by month.

**Source view:** `v_s1_monthly_campaign_summary`

**Built from:**
- `v_campaign_types` (from `promotion_detail`)
- `promotion_user` (`QualificationCount > 0`)
- `reward_redeem_user` + `reward_freebet` (for bonus costs)

**Metrics:**

| Metric | Definition |
|--------|-----------|
| `qualified_users` | Distinct users with `QualificationCount > 0` |
| `total_bets_placed` | `SUM(ConfirmedBetsPlaced)` |
| `total_stakes` | `SUM(ConfirmedGrossAmountStaked)` — volume proxy |
| `rewards_issued` | Distinct `RewardItemId` in `reward_redeem_user` |
| `rewards_redeemed` | Distinct `RewardItemId` where `RedeemedOnUtc IS NOT NULL` |
| `total_cost_redeemed` | `SUM(Amount)` from `reward_freebet` for redeemed rewards |
| `redemption_rate_pct` | `rewards_redeemed / rewards_issued * 100` |
| `cost_per_qualified_user` | `total_cost_redeemed / qualified_users` |
| `avg_stakes_per_user` | `total_stakes / qualified_users` |
| NGR | `GGR - total_cost_redeemed` — **pending `db_silver.bets`** |

**Suggested widgets:**
- Table with all columns, filterable by `campaign_month`, `campaign_type`, `BrandId`, `target_segment`
- Bar chart: `total_stakes` and `total_cost_redeemed` per month
- KPI cards: total `qualified_users`, `redemption_rate_pct`, `cost_per_qualified_user`

---

### S2 — New vs. Returning Users per Promotion

**Goal:** Understand how many participants are being exposed to promotions for the first time vs. recurring users.

**Source view:** `v_s2_new_users_per_promotion`

**Built from:**
- `v_campaign_types`
- `promotion_user` (`QualificationCount > 0`)
- `v_s2_user_first_promo_dedup` — each user's first ever qualifying promotion (ordered by `OptInDateTimeUtc`, fallback to `promotion_detail.StartDateUtc`)

**Definition of "new user":** The first promotion (across all history in the BonusEngine) in which a user has `QualificationCount > 0`.

**Metrics:**

| Metric | Definition |
|--------|-----------|
| `total_qualified_users` | Distinct qualified users in this promotion |
| `new_users` | Users for whom `first_promo_id = PromotionId` |
| `returning_users` | Users who had already qualified in a previous promotion |
| `new_user_pct` | `new_users / total_qualified_users * 100` |

**Suggested widgets:**
- Stacked bar chart per month: new vs. returning users
- Table sorted by `new_user_pct DESC` — identify which promos attract fresh users
- Line chart: `new_user_pct` trend over time

---

### S3 — Weekly Cohort Retention

**Goal:** Track how well weekly promotions retain their participants over subsequent weeks.

> Applies only to campaigns with `duration_days <= 7` (`Semanal` type).

**Source views:**
- `v_s3_cohort_retention` — time-series retention per cohort week
- `v_s3_cohort_matrix` — pivot table (cohort week × week offset)
- `v_s3_cohort_size_evolution` — new users entering each week + running total

**Definitions:**
- **Cohort week:** The week (`DATE_TRUNC('week', ...)`) of a user's first qualification in any weekly campaign. Uses `OptInDateTimeUtc` if available, else `StartDateUtc`.
- **Active in a week:** User has `QualificationCount > 0` in a weekly campaign starting that week.
- **Segment:** Derived from `IsSegmented` field of the user's first weekly campaign.

**Key metrics in `v_s3_cohort_retention`:**

| Metric | Definition |
|--------|-----------|
| `cohort_week` | ISO week of the user's first participation |
| `cohort_size` | Total distinct users in that cohort |
| `weeks_since_start` | `DATEDIFF(activity_week, cohort_week) / 7` |
| `active_users` | Users from that cohort active in `activity_week` |
| `retention_pct` | `active_users / cohort_size * 100` |

**Key metrics in `v_s3_cohort_matrix`:**
- Columns `week_0` through `week_9`: retention % at each week offset (100% on diagonal = week_0)

**Key metrics in `v_s3_cohort_size_evolution`:**
- `new_promo_users`: Users entering the promotion programme for the first time that week
- `cumulative_promo_users`: Running total of promo participants, partitioned by segment

**Suggested widgets:**
- Line chart: `retention_pct` by `weeks_since_start`, one line per `cohort_week`, filter by `segment`
- Heatmap: `v_s3_cohort_matrix` — X axis = `week_N`, Y axis = `cohort_week`
- Bar + line chart: `new_promo_users` per week + `cumulative_promo_users`

---

### S4 — Monthly ARPU: Participants vs. Control Group

> **Requires `db_silver.bets` and `db_silver.users`**

**Goal:** Compare revenue per user between promotion participants and a same-segment control group (users who never qualified in a weekly campaign).

**Source view:** `v_s4_arpu_monthly_comparison`

**Control group definition (`v_s4_control_users`):**
Users in `db_silver.users` whose `user_id` does NOT appear in `v_s3_user_cohorts_dedup`.

**Metrics:**

| Metric | Definition |
|--------|-----------|
| `active_users` | Distinct users with at least 1 bet that month |
| `total_ggr` | `SUM(stake - CASE WHEN result='won' THEN stake*odds ELSE 0 END)` |
| `arpu` | `total_ggr / active_users` |

**Dimensions:** `activity_month`, `user_type` (`participant` / `control`), `segment`

**Suggested widgets:**
- Line chart: `arpu` per month, two lines (participant vs. control), filter by `segment`
- Grouped bar chart: `arpu` side-by-side per segment for a selected month

---

### S5 — Key Engagement Metrics: Participants vs. Control

> **Requires `db_silver.bets`**

**Goal:** Compare behavioural engagement between promo participants and control users.

**Source view:** `v_s5_key_metrics_comparison`

**Metrics:**

| Metric | Definition |
|--------|-----------|
| `avg_stakes_per_user` | Average total stake per user per month |
| `avg_active_days_per_month` | Average distinct days with at least 1 bet |
| `avg_active_days_per_week` | `active_days / active_weeks` — betting density per week |

**Dimensions:** `user_type`, `segment`, `activity_month`

**Suggested widgets:**
- 3 KPI cards per group: `avg_stakes_per_user`, `avg_active_days_per_month`, `avg_active_days_per_week`
- Grouped bar chart: all three metrics side-by-side, participant vs. control

---

### S6a — ARPU Uplift Before/After First Promotion

> **Requires `db_silver.bets`**

**Goal:** For each participant, measure the change in GGR in a symmetric window around their first weekly promotion.

**Window:** ±`WINDOW_DAYS` days (default 28) around `cohort_week`:
- **Before:** `[cohort_week − 28d, cohort_week − 1d]`
- **After:** `[cohort_week, cohort_week + 27d]`

**Source view:** `v_s6_arpu_uplift_by_segment`

**Metrics:**

| Metric | Definition |
|--------|-----------|
| `users_analyzed` | Users with bets in both windows |
| `avg_ggr_before_28d` | Average GGR in the 28 days before first promo |
| `avg_ggr_after_28d` | Average GGR in the 28 days after first promo |
| `avg_arpu_uplift` | `avg_ggr_after - avg_ggr_before` |
| `p25_uplift` / `p75_uplift` | Interquartile range of individual uplift values |
| `avg_uplift_pct` | Mean percentage change in GGR |
| `avg_active_days_before/after` | Change in activity days |

**Suggested widgets:**
- KPI cards per segment: `avg_arpu_uplift` + `avg_uplift_pct`
- Waterfall chart: `avg_ggr_before` → `avg_ggr_after` per segment
- Box plot or p25/p75 error bars showing uplift distribution

---

### S6b — Expected ARPU Uplift by Segment × Promotion Type

> **Requires `db_silver.bets`**

**Goal:** Identify which combinations of user segment and campaign type generate the highest revenue uplift. Uses historical observed uplift grouped by segment × first promotion type (SQL version) or an XGBoost-predicted uplift (Python version).

**Source view:** `v_s6_expected_arpu_by_segment`

**Input features (for the ML model):**
- `segment` — user segment from their first weekly campaign
- `first_promo_name` — name of the first weekly campaign the user qualified in
- `avg_stake_28d_before` — average bet size in the 28 days prior
- `active_days_28d_before` — days with at least 1 bet in the 28 days prior
- `total_bets_28d_before` — total bet count in the 28 days prior
- `total_stakes_28d_before` — total stake volume in the 28 days prior

**Output metrics:**

| Metric | Definition |
|--------|-----------|
| `user_count` | Users in this segment × promo combination |
| `avg_uplift` | Mean observed (SQL) or predicted (XGBoost) ARPU uplift |
| `p25_uplift` / `p50_uplift` / `p75_uplift` | Uplift percentiles |
| `avg_stake_pre_promo` | Average pre-promo stake (context) |
| `avg_active_days_pre_promo` | Average pre-promo activity days (context) |

**Suggested widgets:**
- Heatmap: segment (Y) × promo type (X), value = `avg_uplift`
- Ranked table: sorted by `avg_uplift DESC` with p25/p75 as confidence bands

---

## 6. Full View Reference

| View | Section | Status | Source tables | Dashboard widget |
|------|---------|--------|---------------|-----------------|
| `v_s1_monthly_campaign_summary` | S1 | ✅ Available | `promotion_detail`, `promotion_user`, `reward_redeem_user`, `reward_freebet` | Table + bar chart |
| `v_s2_new_users_per_promotion` | S2 | ✅ Available | `promotion_detail`, `promotion_user` | Stacked bar + table |
| `v_s3_cohort_retention` | S3 | ✅ Available | `promotion_detail`, `promotion_user` | Line chart |
| `v_s3_cohort_matrix` | S3 | ✅ Available | `promotion_detail`, `promotion_user` | Heatmap |
| `v_s3_cohort_size_evolution` | S3 | ✅ Available | `promotion_detail`, `promotion_user` | Bar + line chart |
| `v_s4_arpu_monthly_comparison` | S4 | ⏳ Pending `db_silver.bets` | `promotion_user`, `db_silver.bets`, `db_silver.users` | Line chart by segment |
| `v_s5_key_metrics_comparison` | S5 | ⏳ Pending `db_silver.bets` | `promotion_user`, `db_silver.bets`, `db_silver.users` | Grouped bar / KPI cards |
| `v_s6_arpu_uplift_by_segment` | S6a | ⏳ Pending `db_silver.bets` | `promotion_user`, `db_silver.bets` | KPI cards + waterfall |
| `v_s6_expected_arpu_by_segment` | S6b | ⏳ Pending `db_silver.bets` | `promotion_user`, `db_silver.bets` | Heatmap + ranked table |

---

## 7. Recommended Dashboard Filters (Global)

| Filter | Source | Applies to |
|--------|--------|-----------|
| `campaign_month` | `promotion_detail.StartDateUtc` | S1, S2, S4, S5 |
| `campaign_type` | Derived (`v_campaign_types`) | S1, S2 |
| `BrandId` | `promotion_detail.BrandId` | S1, S2, S3 |
| `segment` | `promotion_user.IsSegmented` | S1, S2, S3, S4, S5, S6 |
| `cohort_week` | `v_s3_user_cohorts_dedup` | S3 |

---

## 8. Known Limitations & Pending Work

| Item | Impact | When |
|------|--------|------|
| No `db_silver.bets` connection | S4–S6 cannot be built; NGR cannot be calculated | Blocked on data team |
| `ConfirmedGrossAmountStaked` is a volume proxy | Cannot compute GGR or NGR from BonusEngine alone | Resolved when bets table is available |
| NGR = GGR − Bonus Costs | GGR requires individual bets; add to S1 once bets table is connected | Next iteration |
| Cohort matrix fixed at 10 weeks | `v_s3_cohort_matrix` has hardcoded `week_0`…`week_9` columns | Extend if needed |
| XGBoost uplift model (S6b Python) | Requires ≥ 30 users with complete data; falls back to `sklearn GradientBoosting` if XGBoost not installed | No action needed |
| Multi-brand analysis | `BrandId` filter available; cross-brand aggregations are possible but currency normalisation may be needed | Future iteration |

---

## 9. How to Run

### Prerequisites

```bash
# Generate synthetic data (local test)
python scripts/generate_bonusengine_data.py --users 2000 --months 6

# Upload CSVs to DBFS, then load tables:
# Run analysis/bonusengine/00_load_bonusengine_data.sql in Databricks
```

### Execution order in Databricks

1. Run `analysis/bonusengine/00_load_bonusengine_data.sql` — creates the 5 BonusEngine tables
2. Open `notebooks/01_bonusengine_analysis.py` (or `.sql`)
3. Adjust parameters in the **Configuration** cell (`START_DATE`, `END_DATE`, `BRAND_ID_FILTER`)
4. Run all cells **in order** — each view depends on the previous ones
5. Pin `SELECT * FROM v_s<N>_...` outputs as dashboard widgets

### When `db_silver.bets` becomes available

Update the configuration cell:
```python
BETS_TABLE  = "db_silver.bets"
USERS_TABLE = "db_silver.users"
```
Then re-run from S4 onwards.
