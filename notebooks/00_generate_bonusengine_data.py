# Databricks notebook source

# MAGIC %md
# MAGIC # 00 · Generar datos sintéticos — BonusEngine + Bets + Users
# MAGIC
# MAGIC Genera **todas las tablas necesarias** para el notebook de análisis directamente en Databricks:
# MAGIC
# MAGIC | Tabla | Descripción |
# MAGIC |-------|-------------|
# MAGIC | `promotion_detail` | Definición de campañas |
# MAGIC | `promotion_user` | Participación de usuarios |
# MAGIC | `reward_detail` | Definición de recompensas |
# MAGIC | `reward_redeem_user` | Emisión y canje de recompensas |
# MAGIC | `reward_freebet` | Detalle de freebets |
# MAGIC | `bets` | Apuestas sintéticas por usuario (para S4–S6) |
# MAGIC | `users` | Segmento por usuario (para S4–S6) |
# MAGIC
# MAGIC **No requiere subir ficheros.** Todo se genera en Python y se guarda como Delta table.
# MAGIC
# MAGIC Una vez ejecutado, abre `01_bonusengine_analysis` y asegúrate de que el config apunta a estas tablas.

# COMMAND ----------

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
NUM_USERS  = 2000          # número de usuarios sintéticos
NUM_MONTHS = 6             # meses de datos de promociones
START_DATE = "2025-08-21"  # inicio del período de promociones

# Base de datos / schema donde se crearán las tablas.
# Déjalo vacío "" para usar el esquema activo (default).
TARGET_DB  = ""

# Las apuestas se generan desde 60 días antes del START_DATE hasta el final
# del período de promociones, para que S6 tenga ventana "before" suficiente.
BETS_LEAD_DAYS = 60
# ──────────────────────────────────────────────────────────────────────────────

def _tbl(name):
    """Full table reference respecting TARGET_DB."""
    return f"{TARGET_DB}.{name}" if TARGET_DB else name

if TARGET_DB:
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {TARGET_DB}")
    spark.sql(f"USE {TARGET_DB}")

print(f"Parámetros:")
print(f"  Usuarios    : {NUM_USERS:,}")
print(f"  Meses       : {NUM_MONTHS}")
print(f"  Inicio      : {START_DATE}")
print(f"  Schema      : {TARGET_DB or '(default)'}")
print(f"  Tablas      : {_tbl('promotion_detail')}, {_tbl('bets')}, ...")

# COMMAND ----------

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

START = datetime.strptime(START_DATE, "%Y-%m-%d")

# COMMAND ----------

# ─── CONSTANTES ───────────────────────────────────────────────────────────────

BRANDS = [
    {"BrandId": 1, "tz_offset_hours":  1},   # ES (CET)
    {"BrandId": 2, "tz_offset_hours": -6},   # MX
    {"BrandId": 3, "tz_offset_hours": -5},   # CO
]

PROMOTION_TEMPLATES = [
    {"name": "Freebet Semanal Deportes",   "desc": "Apuesta y recibe una freebet semanal",       "type": "freebet",       "duration_days":  7, "recurrence": "weekly",  "requires_optin": True,  "target_bets":  3, "target_stake": 15.0, "max_redemptions":  5000, "max_per_user": 1},
    {"name": "Cashback Fin de Semana",     "desc": "Cashback del 10% en apuestas del fin de semana", "type": "cashback",  "duration_days":  3, "recurrence": "weekly",  "requires_optin": True,  "target_bets":  5, "target_stake": 25.0, "max_redemptions":  3000, "max_per_user": 1},
    {"name": "Bonus Acumulador",           "desc": "Bonus extra en apuestas combinadas",          "type": "accumulator", "duration_days":  7, "recurrence": "weekly",  "requires_optin": False, "target_bets":  1, "target_stake":  5.0, "max_redemptions": 10000, "max_per_user": 3},
    {"name": "Reto Mensual Deportes",      "desc": "Completa el reto mensual y gana premios",     "type": "challenge",   "duration_days": 30, "recurrence": "monthly", "requires_optin": True,  "target_bets": 20, "target_stake": 50.0, "max_redemptions":  2000, "max_per_user": 1},
    {"name": "Bienvenida Nuevo Usuario",   "desc": "Promocion de bienvenida para nuevos registros","type": "welcome",    "duration_days": 14, "recurrence": "once",    "requires_optin": False, "target_bets":  1, "target_stake":  5.0, "max_redemptions": 50000, "max_per_user": 1},
    {"name": "Casino Bonus Deposito",      "desc": "Bonus del 100% en tu primer deposito casino", "type": "deposit_bonus","duration_days": 30, "recurrence": "monthly", "requires_optin": True,  "target_bets":  0, "target_stake":  0.0, "max_redemptions":  5000, "max_per_user": 1},
    {"name": "Tiradas Gratis Slot",        "desc": "50 tiradas gratis en la slot de la semana",   "type": "free_spins",  "duration_days":  7, "recurrence": "weekly",  "requires_optin": True,  "target_bets":  0, "target_stake":  0.0, "max_redemptions":  8000, "max_per_user": 1},
    {"name": "Apuesta Sin Riesgo Champions","desc": "Tu primera apuesta en Champions sin riesgo", "type": "risk_free",   "duration_days":  2, "recurrence": "event",   "requires_optin": True,  "target_bets":  1, "target_stake": 10.0, "max_redemptions": 10000, "max_per_user": 1},
]

REWARD_NAMES = [
    ("Freebet 5€", 5.0), ("Freebet 10€", 10.0), ("Freebet 15€", 15.0),
    ("Freebet Live 5€", 5.0), ("Freebet Live 10€", 10.0),
    ("Cashback 5€", 5.0), ("Cashback 10€", 10.0), ("Cashback 25€", 25.0),
    ("Casino Bonus 10€", 10.0), ("Casino Bonus 25€", 25.0), ("Casino Bonus 50€", 50.0),
    ("Tiradas Gratis x50", 0.0),
]

FREEBET_TYPES = {
    "standard":     {"code": "STD",  "id": 1, "name": "Standard Freebet"},
    "live":         {"code": "LIVE", "id": 2, "name": "Live Freebet"},
    "cashback":     {"code": "CSH",  "id": 3, "name": "Cashback"},
    "casino_bonus": {"code": "CBN",  "id": 4, "name": "Casino Bonus"},
    "free_spins":   {"code": "FSP",  "id": 5, "name": "Free Spins"},
}

PRODUCTS = {
    "sports":      {"code": "SPR", "id": 1},
    "live_sports": {"code": "LSP", "id": 2},
    "casino":      {"code": "CAS", "id": 3},
    "live_casino": {"code": "LCS", "id": 4},
    "virtual":     {"code": "VRT", "id": 5},
}

PROMOTION_STATES = [
    {"id": 1, "desc": "Active"},
    {"id": 2, "desc": "Completed"},
    {"id": 3, "desc": "Expired"},
    {"id": 4, "desc": "Cancelled"},
]

ISSUED_USER_TYPES = [
    {"id": 1, "name": "Automatic"},
    {"id": 2, "name": "Manual"},
    {"id": 3, "name": "Segmented"},
]

SEGMENTS = ["VIP", "Regular", "New", "Reactivated", "All"]

# Segmentos reales asignados a cada usuario (independiente del target de la promo)
USER_SEGMENT_DIST = [
    ("VIP",         0.05),
    ("Regular",     0.60),
    ("New",         0.20),
    ("Reactivated", 0.15),
]

# COMMAND ----------

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _add_tz(row, prefix, utc_val, tz=1):
    row[f"{prefix}Utc"]   = utc_val
    row[f"{prefix}Local"] = (utc_val + timedelta(hours=tz)) if utc_val else None
    row[f"{prefix}CET"]   = (utc_val + timedelta(hours=1))  if utc_val else None


def _promo_instances(tmpl, month, month_start):
    results = []
    if tmpl["recurrence"] == "weekly":
        for w in range(4):
            s = month_start + timedelta(weeks=w)
            results.append((s, s + timedelta(days=tmpl["duration_days"]), f"S{month*4+w+1}"))
    elif tmpl["recurrence"] == "monthly":
        s = month_start
        results.append((s, s + timedelta(days=tmpl["duration_days"]), f"M{month+1}"))
    elif tmpl["recurrence"] == "once" and month == 0:
        s = month_start
        results.append((s, s + timedelta(days=tmpl["duration_days"]), ""))
    elif tmpl["recurrence"] == "event":
        for ev in range(random.randint(1, 3)):
            s = month_start + timedelta(days=random.randint(0, 20))
            results.append((s, s + timedelta(days=tmpl["duration_days"]), f"E{month*3+ev+1}"))
    return results

# COMMAND ----------

# ─── GENERADORES: BonusEngine ─────────────────────────────────────────────────

def gen_reward_detail(start, n_months):
    rows, rid = [], 0
    for m in range(n_months):
        ms = start + timedelta(days=m * 30)
        for name, _ in REWARD_NAMES:
            rid += 1
            brand = random.choice(BRANDS)
            row = {
                "RewardId": rid, "BrandId": brand["BrandId"],
                "RewardName": name, "ExpirationDays": random.choice([7, 14, 30]),
                "IsEnabled": random.random() < 0.90,
            }
            _add_tz(row, "ValidFrom", ms + timedelta(days=random.randint(0, 5)), brand["tz_offset_hours"])
            rows.append(row)
    return pd.DataFrame(rows)


def gen_promotion_detail(start, n_months, rewards_df):
    rows, pid = [], 0
    reward_ids = rewards_df["RewardId"].tolist()
    for m in range(n_months):
        ms = start + timedelta(days=m * 30)
        for tmpl in PROMOTION_TEMPLATES:
            for s, e, suffix in _promo_instances(tmpl, m, ms):
                pid += 1
                brand = random.choice(BRANDS)
                has_rules = tmpl["target_bets"] > 0
                row = {
                    "PromotionId": pid,
                    "PromotionName": f"{tmpl['name']} {suffix}".strip(),
                    "PromotionDescription": tmpl["desc"],
                    "BrandId": brand["BrandId"],
                    "IsSegmented": random.choice(SEGMENTS),
                    "PromotionRequiresOptIn": tmpl["requires_optin"],
                    "PromotionKey": f"PROMO-{pid:04d}",
                    "RewardId": random.choice(reward_ids),
                    "BetValidationRulesName": f"Rule_{tmpl['type']}_{pid}" if has_rules else None,
                    "BetValidationRulesExpression": (
                        f"bets >= {tmpl['target_bets']} AND stake >= {tmpl['target_stake']}"
                        if has_rules else None
                    ),
                    "ValidationTargetBetsPlaced": float(tmpl["target_bets"]),
                    "ValidationTargetAmountStaked": tmpl["target_stake"],
                    "MaxRedemptions": float(tmpl["max_redemptions"]),
                    "MaxRedemptionsPerUser": float(tmpl["max_per_user"]),
                }
                _add_tz(row, "StartDate", s, brand["tz_offset_hours"])
                _add_tz(row, "EndDate",   e, brand["tz_offset_hours"])
                rows.append(row)
    return pd.DataFrame(rows)


def gen_promotion_user(promos_df, n_users):
    rows = []
    user_ids = list(range(1, n_users + 1))
    now = datetime(2026, 2, 22)

    # Affinity per user: probability of appearing in any given promo
    affinity = {}
    for uid in user_ids:
        r = random.random()
        if   r < 0.15: affinity[uid] = 0.0
        elif r < 0.40: affinity[uid] = np.random.beta(1.2, 15)
        elif r < 0.75: affinity[uid] = np.random.beta(3, 12)
        else:          affinity[uid] = np.random.beta(5, 5)

    for _, promo in promos_df.iterrows():
        eligible = [uid for uid in user_ids if random.random() < affinity[uid]]
        ps, pe = promo["StartDateUtc"], promo["EndDateUtc"]
        req_optin = promo["PromotionRequiresOptIn"]

        for uid in eligible:
            state = random.choices(
                PROMOTION_STATES,
                weights=[0.05, 0.55, 0.35, 0.05] if pe < now else [0.60, 0.20, 0.05, 0.15]
            )[0]

            optin_utc, opted_in = None, False
            if req_optin:
                opted_in = random.random() < 0.45
                if opted_in:
                    days = max(1, (pe - ps).days)
                    optin_utc = ps + timedelta(days=random.randint(0, min(3, days-1)),
                                               hours=random.randint(8, 22),
                                               minutes=random.randint(0, 59))
            else:
                opted_in = True
                optin_utc = ps + timedelta(hours=random.randint(0, 12))

            tb = int(promo["ValidationTargetBetsPlaced"])
            if opted_in and state["id"] in (1, 2):
                if state["id"] == 2:
                    cb = tb + random.randint(0, 3)
                    cs = round(promo["ValidationTargetAmountStaked"] * random.uniform(1.0, 2.5), 2)
                else:
                    cb = random.randint(0, max(1, tb))
                    cs = round(promo["ValidationTargetAmountStaked"] * random.uniform(0.2, 1.2), 2)
                qc = 1 if cb >= tb else 0
            else:
                cb, cs, qc = 0, 0.0, 0

            row = {
                "PromotionId": promo["PromotionId"],
                "PromotionState": state["id"],
                "PromotionStateDescription": state["desc"],
                "UserId": uid,
                "IsSegmented": promo["IsSegmented"],
                "PromotionRequiresOptIn": req_optin,
                "UserIsOptIn": opted_in,
                "RewardId": promo["RewardId"],
                "QualificationCount": qc,
                "ConfirmedBetsPlaced": cb,
                "ConfirmedGrossAmountStaked": cs,
            }
            _add_tz(row, "OptInDateTime", optin_utc)
            rows.append(row)

    return pd.DataFrame(rows)


def gen_reward_redeem_user(promo_user_df, promos_df):
    rows, item_id = [], 0
    qualified = promo_user_df[promo_user_df["QualificationCount"] > 0]
    promos_idx = promos_df.set_index("PromotionId")

    for _, pu in qualified.iterrows():
        promo = promos_idx.loc[pu["PromotionId"]]
        item_id += 1
        issued_type = random.choices(ISSUED_USER_TYPES, weights=[0.70, 0.15, 0.15])[0]

        optin = pu["OptInDateTimeUtc"]
        if optin is not None and not pd.isna(optin):
            issued_utc = optin + timedelta(days=random.randint(1, 7), hours=random.randint(0, 23))
        else:
            issued_utc = promo["StartDateUtc"] + timedelta(days=random.randint(3, 10), hours=random.randint(8, 20))

        redeemed_utc = None
        if random.random() < 0.70:
            redeemed_utc = issued_utc + timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))

        row = {
            "PromotionId": pu["PromotionId"], "UserId": pu["UserId"],
            "RewardId": pu["RewardId"], "IssuedUserTypeId": issued_type["id"],
            "IssuedUserType": issued_type["name"], "BrandId": promo["BrandId"],
            "RewardItemId": item_id,
        }
        _add_tz(row, "IssuedOn",   issued_utc)
        _add_tz(row, "RedeemedOn", redeemed_utc)
        rows.append(row)

    return pd.DataFrame(rows)


def gen_reward_freebet(rewards_df, redeem_df):
    rows, fb_id = [], 0
    rewards_idx = rewards_df.set_index("RewardId")

    for _, redeem in redeem_df.iterrows():
        rid = redeem["RewardId"]
        if rid not in rewards_idx.index:
            continue
        rname = rewards_idx.loc[rid, "RewardName"]

        if "Casino" in rname or "Tiradas" in rname:
            fbt = "casino_bonus" if "Casino" in rname else "free_spins"
            prod = "casino"
        elif "Live" in rname:
            fbt, prod = "live", "live_sports"
        elif "Cashback" in rname:
            fbt, prod = "cashback", "sports"
        else:
            fbt, prod = "standard", "sports"

        fb, pr = FREEBET_TYPES[fbt], PRODUCTS[prod]
        fb_id += 1
        amount = random.choice([5.0, 10.0, 15.0, 25.0, 50.0]) if "Tiradas" not in rname else 0.0

        rows.append({
            "RewardId": rid, "RewardName": rname, "Amount": amount,
            "FreebetId": fb_id, "RewardItemId": redeem["RewardItemId"],
            "RewardItemType": fb["id"], "FreebetTypeCode": fb["code"],
            "FreebetTypeId": fb["id"], "FreebetTypeName": fb["name"],
            "ProductsCriteriaCode": pr["code"], "ProductCode": pr["code"], "ProductId": pr["id"],
        })

    return pd.DataFrame(rows)

# COMMAND ----------

# ─── GENERADORES: Users + Bets ────────────────────────────────────────────────

# Segmento real de cada usuario (independiente del segmento objetivo de las promos)
_seg_names  = [s for s, _ in USER_SEGMENT_DIST]
_seg_probs  = [p for _, p in USER_SEGMENT_DIST]

USER_SEGMENTS = {
    uid: np.random.choice(_seg_names, p=_seg_probs)
    for uid in range(1, NUM_USERS + 1)
}


def gen_users(n_users):
    return pd.DataFrame({
        "user_id": range(1, n_users + 1),
        "segment": [USER_SEGMENTS[uid] for uid in range(1, n_users + 1)],
    })


def gen_bets(n_users, start, n_months, lead_days):
    """
    Genera apuestas sintéticas para todos los usuarios.

    Período: [start - lead_days, start + n_months * 30]
    GGR = stake - stake*odds si won, stake si lost
    """
    bets_start = start - timedelta(days=lead_days)
    bets_end   = start + timedelta(days=n_months * 30)
    period_days = (bets_end - bets_start).days

    # Engagement por segmento: (avg_active_day_fraction, log_stake_mean)
    engagement = {
        "VIP":         (0.50, np.log(50)),
        "Regular":     (0.25, np.log(20)),
        "New":         (0.12, np.log(10)),
        "Reactivated": (0.20, np.log(15)),
    }

    rows = []
    for user_id in range(1, n_users + 1):
        seg = USER_SEGMENTS[user_id]
        day_frac, log_stake = engagement[seg]

        # Número de días activos ~ Poisson(avg)
        avg_days = max(1, int(period_days * day_frac))
        n_days = min(np.random.poisson(avg_days), period_days)
        if n_days == 0:
            continue

        active_offsets = sorted(random.sample(range(period_days), n_days))

        for offset in active_offsets:
            bet_date = bets_start + timedelta(days=offset)
            for _ in range(random.randint(1, 5)):
                stake = round(max(1.0, np.random.lognormal(log_stake, 0.8)), 2)
                odds  = round(random.uniform(1.1, 10.0), 2)
                # Ligera ventaja para la casa (95% del valor justo)
                result = "won" if random.random() < (0.95 / odds) else "lost"
                rows.append({
                    "user_id":  user_id,
                    "bet_date": bet_date,
                    "stake":    stake,
                    "odds":     odds,
                    "result":   result,
                })

    df = pd.DataFrame(rows)
    df["bet_id"] = range(1, len(df) + 1)
    return df[["bet_id", "user_id", "bet_date", "stake", "odds", "result"]]

# COMMAND ----------

# ─── GENERAR TODOS LOS DATOS ──────────────────────────────────────────────────

print("Generando datos sintéticos...")
print("-" * 50)

rewards_df    = gen_reward_detail(START, NUM_MONTHS)
print(f"  reward_detail      : {len(rewards_df):>8,} filas")

promos_df     = gen_promotion_detail(START, NUM_MONTHS, rewards_df)
print(f"  promotion_detail   : {len(promos_df):>8,} filas")

promo_user_df = gen_promotion_user(promos_df, NUM_USERS)
print(f"  promotion_user     : {len(promo_user_df):>8,} filas")

redeem_df     = gen_reward_redeem_user(promo_user_df, promos_df)
print(f"  reward_redeem_user : {len(redeem_df):>8,} filas")

freebet_df    = gen_reward_freebet(rewards_df, redeem_df)
print(f"  reward_freebet     : {len(freebet_df):>8,} filas")

users_df      = gen_users(NUM_USERS)
print(f"  users              : {len(users_df):>8,} filas")

bets_df       = gen_bets(NUM_USERS, START, NUM_MONTHS, BETS_LEAD_DAYS)
print(f"  bets               : {len(bets_df):>8,} filas")

print("-" * 50)
print("Generación completada.")

# COMMAND ----------

# ─── GUARDAR COMO DELTA TABLES ────────────────────────────────────────────────

tables = {
    "promotion_detail":   promos_df,
    "promotion_user":     promo_user_df,
    "reward_detail":      rewards_df,
    "reward_redeem_user": redeem_df,
    "reward_freebet":     freebet_df,
    "users":              users_df,
    "bets":               bets_df,
}

print("Guardando Delta tables...")
for name, df in tables.items():
    full_name = _tbl(name)
    (spark
        .createDataFrame(df)
        .write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(full_name))
    print(f"  ✓ {full_name}")

print("\nTablas listas.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Validación

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
# MAGIC UNION ALL
# MAGIC SELECT 'users',                       COUNT(*) FROM users
# MAGIC UNION ALL
# MAGIC SELECT 'bets',                        COUNT(*) FROM bets
# MAGIC ORDER BY tabla

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Muestra de bets con GGR calculado
# MAGIC SELECT
# MAGIC   result,
# MAGIC   COUNT(*)                                                        AS num_apuestas,
# MAGIC   ROUND(AVG(stake), 2)                                           AS stake_medio,
# MAGIC   ROUND(AVG(odds),  2)                                           AS odds_media,
# MAGIC   ROUND(SUM(stake - CASE WHEN result='won' THEN stake*odds ELSE 0 END)
# MAGIC         / COUNT(DISTINCT user_id), 2)                            AS ggr_por_usuario
# MAGIC FROM bets
# MAGIC GROUP BY result

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ### Próximo paso
# MAGIC
# MAGIC Abre **`01_bonusengine_analysis`** y en la celda de configuración (⚙️) ajusta:
# MAGIC
# MAGIC ```python
# MAGIC BETS_TABLE  = "bets"    # o f"{TARGET_DB}.bets" si usaste TARGET_DB
# MAGIC USERS_TABLE = "users"   # o f"{TARGET_DB}.users"
# MAGIC ```
# MAGIC
# MAGIC Luego ejecuta todas las celdas de arriba abajo.
