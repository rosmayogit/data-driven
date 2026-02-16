# Databricks notebook source
# MAGIC %md
# MAGIC # Generar datos sintéticos — Motor de Promociones
# MAGIC
# MAGIC Este notebook genera datos realistas que simulan un motor de promociones
# MAGIC de una plataforma de apuestas. Crea 5 tablas directamente en Spark.
# MAGIC
# MAGIC **Ejecuta las celdas en orden, una por una.**

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Instalar dependencias y configurar

# COMMAND ----------

# MAGIC %pip install faker
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("es_ES")
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# --- CONFIGURACIÓN: ajusta estos valores si quieres ---
N_USERS = 2000       # número de usuarios
N_WEEKS = 12         # semanas de datos
START_DATE = datetime(2025, 10, 1)

print(f"Configuración: {N_USERS} usuarios, {N_WEEKS} semanas desde {START_DATE.date()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Definir constantes del modelo

# COMMAND ----------

PRODUCTS = ["sports", "live_sports", "casino", "live_casino", "virtual"]

PROMO_TEMPLATES = [
    {"name": "Freebet Semanal",      "type": "freebet",           "min_stake": 5.0,  "min_odds": 1.50, "required_bets": 3,  "reward_range": (5, 10),   "recurrence": "weekly"},
    {"name": "Cashback Fin de Semana","type": "cashback",          "min_stake": 10.0, "min_odds": 1.80, "required_bets": 5,  "reward_range": (5, 25),   "recurrence": "weekly"},
    {"name": "Bonus Acumulador",     "type": "accumulator_bonus", "min_stake": 2.0,  "min_odds": 3.00, "required_bets": 1,  "reward_range": (10, 50),  "recurrence": "weekly"},
    {"name": "Reto Mensual",         "type": "challenge",         "min_stake": 5.0,  "min_odds": 1.40, "required_bets": 20, "reward_range": (20, 100), "recurrence": "monthly"},
    {"name": "Bienvenida Promo",     "type": "welcome",           "min_stake": 1.0,  "min_odds": 1.20, "required_bets": 1,  "reward_range": (10, 10),  "recurrence": "once"},
]

SEGMENTS = ["high_value", "medium", "low", "new"]
COUNTRIES = ["ES", "MX", "CO", "AR", "PE", "CL"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Generar tabla de USERS

# COMMAND ----------

def generate_users(n_users, start_date):
    users = []
    for i in range(1, n_users + 1):
        reg_date = fake.date_between(
            start_date=start_date - timedelta(days=365),
            end_date=start_date + timedelta(days=30),
        )
        segment = random.choices(SEGMENTS, weights=[0.10, 0.30, 0.45, 0.15])[0]
        country = random.choices(COUNTRIES, weights=[0.40, 0.20, 0.15, 0.10, 0.08, 0.07])[0]
        users.append({"user_id": i, "registration_date": reg_date, "segment": segment, "country": country})
    return pd.DataFrame(users)

users_pdf = generate_users(N_USERS, START_DATE)
print(f"Users generados: {len(users_pdf):,} filas")
users_pdf.head(10)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Generar tabla de PROMOTIONS

# COMMAND ----------

def generate_promotions(start_date, n_weeks):
    promos = []
    promo_id = 0
    for t in PROMO_TEMPLATES:
        if t["recurrence"] == "weekly":
            for week in range(n_weeks):
                promo_id += 1
                s = start_date + timedelta(weeks=week)
                e = s + timedelta(days=6)
                promos.append({
                    "promo_id": promo_id, "promo_name": t["name"], "promo_type": t["type"],
                    "start_date": s.date(), "end_date": e.date(),
                    "min_stake": t["min_stake"], "min_odds": t["min_odds"],
                    "required_bets": t["required_bets"],
                    "reward_min": t["reward_range"][0], "reward_max": t["reward_range"][1],
                })
        elif t["recurrence"] == "monthly":
            for m in range(0, n_weeks // 4 + 1):
                promo_id += 1
                s = start_date + timedelta(weeks=m * 4)
                e = s + timedelta(days=27)
                promos.append({
                    "promo_id": promo_id, "promo_name": t["name"], "promo_type": t["type"],
                    "start_date": s.date(), "end_date": e.date(),
                    "min_stake": t["min_stake"], "min_odds": t["min_odds"],
                    "required_bets": t["required_bets"],
                    "reward_min": t["reward_range"][0], "reward_max": t["reward_range"][1],
                })
        else:  # once
            promo_id += 1
            promos.append({
                "promo_id": promo_id, "promo_name": t["name"], "promo_type": t["type"],
                "start_date": start_date.date(),
                "end_date": (start_date + timedelta(weeks=n_weeks)).date(),
                "min_stake": t["min_stake"], "min_odds": t["min_odds"],
                "required_bets": t["required_bets"],
                "reward_min": t["reward_range"][0], "reward_max": t["reward_range"][1],
            })
    return pd.DataFrame(promos)

promos_pdf = generate_promotions(START_DATE, N_WEEKS)
print(f"Promotions generadas: {len(promos_pdf):,} filas")
promos_pdf.head(10)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Generar FUNNEL, BETS y DAILY_ACTIVITY
# MAGIC
# MAGIC Esta es la celda más pesada — genera el funnel completo, las apuestas
# MAGIC y la actividad diaria. Con 2000 usuarios tarda ~2-3 minutos.

# COMMAND ----------

def _user_base_activity(segment):
    return {
        "high_value": {"daily_active_prob": 0.70, "avg_bets": 6, "avg_stake": 30.0, "product_diversity": 3},
        "medium":     {"daily_active_prob": 0.40, "avg_bets": 3, "avg_stake": 12.0, "product_diversity": 2},
        "low":        {"daily_active_prob": 0.15, "avg_bets": 1.5, "avg_stake": 5.0, "product_diversity": 1},
        "new":        {"daily_active_prob": 0.50, "avg_bets": 2, "avg_stake": 8.0, "product_diversity": 2},
    }[segment]


def generate_funnel_and_bets(users_df, promos_df, start_date, n_weeks):
    end_date = start_date + timedelta(weeks=n_weeks)
    all_dates = pd.date_range(start_date, end_date - timedelta(days=1))

    funnel_rows = []
    bet_rows = []
    daily_rows = []
    bet_id = 0

    users_df = users_df.copy()
    users_df["promo_affinity"] = np.where(
        users_df["segment"] == "high_value",
        np.random.beta(5, 2, len(users_df)),
        np.where(
            users_df["segment"] == "medium",
            np.random.beta(3, 3, len(users_df)),
            np.where(
                users_df["segment"] == "new",
                np.random.beta(4, 3, len(users_df)),
                np.random.beta(1.5, 4, len(users_df)),
            ),
        ),
    )

    total_users = len(users_df)
    for idx, (_, user) in enumerate(users_df.iterrows()):
        if (idx + 1) % 500 == 0:
            print(f"  Procesando usuario {idx + 1}/{total_users}...")

        uid = user["user_id"]
        reg_date = pd.Timestamp(user["registration_date"])
        segment = user["segment"]
        affinity = user["promo_affinity"]
        base = _user_base_activity(segment)
        promo_days = set()

        for _, promo in promos_df.iterrows():
            p_start = pd.Timestamp(promo["start_date"])
            p_end = pd.Timestamp(promo["end_date"])

            if reg_date > p_end:
                continue

            eligible = random.random() < 0.80
            if not eligible:
                funnel_rows.append({
                    "user_id": uid, "promo_id": promo["promo_id"],
                    "eligible": False, "opted_in": False, "opted_in_date": None,
                    "participated": False, "participation_date": None,
                    "won": False, "reward_amount": 0.0,
                    "reward_redeemed": False, "reward_redeemed_date": None,
                })
                continue

            opted_in = random.random() < affinity * 0.6
            opted_in_date = None
            if opted_in:
                days_range = (p_end - p_start).days
                opted_in_date = p_start + timedelta(days=random.randint(0, max(0, min(2, days_range))))

            participated = False
            participation_date = None
            qualifying_bets = 0
            if opted_in:
                participated = random.random() < 0.55
                if participated:
                    participation_date = opted_in_date + timedelta(
                        days=random.randint(0, max(0, (p_end - opted_in_date).days))
                    )
                    qualifying_bets = promo["required_bets"]
                    for d in range(
                        max(0, (opted_in_date - start_date).days),
                        min(len(all_dates), (p_end - start_date).days + 1),
                    ):
                        promo_days.add(d)

            won = participated and random.random() < 0.40
            reward_amount = 0.0
            if won:
                reward_amount = round(random.uniform(promo["reward_min"], promo["reward_max"]), 2)

            redeemed = won and random.random() < 0.75
            redeemed_date = None
            if redeemed and participation_date is not None:
                redeemed_date = participation_date + timedelta(days=random.randint(0, 7))

            funnel_rows.append({
                "user_id": uid, "promo_id": promo["promo_id"],
                "eligible": True, "opted_in": opted_in, "opted_in_date": opted_in_date,
                "participated": participated, "participation_date": participation_date,
                "won": won, "reward_amount": reward_amount,
                "reward_redeemed": redeemed, "reward_redeemed_date": redeemed_date,
            })

            if participated:
                for _ in range(qualifying_bets):
                    bet_id += 1
                    bet_date = p_start + timedelta(days=random.randint(0, (p_end - p_start).days))
                    stake = max(promo["min_stake"],
                        round(np.random.lognormal(np.log(promo["min_stake"] * 1.5), 0.5), 2))
                    odds = max(promo["min_odds"],
                        round(promo["min_odds"] + np.random.exponential(0.5), 2))
                    bet_rows.append({
                        "bet_id": bet_id, "user_id": uid, "bet_date": bet_date.date(),
                        "stake": stake, "odds": odds,
                        "product": random.choice(PRODUCTS[:3]),
                        "is_promo_bet": True, "promo_id": promo["promo_id"],
                        "result": random.choices(["won", "lost"], weights=[0.45, 0.55])[0],
                    })

        for day_idx, day in enumerate(all_dates):
            if day < reg_date:
                continue

            in_promo_window = day_idx in promo_days
            active_prob = base["daily_active_prob"]
            if in_promo_window:
                active_prob = min(0.95, active_prob * 1.4)

            is_active = random.random() < active_prob
            n_bets = 0
            total_stake = 0.0
            products_used = []

            if is_active:
                avg_bets = base["avg_bets"] * (1.3 if in_promo_window else 1.0)
                n_bets = max(1, int(np.random.poisson(avg_bets)))
                n_products = min(len(PRODUCTS), max(1, int(np.random.poisson(base["product_diversity"]))))
                products_used = random.sample(PRODUCTS, n_products)

                for _ in range(n_bets):
                    bet_id += 1
                    avg_stake = base["avg_stake"] * (1.25 if in_promo_window else 1.0)
                    stake = round(max(0.50, np.random.lognormal(np.log(avg_stake), 0.6)), 2)
                    odds = round(max(1.05, np.random.lognormal(0.3, 0.5)), 2)
                    total_stake += stake
                    bet_rows.append({
                        "bet_id": bet_id, "user_id": uid, "bet_date": day.date(),
                        "stake": stake, "odds": odds,
                        "product": random.choice(products_used),
                        "is_promo_bet": False, "promo_id": None,
                        "result": random.choices(["won", "lost"], weights=[0.45, 0.55])[0],
                    })

            daily_rows.append({
                "user_id": uid, "activity_date": day.date(),
                "is_active": is_active, "num_bets": n_bets,
                "total_stake": round(total_stake, 2),
                "products_used": ",".join(sorted(products_used)) if products_used else None,
                "num_products": len(products_used),
            })

    return pd.DataFrame(funnel_rows), pd.DataFrame(bet_rows), pd.DataFrame(daily_rows)


print("Generando funnel, apuestas y actividad diaria...")
funnel_pdf, bets_pdf, daily_pdf = generate_funnel_and_bets(users_pdf, promos_pdf, START_DATE, N_WEEKS)

print(f"\nResultado:")
print(f"  Funnel:         {len(funnel_pdf):,} filas")
print(f"  Bets:           {len(bets_pdf):,} filas")
print(f"  Daily activity: {len(daily_pdf):,} filas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Crear tablas en Spark
# MAGIC
# MAGIC Convierte los DataFrames de pandas a Spark y los registra como tablas
# MAGIC temporales. Después puedes usarlas desde cualquier celda SQL.

# COMMAND ----------

# Convertir pandas → Spark y registrar como tablas temporales
for name, pdf in [("users", users_pdf), ("promotions", promos_pdf),
                   ("funnel", funnel_pdf), ("bets", bets_pdf),
                   ("daily_activity", daily_pdf)]:
    sdf = spark.createDataFrame(pdf)
    sdf.createOrReplaceTempView(name)
    print(f"  Tabla '{name}' creada: {sdf.count():,} filas")

print("\n¡Listo! Ya puedes usar las tablas en celdas SQL con: SELECT * FROM users")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Verificación rápida

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Comprobar que todas las tablas tienen datos
# MAGIC SELECT 'users' AS tabla, COUNT(*) AS filas FROM users
# MAGIC UNION ALL
# MAGIC SELECT 'promotions', COUNT(*) FROM promotions
# MAGIC UNION ALL
# MAGIC SELECT 'funnel', COUNT(*) FROM funnel
# MAGIC UNION ALL
# MAGIC SELECT 'bets', COUNT(*) FROM bets
# MAGIC UNION ALL
# MAGIC SELECT 'daily_activity', COUNT(*) FROM daily_activity

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Vista rápida de las promos disponibles
# MAGIC SELECT promo_type, COUNT(*) AS instancias, MIN(start_date) AS primera, MAX(end_date) AS ultima
# MAGIC FROM promotions
# MAGIC GROUP BY promo_type
# MAGIC ORDER BY instancias DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Siguiente paso
# MAGIC
# MAGIC Las tablas ya están listas. Ahora puedes:
# MAGIC 1. Abrir `analysis/01_funnel_analysis.sql` y ejecutar las queries
# MAGIC 2. Abrir `analysis/04_temp_tables_tutorial.sql` para aprender paso a paso
# MAGIC 3. O escribir tus propias queries aquí abajo:

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Tu query aquí:
# MAGIC SELECT * FROM users LIMIT 5
