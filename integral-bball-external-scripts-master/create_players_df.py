import pandas as pd

LEAGUE_NAME = "Israeli League"

players_ids = pd.read_csv("{}-players.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))
players_ids.rename(columns={"Unnamed: 0": "ID"}, inplace=True)

on_court = pd.read_csv("{}-1p-lineups.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))
on_court.set_index("LINEUP", inplace=True)
if 0 in on_court.index:  # 0 = UNDETECTED player
    on_court.drop(0, inplace=True)

# Init df with ID, Name, Team
players_df = players_ids.set_index("ID")

# Take info
players_df.loc[on_court.index, "SECONDS"] = on_court["SECONDS"]
players_df.loc[on_court.index, "POSSESSIONS"] = on_court["POSSESSIONS"]
players_df.loc[on_court.index, "OPPONENT_POSSESSIONS"] = on_court["OPPONENT_POSSESSIONS"]

# Set origin stats
plays_df = pd.read_csv("{}-plays.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))
origin = plays_df.groupby("ORIGIN_PLAYER").sum()
if 0 in origin.index:  # 0 = UNDETECTED player
    origin.drop(0, inplace=True)
players_df.loc[origin.index, "ORIGIN_OFF_REB"] = origin["ORIGIN_OFF_REB"]
players_df.loc[origin.index, "ORIGIN_PICK_ROLL_BALL_HANDLER"] = origin["ORIGIN_PICK_ROLL_BALL_HANDLER"]
players_df.loc[origin.index, "ORIGIN_ISOLATION"] = origin["ORIGIN_ISOLATION"]
players_df.loc[origin.index, "ORIGIN_POST_UP"] = origin["ORIGIN_POST_UP"]

for play in ["OFF_REB", "PICK_ROLL_BALL_HANDLER", "ISOLATION", "POST_UP"]:
    origin_stats = plays_df[plays_df["ORIGIN_{}".format(play)] == 1].groupby("ORIGIN_PLAYER").sum()
    if 0 in origin_stats.index:  # 0 = UNDETECTED player
        origin_stats.drop(0, inplace=True)
    players_df.loc[origin_stats.index, "{}_POINTS".format(play)] = 2 * origin_stats["FGM"] + origin_stats["3PM"] + origin_stats["FTM"]

    players_df["{}_FREQ".format(play)] = players_df["ORIGIN_{}".format(play)] / players_df["POSSESSIONS"]
    players_df["{}_PPP".format(play)] = players_df["{}_POINTS".format(play)] / players_df["ORIGIN_{}".format(play)]

# Set individual stats
finishing = plays_df.groupby("FINISHING_PLAYER").sum()
if 0 in finishing.index:  # 0 = UNDETECTED player
    finishing.drop(0, inplace=True)
players_df.loc[finishing.index, "3PM"] = finishing["3PM"]
players_df.loc[finishing.index, "3PA"] = finishing["3PA"]
players_df.loc[finishing.index, "FGM"] = finishing["FGM"]
players_df.loc[finishing.index, "FGA"] = finishing["FGA"]
players_df.loc[finishing.index, "FTM"] = finishing["FTM"]
players_df.loc[finishing.index, "FTA"] = finishing["FTA"]
players_df.loc[finishing.index, "TOV"] = finishing["TOV"]
players_df.loc[finishing.index, "FOULS_DRAWN"] = finishing["FOUL"]

players_df["3PT%"] = players_df["3PM"] / players_df["3PA"]
players_df["FG%"] = players_df["FGM"] / players_df["FGA"]
players_df["FT%"] = players_df["FTM"] / players_df["FTA"]
players_df["eFG%"] = (players_df["FGM"] + (0.5 * players_df["3PM"])) / players_df["FGA"]
players_df["OFF_REB"] = players_df["ORIGIN_OFF_REB"]  # Every time the player took an off reb it started a play. Duplicate stat is for convenience.
players_df["DEF_REB"] = 0  # TODO: We don't have this stat at the moment

# Set team stats
on_court.drop(["SECONDS", "POSSESSIONS", "OPPONENT_POSSESSIONS"], axis=1, inplace=True)
columns = ["TEAM_{}".format(c) if "OPPONENT" not in c else c for c in on_court.columns]
players_df = pd.concat([players_df, pd.DataFrame(columns=columns)], sort=True)
on_court.columns = columns
players_df.loc[on_court.index, columns] = on_court[columns]

players_df.reset_index().rename(columns={"index":"ID"}).fillna(0).to_csv("{}-players-stats.csv".format(LEAGUE_NAME.lower().replace(" ", "-")), index=False)
