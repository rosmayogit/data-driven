"""
Synthetic data generator for a promotions engine.

Generates realistic data simulating:
- Users with registration dates and segments
- Promotions with rules (min stake, min odds, required bets)
- Promotion funnel: eligible → opt-in → participate → win → redeem
- Bet history (promo and organic bets)
- Daily user activity metrics

Usage:
    python scripts/generate_data.py
    python scripts/generate_data.py --users 50000 --weeks 26
"""

import argparse
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("es_ES")
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PRODUCTS = ["sports", "live_sports", "casino", "live_casino", "virtual"]

PROMO_TEMPLATES = [
    {
        "name": "Freebet Semanal",
        "type": "freebet",
        "min_stake": 5.0,
        "min_odds": 1.50,
        "required_bets": 3,
        "reward_range": (5, 10),
        "recurrence": "weekly",
    },
    {
        "name": "Cashback Fin de Semana",
        "type": "cashback",
        "min_stake": 10.0,
        "min_odds": 1.80,
        "required_bets": 5,
        "reward_range": (5, 25),
        "recurrence": "weekly",
    },
    {
        "name": "Bonus Acumulador",
        "type": "accumulator_bonus",
        "min_stake": 2.0,
        "min_odds": 3.00,
        "required_bets": 1,
        "reward_range": (10, 50),
        "recurrence": "weekly",
    },
    {
        "name": "Reto Mensual",
        "type": "challenge",
        "min_stake": 5.0,
        "min_odds": 1.40,
        "required_bets": 20,
        "reward_range": (20, 100),
        "recurrence": "monthly",
    },
    {
        "name": "Bienvenida Promo",
        "type": "welcome",
        "min_stake": 1.0,
        "min_odds": 1.20,
        "required_bets": 1,
        "reward_range": (10, 10),
        "recurrence": "once",
    },
]

SEGMENTS = ["high_value", "medium", "low", "new"]
COUNTRIES = ["ES", "MX", "CO", "AR", "PE", "CL"]


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------
def generate_users(n_users: int, start_date: datetime) -> pd.DataFrame:
    """Generate a user base with registration dates spread over time."""
    users = []
    for i in range(1, n_users + 1):
        # Most users registered before the analysis window; some during
        reg_date = fake.date_between(
            start_date=start_date - timedelta(days=365),
            end_date=start_date + timedelta(days=30),
        )
        segment = random.choices(
            SEGMENTS, weights=[0.10, 0.30, 0.45, 0.15]
        )[0]
        country = random.choices(
            COUNTRIES, weights=[0.40, 0.20, 0.15, 0.10, 0.08, 0.07]
        )[0]
        users.append(
            {
                "user_id": i,
                "registration_date": reg_date,
                "segment": segment,
                "country": country,
            }
        )
    return pd.DataFrame(users)


def generate_promotions(start_date: datetime, n_weeks: int) -> pd.DataFrame:
    """Generate promotion instances from templates across the time window."""
    promos = []
    promo_id = 0
    for template in PROMO_TEMPLATES:
        if template["recurrence"] == "weekly":
            for week in range(n_weeks):
                promo_id += 1
                s = start_date + timedelta(weeks=week)
                e = s + timedelta(days=6)
                promos.append(
                    {
                        "promo_id": promo_id,
                        "promo_name": template["name"],
                        "promo_type": template["type"],
                        "start_date": s.date(),
                        "end_date": e.date(),
                        "min_stake": template["min_stake"],
                        "min_odds": template["min_odds"],
                        "required_bets": template["required_bets"],
                        "reward_min": template["reward_range"][0],
                        "reward_max": template["reward_range"][1],
                    }
                )
        elif template["recurrence"] == "monthly":
            for month_offset in range(0, n_weeks // 4 + 1):
                promo_id += 1
                s = start_date + timedelta(weeks=month_offset * 4)
                e = s + timedelta(days=27)
                promos.append(
                    {
                        "promo_id": promo_id,
                        "promo_name": template["name"],
                        "promo_type": template["type"],
                        "start_date": s.date(),
                        "end_date": e.date(),
                        "min_stake": template["min_stake"],
                        "min_odds": template["min_odds"],
                        "required_bets": template["required_bets"],
                        "reward_min": template["reward_range"][0],
                        "reward_max": template["reward_range"][1],
                    }
                )
        else:  # once
            promo_id += 1
            promos.append(
                {
                    "promo_id": promo_id,
                    "promo_name": template["name"],
                    "promo_type": template["type"],
                    "start_date": start_date.date(),
                    "end_date": (
                        start_date + timedelta(weeks=n_weeks)
                    ).date(),
                    "min_stake": template["min_stake"],
                    "min_odds": template["min_odds"],
                    "required_bets": template["required_bets"],
                    "reward_min": template["reward_range"][0],
                    "reward_max": template["reward_range"][1],
                }
            )
    return pd.DataFrame(promos)


def _user_base_activity(segment: str) -> dict:
    """Return base activity probabilities per segment."""
    return {
        "high_value": {
            "daily_active_prob": 0.70,
            "avg_bets": 6,
            "avg_stake": 30.0,
            "product_diversity": 3,
        },
        "medium": {
            "daily_active_prob": 0.40,
            "avg_bets": 3,
            "avg_stake": 12.0,
            "product_diversity": 2,
        },
        "low": {
            "daily_active_prob": 0.15,
            "avg_bets": 1.5,
            "avg_stake": 5.0,
            "product_diversity": 1,
        },
        "new": {
            "daily_active_prob": 0.50,
            "avg_bets": 2,
            "avg_stake": 8.0,
            "product_diversity": 2,
        },
    }[segment]


def generate_funnel_and_bets(
    users_df: pd.DataFrame,
    promos_df: pd.DataFrame,
    start_date: datetime,
    n_weeks: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Simulate the full funnel and betting activity.

    Returns (funnel_df, bets_df, daily_activity_df).

    The simulation ensures that promo participants show a realistic uplift
    in activity metrics vs non-participants, so comparative analyses work.
    """
    end_date = start_date + timedelta(weeks=n_weeks)
    all_dates = pd.date_range(start_date, end_date - timedelta(days=1))

    funnel_rows = []
    bet_rows = []
    daily_rows = []
    bet_id = 0

    # Pre-decide which users are "promo-inclined" (they tend to opt in)
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
                np.random.beta(1.5, 4, len(users_df)),  # low
            ),
        ),
    )

    for _, user in users_df.iterrows():
        uid = user["user_id"]
        reg_date = pd.Timestamp(user["registration_date"])
        segment = user["segment"]
        affinity = user["promo_affinity"]
        base = _user_base_activity(segment)

        # Track promo participation per day for activity uplift
        promo_days = set()

        # --- Funnel simulation per promo ---
        for _, promo in promos_df.iterrows():
            p_start = pd.Timestamp(promo["start_date"])
            p_end = pd.Timestamp(promo["end_date"])

            # Skip if user not yet registered
            if reg_date > p_end:
                continue

            # Eligibility: most users are eligible, some aren't
            eligible = random.random() < 0.80
            if not eligible:
                funnel_rows.append(
                    {
                        "user_id": uid,
                        "promo_id": promo["promo_id"],
                        "eligible": False,
                        "opted_in": False,
                        "opted_in_date": None,
                        "participated": False,
                        "participation_date": None,
                        "won": False,
                        "reward_amount": 0.0,
                        "reward_redeemed": False,
                        "reward_redeemed_date": None,
                    }
                )
                continue

            # Opt-in decision based on affinity
            opted_in = random.random() < affinity * 0.6
            opted_in_date = None
            if opted_in:
                days_range = (p_end - p_start).days
                opted_in_date = p_start + timedelta(
                    days=random.randint(0, max(0, min(2, days_range)))
                )

            # Participation: user places enough qualifying bets
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
                    # Mark promo days
                    for d in range(
                        max(0, (opted_in_date - start_date).days),
                        min(len(all_dates), (p_end - start_date).days + 1),
                    ):
                        promo_days.add(d)

            # Win
            won = participated and random.random() < 0.40
            reward_amount = 0.0
            if won:
                reward_amount = round(
                    random.uniform(promo["reward_min"], promo["reward_max"]), 2
                )

            # Redeem
            redeemed = won and random.random() < 0.75
            redeemed_date = None
            if redeemed and participation_date is not None:
                redeemed_date = participation_date + timedelta(
                    days=random.randint(0, 7)
                )

            funnel_rows.append(
                {
                    "user_id": uid,
                    "promo_id": promo["promo_id"],
                    "eligible": True,
                    "opted_in": opted_in,
                    "opted_in_date": opted_in_date,
                    "participated": participated,
                    "participation_date": participation_date,
                    "won": won,
                    "reward_amount": reward_amount,
                    "reward_redeemed": redeemed,
                    "reward_redeemed_date": redeemed_date,
                }
            )

            # Generate qualifying promo bets
            if participated:
                for _ in range(qualifying_bets):
                    bet_id += 1
                    bet_date = p_start + timedelta(
                        days=random.randint(0, (p_end - p_start).days)
                    )
                    stake = max(
                        promo["min_stake"],
                        round(
                            np.random.lognormal(
                                np.log(promo["min_stake"] * 1.5), 0.5
                            ),
                            2,
                        ),
                    )
                    odds = max(
                        promo["min_odds"],
                        round(promo["min_odds"] + np.random.exponential(0.5), 2),
                    )
                    bet_rows.append(
                        {
                            "bet_id": bet_id,
                            "user_id": uid,
                            "bet_date": bet_date.date(),
                            "stake": stake,
                            "odds": odds,
                            "product": random.choice(
                                PRODUCTS[:3]
                            ),  # promos mostly sports
                            "is_promo_bet": True,
                            "promo_id": promo["promo_id"],
                            "result": random.choices(
                                ["won", "lost"], weights=[0.45, 0.55]
                            )[0],
                        }
                    )

        # --- Daily activity & organic bets ---
        for day_idx, day in enumerate(all_dates):
            if day < reg_date:
                continue

            # Promo participation gives an activity uplift
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
                n_products = min(
                    len(PRODUCTS),
                    max(1, int(np.random.poisson(base["product_diversity"]))),
                )
                products_used = random.sample(PRODUCTS, n_products)

                for _ in range(n_bets):
                    bet_id += 1
                    avg_stake = base["avg_stake"] * (
                        1.25 if in_promo_window else 1.0
                    )
                    stake = round(
                        max(0.50, np.random.lognormal(np.log(avg_stake), 0.6)),
                        2,
                    )
                    odds = round(max(1.05, np.random.lognormal(0.3, 0.5)), 2)
                    total_stake += stake
                    bet_rows.append(
                        {
                            "bet_id": bet_id,
                            "user_id": uid,
                            "bet_date": day.date(),
                            "stake": stake,
                            "odds": odds,
                            "product": random.choice(products_used),
                            "is_promo_bet": False,
                            "promo_id": None,
                            "result": random.choices(
                                ["won", "lost"], weights=[0.45, 0.55]
                            )[0],
                        }
                    )

            daily_rows.append(
                {
                    "user_id": uid,
                    "activity_date": day.date(),
                    "is_active": is_active,
                    "num_bets": n_bets,
                    "total_stake": round(total_stake, 2),
                    "products_used": ",".join(sorted(products_used)) if products_used else None,
                    "num_products": len(products_used),
                }
            )

    funnel_df = pd.DataFrame(funnel_rows)
    bets_df = pd.DataFrame(bet_rows)
    daily_df = pd.DataFrame(daily_rows)

    return funnel_df, bets_df, daily_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic promotions engine data"
    )
    parser.add_argument(
        "--users", type=int, default=2000, help="Number of users (default: 2000)"
    )
    parser.add_argument(
        "--weeks", type=int, default=12, help="Weeks of data (default: 12)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2025-10-01",
        help="Start date YYYY-MM-DD (default: 2025-10-01)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory (default: data)",
    )
    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Generating data for {args.users} users over {args.weeks} weeks...")
    print(f"Start date: {args.start_date}")

    # Generate
    users_df = generate_users(args.users, start_date)
    print(f"  Users: {len(users_df):,} rows")

    promos_df = generate_promotions(start_date, args.weeks)
    print(f"  Promotions: {len(promos_df):,} rows")

    funnel_df, bets_df, daily_df = generate_funnel_and_bets(
        users_df, promos_df, start_date, args.weeks
    )
    print(f"  Funnel: {len(funnel_df):,} rows")
    print(f"  Bets: {len(bets_df):,} rows")
    print(f"  Daily activity: {len(daily_df):,} rows")

    # Save
    for name, df in [
        ("users", users_df),
        ("promotions", promos_df),
        ("funnel", funnel_df),
        ("bets", bets_df),
        ("daily_activity", daily_df),
    ]:
        path = os.path.join(args.output_dir, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"  Saved {path}")

    print("\nDone! Load these CSVs into Databricks with:")
    print("  df = spark.read.csv('/path/to/file.csv', header=True, inferSchema=True)")
    print("  df.createOrReplaceTempView('table_name')")


if __name__ == "__main__":
    main()
