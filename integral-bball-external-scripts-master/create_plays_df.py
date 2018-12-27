import pandas as pd

LEAGUE_NAME = "Israeli League"

play_types = ["No Play Type", "P&R Ball Handler", "P&R Roll Man", "ISO", "Post-Up",
              "Spot-Up", "Off-Screen", "Hand-Off", "Transition", "Cut", "Offensive Rebound"]

players_ids = pd.read_csv("{}-players.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))
players_ids.rename(columns={"Unnamed: 0": "ID"}, inplace=True)

def GetPlayerID(name, team, backup_team):
    if name == "UNDETECTED":
        return 0

    player = players_ids[(players_ids["NAME"] == name) & (players_ids["TEAM"] == team)]

    # Sometimes there is a problem in the data and player show as belonging to opposite team, so check for that
    if len(player) == 0:
        player = players_ids[(players_ids["NAME"] == name) & (players_ids["TEAM"] == backup_team)]

    return str(player.iloc[0]["ID"])


df = pd.read_csv("SingleSheet_{} 17-18.csv".format(LEAGUE_NAME), index_col=None, error_bad_lines=False).rename(columns={
    "Date": "DATE",
    "Time": "TIME",
    "Period": "PERIOD",
    "Team": "TEAM",
    "Move": "MOVE",
    "Action Player": "PLAYER_1",
    "Away Team": "AWAY_TEAM",
    "Away Score": "AWAY_SCORE",
    "Home Team": "HOME_TEAM",
    "Home Score": "HOME_SCORE",
    "Away Lineup": "AWAY_LINEUP",
    "Home Lineup": "HOME_LINEUP"
})

# Remove unnecessary lines - Misc & Shot which don't describe free throw & Substitutions ("Player Movement")
df = df[(~df["MOVE"].str.contains("Misc|Player Movement")) & ~(df["MOVE"].str.contains("Shot") & ~df["MOVE"].str.contains("Free Throw"))]

# Fix Herzliya's name
df.loc[df.AWAY_TEAM == "Bariach Herzliya", "AWAY_TEAM"] = "Bnei Rav-Bariach Herzliya"

# Fix TEAM field to proper team names
team_info = pd.read_csv("{} Team Names Modifier.csv".format(LEAGUE_NAME), index_col=None, error_bad_lines=False).rename(columns={
    "TEAM": "SHORT",
    "HOME_TEAM": "FULL",
})
df["TEAM"] = df["TEAM"].transform(lambda t: team_info[team_info.SHORT == t]["FULL"].iloc[0])

# Create a unique game id for every game.
df[["DATE", "TIME"]] = df[["DATE", "TIME"]].apply(pd.to_datetime)
df.sort_values("DATE", ascending=False, inplace=True)
df["GAME_ID"] = df.groupby(["DATE", "HOME_TEAM", "AWAY_TEAM"]).grouper.group_info[0] + 1

# Remove corrupted games
df = df.groupby("GAME_ID").filter(lambda g: len(g) >= 200)

# Group by plays.
# All lines of the play have same time.
# Only exception is plays which start with "Offensive rebound" + "Run offense". In this case the next group is the matching play.
# To avoid this - Before grouping change the times of those rows to that of their play.
df.loc[df["MOVE"].str.contains("Run Offense"), "TIME"] = df["TIME"].shift(-1)
plays_groups = df.groupby(["GAME_ID", "TIME", "TEAM"])

plays_df = pd.DataFrame()
for pg in plays_groups:
    play = pd.Series(index=["DATE", "LINEUP","TEAM","OPPONENT_LINEUP","HOME_TEAM", "AWAY_TEAM", "GAME_ID", "HOME_TEAM_ROUND", "AWAY_TEAM_ROUND",
                            "ORIGIN_OFF_REB", "ORIGIN_PICK_ROLL_BALL_HANDLER", "ORIGIN_ISOLATION", "ORIGIN_POST_UP", "PLAYTYPE",
                            "FGM", "FGA", "3PM", "3PA", "FTM", "FTA", "TOV", "FOUL"])
    rows = pg[1]

    # Fill info
    first_row = rows.iloc[0]
    lineups = (first_row["HOME_LINEUP"], first_row["AWAY_LINEUP"]) if first_row["TEAM"] == first_row["HOME_TEAM"] else (first_row["AWAY_LINEUP"], first_row["HOME_LINEUP"])
    teams = (first_row["HOME_TEAM"], first_row["AWAY_TEAM"]) if first_row["TEAM"] == first_row["HOME_TEAM"] else (first_row["AWAY_TEAM"], first_row["HOME_TEAM"])

    play["DATE"] = first_row["DATE"].strftime('%Y-%m-%d')
    play["LINEUP"] = '/'.join(sorted([GetPlayerID(p, teams[0], teams[1]) for p in lineups[0].split('/')]))
    play["TEAM"] = first_row["TEAM"]
    play["OPPONENT_LINEUP"] = '/'.join(sorted([GetPlayerID(p, teams[1], teams[0]) for p in lineups[1].split('/')]))
    play["HOME_TEAM"] = first_row["HOME_TEAM"]
    play["AWAY_TEAM"] = first_row["AWAY_TEAM"]
    play["GAME_ID"] = first_row["GAME_ID"]

    # Get 'action' row - rows with a playtype
    action_rows = rows[rows["MOVE"].str.contains("|".join(play_types))]

    # If there weren't any (example: player fouled on start of possession without making a play)
    # then take rows where a player was involved (start with player number)
    if len(action_rows) == 0:
        action_rows = rows[rows["MOVE"].str.get(0).str.isdigit()]

    # If still no lines then this are unimportant lines
    if len(action_rows) == 0:
        continue

    # Set playtype indications
    first_action = action_rows.iloc[0]
    play["ORIGIN_OFF_REB"] = int("Offensive Rebound" in first_action["MOVE"])
    play["ORIGIN_PICK_ROLL_BALL_HANDLER"] = int("P&R Ball Handler" in first_action["MOVE"])
    play["ORIGIN_ISOLATION"] = int("ISO" in first_action["MOVE"])
    play["ORIGIN_POST_UP"] = int("Post-Up" in first_action["MOVE"])
    play["ORIGIN_PLAYER"] = GetPlayerID(first_action["PLAYER_1"], teams[0], teams[1])

    last_action = action_rows.iloc[-1]
    pts = [p for p in play_types if p in last_action["MOVE"]]
    play["PLAYTYPE"] = pts[0] if len(pts) else "NONE"
    play["FINISHING_PLAYER"] = GetPlayerID(last_action["PLAYER_1"], teams[0], teams[1])

    play["3PM"] = len(rows[rows["MOVE"].str.contains("Make 3 Pts")])
    play["3PA"] = len(rows[rows["MOVE"].str.contains("Miss 3 Pts")]) + play["3PM"]
    play["FGM"] = len(rows[rows["MOVE"].str.contains("Make 2 Pts")]) + play["3PM"]
    play["FGA"] = len(rows[rows["MOVE"].str.contains("Miss 2 Pts")]) + len(rows[rows["MOVE"].str.contains("Miss 3 Pts")]) + play["FGM"]
    play["FTM"] = len(rows[rows["MOVE"].str.contains("Free Throw > Made")])
    play["FTA"] = len(rows[rows["MOVE"].str.contains("Free Throw > Missed")])
    play["TOV"] = int(len(rows[rows["MOVE"].str.contains("Turnover")]) > 0)
    play["FOUL"] = int(len(rows[rows["MOVE"].str.contains("Foul")]) > 0)

    plays_df = plays_df.append(play, ignore_index=True)

# Set rounds
team_info["ROUNDS"] = 0
team_rounds = team_info.set_index('FULL').to_dict('dict')["ROUNDS"]

plays_df.sort_values("DATE")
games = plays_df.groupby("GAME_ID")

for g in games:
    game = g[1]
    h = game["HOME_TEAM"].iloc[0]
    a = game["AWAY_TEAM"].iloc[0]
    indexes = game.index
    team_rounds[h] += 1
    team_rounds[a] += 1
    plays_df.loc[indexes, "HOME_TEAM_ROUND"] = team_rounds[h]
    plays_df.loc[indexes, "AWAY_TEAM_ROUND"] = team_rounds[a]

plays_df.to_csv("{}-plays.csv".format(LEAGUE_NAME.lower().replace(" ", "-")), index=False)
