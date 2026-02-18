import requests
import argparse
import csv
from collections import defaultdict
from datetime import datetime

HERO_ID_MAPPINGS = {1: 'Infernus', 2: 'Seven', 3: 'Vindicta', 4: 'Lady Geist',
                    6: 'Abrams', 7: 'Wraith', 8: 'McGinnis', 10: 'Paradox',
                    11: 'Dynamo', 12: 'Kelvin', 13: 'Haze', 14: 'Holliday',
                    15: 'Bebop', 16: 'Calico', 17: 'Grey Talon', 18: 'Mo & Krill',
                    19: 'Shiv', 20: 'Ivy', 21: 'Kali', 25: 'Warden', 27: 'Yamato',
                    31: 'Lash', 35: 'Viscous', 38: 'Gunslinger', 39: 'The Boss',
                    47: 'Tokamak', 48: 'Wrecker', 49: 'Rutger', 50: 'Pocket',
                    51: 'Thumper', 52: 'Mirage', 53: 'Fathom', 54: 'Cadence',
                    56: 'Bomber', 57: 'Shield Guy', 58: 'Vyper', 59: 'Vandal',
                    60: 'Sinclair', 61: 'Trapper', 62: 'Raven', 63: 'Mina',
                    64: 'Drifter', 65: 'Venator', 66: 'Victor', 67: 'Paige',
                    68: 'Boho', 69: 'The Doorman', 70: 'Skyrunner', 71: 'Swan',
                    72: 'Billy', 73: 'Druid', 74: 'Graf', 75: 'Fortuna',
                    76: 'Graves', 77: 'Apollo', 78: 'Airheart', 79: 'Rem',
                    80: 'Silver', 81: 'Celeste', 82: 'Opera'}


def get_player_name(steam_id):
    try:
        resp = requests.get(f"https://statlocker.gg/api/profile/steam-profile/{steam_id}")
        resp.raise_for_status()
        data = resp.json()
        return data.get("personaname") or data.get("name") or str(steam_id)
    except Exception:
        return str(steam_id)


def generate_summary(steam_id, top_k=None):
    resp = requests.get(f"https://statlocker.gg/api/profile/data/matches/{steam_id}/true?gameMode=1")
    resp.raise_for_status()
    data = resp.json()
    matches = data["matchHistory"]
    total = data["profileAggregateStats"]["totalMatches"]
    print(f"  Fetched {len(matches)} / {total} matches")

    heroes = defaultdict(lambda: {"games": 0, "wins": 0, "mvp_total": 0, "mvp_count": 0, "kda_total": 0})

    for m in matches:
        hero_id = m["hero_id"]
        h = heroes[hero_id]
        h["games"] += 1

        won = (m["match_result"] == m["player_team"])
        h["wins"] += 1 if won else 0

        mvp = m.get("globalRank")
        if mvp:
            h["mvp_total"] += mvp
            h["mvp_count"] += 1

        deaths = m.get("player_deaths", 1) or 1
        kda = (m.get("player_kills", 0) + m.get("player_assists", 0)) / deaths
        h["kda_total"] += kda

    summary = []
    for hero_id, stats in heroes.items():
        g = stats["games"]
        hero_name = HERO_ID_MAPPINGS.get(hero_id, f"Unknown ({hero_id})")
        summary.append({
            "hero_name": hero_name,
            "games": g,
            "win_rate": round(stats["wins"] / g * 100, 1),
            "avg_mvp": round(stats["mvp_total"] / stats["mvp_count"], 1) if stats["mvp_count"] else None,
            "avg_kda": round(stats["kda_total"] / g, 2),
        })

    summary.sort(key=lambda x: x["games"], reverse=True)

    if top_k:
        summary = summary[:top_k]

    player_name = get_player_name(steam_id)
    return player_name, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deadlock hero stats from StatLocker")
    parser.add_argument("steam_ids", nargs="+", help="One or more Steam IDs")
    parser.add_argument("-k", "--top", type=int, default=None, help="Limit to top K heroes by games played")
    parser.add_argument("-o", "--output", default="stats.csv", help="Output CSV file (default: stats.csv)")
    args = parser.parse_args()

    results = []
    for raw_id in args.steam_ids:
        try:
            steam_id = int(raw_id)
        except ValueError:
            print(f"Skipping invalid ID: {raw_id}")
            continue

        print(f"\n=== {steam_id} ===")
        try:
            player_name, summary = generate_summary(steam_id, top_k=args.top)
            if summary:
                results.append((player_name, summary))
        except requests.RequestException as e:
            print(f"  API error: {e}")
        except Exception as e:
            print(f"  Error: {e}")

    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        for player_name, summary in results:
            writer.writerow([player_name])
            writer.writerow(["Hero", "Games", "WR%", "Avg MVP", "Avg KDA", "Analysis"])
            for s in summary:
                writer.writerow([
                    s["hero_name"],
                    s["games"],
                    f"{s['win_rate']}%",
                    s["avg_mvp"] or "N/A",
                    s["avg_kda"],
                    ""
                ])
            writer.writerow([])  # blank line between players

    print(f"\nSaved to {args.output}")