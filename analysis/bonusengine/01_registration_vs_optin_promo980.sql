-- ============================================================================
-- REGISTRATION VS OPT-IN: Promotion 980
-- ============================================================================
-- Para cada fecha de registro muestra:
--   - Nuevos usuarios registrados
--   - Usuarios que hicieron opt-in en la promo 980 el mismo día que se registraron
--   - Usuarios que hicieron opt-in en la promo 980 en cualquier momento
--
-- Tablas:
--   hive_metastore.db_bronze_tps.users_user          → columnas: id, date_joined
--   hive_metastore.db_silver_bonusengine.promotion_user → columnas: UserId, PromotionId,
--                                                           UserIsOptIn, OptInDateTimeUtc
--
-- NOTA: Ajusta los nombres de columna si difieren en tu entorno:
--   · users_user.id          → el UserId del usuario
--   · users_user.date_joined → fecha/timestamp de registro
-- ============================================================================

WITH registrations AS (
  -- Un registro por usuario con su fecha de registro (desde el 2026-01-01)
  SELECT
    u.id                        AS UserId,
    CAST(u.date_joined AS DATE) AS RegistrationDate
  FROM hive_metastore.db_bronze_tps.users_user u
  WHERE CAST(u.date_joined AS DATE) >= '2026-01-01'
),

optins AS (
  -- Usuarios que hicieron opt-in en la promoción 980
  SELECT
    pu.UserId,
    CAST(pu.OptInDateTimeUtc AS DATE) AS OptInDate
  FROM hive_metastore.db_silver_bonusengine.promotion_user pu
  WHERE pu.PromotionId    = 980
    AND pu.UserIsOptIn    = TRUE
)

SELECT
  r.RegistrationDate,

  COUNT(DISTINCT r.UserId)                                                      AS NewUsersRegistered,

  COUNT(DISTINCT CASE
    WHEN o.OptInDate = r.RegistrationDate THEN r.UserId
  END)                                                                          AS OptInSameDay,

  COUNT(DISTINCT CASE
    WHEN o.UserId IS NOT NULL THEN r.UserId
  END)                                                                          AS OptInAnyMoment

FROM registrations r
LEFT JOIN optins o ON r.UserId = o.UserId

GROUP BY r.RegistrationDate
ORDER BY r.RegistrationDate
;
