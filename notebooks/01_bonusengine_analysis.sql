-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Bonus Engine — Analysis Notebook (SQL)
-- MAGIC
-- MAGIC Dashboard-ready SQL views for the promotions engine analysis.
-- MAGIC
-- MAGIC ## What's included
-- MAGIC | Sección | Descripción | Datos necesarios |
-- MAGIC |---------|-------------|-----------------|
-- MAGIC | **S1** | Resumen mensual de campañas (stakes, bonus costs) | BonusEngine ✅ |
-- MAGIC | **S2** | % Usuarios nuevos por promoción | BonusEngine ✅ |
-- MAGIC | **S3** | Cohort de participación semanal + retención | BonusEngine ✅ |
-- MAGIC | S4 | ARPU cohort vs mismo segmento | Requiere `db_silver.bets` ⏳ |
-- MAGIC | S5 | Comparativa métricas clave (active days, stakes) | Requiere `db_silver.bets` ⏳ |
-- MAGIC | S6 | Incremento de ARPU + expected uplift por segmento | Requiere `db_silver.bets` ⏳ |
-- MAGIC
-- MAGIC ## Prerequisitos
-- MAGIC 1. Tablas del BonusEngine cargadas (ver `analysis/bonusengine/00_load_bonusengine_data.sql`)
-- MAGIC 2. Ejecutar las celdas **en orden** — cada view depende de las anteriores
-- MAGIC
-- MAGIC **Nota sobre NGR:** Para calcular NGR necesitamos `GGR - Bonus Costs`. El GGR
-- MAGIC requiere la tabla de apuestas individual. Por ahora usamos `ConfirmedGrossAmountStaked`
-- MAGIC (stakes validados durante la promo) como proxy de volumen, no de revenue.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## ⚙️ Configuración
-- MAGIC
-- MAGIC Ajusta los parámetros antes de ejecutar el notebook.
-- MAGIC
-- MAGIC | Variable | Descripción | Valor por defecto |
-- MAGIC |----------|-------------|-------------------|
-- MAGIC | `START_DATE` | Inicio del período de análisis | `2025-08-01` |
-- MAGIC | `END_DATE` | Fin del período de análisis | `2026-02-28` |
-- MAGIC | `WINDOW_DAYS` | Ventana before/after para S6 (días) | `28` |
-- MAGIC
-- MAGIC > Para S4-S6 se usan las tablas `db_silver.bets` y `db_silver.users`.
-- MAGIC > Si tu catálogo es diferente, busca y reemplaza esas referencias en las secciones S4-S6.

-- COMMAND ----------

SET START_DATE  = '2025-08-01';
SET END_DATE    = '2026-02-28';
SET WINDOW_DAYS = 28;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🔍 Validación de datos
-- MAGIC
-- MAGIC Verifica que las tablas del BonusEngine estén disponibles y tienen datos.

-- COMMAND ----------

SELECT 'promotion_detail'   AS tabla, COUNT(*) AS filas FROM promotion_detail
UNION ALL
SELECT 'promotion_user',              COUNT(*) FROM promotion_user
UNION ALL
SELECT 'reward_detail',               COUNT(*) FROM reward_detail
UNION ALL
SELECT 'reward_redeem_user',          COUNT(*) FROM reward_redeem_user
UNION ALL
SELECT 'reward_freebet',              COUNT(*) FROM reward_freebet

-- COMMAND ----------

-- Rango de fechas y campañas únicas
SELECT
  MIN(StartDateUtc)           AS primera_campana,
  MAX(EndDateUtc)             AS ultima_campana,
  COUNT(DISTINCT PromotionId) AS num_campanas,
  COUNT(DISTINCT BrandId)     AS num_brands
FROM promotion_detail

-- COMMAND ----------

SELECT
  COUNT(DISTINCT UserId)                                              AS usuarios_totales,
  COUNT(DISTINCT CASE WHEN QualificationCount > 0 THEN UserId END)   AS usuarios_cualificados,
  COUNT(DISTINCT CASE WHEN UserIsOptIn = true    THEN UserId END)     AS usuarios_con_optin,
  COUNT(*)                                                            AS filas_participation
FROM promotion_user

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Sección 1 — Resumen mensual de campañas
-- MAGIC
-- MAGIC Métricas agregadas por campaña y mes:
-- MAGIC - **Stakes totales**: suma de `ConfirmedGrossAmountStaked` de usuarios cualificados
-- MAGIC - **Bonus costs**: suma de `Amount` de recompensas **canjeadas** (`RedeemedOnUtc IS NOT NULL`)
-- MAGIC - **Usuarios únicos**: participantes con `QualificationCount > 0`
-- MAGIC - **Tasa de canje**: % de recompensas emitidas que fueron canjeadas
-- MAGIC
-- MAGIC > ⚠️ NGR = GGR − Bonus Costs. El GGR requiere la tabla de apuestas individual.
-- MAGIC > Se añadirá en una próxima iteración cuando esté disponible `db_silver.bets`.

-- COMMAND ----------

-- View base: clasifica cada campaña por tipo (semanal / quincenal / mensual / otro)
CREATE OR REPLACE TEMP VIEW v_campaign_types AS
SELECT
  PromotionId,
  PromotionName,
  BrandId,
  IsSegmented,
  StartDateUtc,
  EndDateUtc,
  DATEDIFF(EndDateUtc, StartDateUtc) AS duration_days,
  CASE
    WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 7  THEN 'Semanal'
    WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 14 THEN 'Quincenal'
    WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 31 THEN 'Mensual'
    ELSE 'Otro'
  END AS campaign_type
FROM promotion_detail
WHERE StartDateUtc >= '${START_DATE}'
  AND StartDateUtc <= '${END_DATE}'

-- COMMAND ----------

-- Stakes y participación por campaña (de usuarios cualificados)
CREATE OR REPLACE TEMP VIEW v_s1_campaign_stakes AS
SELECT
  ct.PromotionId,
  ct.PromotionName,
  ct.campaign_type,
  ct.BrandId,
  ct.IsSegmented                    AS target_segment,
  DATE_TRUNC('month', ct.StartDateUtc) AS campaign_month,
  COUNT(DISTINCT pu.UserId)         AS qualified_users,
  SUM(pu.ConfirmedBetsPlaced)       AS total_bets_placed,
  ROUND(SUM(pu.ConfirmedGrossAmountStaked), 2) AS total_stakes
FROM v_campaign_types ct
JOIN promotion_user pu ON ct.PromotionId = pu.PromotionId
WHERE pu.QualificationCount > 0
GROUP BY
  ct.PromotionId, ct.PromotionName, ct.campaign_type,
  ct.BrandId, ct.IsSegmented, campaign_month

-- COMMAND ----------

-- Bonus costs: recompensas emitidas vs canjeadas por campaña
CREATE OR REPLACE TEMP VIEW v_s1_bonus_costs AS
SELECT
  rru.PromotionId,
  COUNT(DISTINCT rru.RewardItemId)                                       AS rewards_issued,
  COUNT(DISTINCT CASE WHEN rru.RedeemedOnUtc IS NOT NULL
                       THEN rru.RewardItemId END)                        AS rewards_redeemed,
  ROUND(SUM(rf.Amount), 2)                                               AS total_cost_issued,
  ROUND(SUM(CASE WHEN rru.RedeemedOnUtc IS NOT NULL
                 THEN rf.Amount ELSE 0 END), 2)                          AS total_cost_redeemed,
  ROUND(COUNT(DISTINCT CASE WHEN rru.RedeemedOnUtc IS NOT NULL
                             THEN rru.RewardItemId END) * 100.0
        / NULLIF(COUNT(DISTINCT rru.RewardItemId), 0), 1)                AS redemption_rate_pct
FROM reward_redeem_user rru
JOIN reward_freebet rf ON rru.RewardItemId = rf.RewardItemId
GROUP BY rru.PromotionId

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S1: Resumen mensual de campañas                ║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Cómo usarla en el dashboard:
--   SELECT * FROM v_s1_monthly_campaign_summary
--   Filtros recomendados: campaign_month, campaign_type, BrandId, target_segment
--   Widgets sugeridos: tabla + bar chart de total_stakes y total_cost_redeemed por mes

CREATE OR REPLACE TEMP VIEW v_s1_monthly_campaign_summary AS
SELECT
  s.campaign_month,
  s.PromotionName,
  s.campaign_type,
  s.BrandId,
  s.target_segment,
  s.qualified_users,
  s.total_bets_placed,
  s.total_stakes,
  COALESCE(bc.rewards_issued,        0) AS rewards_issued,
  COALESCE(bc.rewards_redeemed,      0) AS rewards_redeemed,
  COALESCE(bc.total_cost_issued,     0) AS total_cost_issued,
  COALESCE(bc.total_cost_redeemed,   0) AS total_cost_redeemed,
  COALESCE(bc.redemption_rate_pct,   0) AS redemption_rate_pct,
  -- Coste por usuario cualificado
  ROUND(COALESCE(bc.total_cost_redeemed, 0)
        / NULLIF(s.qualified_users, 0), 2)  AS cost_per_qualified_user,
  -- Stakes por usuario cualificado
  ROUND(s.total_stakes
        / NULLIF(s.qualified_users, 0), 2)  AS avg_stakes_per_user
  -- NGR = GGR - total_cost_redeemed → pendiente tabla de apuestas
FROM v_s1_campaign_stakes s
LEFT JOIN v_s1_bonus_costs bc ON s.PromotionId = bc.PromotionId
ORDER BY s.campaign_month, s.PromotionName;

SELECT * FROM v_s1_monthly_campaign_summary

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Sección 2 — % Usuarios nuevos por promoción
-- MAGIC
-- MAGIC Para cada promoción, qué porcentaje de los participantes cualificados
-- MAGIC **no habían participado en ninguna otra promoción del BonusEngine antes**.
-- MAGIC
-- MAGIC Definición de "usuario nuevo":
-- MAGIC - Es la **primera** promoción en la que el usuario tiene `QualificationCount > 0`
-- MAGIC - Criterio: ordenado por fecha de opt-in (`OptInDateTimeUtc`)

-- COMMAND ----------

-- Primera promoción cualificada por usuario (en todo el historial del BonusEngine)
CREATE OR REPLACE TEMP VIEW v_s2_user_first_qualifying_promo AS
SELECT
  pu.UserId,
  FIRST_VALUE(pu.PromotionId) OVER (
    PARTITION BY pu.UserId
    ORDER BY COALESCE(pu.OptInDateTimeUtc, pd.StartDateUtc) ASC
  ) AS first_promo_id,
  MIN(COALESCE(pu.OptInDateTimeUtc, pd.StartDateUtc)) OVER (
    PARTITION BY pu.UserId
  ) AS first_participation_ts
FROM promotion_user pu
JOIN promotion_detail pd ON pu.PromotionId = pd.PromotionId
WHERE pu.QualificationCount > 0

-- COMMAND ----------

-- Deduplicar (la window function genera una fila por (user, promo))
CREATE OR REPLACE TEMP VIEW v_s2_user_first_promo_dedup AS
SELECT DISTINCT UserId, first_promo_id, first_participation_ts
FROM v_s2_user_first_qualifying_promo

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S2: % Usuarios nuevos por promoción            ║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Cómo usarla en el dashboard:
--   SELECT * FROM v_s2_new_users_per_promotion
--   Widgets sugeridos: stacked bar por mes (nuevos vs recurrentes)
--   o tabla ordenada por new_user_pct DESC para ver qué promos atraen nuevos usuarios

CREATE OR REPLACE TEMP VIEW v_s2_new_users_per_promotion AS
SELECT
  ct.PromotionId,
  ct.PromotionName,
  ct.campaign_type,
  ct.BrandId,
  ct.IsSegmented                        AS target_segment,
  DATE_TRUNC('month', ct.StartDateUtc)  AS campaign_month,
  ct.StartDateUtc                       AS campaign_start,
  COUNT(DISTINCT pu.UserId)             AS total_qualified_users,
  COUNT(DISTINCT CASE
    WHEN fp.first_promo_id = ct.PromotionId THEN pu.UserId
  END)                                  AS new_users,
  COUNT(DISTINCT CASE
    WHEN fp.first_promo_id != ct.PromotionId THEN pu.UserId
  END)                                  AS returning_users,
  ROUND(
    COUNT(DISTINCT CASE WHEN fp.first_promo_id = ct.PromotionId THEN pu.UserId END) * 100.0
    / NULLIF(COUNT(DISTINCT pu.UserId), 0),
  1) AS new_user_pct
FROM v_campaign_types ct
JOIN promotion_user pu ON ct.PromotionId = pu.PromotionId
LEFT JOIN v_s2_user_first_promo_dedup fp ON pu.UserId = fp.UserId
WHERE pu.QualificationCount > 0
GROUP BY
  ct.PromotionId, ct.PromotionName, ct.campaign_type,
  ct.BrandId, ct.IsSegmented, campaign_month, ct.StartDateUtc
ORDER BY ct.StartDateUtc DESC;

SELECT * FROM v_s2_new_users_per_promotion

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Sección 3 — Cohort de participación semanal
-- MAGIC
-- MAGIC Análisis de retención para campañas con esquema semanal (`duration_days <= 7`):
-- MAGIC
-- MAGIC 1. **Cohort**: semana de primera participación de cada usuario
-- MAGIC 2. **Retención**: % de usuarios del cohort que vuelven a participar cada semana siguiente
-- MAGIC 3. **Matriz de retención**: tabla pivot (cohort × semanas) para el dashboard
-- MAGIC 4. **Evolución del cohort**: cuántos usuarios nuevos entran cada semana
-- MAGIC
-- MAGIC **Nota:** Un usuario está "activo" en una semana si tiene `QualificationCount > 0`
-- MAGIC en alguna campaña semanal que empieza esa semana.

-- COMMAND ----------

-- Campañas semanales únicamente (duration <= 7 días)
CREATE OR REPLACE TEMP VIEW v_s3_weekly_promos AS
SELECT *
FROM v_campaign_types
WHERE duration_days <= 7

-- COMMAND ----------

-- Cohort de cada usuario: semana de su PRIMERA participación en cualquier campaña semanal
CREATE OR REPLACE TEMP VIEW v_s3_user_cohorts AS
SELECT
  pu.UserId,
  DATE_TRUNC('week', MIN(COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc))) AS cohort_week,
  FIRST_VALUE(wp.IsSegmented) OVER (
    PARTITION BY pu.UserId
    ORDER BY COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc) ASC
  ) AS segment
FROM promotion_user pu
JOIN v_s3_weekly_promos wp ON pu.PromotionId = wp.PromotionId
WHERE pu.QualificationCount > 0
GROUP BY pu.UserId, wp.IsSegmented, pu.OptInDateTimeUtc, wp.StartDateUtc

-- COMMAND ----------

-- Deduplicar cohorts
CREATE OR REPLACE TEMP VIEW v_s3_user_cohorts_dedup AS
SELECT
  UserId,
  MIN(cohort_week) AS cohort_week,
  FIRST_VALUE(segment) OVER (PARTITION BY UserId ORDER BY cohort_week ASC) AS segment
FROM v_s3_user_cohorts
GROUP BY UserId, cohort_week, segment
QUALIFY ROW_NUMBER() OVER (PARTITION BY UserId ORDER BY cohort_week ASC) = 1

-- COMMAND ----------

-- Actividad semanal: todas las semanas en las que cada usuario cualificó
CREATE OR REPLACE TEMP VIEW v_s3_weekly_activity AS
SELECT
  pu.UserId,
  DATE_TRUNC('week', COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc)) AS activity_week
FROM promotion_user pu
JOIN v_s3_weekly_promos wp ON pu.PromotionId = wp.PromotionId
WHERE pu.QualificationCount > 0
GROUP BY pu.UserId, DATE_TRUNC('week', COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc))

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S3a: Retención semanal por cohort (time series)║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Widget sugerido: line chart retention_pct por weeks_since_start,
-- una línea por cohort_week, filtro por segment

CREATE OR REPLACE TEMP VIEW v_s3_cohort_retention AS
WITH cohort_sizes AS (
  SELECT
    cohort_week,
    segment,
    COUNT(DISTINCT UserId) AS cohort_size
  FROM v_s3_user_cohorts_dedup
  GROUP BY cohort_week, segment
)
SELECT
  c.cohort_week,
  cs.segment,
  cs.cohort_size,
  a.activity_week,
  DATEDIFF(a.activity_week, c.cohort_week) / 7     AS weeks_since_start,
  COUNT(DISTINCT a.UserId)                         AS active_users,
  ROUND(
    COUNT(DISTINCT a.UserId) * 100.0
    / NULLIF(cs.cohort_size, 0),
  1) AS retention_pct
FROM v_s3_user_cohorts_dedup c
JOIN cohort_sizes cs ON c.cohort_week = cs.cohort_week AND c.segment = cs.segment
JOIN v_s3_weekly_activity a
  ON c.UserId = a.UserId
  AND a.activity_week >= c.cohort_week
GROUP BY c.cohort_week, cs.segment, cs.cohort_size, a.activity_week
ORDER BY c.cohort_week, a.activity_week;

SELECT * FROM v_s3_cohort_retention ORDER BY cohort_week, activity_week LIMIT 100

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S3b: Matriz de retención (pivot cohort × week) ║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Widget sugerido: heatmap — eje X = week_N, eje Y = cohort_week,
-- valor = retention % (100 en diagonal = week_0)

CREATE OR REPLACE TEMP VIEW v_s3_cohort_matrix AS
WITH cohort_sizes AS (
  SELECT cohort_week, COUNT(DISTINCT UserId) AS cohort_size
  FROM v_s3_user_cohorts_dedup
  GROUP BY cohort_week
)
SELECT
  c.cohort_week,
  cs.cohort_size,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 0  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_0,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 1  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_1,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 2  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_2,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 3  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_3,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 4  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_4,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 5  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_5,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 6  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_6,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 7  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_7,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 8  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_8,
  ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 9  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_9
FROM v_s3_user_cohorts_dedup c
JOIN cohort_sizes cs ON c.cohort_week = cs.cohort_week
LEFT JOIN v_s3_weekly_activity a
  ON c.UserId = a.UserId
  AND a.activity_week >= c.cohort_week
GROUP BY c.cohort_week, cs.cohort_size
ORDER BY c.cohort_week;

SELECT * FROM v_s3_cohort_matrix

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S3c: Evolución del cohort (nuevos usuarios/sem)║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Widget sugerido: bar chart nuevos usuarios por semana +
-- line chart de acumulado (cumulative_promo_users)

CREATE OR REPLACE TEMP VIEW v_s3_cohort_size_evolution AS
SELECT
  cohort_week,
  segment,
  COUNT(DISTINCT UserId)                                              AS new_promo_users,
  SUM(COUNT(DISTINCT UserId)) OVER (
    PARTITION BY segment
    ORDER BY cohort_week
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  )                                                                   AS cumulative_promo_users
FROM v_s3_user_cohorts_dedup
GROUP BY cohort_week, segment
ORDER BY cohort_week, segment;

SELECT * FROM v_s3_cohort_size_evolution

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## ⚙️ Configuración — Tablas externas (bets + users)
-- MAGIC
-- MAGIC Las secciones S4-S6 requieren:
-- MAGIC
-- MAGIC | Tabla | Columnas mínimas |
-- MAGIC |-------|-----------------|
-- MAGIC | `db_silver.bets` | `user_id`, `bet_date`, `stake`, `odds`, `result` (`'won'`/`'lost'`) |
-- MAGIC | `db_silver.users` | `user_id`, `segment` |
-- MAGIC
-- MAGIC > Si tu catálogo es diferente, reemplaza `db_silver.bets` y `db_silver.users`
-- MAGIC > en las celdas de S4, S5 y S6.
-- MAGIC >
-- MAGIC > **GGR por apuesta** = `stake - CASE WHEN result='won' THEN stake * odds ELSE 0 END`

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Sección 4 — ARPU mensual: participantes vs mismo segmento
-- MAGIC
-- MAGIC Compara el ARPU (GGR / usuario activo) entre:
-- MAGIC - **Participantes**: usuarios que cualificaron en alguna campaña semanal (de S3)
-- MAGIC - **Control**: usuarios del **mismo segmento** que nunca cualificaron en una campaña semanal
-- MAGIC
-- MAGIC **GGR por apuesta** = `stake − CASE WHEN result='won' THEN stake * odds ELSE 0 END`

-- COMMAND ----------

-- Grupo control: mismo segmento que los participantes, sin participación en promos semanales
CREATE OR REPLACE TEMP VIEW v_s4_control_users AS
SELECT u.user_id AS UserId, u.segment
FROM db_silver.users u
WHERE u.user_id NOT IN (SELECT DISTINCT UserId FROM v_s3_user_cohorts_dedup)

-- COMMAND ----------

-- GGR mensual por usuario (participantes + control)
CREATE OR REPLACE TEMP VIEW v_s4_user_monthly_ggr AS
WITH all_users AS (
  SELECT UserId, 'participant' AS user_type, segment FROM v_s3_user_cohorts_dedup
  UNION ALL
  SELECT UserId, 'control'     AS user_type, segment FROM v_s4_control_users
)
SELECT
  u.UserId,
  u.user_type,
  u.segment,
  DATE_TRUNC('month', b.bet_date)                                              AS activity_month,
  SUM(b.stake - CASE WHEN b.result = 'won' THEN b.stake * b.odds ELSE 0 END)  AS ggr
FROM all_users u
JOIN db_silver.bets b ON u.UserId = b.user_id
GROUP BY u.UserId, u.user_type, u.segment, DATE_TRUNC('month', b.bet_date)

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S4: ARPU mensual participantes vs control      ║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Widget sugerido: line chart ARPU por mes, una línea por user_type,
-- filtro por segment

CREATE OR REPLACE TEMP VIEW v_s4_arpu_monthly_comparison AS
SELECT
  activity_month,
  user_type,
  segment,
  COUNT(DISTINCT UserId)                                      AS active_users,
  ROUND(SUM(ggr), 2)                                         AS total_ggr,
  ROUND(SUM(ggr) / NULLIF(COUNT(DISTINCT UserId), 0), 2)    AS arpu
FROM v_s4_user_monthly_ggr
GROUP BY activity_month, user_type, segment
ORDER BY activity_month, segment, user_type;

SELECT * FROM v_s4_arpu_monthly_comparison ORDER BY activity_month, segment

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Sección 5 — Comparativa de métricas clave
-- MAGIC
-- MAGIC Compara **participantes vs control** en tres métricas de engagement, mes a mes:
-- MAGIC - `avg_stakes_per_user` — apuesta media por usuario activo
-- MAGIC - `avg_active_days_per_month` — días con al menos 1 apuesta
-- MAGIC - `avg_active_days_per_week` — media de días activos por semana del mes

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S5: Métricas clave participantes vs control     ║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Widget sugerido: 3 KPI cards o grouped bar chart
-- Filtro: segment, activity_month

CREATE OR REPLACE TEMP VIEW v_s5_key_metrics_comparison AS
WITH all_users AS (
  SELECT UserId, 'participant' AS user_type, segment FROM v_s3_user_cohorts_dedup
  UNION ALL
  SELECT UserId, 'control'     AS user_type, segment FROM v_s4_control_users
),
user_monthly AS (
  SELECT
    u.UserId,
    u.user_type,
    u.segment,
    DATE_TRUNC('month', b.bet_date)                            AS activity_month,
    COUNT(DISTINCT DATE(b.bet_date))                           AS active_days,
    COUNT(DISTINCT DATE_TRUNC('week', b.bet_date))             AS active_weeks,
    SUM(b.stake)                                               AS total_stakes
  FROM all_users u
  JOIN db_silver.bets b ON u.UserId = b.user_id
  GROUP BY u.UserId, u.user_type, u.segment, DATE_TRUNC('month', b.bet_date)
)
SELECT
  user_type,
  segment,
  activity_month,
  COUNT(DISTINCT UserId)                                                     AS active_users,
  ROUND(AVG(total_stakes),  2)                                               AS avg_stakes_per_user,
  ROUND(AVG(active_days),   1)                                               AS avg_active_days_per_month,
  ROUND(AVG(active_days / NULLIF(active_weeks, 0)), 1)                      AS avg_active_days_per_week
FROM user_monthly
GROUP BY user_type, segment, activity_month
ORDER BY activity_month, segment, user_type;

SELECT * FROM v_s5_key_metrics_comparison ORDER BY activity_month, segment

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Sección 6a — Incremento de ARPU antes/después de la primera promo
-- MAGIC
-- MAGIC Para cada usuario participante, compara su GGR en una ventana de ±`WINDOW_DAYS` días
-- MAGIC alrededor de su **primera participación** en una campaña semanal:
-- MAGIC
-- MAGIC - **Before**: `[first_promo_week − 28d, first_promo_week − 1d]`
-- MAGIC - **After**: `[first_promo_week, first_promo_week + 27d]`
-- MAGIC
-- MAGIC El uplift = `GGR_after − GGR_before` (positivo = más revenue después de la promo)

-- COMMAND ----------

-- GGR individual por usuario en ventanas before/after su primera promo semanal
CREATE OR REPLACE TEMP VIEW v_s6_user_arpu_before_after AS
SELECT
  c.UserId,
  c.segment,
  c.cohort_week                                                                         AS first_promo_week,
  ROUND(SUM(CASE
    WHEN b.bet_date < c.cohort_week
    THEN b.stake - CASE WHEN b.result = 'won' THEN b.stake * b.odds ELSE 0 END
    ELSE 0
  END), 2)                                                                              AS ggr_before,
  ROUND(SUM(CASE
    WHEN b.bet_date >= c.cohort_week
    THEN b.stake - CASE WHEN b.result = 'won' THEN b.stake * b.odds ELSE 0 END
    ELSE 0
  END), 2)                                                                              AS ggr_after,
  COUNT(DISTINCT CASE WHEN b.bet_date <  c.cohort_week THEN DATE(b.bet_date) END)      AS active_days_before,
  COUNT(DISTINCT CASE WHEN b.bet_date >= c.cohort_week THEN DATE(b.bet_date) END)      AS active_days_after
FROM v_s3_user_cohorts_dedup c
JOIN db_silver.bets b ON c.UserId = b.user_id
WHERE b.bet_date BETWEEN DATE_SUB(c.cohort_week, 28)
                     AND DATE_ADD(c.cohort_week, 27)
GROUP BY c.UserId, c.segment, c.cohort_week

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S6a: ARPU uplift by segment                    ║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Widget sugerido: KPI cards por segmento (avg_arpu_uplift + uplift_pct)
-- o waterfall chart avg_ggr_before → avg_ggr_after por segmento

CREATE OR REPLACE TEMP VIEW v_s6_arpu_uplift_by_segment AS
SELECT
  segment,
  COUNT(DISTINCT UserId)                                             AS users_analyzed,
  ROUND(AVG(ggr_before), 2)                                         AS avg_ggr_before_28d,
  ROUND(AVG(ggr_after),  2)                                         AS avg_ggr_after_28d,
  ROUND(AVG(ggr_after - ggr_before), 2)                            AS avg_arpu_uplift,
  ROUND(PERCENTILE(ggr_after - ggr_before, 0.25), 2)              AS p25_uplift,
  ROUND(PERCENTILE(ggr_after - ggr_before, 0.75), 2)              AS p75_uplift,
  ROUND(AVG((ggr_after - ggr_before) * 100.0
        / NULLIF(ABS(ggr_before), 0)), 1)                          AS avg_uplift_pct,
  ROUND(AVG(active_days_before), 1)                                AS avg_active_days_before,
  ROUND(AVG(active_days_after),  1)                                AS avg_active_days_after
FROM v_s6_user_arpu_before_after
GROUP BY segment
ORDER BY avg_arpu_uplift DESC;

SELECT * FROM v_s6_arpu_uplift_by_segment

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Sección 6b — Expected ARPU uplift por segmento × tipo de promo
-- MAGIC
-- MAGIC Calcula el uplift medio observado (y sus percentiles) agrupado por
-- MAGIC **segmento** y **tipo de primera promo** del usuario.
-- MAGIC Sirve para identificar qué combinaciones segmento × campaña generan más uplift.
-- MAGIC
-- MAGIC > **Nota:** La versión Python original usaba XGBoost para predecir el uplift.
-- MAGIC > Esta versión SQL calcula el uplift histórico real por grupo, que es la fuente
-- MAGIC > de verdad y suficiente para las decisiones de dashboard.

-- COMMAND ----------

-- Features: comportamiento pre-promo y target (arpu_uplift) por usuario
CREATE OR REPLACE TEMP VIEW v_s6_model_features AS
WITH user_first_promo_type AS (
  SELECT pu.UserId, wp.PromotionName AS first_promo_name
  FROM promotion_user pu
  JOIN v_s3_weekly_promos wp ON pu.PromotionId = wp.PromotionId
  WHERE pu.QualificationCount > 0
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY pu.UserId
    ORDER BY COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc)
  ) = 1
),
user_bets_before AS (
  SELECT
    c.UserId,
    ROUND(AVG(b.stake),  2)                AS avg_stake_28d_before,
    COUNT(DISTINCT DATE(b.bet_date))       AS active_days_28d_before,
    COUNT(*)                               AS total_bets_28d_before,
    ROUND(SUM(b.stake),  2)               AS total_stakes_28d_before
  FROM v_s3_user_cohorts_dedup c
  JOIN db_silver.bets b ON c.UserId = b.user_id
  WHERE b.bet_date BETWEEN DATE_SUB(c.cohort_week, 28)
                       AND DATE_SUB(c.cohort_week, 1)
  GROUP BY c.UserId
)
SELECT
  ba.UserId,
  ba.segment,
  fp.first_promo_name,
  COALESCE(ub.avg_stake_28d_before,    0) AS avg_stake_28d_before,
  COALESCE(ub.active_days_28d_before,  0) AS active_days_28d_before,
  COALESCE(ub.total_bets_28d_before,   0) AS total_bets_28d_before,
  COALESCE(ub.total_stakes_28d_before, 0) AS total_stakes_28d_before,
  ba.ggr_after - ba.ggr_before            AS arpu_uplift
FROM v_s6_user_arpu_before_after ba
LEFT JOIN user_first_promo_type fp ON ba.UserId = fp.UserId
LEFT JOIN user_bets_before ub       ON ba.UserId = ub.UserId
WHERE fp.first_promo_name IS NOT NULL;

SELECT COUNT(*) AS training_rows, ROUND(AVG(arpu_uplift), 2) AS mean_uplift FROM v_s6_model_features

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW S6b: Expected ARPU uplift por segmento × promo ║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Widget sugerido: heatmap segmento × promo_type (avg_uplift)
-- o tabla ranking con p25/p75 como bandas de confianza

CREATE OR REPLACE TEMP VIEW v_s6_expected_arpu_by_segment AS
SELECT
  segment,
  first_promo_name                                          AS promo_type,
  COUNT(DISTINCT UserId)                                    AS user_count,
  ROUND(AVG(arpu_uplift), 2)                               AS avg_uplift,
  ROUND(PERCENTILE(arpu_uplift, 0.25), 2)                 AS p25_uplift,
  ROUND(PERCENTILE(arpu_uplift, 0.50), 2)                 AS p50_uplift,
  ROUND(PERCENTILE(arpu_uplift, 0.75), 2)                 AS p75_uplift,
  ROUND(AVG(avg_stake_28d_before),   2)                   AS avg_stake_pre_promo,
  ROUND(AVG(active_days_28d_before), 1)                   AS avg_active_days_pre_promo
FROM v_s6_model_features
GROUP BY segment, first_promo_name
ORDER BY avg_uplift DESC;

SELECT * FROM v_s6_expected_arpu_by_segment

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Resumen de todas las views generadas
-- MAGIC
-- MAGIC | View | Sección | Descripción | Dashboard widget |
-- MAGIC |------|---------|-------------|-----------------|
-- MAGIC | `v_s1_monthly_campaign_summary` | S1 | Stakes, costes y tasa de canje por campaña/mes | Tabla + bar chart |
-- MAGIC | `v_s2_new_users_per_promotion` | S2 | % usuarios nuevos vs recurrentes por promo | Stacked bar por mes |
-- MAGIC | `v_s3_cohort_retention` | S3 | Retención semanal por cohort (time series) | Line chart |
-- MAGIC | `v_s3_cohort_matrix` | S3 | Matriz pivot cohort × semana (%) | Heatmap |
-- MAGIC | `v_s3_cohort_size_evolution` | S3 | Nuevos usuarios por semana + acumulado | Bar + line chart |
-- MAGIC | `v_s4_arpu_monthly_comparison` | S4 | ARPU mensual participantes vs control (mismo segmento) | Line chart por segmento |
-- MAGIC | `v_s5_key_metrics_comparison` | S5 | Avg stakes, active days/mes, active days/sem por grupo | Grouped bar chart |
-- MAGIC | `v_s6_arpu_uplift_by_segment` | S6a | Uplift de ARPU observado (before/after) por segmento | KPI cards + waterfall |
-- MAGIC | `v_s6_expected_arpu_by_segment` | S6b | Uplift esperado por segmento × tipo de promo (percentiles) | Heatmap |
