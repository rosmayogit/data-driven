-- Welcome Offer Funnel — por fecha de registro
-- Funnel: Registro | Reward Credited | Reward Redeemed
-- CampaignId: 951
-- Fuente voucher: db_silver_voucher.eventsmaster

SELECT
  CAST(u.RegistrationDate AS DATE)                                       AS fecha,
  COUNT(DISTINCT u.id)                                                   AS usuarios_registrados,
  COUNT(DISTINCT CASE WHEN ev.IssuedOnUTC   IS NOT NULL THEN u.id END)  AS usuarios_rewarded,
  COUNT(DISTINCT CASE WHEN ev.RedeemedOnUTC IS NOT NULL THEN u.id END)  AS usuarios_redeemed
FROM hive_metastore.db_bronze_tps.users_user u
INNER JOIN hive_metastore.db_bronze_tps.users_userdetail ud
  ON ud.UserId = u.id
LEFT JOIN db_silver_voucher.eventsmaster ev
  ON  CAST(ev.IssuedToUserId AS STRING) = CAST(u.id AS STRING)
  AND ev.CampaignId = 951
GROUP BY CAST(u.RegistrationDate AS DATE)
ORDER BY fecha;
