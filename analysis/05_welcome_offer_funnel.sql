-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Welcome Offer — Funnel Analysis
-- MAGIC
-- MAGIC Funnel de 3 pasos para la promoción de bienvenida:
-- MAGIC
-- MAGIC | Paso | Descripción |
-- MAGIC |------|-------------|
-- MAGIC | 1 | **Registro** — Usuarios nuevos registrados |
-- MAGIC | 2 | **Reward credited** — Recibieron la oferta de bienvenida |
-- MAGIC | 3 | **Reward redeemed** — Canjearon la oferta de bienvenida |

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## ⚙️ Configuración
-- MAGIC
-- MAGIC Cambia los valores directamente en las queries si necesitas otro período o promoción.
-- MAGIC - **PROMOTION_ID**: 951
-- MAGIC - **START_DATE**: 2025-01-01
-- MAGIC - **END_DATE**: 2026-03-16

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Paso 1 — Registro
-- MAGIC
-- MAGIC Usuarios nuevos registrados en el período de análisis.

-- COMMAND ----------

CREATE OR REPLACE TEMP VIEW v_wo_step1_registrations AS
SELECT
  CAST(u.RegistrationDate AS DATE)  AS RegistrationDate,
  u.id                              AS UserId
FROM hive_metastore.db_bronze_tps.users_user u
INNER JOIN hive_metastore.db_bronze_tps.users_userdetail ud
  ON ud.UserId = u.id
WHERE CAST(u.RegistrationDate AS DATE) BETWEEN '2025-01-01' AND '2026-03-16';

-- Resumen diario de registros
SELECT
  RegistrationDate,
  COUNT(DISTINCT UserId) AS NewUsersRegistered
FROM v_wo_step1_registrations
GROUP BY RegistrationDate
ORDER BY RegistrationDate;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Paso 2 — Reward Credited
-- MAGIC
-- MAGIC Usuarios registrados que recibieron el reward de la oferta de bienvenida
-- MAGIC (PromotionId = 951).
-- MAGIC
-- MAGIC > **TODO:** Confirma el catálogo/schema de `promotion_detail` y `promotion_user`.
-- MAGIC > Por defecto se asume el mismo que las tablas de usuarios. Ajusta si es diferente.
-- MAGIC >
-- MAGIC > **TODO:** Sustituye `<VOUCHER_TABLE>` por el nombre completo de la tabla de vouchers.
-- MAGIC > Sustituye `<VOUCHER_USER_ID>`, `<VOUCHER_PROMOTION_ID>` y `<VOUCHER_CREDITED_DATE>`
-- MAGIC > por los nombres reales de las columnas.

-- COMMAND ----------

CREATE OR REPLACE TEMP VIEW v_wo_step2_credited AS
SELECT DISTINCT
  pu.UserId,
  -- TODO: sustituir por la columna de fecha de emisión del voucher
  -- vc.<VOUCHER_CREDITED_DATE>   AS CreditedDate
  CAST(pd.StartDateUtc AS DATE) AS CreditedDate   -- proxy: fecha inicio campaña (reemplazar si tienes fecha exacta)
FROM
  -- TODO: confirma el schema de estas tablas (ej. hive_metastore.db_bronze_tps o db_silver_bonusengine)
  promotion_detail   pd   -- <-- reemplaza con schema completo si es necesario
  JOIN promotion_user pu
    ON pu.PromotionId = pd.PromotionId
  -- TODO: descomentar y completar el join con la tabla de vouchers cuando esté disponible
  -- JOIN <VOUCHER_TABLE> vc
  --   ON  vc.<VOUCHER_USER_ID>       = pu.UserId
  --   AND vc.<VOUCHER_PROMOTION_ID>  = pu.PromotionId
WHERE
  pd.PromotionId = 951
  -- Filtrar solo usuarios que se registraron en el período
  AND pu.UserId IN (SELECT UserId FROM v_wo_step1_registrations);

SELECT COUNT(DISTINCT UserId) AS users_credited FROM v_wo_step2_credited;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Paso 3 — Reward Redeemed
-- MAGIC
-- MAGIC Usuarios que canjearon el reward de la oferta de bienvenida.
-- MAGIC
-- MAGIC > **TODO:** Sustituye `<VOUCHER_TABLE>` y columnas por los valores reales.
-- MAGIC > La columna de canje suele ser `RedeemedDate`, `RedeemedOn`, o similar (NOT NULL = canjeado).

-- COMMAND ----------

CREATE OR REPLACE TEMP VIEW v_wo_step3_redeemed AS
SELECT DISTINCT
  -- TODO: reemplaza con el join real a la tabla de vouchers
  pu.UserId
  -- , CAST(vc.<VOUCHER_REDEEMED_DATE> AS DATE) AS RedeemedDate
FROM
  promotion_user pu   -- TODO: confirma schema
  -- TODO: descomentar y completar cuando tengas la tabla de vouchers
  -- JOIN <VOUCHER_TABLE> vc
  --   ON  vc.<VOUCHER_USER_ID>      = pu.UserId
  --   AND vc.<VOUCHER_PROMOTION_ID> = pu.PromotionId
  -- WHERE vc.<VOUCHER_REDEEMED_DATE> IS NOT NULL  -- solo canjeados
WHERE
  pu.PromotionId = 951
  AND pu.UserId IN (SELECT UserId FROM v_wo_step2_credited);
  -- NOTA: mientras no esté la tabla de vouchers, este paso devuelve los mismos que step2.
  -- Activa el filtro de redención cuando conectes la tabla.

SELECT COUNT(DISTINCT UserId) AS users_redeemed FROM v_wo_step3_redeemed;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Funnel Summary
-- MAGIC
-- MAGIC Vista consolidada con volúmenes y tasas de conversión entre pasos.

-- COMMAND ----------

-- ╔══════════════════════════════════════════════════════════════════╗
-- ║  DASHBOARD VIEW: Welcome Offer Funnel                          ║
-- ╚══════════════════════════════════════════════════════════════════╝
--
-- Widget sugerido: funnel chart o tabla con las 3 filas + KPI cards
-- para step1→step2 y step2→step3 conversion rates

CREATE OR REPLACE TEMP VIEW v_wo_funnel_summary AS
WITH
  step1 AS (SELECT COUNT(DISTINCT UserId) AS cnt FROM v_wo_step1_registrations),
  step2 AS (SELECT COUNT(DISTINCT UserId) AS cnt FROM v_wo_step2_credited),
  step3 AS (SELECT COUNT(DISTINCT UserId) AS cnt FROM v_wo_step3_redeemed)
SELECT
  1                                   AS step_order,
  'Registro'                          AS step_name,
  step1.cnt                           AS users,
  100.0                               AS conversion_from_prev_pct,
  ROUND(step2.cnt * 100.0 / NULLIF(step1.cnt, 0), 1) AS conversion_to_next_pct
FROM step1, step2, step3

UNION ALL

SELECT
  2,
  'Reward Credited',
  step2.cnt,
  ROUND(step2.cnt * 100.0 / NULLIF(step1.cnt, 0), 1),
  ROUND(step3.cnt * 100.0 / NULLIF(step2.cnt, 0), 1)
FROM step1, step2, step3

UNION ALL

SELECT
  3,
  'Reward Redeemed',
  step3.cnt,
  ROUND(step3.cnt * 100.0 / NULLIF(step2.cnt, 0), 1),
  NULL
FROM step1, step2, step3

ORDER BY step_order;

SELECT * FROM v_wo_funnel_summary;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ---
-- MAGIC ## Funnel por día de registro
-- MAGIC
-- MAGIC Útil para ver si hay variaciones en la tasa de conversión según cuándo se registró el usuario.

-- COMMAND ----------

SELECT
  r.RegistrationDate,
  COUNT(DISTINCT r.UserId)                                                    AS registered,
  COUNT(DISTINCT c.UserId)                                                    AS credited,
  COUNT(DISTINCT rd.UserId)                                                   AS redeemed,
  ROUND(COUNT(DISTINCT c.UserId)  * 100.0 / NULLIF(COUNT(DISTINCT r.UserId), 0), 1) AS reg_to_credited_pct,
  ROUND(COUNT(DISTINCT rd.UserId) * 100.0 / NULLIF(COUNT(DISTINCT c.UserId), 0), 1) AS credited_to_redeemed_pct,
  ROUND(COUNT(DISTINCT rd.UserId) * 100.0 / NULLIF(COUNT(DISTINCT r.UserId), 0), 1) AS overall_conversion_pct
FROM            v_wo_step1_registrations  r
LEFT JOIN       v_wo_step2_credited       c  ON c.UserId  = r.UserId
LEFT JOIN       v_wo_step3_redeemed       rd ON rd.UserId = r.UserId
GROUP BY r.RegistrationDate
ORDER BY r.RegistrationDate;
