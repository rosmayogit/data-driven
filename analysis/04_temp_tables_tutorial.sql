-- ============================================================================
-- TUTORIAL: Tablas temporales (TEMP VIEWS) en Databricks
-- ============================================================================
-- Una temp view es como una tabla que solo existe mientras dure tu sesión.
-- Sirve para guardar resultados intermedios y reutilizarlos en queries
-- posteriores sin tener que repetir JOINs o cálculos complejos.
--
-- Sintaxis básica:
--   CREATE OR REPLACE TEMP VIEW nombre_vista AS
--   SELECT ... FROM ...
--
-- Después la usas como cualquier otra tabla:
--   SELECT * FROM nombre_vista
--
-- Ejecuta cada bloque en orden, uno por uno, en celdas separadas de
-- tu notebook de Databricks.
-- ============================================================================


-- ============================================================================
-- PASO 1: Temp view simple — filtrar una tabla
-- ============================================================================
-- Empezamos fácil: crear una vista solo con los usuarios high_value.
-- Esto es útil cuando quieres trabajar solo con un subconjunto de datos.

CREATE OR REPLACE TEMP VIEW usuarios_high_value AS
SELECT *
FROM users
WHERE segment = 'high_value';

-- Comprueba el resultado:
SELECT * FROM usuarios_high_value LIMIT 10;


-- ============================================================================
-- PASO 2: JOIN de 2 tablas — funnel + users
-- ============================================================================
-- Problema: la tabla funnel tiene user_id pero no sabes el segmento ni el
-- país del usuario. Para eso necesitas cruzarla con users.
--
-- JOIN: combina filas de dos tablas cuando coincide una columna (user_id).
-- INNER JOIN = solo devuelve filas donde hay match en ambas tablas.

CREATE OR REPLACE TEMP VIEW funnel_con_usuario AS
SELECT
    f.user_id,
    u.segment,
    u.country,
    f.promo_id,
    f.eligible,
    f.opted_in,
    f.participated,
    f.won,
    f.reward_redeemed,
    f.reward_amount
FROM funnel f
JOIN users u ON f.user_id = u.user_id;
--                ^^^^^^^^^^^^^^^^^^^^^^^^
-- Esta línea dice: "une las filas donde el user_id de funnel
-- coincide con el user_id de users"
-- f y u son "alias" (nombres cortos) para no escribir el nombre completo

-- Comprueba: ahora ves el segmento y país junto al funnel
SELECT * FROM funnel_con_usuario LIMIT 10;

-- Ejemplo de uso: ¿cuántos usuarios de España participaron en promos?
SELECT
    COUNT(DISTINCT user_id) AS usuarios_participantes_es
FROM funnel_con_usuario
WHERE country = 'ES' AND participated = true;


-- ============================================================================
-- PASO 3: JOIN de 3 tablas — funnel + users + promotions
-- ============================================================================
-- Ahora queremos ver no solo quién es el usuario, sino también qué promo era.
-- Añadimos un segundo JOIN con la tabla promotions.

CREATE OR REPLACE TEMP VIEW funnel_enriquecido AS
SELECT
    f.user_id,
    u.segment,
    u.country,
    p.promo_id,
    p.promo_name,
    p.promo_type,
    p.start_date AS promo_start,
    p.end_date AS promo_end,
    f.eligible,
    f.opted_in,
    f.participated,
    f.won,
    f.reward_amount,
    f.reward_redeemed
FROM funnel f
JOIN users u ON f.user_id = u.user_id          -- primer JOIN: añade datos del usuario
JOIN promotions p ON f.promo_id = p.promo_id;   -- segundo JOIN: añade datos de la promo

-- Comprueba: ahora tienes usuario + promo + funnel todo junto
SELECT * FROM funnel_enriquecido LIMIT 10;

-- Ejemplo: tasa de opt-in por tipo de promo y segmento
SELECT
    segment,
    promo_type,
    COUNT(*) AS elegibles,
    SUM(CASE WHEN opted_in THEN 1 ELSE 0 END) AS opt_ins,
    ROUND(
        SUM(CASE WHEN opted_in THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) AS tasa_optin_pct
FROM funnel_enriquecido
WHERE eligible = true
GROUP BY segment, promo_type
ORDER BY segment, promo_type;


-- ============================================================================
-- PASO 4: Agregación + JOIN — resumen de apuestas por usuario
-- ============================================================================
-- A veces necesitas PRIMERO agregar datos (sumar, contar, promediar)
-- y DESPUÉS cruzar el resultado con otra tabla.
--
-- Aquí: calculamos métricas de apuestas por usuario desde la tabla bets,
-- y luego le pegamos el segmento desde users.

CREATE OR REPLACE TEMP VIEW resumen_apuestas_usuario AS
SELECT
    b.user_id,
    u.segment,
    u.country,
    COUNT(*) AS total_apuestas,
    ROUND(SUM(b.stake), 2) AS stake_total,
    ROUND(AVG(b.stake), 2) AS stake_promedio,
    SUM(CASE WHEN b.is_promo_bet THEN 1 ELSE 0 END) AS apuestas_promo,
    SUM(CASE WHEN NOT b.is_promo_bet THEN 1 ELSE 0 END) AS apuestas_organicas,
    COUNT(DISTINCT b.product) AS productos_distintos,
    COUNT(DISTINCT b.bet_date) AS dias_con_apuestas
FROM bets b
JOIN users u ON b.user_id = u.user_id
GROUP BY b.user_id, u.segment, u.country;
--       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
-- GROUP BY: agrupa todas las apuestas de cada usuario en una sola fila
-- Todo lo que NO está en GROUP BY debe ir dentro de COUNT, SUM, AVG, etc.

-- Comprueba:
SELECT * FROM resumen_apuestas_usuario ORDER BY stake_total DESC LIMIT 10;

-- Ejemplo: comparar stake medio por segmento
SELECT
    segment,
    COUNT(*) AS usuarios,
    ROUND(AVG(stake_total), 2) AS avg_stake_total,
    ROUND(AVG(total_apuestas), 1) AS avg_num_apuestas,
    ROUND(AVG(productos_distintos), 1) AS avg_productos
FROM resumen_apuestas_usuario
GROUP BY segment
ORDER BY avg_stake_total DESC;


-- ============================================================================
-- PASO 5: Temp view que usa otra temp view
-- ============================================================================
-- Las temp views se pueden encadenar: una vista puede leer de otra vista
-- que creaste antes. Esto permite construir análisis paso a paso.
--
-- Aquí: usamos funnel_enriquecido (paso 3) y resumen_apuestas_usuario
-- (paso 4) para crear un perfil completo del usuario.

CREATE OR REPLACE TEMP VIEW perfil_usuario_promo AS
SELECT
    rau.user_id,
    rau.segment,
    rau.country,
    rau.total_apuestas,
    rau.stake_total,
    rau.apuestas_promo,
    rau.apuestas_organicas,
    rau.productos_distintos,
    -- Datos de participación en promos (del funnel enriquecido)
    COUNT(DISTINCT CASE WHEN fe.participated THEN fe.promo_id END) AS promos_participadas,
    COUNT(DISTINCT CASE WHEN fe.won THEN fe.promo_id END) AS promos_ganadas,
    ROUND(SUM(CASE WHEN fe.reward_redeemed THEN fe.reward_amount ELSE 0 END), 2) AS rewards_canjeados
FROM resumen_apuestas_usuario rau    -- <-- esta es la temp view del paso 4
LEFT JOIN funnel_enriquecido fe      -- <-- esta es la temp view del paso 3
    ON rau.user_id = fe.user_id
GROUP BY
    rau.user_id, rau.segment, rau.country,
    rau.total_apuestas, rau.stake_total,
    rau.apuestas_promo, rau.apuestas_organicas,
    rau.productos_distintos;
-- LEFT JOIN: incluye TODOS los usuarios del resumen de apuestas,
-- aunque no tengan registros en el funnel (usuarios que nunca fueron elegibles).
-- Un JOIN normal los descartaría.

-- Comprueba:
SELECT * FROM perfil_usuario_promo ORDER BY promos_participadas DESC LIMIT 10;


-- ============================================================================
-- PASO 6: Caso real — KPIs semanales por usuario
-- ============================================================================
-- Objetivo: para cada usuario, calcular sus KPIs por semana.
-- Combina daily_activity (actividad diaria) con users (segmento)
-- y con una clasificación de si es usuario de promos o no.
--
-- Este tipo de tabla es la base de un dashboard semanal.

-- Primero: clasificamos a cada usuario como promo/no-promo
CREATE OR REPLACE TEMP VIEW clasificacion_usuarios AS
SELECT
    u.user_id,
    u.segment,
    u.country,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM funnel f
            WHERE f.user_id = u.user_id AND f.participated = true
        ) THEN 'promo'
        ELSE 'no_promo'
    END AS tipo_usuario
FROM users u;

-- Después: KPIs semanales cruzando con daily_activity
CREATE OR REPLACE TEMP VIEW kpis_semanales AS
SELECT
    cu.tipo_usuario,
    cu.segment,
    DATE_TRUNC('week', da.activity_date) AS semana,
    COUNT(DISTINCT da.user_id) AS usuarios,
    -- Días activos por usuario
    ROUND(
        SUM(CASE WHEN da.is_active THEN 1 ELSE 0 END) * 1.0
        / COUNT(DISTINCT da.user_id),
        2
    ) AS dias_activos_por_usuario,
    -- Stake por usuario
    ROUND(SUM(da.total_stake) / COUNT(DISTINCT da.user_id), 2) AS stake_por_usuario,
    -- Apuestas por usuario
    ROUND(SUM(da.num_bets) * 1.0 / COUNT(DISTINCT da.user_id), 2) AS apuestas_por_usuario,
    -- Productos por día activo
    ROUND(
        AVG(CASE WHEN da.is_active THEN da.num_products ELSE NULL END),
        2
    ) AS productos_por_dia_activo
FROM daily_activity da
JOIN clasificacion_usuarios cu ON da.user_id = cu.user_id
GROUP BY cu.tipo_usuario, cu.segment, DATE_TRUNC('week', da.activity_date);

-- Resultado final: tabla perfecta para un dashboard
SELECT *
FROM kpis_semanales
ORDER BY semana, segment, tipo_usuario;

-- Ejemplo: ver solo la comparativa promo vs no_promo (sin desglosar segmento)
SELECT
    tipo_usuario,
    semana,
    SUM(usuarios) AS usuarios,
    ROUND(AVG(dias_activos_por_usuario), 2) AS avg_dias_activos,
    ROUND(AVG(stake_por_usuario), 2) AS avg_stake,
    ROUND(AVG(apuestas_por_usuario), 2) AS avg_apuestas
FROM kpis_semanales
GROUP BY tipo_usuario, semana
ORDER BY semana, tipo_usuario;


-- ============================================================================
-- RESUMEN DE LO APRENDIDO
-- ============================================================================
-- 1. CREATE OR REPLACE TEMP VIEW ... AS SELECT  → crea una tabla temporal
-- 2. JOIN ... ON     → cruza dos tablas por una columna común
-- 3. LEFT JOIN       → como JOIN pero mantiene filas sin match
-- 4. GROUP BY + SUM/COUNT/AVG → agrega muchas filas en una
-- 5. Puedes encadenar temp views: una puede leer de otra
-- 6. CASE WHEN ... THEN ... ELSE ... END → lógica condicional
-- 7. DATE_TRUNC('week', fecha) → agrupa fechas por semana
--
-- Siguiente paso: coge cualquiera de estas temp views y crea un
-- dashboard en Databricks arrastrando las columnas a gráficos.
-- ============================================================================
