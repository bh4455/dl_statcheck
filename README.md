# Deadlock Hero Stats Tracker

A command-line tool that pulls player match history from the
[StatLocker](https://statlocker.gg) API and generates per-hero performance
summaries for [Deadlock](https://store.steampowered.com/app/1422450/Deadlock/)
players.

## What It Does

For each player (by Steam ID), the tool:

1. Fetches all available match history from StatLocker's API
2. Groups matches by hero and computes aggregate stats
3. Outputs a CSV with per-hero breakdowns sorted by games played

### Metrics

| Column       | Description                                                              |
| ------------ | ------------------------------------------------------------------------ |
| **Hero**     | Hero name (mapped from internal hero IDs)                                |
| **Games**    | Total matches played on that hero                                        |
| **WR%**      | Win rate as a percentage                                                 |
| **Avg MVP**  | Average in-match global rank (1-12 scale, lower = better; 1 = match MVP) |
| **Avg KDA**  | Average (Kills + Assists) / Deaths ratio                                 |
| **Analysis** | Left blank for manual annotation (e.g., Pick/Ban/Open recommendations)   |

## Requirements

- Python 3.7+
- `requests` library (`pip install requests`)

## Usage

### Basic — single player

```bash
python tracker.py 884260993
```

### Multiple players

```bash
python tracker.py 884260993 123456789 987654321
```

Each Steam ID is a separate argument. Stats for each player are grouped together
in the output.

### Limit to top K heroes

Use `-k` / `--top` to only include the most-played heroes per player:

```bash
# Top 5 heroes per player
python tracker.py 884260993 -k 5

# Top 10 heroes for multiple players
python tracker.py 884260993 123456789 -k 10
```

### Custom output file

Use `-o` / `--output` to specify the output CSV filename (default: `stats.csv`):

```bash
python tracker.py 884260993 -o my_team_stats.csv
```

### Full example

```bash
python tracker.py 884260993 123456789 987654321 -k 8 -o scrim_prep.csv
```

This fetches stats for three players, limits to their top 8 heroes each, and
saves to `scrim_prep.csv`.

## Output Format

The CSV is structured for easy viewing in Excel or Google Sheets:

```
PlayerName1
Hero,Games,WR%,Avg MVP,Avg KDA,Analysis
Dynamo,113,60.2%,5.8,3.85,
Paige,86,53.5%,6.1,5.15,
Mina,78,52.6%,6.4,2.54,

PlayerName2
Hero,Games,WR%,Avg MVP,Avg KDA,Analysis
...
```

Players are separated by blank lines. The **Analysis** column is intentionally
left empty for you to fill in with pick/ban/open recommendations or other notes.

## Finding Steam IDs

Your Steam ID (also called Account ID) can be found on your StatLocker profile
URL:

```
https://statlocker.gg/profile/884260993
                              ^^^^^^^^^
                              This is your Steam ID
```

## How It Works

The tool makes two API calls per player:

1. **`/concise?limit=1`** — A lightweight request to get the player's total
   match count
2. **`/concise?limit={total}`** — Fetches the full match history

### Win detection

Wins are derived by comparing `match_result` to `player_team`. If the result
matches the player's team number, it's a win.

### MVP calculation

The `globalRank` field represents the player's performance rank within a match
(1 = best, 12 = worst). This is averaged across all matches where the field is
available. Some older matches may lack this data and are excluded from the MVP
average.

### KDA calculation

Computed from raw per-match stats:
`(player_kills + player_assists) / player_deaths`. Deaths of 0 are treated as 1
to avoid division errors.

## Limitations

- **Match history depth varies by account.** StatLocker may not have data for
  all matches, especially those played before the player registered on the site.
  The tool reports how many matches it actually fetched vs. the total.
- **MVP data may be missing on older matches.** The average is computed only
  over matches that have the `globalRank` field.
- **Player names** are fetched from the StatLocker steam profile endpoint. If
  unavailable, the Steam ID is used as a fallback.
- **The Analysis column is manual.** There is no API data for pick/ban/open
  recommendations — this is left for you to fill in based on your team's
  strategy.

## API Endpoints Used

| Endpoint                                         | Purpose                            |
| ------------------------------------------------ | ---------------------------------- |
| `/api/profile/data/matches/{id}/concise?limit=N` | Match history with per-match stats |
| `/api/profile/steam-profile/{id}`                | Player display name                |
