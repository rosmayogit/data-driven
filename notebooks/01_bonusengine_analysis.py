# Databricks notebook source
# MAGIC %md
# MAGIC # Bonus Engine — Analysis Notebook
# MAGIC
# MAGIC Dashboard-ready SQL views for the promotions engine analysis.
# MAGIC
# MAGIC ## What's included (datos disponibles ahora)
# MAGIC | Sección | Descripción | Datos necesarios |
# MAGIC |---------|-------------|-----------------|
# MAGIC | **S1** | Resumen mensual de campañas (stakes, bonus costs) | BonusEngine ✅ |
# MAGIC | **S2** | % Usuarios nuevos por promoción | BonusEngine ✅ |
# MAGIC | **S3** | Cohort de participación semanal + retención | BonusEngine ✅ |
# MAGIC | S4 | ARPU cohort vs mismo segmento | Requiere `db_silver.bets` ⏳ |
# MAGIC | S5 | Comparativa métricas clave (active days, stakes) | Requiere `db_silver.bets` ⏳ |
# MAGIC | S6 | Incremento de ARPU + expected uplift por segmento | Requiere `db_silver.bets` ⏳ |
# MAGIC
# MAGIC ## Prerequisitos
# MAGIC 1. Tablas del BonusEngine cargadas (ver `analysis/bonusengine/00_load_bonusengine_data.sql`)
# MAGIC 2. Ejecutar las celdas **en orden** — cada view depende de las anteriores
# MAGIC
# MAGIC **Nota sobre NGR:** Para calcular NGR necesitamos `GGR - Bonus Costs`. El GGR
# MAGIC requiere la tabla de apuestas individual. Por ahora usamos `ConfirmedGrossAmountStaked`
# MAGIC (stakes validados durante la promo) como proxy de volumen, no de revenue.

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚙️ Configuración
# MAGIC
# MAGIC Ajusta los parámetros antes de ejecutar el notebook.

# COMMAND ----------

# Parámetros configurables
# Ajusta el nombre de la base de datos si usas un catálogo Unity o nombre diferente
DB_BONUSENGINE = "db_silver_bonusengine"  # base de datos del BonusEngine

# Filtros opcionales (None = sin filtro)
BRAND_ID_FILTER = None          # None = todos los brands; p.ej. 1 = España
START_DATE     = "2025-08-01"   # inicio del período de análisis
END_DATE       = "2026-02-28"   # fin del período de análisis

# Umbral para clasificar una campaña como "semanal"
WEEKLY_MAX_DURATION_DAYS = 7    # campañas con duración <= 7 días se consideran semanales

# Semanas máximas para la matriz de retención
COHORT_MATRIX_WEEKS = 10

print(f"Base de datos BonusEngine : {DB_BONUSENGINE}")
print(f"Período de análisis       : {START_DATE} → {END_DATE}")
print(f"Brand filter              : {BRAND_ID_FILTER or 'todos'}")
print(f"Max días campaña semanal  : {WEEKLY_MAX_DURATION_DAYS}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 Validación de datos
# MAGIC
# MAGIC Verifica que las tablas del BonusEngine estén disponibles y tienen datos.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'promotion_detail'   AS tabla, COUNT(*) AS filas FROM promotion_detail
# MAGIC UNION ALL
# MAGIC SELECT 'promotion_user',              COUNT(*) FROM promotion_user
# MAGIC UNION ALL
# MAGIC SELECT 'reward_detail',               COUNT(*) FROM reward_detail
# MAGIC UNION ALL
# MAGIC SELECT 'reward_redeem_user',          COUNT(*) FROM reward_redeem_user
# MAGIC UNION ALL
# MAGIC SELECT 'reward_freebet',              COUNT(*) FROM reward_freebet

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Rango de fechas y usuarios únicos
# MAGIC SELECT
# MAGIC   MIN(StartDateUtc)           AS primera_campana,
# MAGIC   MAX(EndDateUtc)             AS ultima_campana,
# MAGIC   COUNT(DISTINCT PromotionId) AS num_campanas,
# MAGIC   COUNT(DISTINCT BrandId)     AS num_brands
# MAGIC FROM promotion_detail

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT UserId)                                              AS usuarios_totales,
# MAGIC   COUNT(DISTINCT CASE WHEN QualificationCount > 0 THEN UserId END)   AS usuarios_cualificados,
# MAGIC   COUNT(DISTINCT CASE WHEN UserIsOptIn = true    THEN UserId END)     AS usuarios_con_optin,
# MAGIC   COUNT(*)                                                            AS filas_participation
# MAGIC FROM promotion_user

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Sección 1 — Resumen mensual de campañas
# MAGIC
# MAGIC Métricas agregadas por campaña y mes:
# MAGIC - **Stakes totales**: suma de `ConfirmedGrossAmountStaked` de usuarios cualificados
# MAGIC - **Bonus costs**: suma de `Amount` de recompensas **canjeadas** (`RedeemedOnUtc IS NOT NULL`)
# MAGIC - **Usuarios únicos**: participantes con `QualificationCount > 0`
# MAGIC - **Tasa de canje**: % de recompensas emitidas que fueron canjeadas
# MAGIC
# MAGIC > ⚠️ NGR = GGR − Bonus Costs. El GGR requiere la tabla de apuestas individual.
# MAGIC > Se añadirá en una próxima iteración cuando esté disponible `db_silver.bets`.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- View base: clasifica cada campaña por tipo (semanal / mensual / evento / única)
# MAGIC CREATE OR REPLACE TEMP VIEW v_campaign_types AS
# MAGIC SELECT
# MAGIC   PromotionId,
# MAGIC   PromotionName,
# MAGIC   BrandId,
# MAGIC   IsSegmented,
# MAGIC   StartDateUtc,
# MAGIC   EndDateUtc,
# MAGIC   DATEDIFF(EndDateUtc, StartDateUtc) AS duration_days,
# MAGIC   CASE
# MAGIC     WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 7  THEN 'Semanal'
# MAGIC     WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 14 THEN 'Quincenal'
# MAGIC     WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 31 THEN 'Mensual'
# MAGIC     ELSE 'Otro'
# MAGIC   END AS campaign_type
# MAGIC FROM promotion_detail
# MAGIC WHERE StartDateUtc >= '${START_DATE}'
# MAGIC   AND StartDateUtc <= '${END_DATE}'

# COMMAND ----------

# Inyectar parámetros de config en Spark SQL
spark.conf.set("START_DATE", START_DATE)
spark.conf.set("END_DATE", END_DATE)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Recrear la view con los parámetros de config correctos
# MAGIC CREATE OR REPLACE TEMP VIEW v_campaign_types AS
# MAGIC SELECT
# MAGIC   PromotionId,
# MAGIC   PromotionName,
# MAGIC   BrandId,
# MAGIC   IsSegmented,
# MAGIC   StartDateUtc,
# MAGIC   EndDateUtc,
# MAGIC   DATEDIFF(EndDateUtc, StartDateUtc) AS duration_days,
# MAGIC   CASE
# MAGIC     WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 7  THEN 'Semanal'
# MAGIC     WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 14 THEN 'Quincenal'
# MAGIC     WHEN DATEDIFF(EndDateUtc, StartDateUtc) <= 31 THEN 'Mensual'
# MAGIC     ELSE 'Otro'
# MAGIC   END AS campaign_type
# MAGIC FROM promotion_detail
# MAGIC WHERE StartDateUtc >= ${START_DATE}
# MAGIC   AND StartDateUtc <= ${END_DATE}

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Stakes y participación por campaña (de usuarios cualificados)
# MAGIC CREATE OR REPLACE TEMP VIEW v_s1_campaign_stakes AS
# MAGIC SELECT
# MAGIC   ct.PromotionId,
# MAGIC   ct.PromotionName,
# MAGIC   ct.campaign_type,
# MAGIC   ct.BrandId,
# MAGIC   ct.IsSegmented                    AS target_segment,
# MAGIC   DATE_TRUNC('month', ct.StartDateUtc) AS campaign_month,
# MAGIC   COUNT(DISTINCT pu.UserId)         AS qualified_users,
# MAGIC   SUM(pu.ConfirmedBetsPlaced)       AS total_bets_placed,
# MAGIC   ROUND(SUM(pu.ConfirmedGrossAmountStaked), 2) AS total_stakes
# MAGIC FROM v_campaign_types ct
# MAGIC JOIN promotion_user pu ON ct.PromotionId = pu.PromotionId
# MAGIC WHERE pu.QualificationCount > 0
# MAGIC GROUP BY
# MAGIC   ct.PromotionId, ct.PromotionName, ct.campaign_type,
# MAGIC   ct.BrandId, ct.IsSegmented, campaign_month

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Bonus costs: recompensas emitidas vs canjeadas por campaña
# MAGIC CREATE OR REPLACE TEMP VIEW v_s1_bonus_costs AS
# MAGIC SELECT
# MAGIC   rru.PromotionId,
# MAGIC   COUNT(DISTINCT rru.RewardItemId)                                       AS rewards_issued,
# MAGIC   COUNT(DISTINCT CASE WHEN rru.RedeemedOnUtc IS NOT NULL
# MAGIC                        THEN rru.RewardItemId END)                        AS rewards_redeemed,
# MAGIC   ROUND(SUM(rf.Amount), 2)                                               AS total_cost_issued,
# MAGIC   ROUND(SUM(CASE WHEN rru.RedeemedOnUtc IS NOT NULL
# MAGIC                  THEN rf.Amount ELSE 0 END), 2)                          AS total_cost_redeemed,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN rru.RedeemedOnUtc IS NOT NULL
# MAGIC                              THEN rru.RewardItemId END) * 100.0
# MAGIC         / NULLIF(COUNT(DISTINCT rru.RewardItemId), 0), 1)                AS redemption_rate_pct
# MAGIC FROM reward_redeem_user rru
# MAGIC JOIN reward_freebet rf ON rru.RewardItemId = rf.RewardItemId
# MAGIC GROUP BY rru.PromotionId

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ╔══════════════════════════════════════════════════════════════════╗
# MAGIC -- ║  DASHBOARD VIEW S1: Resumen mensual de campañas                ║
# MAGIC -- ╚══════════════════════════════════════════════════════════════════╝
# MAGIC --
# MAGIC -- Cómo usarla en el dashboard:
# MAGIC --   SELECT * FROM v_s1_monthly_campaign_summary
# MAGIC --   Filtros recomendados: campaign_month, campaign_type, BrandId, target_segment
# MAGIC --   Widgets sugeridos: tabla + bar chart de total_stakes y total_cost_redeemed por mes
# MAGIC
# MAGIC CREATE OR REPLACE TEMP VIEW v_s1_monthly_campaign_summary AS
# MAGIC SELECT
# MAGIC   s.campaign_month,
# MAGIC   s.PromotionName,
# MAGIC   s.campaign_type,
# MAGIC   s.BrandId,
# MAGIC   s.target_segment,
# MAGIC   s.qualified_users,
# MAGIC   s.total_bets_placed,
# MAGIC   s.total_stakes,
# MAGIC   COALESCE(bc.rewards_issued,        0) AS rewards_issued,
# MAGIC   COALESCE(bc.rewards_redeemed,      0) AS rewards_redeemed,
# MAGIC   COALESCE(bc.total_cost_issued,     0) AS total_cost_issued,
# MAGIC   COALESCE(bc.total_cost_redeemed,   0) AS total_cost_redeemed,
# MAGIC   COALESCE(bc.redemption_rate_pct,   0) AS redemption_rate_pct,
# MAGIC   -- Coste por usuario cualificado
# MAGIC   ROUND(COALESCE(bc.total_cost_redeemed, 0)
# MAGIC         / NULLIF(s.qualified_users, 0), 2)  AS cost_per_qualified_user,
# MAGIC   -- Stakes por usuario cualificado
# MAGIC   ROUND(s.total_stakes
# MAGIC         / NULLIF(s.qualified_users, 0), 2)  AS avg_stakes_per_user
# MAGIC   -- NGR = GGR - total_cost_redeemed → pendiente tabla de apuestas
# MAGIC FROM v_s1_campaign_stakes s
# MAGIC LEFT JOIN v_s1_bonus_costs bc ON s.PromotionId = bc.PromotionId
# MAGIC ORDER BY s.campaign_month, s.PromotionName;
# MAGIC
# MAGIC SELECT * FROM v_s1_monthly_campaign_summary

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Sección 2 — % Usuarios nuevos por promoción
# MAGIC
# MAGIC Para cada promoción, qué porcentaje de los participantes cualificados
# MAGIC **no habían participado en ninguna otra promoción del BonusEngine antes**.
# MAGIC
# MAGIC Definición de "usuario nuevo":
# MAGIC - Es la **primera** promoción en la que el usuario tiene `QualificationCount > 0`
# MAGIC - Criterio: ordenado por fecha de opt-in (`OptInDateTimeUtc`)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Primera promoción cualificada por usuario (en todo el historial del BonusEngine)
# MAGIC CREATE OR REPLACE TEMP VIEW v_s2_user_first_qualifying_promo AS
# MAGIC SELECT
# MAGIC   pu.UserId,
# MAGIC   FIRST_VALUE(pu.PromotionId) OVER (
# MAGIC     PARTITION BY pu.UserId
# MAGIC     ORDER BY COALESCE(pu.OptInDateTimeUtc, pd.StartDateUtc) ASC
# MAGIC   ) AS first_promo_id,
# MAGIC   MIN(COALESCE(pu.OptInDateTimeUtc, pd.StartDateUtc)) OVER (
# MAGIC     PARTITION BY pu.UserId
# MAGIC   ) AS first_participation_ts
# MAGIC FROM promotion_user pu
# MAGIC JOIN promotion_detail pd ON pu.PromotionId = pd.PromotionId
# MAGIC WHERE pu.QualificationCount > 0

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Deduplicate (la window function genera una fila por (user, promo))
# MAGIC CREATE OR REPLACE TEMP VIEW v_s2_user_first_promo_dedup AS
# MAGIC SELECT DISTINCT UserId, first_promo_id, first_participation_ts
# MAGIC FROM v_s2_user_first_qualifying_promo

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ╔══════════════════════════════════════════════════════════════════╗
# MAGIC -- ║  DASHBOARD VIEW S2: % Usuarios nuevos por promoción            ║
# MAGIC -- ╚══════════════════════════════════════════════════════════════════╝
# MAGIC --
# MAGIC -- Cómo usarla en el dashboard:
# MAGIC --   SELECT * FROM v_s2_new_users_per_promotion
# MAGIC --   Widgets sugeridos: stacked bar por mes (nuevos vs recurrentes)
# MAGIC --   o tabla ordenada por new_user_pct DESC para ver qué promos atraen nuevos usuarios
# MAGIC
# MAGIC CREATE OR REPLACE TEMP VIEW v_s2_new_users_per_promotion AS
# MAGIC SELECT
# MAGIC   ct.PromotionId,
# MAGIC   ct.PromotionName,
# MAGIC   ct.campaign_type,
# MAGIC   ct.BrandId,
# MAGIC   ct.IsSegmented                        AS target_segment,
# MAGIC   DATE_TRUNC('month', ct.StartDateUtc)  AS campaign_month,
# MAGIC   ct.StartDateUtc                       AS campaign_start,
# MAGIC   -- Usuarios totales cualificados en esta promo
# MAGIC   COUNT(DISTINCT pu.UserId)             AS total_qualified_users,
# MAGIC   -- Usuarios nuevos: esta es su primera promo cualificada
# MAGIC   COUNT(DISTINCT CASE
# MAGIC     WHEN fp.first_promo_id = ct.PromotionId THEN pu.UserId
# MAGIC   END)                                  AS new_users,
# MAGIC   -- Usuarios recurrentes: ya habían participado antes
# MAGIC   COUNT(DISTINCT CASE
# MAGIC     WHEN fp.first_promo_id != ct.PromotionId THEN pu.UserId
# MAGIC   END)                                  AS returning_users,
# MAGIC   -- % usuarios nuevos
# MAGIC   ROUND(
# MAGIC     COUNT(DISTINCT CASE WHEN fp.first_promo_id = ct.PromotionId THEN pu.UserId END) * 100.0
# MAGIC     / NULLIF(COUNT(DISTINCT pu.UserId), 0),
# MAGIC   1) AS new_user_pct
# MAGIC FROM v_campaign_types ct
# MAGIC JOIN promotion_user pu ON ct.PromotionId = pu.PromotionId
# MAGIC LEFT JOIN v_s2_user_first_promo_dedup fp ON pu.UserId = fp.UserId
# MAGIC WHERE pu.QualificationCount > 0
# MAGIC GROUP BY
# MAGIC   ct.PromotionId, ct.PromotionName, ct.campaign_type,
# MAGIC   ct.BrandId, ct.IsSegmented, campaign_month, ct.StartDateUtc
# MAGIC ORDER BY ct.StartDateUtc DESC;
# MAGIC
# MAGIC SELECT * FROM v_s2_new_users_per_promotion

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Sección 3 — Cohort de participación semanal
# MAGIC
# MAGIC Análisis de retención para campañas con esquema semanal (`duration_days <= 7`):
# MAGIC
# MAGIC 1. **Cohort**: semana de primera participación de cada usuario
# MAGIC 2. **Retención**: % de usuarios del cohort que vuelven a participar cada semana siguiente
# MAGIC 3. **Matriz de retención**: tabla pivot (cohort × semanas) para el dashboard
# MAGIC 4. **Evolución del cohort**: cuántos usuarios nuevos entran cada semana
# MAGIC
# MAGIC **Nota:** Un usuario está "activo" en una semana si tiene `QualificationCount > 0`
# MAGIC en alguna campaña semanal que empieza esa semana.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Campañas semanales únicamente (duration <= 7 días)
# MAGIC CREATE OR REPLACE TEMP VIEW v_s3_weekly_promos AS
# MAGIC SELECT *
# MAGIC FROM v_campaign_types
# MAGIC WHERE duration_days <= 7

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Cohort de cada usuario: semana de su PRIMERA participación en cualquier campaña semanal
# MAGIC -- participation_date = OptInDateTimeUtc si existe, si no StartDateUtc de la promo
# MAGIC CREATE OR REPLACE TEMP VIEW v_s3_user_cohorts AS
# MAGIC SELECT
# MAGIC   pu.UserId,
# MAGIC   DATE_TRUNC('week', MIN(COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc))) AS cohort_week,
# MAGIC   -- Segmento del usuario según la primera promo en la que participó
# MAGIC   FIRST_VALUE(wp.IsSegmented) OVER (
# MAGIC     PARTITION BY pu.UserId
# MAGIC     ORDER BY COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc) ASC
# MAGIC   ) AS segment
# MAGIC FROM promotion_user pu
# MAGIC JOIN v_s3_weekly_promos wp ON pu.PromotionId = wp.PromotionId
# MAGIC WHERE pu.QualificationCount > 0
# MAGIC GROUP BY pu.UserId, wp.IsSegmented, pu.OptInDateTimeUtc, wp.StartDateUtc

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Deduplicar cohorts (el window function genera filas duplicadas por (user, promo))
# MAGIC CREATE OR REPLACE TEMP VIEW v_s3_user_cohorts_dedup AS
# MAGIC SELECT
# MAGIC   UserId,
# MAGIC   MIN(cohort_week) AS cohort_week,
# MAGIC   FIRST_VALUE(segment) OVER (PARTITION BY UserId ORDER BY cohort_week ASC) AS segment
# MAGIC FROM v_s3_user_cohorts
# MAGIC GROUP BY UserId, cohort_week, segment
# MAGIC QUALIFY ROW_NUMBER() OVER (PARTITION BY UserId ORDER BY cohort_week ASC) = 1

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Actividad semanal: todas las semanas en las que cada usuario cualificó
# MAGIC -- en alguna campaña semanal (una fila por (usuario, semana))
# MAGIC CREATE OR REPLACE TEMP VIEW v_s3_weekly_activity AS
# MAGIC SELECT
# MAGIC   pu.UserId,
# MAGIC   DATE_TRUNC('week', COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc)) AS activity_week
# MAGIC FROM promotion_user pu
# MAGIC JOIN v_s3_weekly_promos wp ON pu.PromotionId = wp.PromotionId
# MAGIC WHERE pu.QualificationCount > 0
# MAGIC GROUP BY pu.UserId, DATE_TRUNC('week', COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc))

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ╔══════════════════════════════════════════════════════════════════╗
# MAGIC -- ║  DASHBOARD VIEW S3a: Retención semanal por cohort (time series)║
# MAGIC -- ╚══════════════════════════════════════════════════════════════════╝
# MAGIC --
# MAGIC -- Cómo usarla:
# MAGIC --   SELECT * FROM v_s3_cohort_retention WHERE cohort_week = '2025-09-01'
# MAGIC --   Widget sugerido: line chart retention_pct por weeks_since_start,
# MAGIC --   una línea por cohort_week, filtro por segment

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW v_s3_cohort_retention AS
# MAGIC WITH cohort_sizes AS (
# MAGIC   SELECT
# MAGIC     cohort_week,
# MAGIC     segment,
# MAGIC     COUNT(DISTINCT UserId) AS cohort_size
# MAGIC   FROM v_s3_user_cohorts_dedup
# MAGIC   GROUP BY cohort_week, segment
# MAGIC )
# MAGIC SELECT
# MAGIC   c.cohort_week,
# MAGIC   cs.segment,
# MAGIC   cs.cohort_size,
# MAGIC   a.activity_week,
# MAGIC   DATEDIFF(a.activity_week, c.cohort_week) / 7     AS weeks_since_start,
# MAGIC   COUNT(DISTINCT a.UserId)                         AS active_users,
# MAGIC   ROUND(
# MAGIC     COUNT(DISTINCT a.UserId) * 100.0
# MAGIC     / NULLIF(cs.cohort_size, 0),
# MAGIC   1) AS retention_pct
# MAGIC FROM v_s3_user_cohorts_dedup c
# MAGIC JOIN cohort_sizes cs ON c.cohort_week = cs.cohort_week AND c.segment = cs.segment
# MAGIC JOIN v_s3_weekly_activity a
# MAGIC   ON c.UserId = a.UserId
# MAGIC   AND a.activity_week >= c.cohort_week
# MAGIC GROUP BY c.cohort_week, cs.segment, cs.cohort_size, a.activity_week
# MAGIC ORDER BY c.cohort_week, a.activity_week;
# MAGIC
# MAGIC SELECT * FROM v_s3_cohort_retention ORDER BY cohort_week, activity_week LIMIT 100

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ╔══════════════════════════════════════════════════════════════════╗
# MAGIC -- ║  DASHBOARD VIEW S3b: Matriz de retención (pivot cohort × week) ║
# MAGIC -- ╚══════════════════════════════════════════════════════════════════╝
# MAGIC --
# MAGIC -- Cómo usarla:
# MAGIC --   SELECT * FROM v_s3_cohort_matrix
# MAGIC --   Widget sugerido: heatmap — eje X = week_N, eje Y = cohort_week,
# MAGIC --   valor = retention % (100 en diagonal = week_0)

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW v_s3_cohort_matrix AS
# MAGIC WITH cohort_sizes AS (
# MAGIC   SELECT cohort_week, COUNT(DISTINCT UserId) AS cohort_size
# MAGIC   FROM v_s3_user_cohorts_dedup
# MAGIC   GROUP BY cohort_week
# MAGIC )
# MAGIC SELECT
# MAGIC   c.cohort_week,
# MAGIC   cs.cohort_size,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 0  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_0,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 1  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_1,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 2  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_2,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 3  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_3,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 4  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_4,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 5  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_5,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 6  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_6,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 7  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_7,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 8  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_8,
# MAGIC   ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(a.activity_week, c.cohort_week)/7 = 9  THEN a.UserId END) * 100.0 / NULLIF(cs.cohort_size, 0), 1) AS week_9
# MAGIC FROM v_s3_user_cohorts_dedup c
# MAGIC JOIN cohort_sizes cs ON c.cohort_week = cs.cohort_week
# MAGIC LEFT JOIN v_s3_weekly_activity a
# MAGIC   ON c.UserId = a.UserId
# MAGIC   AND a.activity_week >= c.cohort_week
# MAGIC GROUP BY c.cohort_week, cs.cohort_size
# MAGIC ORDER BY c.cohort_week;
# MAGIC
# MAGIC SELECT * FROM v_s3_cohort_matrix

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ╔══════════════════════════════════════════════════════════════════╗
# MAGIC -- ║  DASHBOARD VIEW S3c: Evolución del cohort (nuevos usuarios/sem)║
# MAGIC -- ╚══════════════════════════════════════════════════════════════════╝
# MAGIC --
# MAGIC -- Cómo usarla:
# MAGIC --   SELECT * FROM v_s3_cohort_size_evolution
# MAGIC --   Widget sugerido: bar chart nuevos usuarios por semana +
# MAGIC --   line chart de acumulado (cumulative_promo_users)

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW v_s3_cohort_size_evolution AS
# MAGIC SELECT
# MAGIC   cohort_week,
# MAGIC   segment,
# MAGIC   COUNT(DISTINCT UserId)                                              AS new_promo_users,
# MAGIC   SUM(COUNT(DISTINCT UserId)) OVER (
# MAGIC     PARTITION BY segment
# MAGIC     ORDER BY cohort_week
# MAGIC     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
# MAGIC   )                                                                   AS cumulative_promo_users
# MAGIC FROM v_s3_user_cohorts_dedup
# MAGIC GROUP BY cohort_week, segment
# MAGIC ORDER BY cohort_week, segment;
# MAGIC
# MAGIC SELECT * FROM v_s3_cohort_size_evolution

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## ⚙️ Configuración — Tablas externas (bets + users)

# COMMAND ----------

# Tablas externas — ajusta a tu catálogo real
BETS_TABLE  = "db_silver.bets"    # columnas requeridas: user_id, bet_date, stake, odds, result
USERS_TABLE = "db_silver.users"   # columnas requeridas: user_id, segment

# Ventana de días para el análisis before/after (S6)
WINDOW_DAYS = 28

spark.conf.set("BETS_TABLE",  BETS_TABLE)
spark.conf.set("USERS_TABLE", USERS_TABLE)
spark.conf.set("WINDOW_DAYS", str(WINDOW_DAYS))

print(f"Bets table  : {BETS_TABLE}")
print(f"Users table : {USERS_TABLE}")
print(f"Ventana B/A : ±{WINDOW_DAYS} días")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Sección 4 — ARPU mensual: participantes vs mismo segmento
# MAGIC
# MAGIC Compara el ARPU (GGR / usuario activo) entre:
# MAGIC - **Participantes**: usuarios que cualificaron en alguna campaña semanal (de S3)
# MAGIC - **Control**: usuarios del **mismo segmento** que nunca cualificaron en una campaña semanal
# MAGIC
# MAGIC **GGR por apuesta** = `stake − (stake × odds)` si ganó, `stake` si perdió
# MAGIC = `stake − CASE WHEN result='won' THEN stake * odds ELSE 0 END`

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grupo control: mismo segmento que los participantes, sin participación en promos semanales
# MAGIC CREATE OR REPLACE TEMP VIEW v_s4_control_users AS
# MAGIC SELECT u.user_id AS UserId, u.segment
# MAGIC FROM db_silver.users u
# MAGIC WHERE u.user_id NOT IN (SELECT DISTINCT UserId FROM v_s3_user_cohorts_dedup)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- GGR mensual por usuario (participantes + control)
# MAGIC CREATE OR REPLACE TEMP VIEW v_s4_user_monthly_ggr AS
# MAGIC WITH all_users AS (
# MAGIC   SELECT UserId, 'participant' AS user_type, segment FROM v_s3_user_cohorts_dedup
# MAGIC   UNION ALL
# MAGIC   SELECT UserId, 'control'     AS user_type, segment FROM v_s4_control_users
# MAGIC )
# MAGIC SELECT
# MAGIC   u.UserId,
# MAGIC   u.user_type,
# MAGIC   u.segment,
# MAGIC   DATE_TRUNC('month', b.bet_date)                                              AS activity_month,
# MAGIC   SUM(b.stake - CASE WHEN b.result = 'won' THEN b.stake * b.odds ELSE 0 END)  AS ggr
# MAGIC FROM all_users u
# MAGIC JOIN db_silver.bets b ON u.UserId = b.user_id
# MAGIC GROUP BY u.UserId, u.user_type, u.segment, DATE_TRUNC('month', b.bet_date)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ╔══════════════════════════════════════════════════════════════════╗
# MAGIC -- ║  DASHBOARD VIEW S4: ARPU mensual participantes vs control      ║
# MAGIC -- ╚══════════════════════════════════════════════════════════════════╝
# MAGIC --
# MAGIC -- Widget sugerido: line chart ARPU por mes, una línea por user_type,
# MAGIC -- filtro por segment
# MAGIC CREATE OR REPLACE TEMP VIEW v_s4_arpu_monthly_comparison AS
# MAGIC SELECT
# MAGIC   activity_month,
# MAGIC   user_type,
# MAGIC   segment,
# MAGIC   COUNT(DISTINCT UserId)                                      AS active_users,
# MAGIC   ROUND(SUM(ggr), 2)                                         AS total_ggr,
# MAGIC   ROUND(SUM(ggr) / NULLIF(COUNT(DISTINCT UserId), 0), 2)    AS arpu
# MAGIC FROM v_s4_user_monthly_ggr
# MAGIC GROUP BY activity_month, user_type, segment
# MAGIC ORDER BY activity_month, segment, user_type;
# MAGIC
# MAGIC SELECT * FROM v_s4_arpu_monthly_comparison ORDER BY activity_month, segment

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Sección 5 — Comparativa de métricas clave
# MAGIC
# MAGIC Compara **participantes vs control** en tres métricas de engagement, mes a mes:
# MAGIC - `avg_stakes_per_user` — apuesta media por usuario activo
# MAGIC - `avg_active_days_per_month` — días con al menos 1 apuesta
# MAGIC - `avg_active_days_per_week` — media de días activos por semana del mes

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ╔══════════════════════════════════════════════════════════════════╗
# MAGIC -- ║  DASHBOARD VIEW S5: Métricas clave participantes vs control     ║
# MAGIC -- ╚══════════════════════════════════════════════════════════════════╝
# MAGIC --
# MAGIC -- Widget sugerido: 3 KPI cards o grouped bar chart
# MAGIC -- Filtro: segment, activity_month
# MAGIC CREATE OR REPLACE TEMP VIEW v_s5_key_metrics_comparison AS
# MAGIC WITH all_users AS (
# MAGIC   SELECT UserId, 'participant' AS user_type, segment FROM v_s3_user_cohorts_dedup
# MAGIC   UNION ALL
# MAGIC   SELECT UserId, 'control'     AS user_type, segment FROM v_s4_control_users
# MAGIC ),
# MAGIC user_monthly AS (
# MAGIC   SELECT
# MAGIC     u.UserId,
# MAGIC     u.user_type,
# MAGIC     u.segment,
# MAGIC     DATE_TRUNC('month', b.bet_date)                            AS activity_month,
# MAGIC     COUNT(DISTINCT DATE(b.bet_date))                           AS active_days,
# MAGIC     COUNT(DISTINCT DATE_TRUNC('week', b.bet_date))             AS active_weeks,
# MAGIC     SUM(b.stake)                                               AS total_stakes
# MAGIC   FROM all_users u
# MAGIC   JOIN db_silver.bets b ON u.UserId = b.user_id
# MAGIC   GROUP BY u.UserId, u.user_type, u.segment, DATE_TRUNC('month', b.bet_date)
# MAGIC )
# MAGIC SELECT
# MAGIC   user_type,
# MAGIC   segment,
# MAGIC   activity_month,
# MAGIC   COUNT(DISTINCT UserId)                                                     AS active_users,
# MAGIC   ROUND(AVG(total_stakes),  2)                                               AS avg_stakes_per_user,
# MAGIC   ROUND(AVG(active_days),   1)                                               AS avg_active_days_per_month,
# MAGIC   -- días activos / semanas activas del mes = densidad de actividad por semana
# MAGIC   ROUND(AVG(active_days / NULLIF(active_weeks, 0)), 1)                      AS avg_active_days_per_week
# MAGIC FROM user_monthly
# MAGIC GROUP BY user_type, segment, activity_month
# MAGIC ORDER BY activity_month, segment, user_type;
# MAGIC
# MAGIC SELECT * FROM v_s5_key_metrics_comparison ORDER BY activity_month, segment

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Sección 6a — Incremento de ARPU antes/después de la primera promo
# MAGIC
# MAGIC Para cada usuario participante, compara su GGR en una ventana de ±`WINDOW_DAYS` días
# MAGIC alrededor de su **primera participación** en una campaña semanal:
# MAGIC
# MAGIC - **Before**: `[first_promo_week − 28d, first_promo_week − 1d]`
# MAGIC - **After**: `[first_promo_week, first_promo_week + 27d]`
# MAGIC
# MAGIC El uplift = `GGR_after − GGR_before` (positivo = más revenue después de la promo)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- GGR individual por usuario en ventanas before/after su primera promo semanal
# MAGIC CREATE OR REPLACE TEMP VIEW v_s6_user_arpu_before_after AS
# MAGIC SELECT
# MAGIC   c.UserId,
# MAGIC   c.segment,
# MAGIC   c.cohort_week                                                                         AS first_promo_week,
# MAGIC   -- GGR en los 28 días ANTES de la primera promo
# MAGIC   ROUND(SUM(CASE
# MAGIC     WHEN b.bet_date < c.cohort_week
# MAGIC     THEN b.stake - CASE WHEN b.result = 'won' THEN b.stake * b.odds ELSE 0 END
# MAGIC     ELSE 0
# MAGIC   END), 2)                                                                              AS ggr_before,
# MAGIC   -- GGR en los 28 días DESPUÉS (inclusive el día de la promo)
# MAGIC   ROUND(SUM(CASE
# MAGIC     WHEN b.bet_date >= c.cohort_week
# MAGIC     THEN b.stake - CASE WHEN b.result = 'won' THEN b.stake * b.odds ELSE 0 END
# MAGIC     ELSE 0
# MAGIC   END), 2)                                                                              AS ggr_after,
# MAGIC   -- Días activos en cada ventana
# MAGIC   COUNT(DISTINCT CASE WHEN b.bet_date <  c.cohort_week THEN DATE(b.bet_date) END)      AS active_days_before,
# MAGIC   COUNT(DISTINCT CASE WHEN b.bet_date >= c.cohort_week THEN DATE(b.bet_date) END)      AS active_days_after
# MAGIC FROM v_s3_user_cohorts_dedup c
# MAGIC JOIN db_silver.bets b ON c.UserId = b.user_id
# MAGIC WHERE b.bet_date BETWEEN DATE_SUB(c.cohort_week, 28)
# MAGIC                      AND DATE_ADD(c.cohort_week, 27)
# MAGIC GROUP BY c.UserId, c.segment, c.cohort_week

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ╔══════════════════════════════════════════════════════════════════╗
# MAGIC -- ║  DASHBOARD VIEW S6a: ARPU uplift by segment                    ║
# MAGIC -- ╚══════════════════════════════════════════════════════════════════╝
# MAGIC --
# MAGIC -- Widget sugerido: KPI cards por segmento (avg_arpu_uplift + uplift_pct)
# MAGIC -- o waterfall chart avg_ggr_before → avg_ggr_after por segmento
# MAGIC CREATE OR REPLACE TEMP VIEW v_s6_arpu_uplift_by_segment AS
# MAGIC SELECT
# MAGIC   segment,
# MAGIC   COUNT(DISTINCT UserId)                                             AS users_analyzed,
# MAGIC   ROUND(AVG(ggr_before), 2)                                         AS avg_ggr_before_28d,
# MAGIC   ROUND(AVG(ggr_after),  2)                                         AS avg_ggr_after_28d,
# MAGIC   ROUND(AVG(ggr_after - ggr_before), 2)                            AS avg_arpu_uplift,
# MAGIC   ROUND(PERCENTILE(ggr_after - ggr_before, 0.25), 2)              AS p25_uplift,
# MAGIC   ROUND(PERCENTILE(ggr_after - ggr_before, 0.75), 2)              AS p75_uplift,
# MAGIC   ROUND(AVG((ggr_after - ggr_before) * 100.0
# MAGIC         / NULLIF(ABS(ggr_before), 0)), 1)                          AS avg_uplift_pct,
# MAGIC   ROUND(AVG(active_days_before), 1)                                AS avg_active_days_before,
# MAGIC   ROUND(AVG(active_days_after),  1)                                AS avg_active_days_after
# MAGIC FROM v_s6_user_arpu_before_after
# MAGIC GROUP BY segment
# MAGIC ORDER BY avg_arpu_uplift DESC;
# MAGIC
# MAGIC SELECT * FROM v_s6_arpu_uplift_by_segment

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Sección 6b — Expected ARPU uplift por segmento (modelo XGBoost)
# MAGIC
# MAGIC Entrena un modelo para predecir el uplift de ARPU esperado dado:
# MAGIC - El **segmento** del usuario
# MAGIC - El **tipo de campaña** (primera promo semanal que recibió)
# MAGIC - Su **comportamiento previo** (stakes, días activos, bets en los 28d anteriores)
# MAGIC
# MAGIC **Output**: `v_s6_expected_arpu_by_segment` — uplift medio esperado por segmento × tipo de promo,
# MAGIC con percentiles p25/p75 para dar un rango de confianza.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Features de entrenamiento: comportamiento pre-promo + target (arpu_uplift)
# MAGIC CREATE OR REPLACE TEMP VIEW v_s6_model_features AS
# MAGIC WITH user_first_promo_type AS (
# MAGIC   -- Primera campaña semanal en la que cada usuario cualificó
# MAGIC   SELECT pu.UserId, wp.PromotionName AS first_promo_name
# MAGIC   FROM promotion_user pu
# MAGIC   JOIN v_s3_weekly_promos wp ON pu.PromotionId = wp.PromotionId
# MAGIC   WHERE pu.QualificationCount > 0
# MAGIC   QUALIFY ROW_NUMBER() OVER (
# MAGIC     PARTITION BY pu.UserId
# MAGIC     ORDER BY COALESCE(pu.OptInDateTimeUtc, wp.StartDateUtc)
# MAGIC   ) = 1
# MAGIC ),
# MAGIC user_bets_before AS (
# MAGIC   -- Comportamiento del usuario en los 28 días ANTERIORES a su primera promo
# MAGIC   SELECT
# MAGIC     c.UserId,
# MAGIC     AVG(b.stake)                             AS avg_stake_28d_before,
# MAGIC     COUNT(DISTINCT DATE(b.bet_date))         AS active_days_28d_before,
# MAGIC     COUNT(*)                                 AS total_bets_28d_before,
# MAGIC     SUM(b.stake)                             AS total_stakes_28d_before
# MAGIC   FROM v_s3_user_cohorts_dedup c
# MAGIC   JOIN db_silver.bets b ON c.UserId = b.user_id
# MAGIC   WHERE b.bet_date BETWEEN DATE_SUB(c.cohort_week, 28)
# MAGIC                        AND DATE_SUB(c.cohort_week, 1)
# MAGIC   GROUP BY c.UserId
# MAGIC )
# MAGIC SELECT
# MAGIC   ba.UserId,
# MAGIC   ba.segment,
# MAGIC   fp.first_promo_name,
# MAGIC   COALESCE(ub.avg_stake_28d_before,    0) AS avg_stake_28d_before,
# MAGIC   COALESCE(ub.active_days_28d_before,  0) AS active_days_28d_before,
# MAGIC   COALESCE(ub.total_bets_28d_before,   0) AS total_bets_28d_before,
# MAGIC   COALESCE(ub.total_stakes_28d_before, 0) AS total_stakes_28d_before,
# MAGIC   ba.ggr_after - ba.ggr_before             AS arpu_uplift
# MAGIC FROM v_s6_user_arpu_before_after ba
# MAGIC LEFT JOIN user_first_promo_type fp ON ba.UserId = fp.UserId
# MAGIC LEFT JOIN user_bets_before ub       ON ba.UserId = ub.UserId
# MAGIC WHERE fp.first_promo_name IS NOT NULL;
# MAGIC
# MAGIC SELECT COUNT(*) AS training_rows, AVG(arpu_uplift) AS mean_uplift FROM v_s6_model_features

# COMMAND ----------

import pandas as pd
import numpy as np

try:
    from xgboost import XGBRegressor
    MODEL_BACKEND = "xgboost"
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor as XGBRegressor
    MODEL_BACKEND = "sklearn GradientBoosting"

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

print(f"Usando: {MODEL_BACKEND}")

# Cargar datos de entrenamiento
features_pdf = spark.sql("SELECT * FROM v_s6_model_features").toPandas()
features_pdf = features_pdf.dropna(subset=["arpu_uplift"])

MIN_ROWS = 30
if len(features_pdf) < MIN_ROWS:
    print(f"⚠️  Solo {len(features_pdf)} usuarios con datos completos. "
          f"Necesitas al menos {MIN_ROWS} para entrenar el modelo.")
else:
    print(f"Entrenando con {len(features_pdf)} usuarios...")

    # Encode categoricals
    le_seg   = LabelEncoder()
    le_promo = LabelEncoder()
    features_pdf["segment_enc"]    = le_seg.fit_transform(features_pdf["segment"])
    features_pdf["promo_type_enc"] = le_promo.fit_transform(features_pdf["first_promo_name"])

    feature_cols = [
        "segment_enc", "promo_type_enc",
        "avg_stake_28d_before", "active_days_28d_before",
        "total_bets_28d_before", "total_stakes_28d_before",
    ]
    X = features_pdf[feature_cols].fillna(0)
    y = features_pdf["arpu_uplift"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)

    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"MAE en test : {mae:.2f}€  ({len(X_test)} usuarios)")

    # Feature importance
    fi = pd.DataFrame({
        "feature":    feature_cols,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    print("\nImportancia de features:")
    print(fi.to_string(index=False))

    # Predecir para todos los usuarios
    features_pdf["predicted_uplift"] = model.predict(X)

    # Agregar por segmento × tipo de promo
    summary = (
        features_pdf
        .groupby(["segment", "first_promo_name"])
        .agg(
            user_count          =("UserId",           "count"),
            avg_actual_uplift   =("arpu_uplift",      "mean"),
            avg_predicted_uplift=("predicted_uplift", "mean"),
            p25_predicted       =("predicted_uplift", lambda x: np.percentile(x, 25)),
            p75_predicted       =("predicted_uplift", lambda x: np.percentile(x, 75)),
        )
        .reset_index()
        .rename(columns={"first_promo_name": "promo_type"})
        .round(2)
        .sort_values("avg_predicted_uplift", ascending=False)
    )

    # ╔══════════════════════════════════════════════════════════════════╗
    # ║  DASHBOARD VIEW S6b: Expected ARPU uplift por segmento         ║
    # ╚══════════════════════════════════════════════════════════════════╝
    # Widget sugerido: heatmap segmento × promo_type (avg_predicted_uplift)
    # o tabla ranking con p25/p75 como error bars
    spark.createDataFrame(summary).createOrReplaceTempView("v_s6_expected_arpu_by_segment")
    print("\n✓ View creada: v_s6_expected_arpu_by_segment")
    display(spark.sql("SELECT * FROM v_s6_expected_arpu_by_segment"))

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Resumen de todas las views generadas
# MAGIC
# MAGIC | View | Sección | Descripción | Dashboard widget |
# MAGIC |------|---------|-------------|-----------------|
# MAGIC | `v_s1_monthly_campaign_summary` | S1 | Stakes, costes y tasa de canje por campaña/mes | Tabla + bar chart |
# MAGIC | `v_s2_new_users_per_promotion` | S2 | % usuarios nuevos vs recurrentes por promo | Stacked bar por mes |
# MAGIC | `v_s3_cohort_retention` | S3 | Retención semanal por cohort (time series) | Line chart |
# MAGIC | `v_s3_cohort_matrix` | S3 | Matriz pivot cohort × semana (%) | Heatmap |
# MAGIC | `v_s3_cohort_size_evolution` | S3 | Nuevos usuarios por semana + acumulado | Bar + line chart |
# MAGIC | `v_s4_arpu_monthly_comparison` | S4 | ARPU mensual participantes vs control (mismo segmento) | Line chart por segmento |
# MAGIC | `v_s5_key_metrics_comparison` | S5 | Avg stakes, active days/mes, active days/sem por grupo | Grouped bar chart |
# MAGIC | `v_s6_arpu_uplift_by_segment` | S6a | Uplift de ARPU observado (before/after) por segmento | KPI cards + waterfall |
# MAGIC | `v_s6_expected_arpu_by_segment` | S6b | Expected ARPU uplift predicho por XGBoost (segmento × promo) | Heatmap |
