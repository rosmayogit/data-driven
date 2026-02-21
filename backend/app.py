"""
Flask API that reads generated CSVs and serves data to the frontend.

Endpoints:
    GET /api/dashboard       - Dashboard metrics + top campaigns
    GET /api/campaigns       - All campaigns with stats
    GET /api/analytics       - Issuance trends + redemption by type
    GET /api/users           - User list with reward stats

Usage:
    pip install flask flask-cors pandas
    python backend/app.py
"""

import os
from datetime import datetime, timedelta

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
BE_DIR = os.path.join(DATA_DIR, "bonusengine")

# Type mappings: FreebetTypeCode -> frontend display type
FREEBET_TYPE_MAP = {
    "STD": "FreeBet",
    "LIVE": "FreeBet",
    "CSH": "Cash",
    "CBN": "CasinoBonus",
    "FSP": "FreeSpin",
}

# Promotion state mapping
STATE_MAP = {1: "Active", 2: "Completed", 3: "Expired", 4: "Cancelled"}
STATUS_DISPLAY = {1: "Active", 2: "Paused", 3: "Archived", 4: "Archived"}


def load_csv(path):
    """Load a CSV file, return empty DataFrame if not found."""
    full_path = os.path.join(BASE_DIR, path) if not os.path.isabs(path) else path
    if os.path.exists(full_path):
        return pd.read_csv(full_path, parse_dates=True)
    return pd.DataFrame()


def load_data():
    """Load all CSVs into memory."""
    data = {
        "users": load_csv("data/users.csv"),
        "promotions": load_csv("data/promotions.csv"),
        "funnel": load_csv("data/funnel.csv"),
        "bets": load_csv("data/bets.csv"),
        "daily_activity": load_csv("data/daily_activity.csv"),
        "promo_detail": load_csv("data/bonusengine/promotion_detail.csv"),
        "promo_user": load_csv("data/bonusengine/promotion_user.csv"),
        "reward_detail": load_csv("data/bonusengine/reward_detail.csv"),
        "reward_redeem": load_csv("data/bonusengine/reward_redeem_user.csv"),
        "reward_freebet": load_csv("data/bonusengine/reward_freebet.csv"),
    }

    # Parse date columns
    for col in ["IssuedOnUtc", "RedeemedOnUtc"]:
        if col in data["reward_redeem"].columns:
            data["reward_redeem"][col] = pd.to_datetime(
                data["reward_redeem"][col], errors="coerce"
            )

    for col in ["StartDateUtc", "EndDateUtc"]:
        if col in data["promo_detail"].columns:
            data["promo_detail"][col] = pd.to_datetime(
                data["promo_detail"][col], errors="coerce"
            )

    return data


# Load data at startup
DATA = load_data()


def _get_reward_type(reward_id):
    """Get the frontend display type for a reward."""
    fb = DATA["reward_freebet"]
    if fb.empty:
        return "FreeBet"
    match = fb[fb["RewardId"] == reward_id]
    if match.empty:
        return "FreeBet"
    code = match.iloc[0]["FreebetTypeCode"]
    return FREEBET_TYPE_MAP.get(code, "FreeBet")


def _build_campaign_stats():
    """Build campaign-level statistics from bonusengine data."""
    pd_detail = DATA["promo_detail"]
    pu = DATA["promo_user"]
    redeem = DATA["reward_redeem"]

    if pd_detail.empty:
        return []

    campaigns = []
    now = datetime.utcnow()

    for _, promo in pd_detail.iterrows():
        pid = promo["PromotionId"]

        # Users in this promotion
        promo_users = pu[pu["PromotionId"] == pid] if not pu.empty else pd.DataFrame()

        # Rewards issued/redeemed for this promotion
        promo_redeem = (
            redeem[redeem["PromotionId"] == pid]
            if not redeem.empty
            else pd.DataFrame()
        )

        issued = len(promo_redeem)
        redeemed = (
            promo_redeem["RedeemedOnUtc"].notna().sum() if not promo_redeem.empty else 0
        )

        # Active = issued but not redeemed and promo still running
        active_users = (
            promo_users[promo_users["PromotionState"] == 1].shape[0]
            if not promo_users.empty
            else 0
        )
        expired_users = (
            promo_users[promo_users["PromotionState"] == 3].shape[0]
            if not promo_users.empty
            else 0
        )

        # Determine campaign status
        end_date = promo.get("EndDateUtc")
        if pd.notna(end_date) and pd.Timestamp(end_date) < pd.Timestamp(now):
            status = "Archived"
        elif active_users > 0:
            status = "Active"
        else:
            status = "Paused"

        # Get reward type
        reward_type = _get_reward_type(promo["RewardId"])

        # Get amount info from reward_freebet
        fb = DATA["reward_freebet"]
        amount_mode = "Fixed"
        amount_value = "N/A"
        if not fb.empty:
            fb_match = fb[fb["RewardId"] == promo["RewardId"]]
            if not fb_match.empty:
                amt = fb_match.iloc[0]["Amount"]
                if amt > 0:
                    amount_value = f"{amt:.0f} EUR"
                else:
                    amount_value = "50 spins"

        redemption_rate = round(redeemed / issued * 100, 1) if issued > 0 else 0.0
        roi = round(1.0 + redemption_rate / 100, 1)

        campaigns.append(
            {
                "id": f"RW-{pid:04d}",
                "name": str(promo["PromotionName"]),
                "type": reward_type,
                "status": status,
                "amount": {"mode": amount_mode, "value": amount_value},
                "issued": int(issued),
                "redeemed": int(redeemed),
                "active": int(active_users),
                "expired": int(expired_users),
                "redemptionRate": redemption_rate,
                "roi": roi,
                "createdAt": str(promo.get("StartDateUtc", ""))[:10],
            }
        )

    return campaigns


@app.route("/api/dashboard")
def dashboard():
    """Dashboard metrics and top campaigns."""
    campaigns = _build_campaign_stats()
    redeem = DATA["reward_redeem"]

    active_count = sum(1 for c in campaigns if c["status"] == "Active")
    total_issued = sum(c["issued"] for c in campaigns)
    total_redeemed = sum(c["redeemed"] for c in campaigns)
    redemption_rate = (
        round(total_redeemed / total_issued * 100, 1) if total_issued > 0 else 0.0
    )

    # Rewards issued in last 7 days
    recent_issued = 0
    if not redeem.empty and "IssuedOnUtc" in redeem.columns:
        cutoff = pd.Timestamp.now().tz_localize(None) - pd.Timedelta(days=7)
        recent_issued = int(
            redeem[redeem["IssuedOnUtc"].dt.tz_localize(None) >= cutoff].shape[0]
            if redeem["IssuedOnUtc"].dt.tz is not None
            else redeem[redeem["IssuedOnUtc"] >= cutoff].shape[0]
        )

    # Format large numbers
    if recent_issued >= 1000:
        recent_label = f"{recent_issued / 1000:.1f}K"
    else:
        recent_label = str(recent_issued)

    avg_roi = round(
        sum(c["roi"] for c in campaigns) / len(campaigns), 1
    ) if campaigns else 0.0

    # Top 5 campaigns by issued
    top_campaigns = sorted(campaigns, key=lambda c: c["issued"], reverse=True)[:5]

    return jsonify(
        {
            "metrics": {
                "activeCampaigns": active_count,
                "rewardsIssued7d": recent_label,
                "redemptionRate": f"{redemption_rate}%",
                "avgROI": f"{avg_roi}x",
            },
            "topCampaigns": top_campaigns,
        }
    )


@app.route("/api/campaigns")
def campaigns():
    """All campaigns with stats."""
    all_campaigns = _build_campaign_stats()

    # Apply filters
    status = request.args.get("status", "all")
    search = request.args.get("search", "").lower()

    if status != "all":
        all_campaigns = [
            c for c in all_campaigns if c["status"].lower() == status.lower()
        ]

    if search:
        all_campaigns = [
            c for c in all_campaigns if search in c["name"].lower()
        ]

    return jsonify(all_campaigns)


@app.route("/api/analytics")
def analytics():
    """Issuance trends and redemption by reward type."""
    redeem = DATA["reward_redeem"]
    fb = DATA["reward_freebet"]
    period = request.args.get("period", "30d")

    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)

    # --- Issuance trends (daily, by type) ---
    issuance_data = []
    if not redeem.empty and "IssuedOnUtc" in redeem.columns:
        cutoff = pd.Timestamp.now().tz_localize(None) - pd.Timedelta(days=days)
        issued_col = redeem["IssuedOnUtc"]
        if issued_col.dt.tz is not None:
            issued_col = issued_col.dt.tz_localize(None)
        recent = redeem[issued_col >= cutoff].copy()

        if not recent.empty and not fb.empty:
            # Map RewardId to type via reward_freebet
            type_map = (
                fb.drop_duplicates("RewardId")
                .set_index("RewardId")["FreebetTypeCode"]
                .map(FREEBET_TYPE_MAP)
            )
            recent["rewardType"] = recent["RewardId"].map(type_map).fillna("FreeBet")
            recent["date"] = recent["IssuedOnUtc"].dt.strftime("%b %d")
            recent["date_sort"] = recent["IssuedOnUtc"].dt.date

            pivot = (
                recent.groupby(["date_sort", "date", "rewardType"])
                .size()
                .unstack(fill_value=0)
                .reset_index()
                .sort_values("date_sort")
            )

            for _, row in pivot.iterrows():
                entry = {"date": row["date"]}
                for rtype in ["FreeBet", "FreeSpin", "Cash", "CasinoBonus"]:
                    key = {
                        "FreeBet": "freeBets",
                        "FreeSpin": "freeSpins",
                        "Cash": "cash",
                        "CasinoBonus": "casinoBonus",
                    }[rtype]
                    entry[key] = int(row.get(rtype, 0))
                issuance_data.append(entry)

    # --- Redemption by type ---
    redemption_data = []
    if not redeem.empty and not fb.empty:
        type_map = (
            fb.drop_duplicates("RewardId")
            .set_index("RewardId")["FreebetTypeCode"]
            .map(FREEBET_TYPE_MAP)
        )
        redeem_typed = redeem.copy()
        redeem_typed["rewardType"] = (
            redeem_typed["RewardId"].map(type_map).fillna("FreeBet")
        )

        for rtype, display in [
            ("FreeBet", "Free Bet"),
            ("FreeSpin", "Free Spin"),
            ("Cash", "Cash"),
            ("CasinoBonus", "Casino Bonus"),
        ]:
            subset = redeem_typed[redeem_typed["rewardType"] == rtype]
            issued = len(subset)
            redeemed_count = int(subset["RedeemedOnUtc"].notna().sum())
            rate = round(redeemed_count / issued * 100) if issued > 0 else 0

            redemption_data.append(
                {
                    "type": display,
                    "issued": issued,
                    "redeemed": redeemed_count,
                    "rate": rate,
                }
            )

    return jsonify(
        {
            "issuanceData": issuance_data,
            "redemptionData": redemption_data,
        }
    )


@app.route("/api/users")
def users():
    """User list with reward stats."""
    users_df = DATA["users"]
    redeem = DATA["reward_redeem"]
    promo_user = DATA["promo_user"]
    search = request.args.get("search", "").lower()

    if users_df.empty:
        return jsonify([])

    result = []

    # Pre-compute user-level stats from redeem data
    user_issued = {}
    user_redeemed = {}
    user_active_rewards = {}

    if not redeem.empty:
        issued_counts = redeem.groupby("UserId").size()
        user_issued = issued_counts.to_dict()

        redeemed_counts = (
            redeem[redeem["RedeemedOnUtc"].notna()].groupby("UserId").size()
        )
        user_redeemed = redeemed_counts.to_dict()

        # Active rewards = issued but not redeemed
        active = redeem[redeem["RedeemedOnUtc"].isna()].groupby("UserId").size()
        user_active_rewards = active.to_dict()

    # Compute lifetime value from bets
    bets_df = DATA["bets"]
    user_ltv = {}
    if not bets_df.empty and "stake" in bets_df.columns:
        ltv = bets_df.groupby("user_id")["stake"].sum()
        user_ltv = ltv.to_dict()

    # Map segments
    segment_map = {"high_value": "VIP", "medium": "Returning", "low": "Returning", "new": "New"}

    for _, user in users_df.iterrows():
        uid = user["user_id"]
        segment = segment_map.get(user.get("segment", ""), "Regular")
        issued = user_issued.get(uid, 0)
        redeemed = user_redeemed.get(uid, 0)
        active = user_active_rewards.get(uid, 0)
        ltv = user_ltv.get(uid, 0.0)

        user_id_str = f"USR-{uid:04d}"
        name = f"User {uid}"
        email = f"user{uid}@example.com"

        # Apply search filter
        if search and search not in f"{user_id_str} {name} {email}".lower():
            continue

        result.append(
            {
                "id": user_id_str,
                "name": name,
                "email": email,
                "segment": segment,
                "activeRewards": int(active),
                "totalIssued": int(issued),
                "totalRedeemed": int(redeemed),
                "lifetimeValue": f"€{ltv:,.0f}",
            }
        )

    # Sort by lifetime value descending, limit to 100
    result.sort(key=lambda u: u["totalIssued"], reverse=True)
    return jsonify(result[:100])


@app.route("/api/reload", methods=["POST"])
def reload_data():
    """Reload CSVs from disk (after regenerating data)."""
    global DATA
    DATA = load_data()
    return jsonify({"status": "ok", "message": "Data reloaded"})


if __name__ == "__main__":
    print(f"Data directory: {DATA_DIR}")
    print(f"BonusEngine directory: {BE_DIR}")
    for name, df in DATA.items():
        print(f"  {name}: {len(df)} rows")
    print("\nStarting API on http://localhost:5000")
    app.run(debug=True, port=5000)
