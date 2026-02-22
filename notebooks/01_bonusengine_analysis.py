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
# MAGIC ## Resumen de views generadas
# MAGIC
# MAGIC | View | Sección | Descripción | Dashboard widget |
# MAGIC |------|---------|-------------|-----------------|
# MAGIC | `v_s1_monthly_campaign_summary` | S1 | Stakes, costes y tasa de canje por campaña/mes | Tabla + bar chart |
# MAGIC | `v_s2_new_users_per_promotion` | S2 | % usuarios nuevos vs recurrentes por promo | Stacked bar por mes |
# MAGIC | `v_s3_cohort_retention` | S3 | Retención semanal por cohort (time series) | Line chart |
# MAGIC | `v_s3_cohort_matrix` | S3 | Matriz pivot cohort × semana (%) | Heatmap |
# MAGIC | `v_s3_cohort_size_evolution` | S3 | Nuevos usuarios por semana + acumulado | Bar + line chart |
# MAGIC
# MAGIC ---
# MAGIC ## ⏳ Próximas secciones (requieren `db_silver.bets`)
# MAGIC
# MAGIC | Sección | Descripción | Columnas necesarias en `bets` |
# MAGIC |---------|-------------|-------------------------------|
# MAGIC | S4 | ARPU cohort vs mismo segmento | `user_id`, `bet_date`, `stake`, `odds`, `result` |
# MAGIC | S5 | Comparativa métricas clave (active days, stakes) | `user_id`, `bet_date`, `stake` |
# MAGIC | S6a | Incremento de ARPU antes/después de primera promo | `user_id`, `bet_date`, `stake`, `odds`, `result` |
# MAGIC | S6b | Expected ARPU uplift por segmento (modelo XGBoost) | Todo lo anterior + `db_silver.users` con `segment` |
# MAGIC
# MAGIC > **Columnas mínimas de `db_silver.bets`:**
# MAGIC > - `user_id` — debe coincidir con `UserId` del BonusEngine
# MAGIC > - `bet_date` — timestamp o date de la apuesta
# MAGIC > - `stake` — importe apostado
# MAGIC > - `odds` — cuota decimal (para calcular GGR)
# MAGIC > - `result` — `'won'` / `'lost'` (para calcular GGR)
# MAGIC >
# MAGIC > **GGR por apuesta** = `stake - CASE WHEN result='won' THEN stake * odds ELSE 0 END`
# MAGIC >
# MAGIC > Si no tienes `odds` y `result` pero sí tienes `net_revenue` o `pnl` ya calculado,
# MAGIC > podemos adaptar las queries directamente.
