"""
Synthetic data generator for the BonusEngine schema (db_silver_bonusengine).

Generates realistic data for 5 tables:
- promotion_detail: Promotion definitions with rules and rewards
- promotion_user: User participation per promotion
- reward_detail: Reward definitions
- reward_redeem_user: Reward issuance and redemption per user
- reward_freebet: Freebet reward specifics

Technical metadata columns (dw_insert_ts, dw_update_ts, row_valid_to_ts,
key_hash, data_hash) are intentionally omitted.

Usage:
    python scripts/generate_bonusengine_data.py
    python scripts/generate_bonusengine_data.py --users 5000
    python scripts/generate_bonusengine_data.py --months 12
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
BRANDS = [
    {"BrandId": 1, "tz_offset_hours": 1},   # ES (CET)
    {"BrandId": 2, "tz_offset_hours": -6},  # MX
    {"BrandId": 3, "tz_offset_hours": -5},  # CO
]

PROMOTION_TEMPLATES = [
    # --- Weekly Club family (recurring weekly, numbered sequentially) ---
    {
        "name": "Weekly Club",
        "desc": "Weekly freebet club – place qualifying bets to earn a freebet",
        "type": "freebet",
        "duration_days": 7,
        "recurrence": "weekly",
        "requires_optin": True,
        "target_bets": 3,
        "target_stake": 15.0,
        "max_redemptions": 5000,
        "max_per_user": 1,
    },
    {
        "name": "Weekly Club Cashback",
        "desc": "Weekly cashback on weekend bets",
        "type": "cashback",
        "duration_days": 3,
        "recurrence": "weekly",
        "requires_optin": True,
        "target_bets": 5,
        "target_stake": 25.0,
        "max_redemptions": 3000,
        "max_per_user": 1,
    },
    {
        "name": "Weekly Club Acca Boost",
        "desc": "Weekly accumulator boost – extra bonus on combo bets",
        "type": "accumulator",
        "duration_days": 7,
        "recurrence": "weekly",
        "requires_optin": False,
        "target_bets": 1,
        "target_stake": 5.0,
        "max_redemptions": 10000,
        "max_per_user": 3,
    },
    # --- Welcome Offer family (one-time for new users) ---
    {
        "name": "Welcome Offer",
        "desc": "Welcome bonus for new registrations – first bet risk-free",
        "type": "welcome",
        "duration_days": 14,
        "recurrence": "once",
        "requires_optin": False,
        "target_bets": 1,
        "target_stake": 5.0,
        "max_redemptions": 50000,
        "max_per_user": 1,
    },
    {
        "name": "Welcome Offer Casino",
        "desc": "Welcome casino bonus – 100% deposit match for new users",
        "type": "deposit_bonus",
        "duration_days": 14,
        "recurrence": "once",
        "requires_optin": False,
        "target_bets": 0,
        "target_stake": 0.0,
        "max_redemptions": 50000,
        "max_per_user": 1,
    },
    # --- VIP – High Depositors family (monthly, segmented) ---
    {
        "name": "VIP - High Depositors",
        "desc": "Exclusive monthly freebet for high-value depositors",
        "type": "freebet",
        "duration_days": 30,
        "recurrence": "monthly",
        "requires_optin": True,
        "target_bets": 10,
        "target_stake": 100.0,
        "max_redemptions": 500,
        "max_per_user": 1,
    },
    {
        "name": "VIP - High Depositors Cashback",
        "desc": "Premium monthly cashback for VIP segment",
        "type": "cashback",
        "duration_days": 30,
        "recurrence": "monthly",
        "requires_optin": True,
        "target_bets": 15,
        "target_stake": 200.0,
        "max_redemptions": 300,
        "max_per_user": 1,
    },
    {
        "name": "VIP - High Depositors Free Spins",
        "desc": "Exclusive free spins package for VIP players",
        "type": "free_spins",
        "duration_days": 7,
        "recurrence": "monthly",
        "requires_optin": True,
        "target_bets": 0,
        "target_stake": 0.0,
        "max_redemptions": 200,
        "max_per_user": 1,
    },
    # --- Other recurring promos ---
    {
        "name": "Monthly Challenge",
        "desc": "Complete the monthly challenge to win prizes",
        "type": "challenge",
        "duration_days": 30,
        "recurrence": "monthly",
        "requires_optin": True,
        "target_bets": 20,
        "target_stake": 50.0,
        "max_redemptions": 2000,
        "max_per_user": 1,
    },
    {
        "name": "Free Spins Slot of the Week",
        "desc": "50 free spins on the featured slot of the week",
        "type": "free_spins",
        "duration_days": 7,
        "recurrence": "weekly",
        "requires_optin": True,
        "target_bets": 0,
        "target_stake": 0.0,
        "max_redemptions": 8000,
        "max_per_user": 1,
    },
    {
        "name": "Champions League Risk-Free",
        "desc": "Risk-free first bet on Champions League matches",
        "type": "risk_free",
        "duration_days": 2,
        "recurrence": "event",
        "requires_optin": True,
        "target_bets": 1,
        "target_stake": 10.0,
        "max_redemptions": 10000,
        "max_per_user": 1,
    },
]

REWARD_NAMES = [
    ("Freebet 5€", 5.0),
    ("Freebet 10€", 10.0),
    ("Freebet 15€", 15.0),
    ("Freebet Live 5€", 5.0),
    ("Freebet Live 10€", 10.0),
    ("Cashback 5€", 5.0),
    ("Cashback 10€", 10.0),
    ("Cashback 25€", 25.0),
    ("Casino Bonus 10€", 10.0),
    ("Casino Bonus 25€", 25.0),
    ("Casino Bonus 50€", 50.0),
    ("Free Spins x50", 0.0),
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


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _add_tz_variants(row: dict, field_prefix: str, utc_value, tz_offset: int = 1):
    """Add UTC, Local and CET timestamp variants for a field."""
    row[f"{field_prefix}Utc"] = utc_value
    row[f"{field_prefix}Local"] = utc_value + timedelta(hours=tz_offset) if utc_value else None
    row[f"{field_prefix}CET"] = utc_value + timedelta(hours=1) if utc_value else None


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------
def generate_reward_detail(start_date: datetime, n_months: int) -> pd.DataFrame:
    """Generate reward definitions."""
    rows = []
    reward_id = 0

    for month in range(n_months):
        month_start = start_date + timedelta(days=month * 30)
        for name, _ in REWARD_NAMES:
            reward_id += 1
            brand = random.choice(BRANDS)
            valid_from = month_start + timedelta(days=random.randint(0, 5))

            row = {
                "RewardId": reward_id,
                "BrandId": brand["BrandId"],
                "RewardName": name,
                "ExpirationDays": random.choice([7, 14, 30]),
                "IsEnabled": random.random() < 0.90,
            }
            _add_tz_variants(row, "ValidFrom", valid_from, brand["tz_offset_hours"])
            rows.append(row)

    return pd.DataFrame(rows)


def generate_promotion_detail(
    start_date: datetime, n_months: int, rewards_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate promotion definitions linked to rewards."""
    rows = []
    promo_id = 0
    reward_ids = rewards_df["RewardId"].tolist()

    for month in range(n_months):
        month_start = start_date + timedelta(days=month * 30)

        for tmpl in PROMOTION_TEMPLATES:
            instances = _promotion_instances(tmpl, month, month_start)
            for s, e, suffix in instances:
                promo_id += 1
                brand = random.choice(BRANDS)
                reward_id = random.choice(reward_ids)
                segment = random.choice(SEGMENTS)
                has_bet_rules = tmpl["target_bets"] > 0

                row = {
                    "PromotionId": promo_id,
                    "PromotionName": f"{tmpl['name']} {suffix}",
                    "PromotionDescription": tmpl["desc"],
                    "BrandId": brand["BrandId"],
                    "IsSegmented": segment,
                    "PromotionRequiresOptIn": tmpl["requires_optin"],
                    "PromotionKey": f"PROMO-{promo_id:04d}",
                    "RewardId": reward_id,
                    "BetValidationRulesName": (
                        f"Rule_{tmpl['type']}_{promo_id}" if has_bet_rules else None
                    ),
                    "BetValidationRulesExpression": (
                        f"bets >= {tmpl['target_bets']} AND stake >= {tmpl['target_stake']}"
                        if has_bet_rules
                        else None
                    ),
                    "ValidationTargetBetsPlaced": float(tmpl["target_bets"]),
                    "ValidationTargetAmountStaked": tmpl["target_stake"],
                    "MaxRedemptions": float(tmpl["max_redemptions"]),
                    "MaxRedemptionsPerUser": float(tmpl["max_per_user"]),
                }
                tz = brand["tz_offset_hours"]
                _add_tz_variants(row, "StartDate", s, tz)
                _add_tz_variants(row, "EndDate", e, tz)
                rows.append(row)

    return pd.DataFrame(rows)


def _promotion_instances(tmpl, month, month_start):
    """Return (start, end, suffix) tuples for a template within a month."""
    results = []
    if tmpl["recurrence"] == "weekly":
        for week in range(4):
            s = month_start + timedelta(weeks=week)
            e = s + timedelta(days=tmpl["duration_days"])
            results.append((s, e, f"W{month * 4 + week + 1}"))
    elif tmpl["recurrence"] == "monthly":
        s = month_start
        e = s + timedelta(days=tmpl["duration_days"])
        results.append((s, e, f"M{month + 1}"))
    elif tmpl["recurrence"] == "once" and month == 0:
        s = month_start
        e = s + timedelta(days=tmpl["duration_days"])
        results.append((s, e, ""))
    elif tmpl["recurrence"] == "event":
        n_events = random.randint(1, 3)
        for ev in range(n_events):
            s = month_start + timedelta(days=random.randint(0, 20))
            e = s + timedelta(days=tmpl["duration_days"])
            results.append((s, e, f"E{month * 3 + ev + 1}"))
    return results


def generate_promotion_user(
    promos_df: pd.DataFrame, n_users: int
) -> pd.DataFrame:
    """Generate user participation records per promotion.

    Users are assigned an affinity profile that controls how likely they
    are to appear in any given promotion, creating realistic cohorts:
      - ~15% of users never participate (affinity = 0)
      - ~25% participate in very few promos (affinity low)
      - ~35% are moderate participants
      - ~25% are heavy promo users
    """
    rows = []
    user_ids = list(range(1, n_users + 1))
    now = datetime(2026, 2, 21)

    # Assign affinity per user (probability of being eligible for any promo)
    # Using a mixture: some zeros + beta distribution for the rest
    user_affinity = {}
    for uid in user_ids:
        r = random.random()
        if r < 0.15:
            # Never participates in promos
            user_affinity[uid] = 0.0
        elif r < 0.40:
            # Low engagement: appears in ~2-8% of promos
            user_affinity[uid] = np.random.beta(1.2, 15)
        elif r < 0.75:
            # Moderate: appears in ~10-25% of promos
            user_affinity[uid] = np.random.beta(3, 12)
        else:
            # Heavy promo users: appears in ~25-60% of promos
            user_affinity[uid] = np.random.beta(5, 5)

    for _, promo in promos_df.iterrows():
        # Each user independently decides to be in this promo based on affinity
        eligible_users = [
            uid for uid in user_ids if random.random() < user_affinity[uid]
        ]

        promo_start = promo["StartDateUtc"]
        promo_end = promo["EndDateUtc"]
        requires_optin = promo["PromotionRequiresOptIn"]

        for uid in eligible_users:
            # Determine promotion state
            if promo_end < now:
                state = random.choices(
                    PROMOTION_STATES, weights=[0.05, 0.55, 0.35, 0.05]
                )[0]
            else:
                state = random.choices(
                    PROMOTION_STATES, weights=[0.60, 0.20, 0.05, 0.15]
                )[0]

            # Opt-in logic
            user_opted_in = False
            optin_utc = None
            if requires_optin:
                user_opted_in = random.random() < 0.45
                if user_opted_in:
                    days_range = max(1, (promo_end - promo_start).days)
                    optin_utc = promo_start + timedelta(
                        days=random.randint(0, min(3, days_range - 1)),
                        hours=random.randint(8, 22),
                        minutes=random.randint(0, 59),
                    )
            else:
                user_opted_in = True
                optin_utc = promo_start + timedelta(
                    hours=random.randint(0, 12)
                )

            # Qualification and confirmed bets
            target_bets = int(promo["ValidationTargetBetsPlaced"])
            if user_opted_in and state["id"] in (1, 2):
                if state["id"] == 2:  # Completed
                    confirmed_bets = target_bets + random.randint(0, 3)
                    confirmed_stake = round(
                        promo["ValidationTargetAmountStaked"]
                        * random.uniform(1.0, 2.5),
                        2,
                    )
                else:  # Active
                    confirmed_bets = random.randint(0, max(1, target_bets))
                    confirmed_stake = round(
                        promo["ValidationTargetAmountStaked"]
                        * random.uniform(0.2, 1.2),
                        2,
                    )
                qualification_count = 1 if confirmed_bets >= target_bets else 0
            else:
                confirmed_bets = 0
                confirmed_stake = 0.0
                qualification_count = 0

            row = {
                "PromotionId": promo["PromotionId"],
                "PromotionState": state["id"],
                "PromotionStateDescription": state["desc"],
                "UserId": uid,
                "IsSegmented": promo["IsSegmented"],
                "PromotionRequiresOptIn": requires_optin,
                "UserIsOptIn": user_opted_in,
                "RewardId": promo["RewardId"],
                "QualificationCount": qualification_count,
                "ConfirmedBetsPlaced": confirmed_bets,
                "ConfirmedGrossAmountStaked": confirmed_stake,
            }
            _add_tz_variants(row, "OptInDateTime", optin_utc)
            rows.append(row)

    return pd.DataFrame(rows)


def generate_reward_redeem_user(
    promo_user_df: pd.DataFrame, promos_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate reward issuance and redemption records for qualified users."""
    rows = []
    reward_item_id = 0

    qualified = promo_user_df[promo_user_df["QualificationCount"] > 0]

    # Index promos for fast lookup
    promos_idx = promos_df.set_index("PromotionId")

    for _, pu in qualified.iterrows():
        promo = promos_idx.loc[pu["PromotionId"]]
        reward_item_id += 1

        issued_type = random.choices(
            ISSUED_USER_TYPES, weights=[0.70, 0.15, 0.15]
        )[0]

        # Issued shortly after opt-in
        optin_date = pu["OptInDateTimeUtc"]
        if optin_date is not None and not pd.isna(optin_date):
            issued_utc = optin_date + timedelta(
                days=random.randint(1, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
        else:
            issued_utc = promo["StartDateUtc"] + timedelta(
                days=random.randint(3, 10),
                hours=random.randint(8, 20),
            )

        # ~70% redeem their reward
        redeemed = random.random() < 0.70
        redeemed_utc = None
        if redeemed:
            redeemed_utc = issued_utc + timedelta(
                days=random.randint(0, 14),
                hours=random.randint(0, 23),
            )

        row = {
            "PromotionId": pu["PromotionId"],
            "UserId": pu["UserId"],
            "RewardId": pu["RewardId"],
            "IssuedUserTypeId": issued_type["id"],
            "IssuedUserType": issued_type["name"],
            "BrandId": promo["BrandId"],
            "RewardItemId": reward_item_id,
        }
        _add_tz_variants(row, "IssuedOn", issued_utc)
        _add_tz_variants(row, "RedeemedOn", redeemed_utc)
        rows.append(row)

    return pd.DataFrame(rows)


def generate_reward_freebet(
    rewards_df: pd.DataFrame, redeem_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate freebet specifics for each issued reward item."""
    rows = []
    freebet_id = 0

    rewards_idx = rewards_df.set_index("RewardId")

    for _, redeem in redeem_df.iterrows():
        rid = redeem["RewardId"]
        if rid not in rewards_idx.index:
            continue
        reward = rewards_idx.loc[rid]
        reward_name = reward["RewardName"]

        # Determine freebet type and product by reward name
        if "Casino" in reward_name or "Tiradas" in reward_name:
            fb_type_key = "casino_bonus" if "Casino" in reward_name else "free_spins"
            product_key = "casino"
        elif "Live" in reward_name:
            fb_type_key = "live"
            product_key = "live_sports"
        elif "Cashback" in reward_name:
            fb_type_key = "cashback"
            product_key = "sports"
        else:
            fb_type_key = "standard"
            product_key = "sports"

        fb = FREEBET_TYPES[fb_type_key]
        prod = PRODUCTS[product_key]
        freebet_id += 1

        # Amount from reward name or random
        amounts = [5.0, 10.0, 15.0, 25.0, 50.0]
        amount = random.choice(amounts) if "Tiradas" not in reward_name else 0.0

        rows.append(
            {
                "RewardId": rid,
                "RewardName": reward_name,
                "Amount": amount,
                "FreebetId": freebet_id,
                "RewardItemId": redeem["RewardItemId"],
                "RewardItemType": fb["id"],
                "FreebetTypeCode": fb["code"],
                "FreebetTypeId": fb["id"],
                "FreebetTypeName": fb["name"],
                "ProductsCriteriaCode": prod["code"],
                "ProductCode": prod["code"],
                "ProductId": prod["id"],
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic BonusEngine data"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=2000,
        help="Number of users (default: 2000)",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Months of data (default: 6)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2025-08-21",
        help="Start date YYYY-MM-DD (default: 2025-08-21)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/bonusengine",
        help="Output directory (default: data/bonusengine)",
    )
    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    os.makedirs(args.output_dir, exist_ok=True)

    print(
        f"Generating BonusEngine data: {args.users} users, "
        f"{args.months} months from {args.start_date}"
    )
    print("-" * 60)

    # 1. Rewards
    rewards_df = generate_reward_detail(start_date, args.months)
    print(f"  reward_detail:      {len(rewards_df):>8,} rows")

    # 2. Promotions (linked to rewards)
    promos_df = generate_promotion_detail(start_date, args.months, rewards_df)
    print(f"  promotion_detail:   {len(promos_df):>8,} rows")

    # 3. User participation (linked to promotions)
    promo_user_df = generate_promotion_user(promos_df, args.users)
    print(f"  promotion_user:     {len(promo_user_df):>8,} rows")

    # 4. Reward issuance/redemption (qualified users only)
    redeem_df = generate_reward_redeem_user(promo_user_df, promos_df)
    print(f"  reward_redeem_user: {len(redeem_df):>8,} rows")

    # 5. Freebet details (one per issued reward)
    freebet_df = generate_reward_freebet(rewards_df, redeem_df)
    print(f"  reward_freebet:     {len(freebet_df):>8,} rows")

    # Save CSVs
    print("-" * 60)
    for name, df in [
        ("promotion_detail", promos_df),
        ("promotion_user", promo_user_df),
        ("reward_detail", rewards_df),
        ("reward_redeem_user", redeem_df),
        ("reward_freebet", freebet_df),
    ]:
        path = os.path.join(args.output_dir, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"  Saved {path}")

    print("\nDone! Load into Databricks with:")
    print("  Run analysis/bonusengine/00_load_bonusengine_data.sql")


if __name__ == "__main__":
    main()
