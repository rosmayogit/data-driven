-- Welcome Offer Funnel — por fecha de registro
-- Funnel: Registro | Reward Credited | Reward Redeemed
-- CampaignId: 951 | BrandId: 1901 (Nigeria) | Desde: 2025-02-02

SELECT
  CAST(u.RegistrationDate AS DATE)                                        AS fecha,
  COUNT(DISTINCT u.id)                                                    AS usuarios_registrados,
  COUNT(DISTINCT CASE WHEN ev.IssuedOnUTC   IS NOT NULL THEN u.id END)   AS usuarios_rewarded,
  COUNT(DISTINCT CASE WHEN ev.RedeemedOnUTC IS NOT NULL THEN u.id END)   AS usuarios_redeemed
FROM hive_metastore.db_bronze_tps.users_user u
INNER JOIN hive_metastore.db_bronze_tps.users_userdetail ud
  ON ud.UserId = u.id
LEFT JOIN (
  SELECT IssuedToUserId, IssuedOnUTC, RedeemedOnUTC
  FROM db_silver_voucher.eventsmaster
  WHERE CampaignId = '951'
) ev
  ON CAST(ev.IssuedToUserId AS STRING) = CAST(u.id AS STRING)
WHERE u.BrandId = 1901
  AND CAST(u.RegistrationDate AS DATE) >= '2025-02-02'
  AND u.IsTest = False
  AND u.UserTypeId = 2
GROUP BY CAST(u.RegistrationDate AS DATE)
ORDER BY fecha;
