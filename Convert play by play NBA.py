from IPython import get_ipython
get_ipython().magic('reset -sf')

import pandas as pd
import numpy as np

LEAGUE_NAME = "NBA"

# Get the first element of the dataframe, or return default if it is empty.
def get_first(x, default):
    return x.iloc[0] if not x.empty else default


# Load dataframe and rename to capital names with no spaces.
#df = pd.read_csv("SingleSheet_{} 17-18.csv".format(LEAGUE_NAME), index_col=None, error_bad_lines=False).rename(columns={
#    "Date": "DATE",
#    "Time": "TIME",
#    "Period": "PERIOD",
#    "Team": "TEAM",
#    "Move": "MOVE",
#    "Action Player": "PLAYER_1",
#    "Away Team": "AWAY_TEAM",
#    "Away Score": "AWAY_SCORE",
#    "Home Team": "HOME_TEAM",
#    "Home Score": "HOME_SCORE",
#    "Away Lineup": "AWAY_LINEUP",
#    "Home Lineup": "HOME_LINEUP"
# })

df = pd.read_csv("C:/Users/Lenovo_X1/Documents/Integral Value/App/Demo/From Daniel/SingleSheet_NBA NOV 2017-18.csv", low_memory=False)

df = df.rename(columns={"Date": "DATE", "Time": "TIME", "Period": "PERIOD", "Team": "TEAM", "Move": "MOVE", "Action Player": "PLAYER_1", "Away Team": "AWAY_TEAM", "Away Score": "AWAY_SCORE", "Home Team": "HOME_TEAM", "Home Score": "HOME_SCORE", "Away Lineup": "AWAY_LINEUP", "Home Lineup": "HOME_LINEUP"})
df.loc[df.AWAY_TEAM == "Bariach Herzliya", "AWAY_TEAM"] = "Bnei Rav-Bariach Herzliya"

df1 = pd.read_csv("C:/Users/Lenovo_X1/Documents/Integral Value/App/Demo/From Daniel/SingleSheet_NBA2 17-18.csv",\
                  low_memory=False)

dfs = []
chunksize = 10 ** 6
for chunk in pd.read_csv("C:/Users/Lenovo_X1/Documents/Integral Value/App/Demo/From Daniel/SingleSheet_NBA2 17-18.csv",\
                         chunksize=chunksize):
    dfs.append(chunk)

df1 = pd.concat(dfs)

df1.shape

df1 = df1.rename(columns={"Date": "DATE", "Time": "TIME", "Period": "PERIOD", "Team": "TEAM", "Move": "MOVE",\
                          "Action.Player": "PLAYER_1", "Away.Team": "AWAY_TEAM", "Away.Score": "AWAY_SCORE",\
                          "Home.Team": "HOME_TEAM", "Home.Score": "HOME_SCORE", "Away.Lineup": "AWAY_LINEUP",\
                          "Home.Lineup": "HOME_LINEUP"})

#list(df)
    
 #Fix Herzliya's name


# Fix TEAM field to proper team names
#team_info = pd.read_csv(".csv".format(LEAGUE_NAME), index_col=None, error_bad_lines=False).rename(columns={
#    "TEAM": "SHORT",
#    "HOME_TEAM": "FULL",
#})

## Remove Team Rows with a "MOVE"

team_info = pd.read_csv("C:/Users/Lenovo_X1/Documents/Integral Value/App/Demo/From Daniel/NBA Teams.csv", low_memory=False)    
team_info = team_info.rename(columns={"TEAM": "SHORT", "HOME_TEAM": "FULL"})


df1["TEAM"] = df1["TEAM"].map(team_info.set_index("SHORT")["FULL"])


# Creating a dataframe of unique players. Will contain name and team columns, and an index which will be the id.
unique_players = pd.concat([pd.DataFrame(df1.HOME_LINEUP.str.split("/").tolist(), index=df1.HOME_TEAM),
                            pd.DataFrame(df1.AWAY_LINEUP.str.split("/").tolist(), index=df1.AWAY_TEAM)])
unique_players = unique_players.stack().reset_index(level=1, drop=True).reset_index()
unique_players = unique_players.drop_duplicates().rename(columns={0: "NAME", "index": "TEAM"}).reset_index(drop=True)
unique_players.index += 100

# Replacing player names with their ids.
replacing_series = pd.Series(unique_players.index, index=[unique_players.TEAM, unique_players.NAME]).astype(str)
for team in replacing_series.index.get_level_values("TEAM").unique():
    for column in ["HOME", "AWAY"]:
        team_players = df[df[column + "_TEAM"] == team]["PLAYER_1"]
        df.loc[df[column + "_TEAM"] == team, "PLAYER_1"] = team_players.map(replacing_series.loc[team]).fillna(team_players)
        df.loc[df[column + "_TEAM"] == team, column + "_LINEUP"] = df[df[column + "_TEAM"] == team].apply(lambda row: "/".join(sorted([replacing_series[(team, p)] for p in row[column + "_LINEUP"].split("/")])), axis=1)

# Create a unique game id for every game.
df[["DATE", "TIME"]] = df[["DATE", "TIME"]].apply(pd.to_datetime)
df.sort_values("DATE", ascending=False, inplace=True)
df["GAME_ID"] = df.groupby(["DATE", "HOME_TEAM", "AWAY_TEAM"]).grouper.group_info[0] + 1

# Create play type dataframe and create column in main dataset.
play_types = pd.DataFrame(["No Play Type", "P&R Ball Handler", "P&R Roll Man", "Post-Up", "Spot-Up", "Hand-Off",
                           "Off-Screen", "Transition", "Cut", "ISO", "Offensive Rebound"], columns=["PLAY_TYPES"])
play_types = play_types.reset_index().rename(columns={"index": "PLAY_ID"}).set_index("PLAY_TYPES")

df["PLAY_TYPE"] = df.MOVE.apply(lambda x: get_first(play_types[play_types.index.isin(x.split(" > "))].PLAY_ID, 0))

# Create actions dataset.
# Actions dataframe will have these columns: index (name of the secondary action), PRIMARY_ACTION_ID, SECONDARY_ACTION_ID.
# Every action has a SECONDARY_ACTION_ID that is unique within the actions that have the same PRIMARY_ACTION_ID.
primary_actions = ["NONE", "SHOT", "FREE_THROW", "FOUL", "TURNOVER", "REBOUND", "SUBSTITUTION"]
actions = {
    primary_actions.index("SHOT"): ["Make 2 Pts", "Miss 2 Pts", "Make 3 Pts", "Miss 3 Pts"],
    primary_actions.index("FREE_THROW"): ["Made", "Missed"],
    primary_actions.index("FOUL"): ["Foul", "Non Shooting Foul"],
    primary_actions.index("TURNOVER"): ["Turnover"],
    primary_actions.index("REBOUND"): ["Offensive Rebound", "Defensive Rebound"],
    primary_actions.index("SUBSTITUTION"): ["Sub In", "Sub Out"]
}
action_labels = [
    "MADE2", "MISS2", "MADE3", "MISS3",
    "MADE_FT", "MISS_FT",
    "FOUL", "FOUL",
    "TOV",
    "OFF_REB", "DEF_REB",
    None, None
]

actions = {secondary_action: primary_id for primary_id, secondary_actions in actions.items() for secondary_action in secondary_actions}
actions = pd.DataFrame.from_dict({"ACTION": list(actions.keys()), "PRIMARY_ACTION_ID": list(actions.values())})
actions["SECONDARY_ACTION_ID"] = actions.groupby("PRIMARY_ACTION_ID").cumcount() + 1
actions["LABEL"] = pd.Series(action_labels).values
actions = actions.set_index("ACTION").sort_index()

# Create columns for action ids, by looking for the secondary actions in the move string.
df["PRIMARY_ACTION"] = df.MOVE.apply(lambda x: get_first(actions[actions.index.isin(x.split(" > "))].PRIMARY_ACTION_ID, 0))
df["SECONDARY_ACTION"] = df.MOVE.apply(lambda x: get_first(actions[actions.index.isin(x.split(" > "))].SECONDARY_ACTION_ID, 0))

# The keys are actions that affected the actions in their respective values.
additional_box_score_actions = {
    "Assist": ["Make 2 Pts", "Make 3 Pts", "Made"],
    "Block": ["Miss 2 Pts", "Miss 3 Pts", "Missed"],
    "Steal": ["Turnover"],
    "Personal Foul": ["Foul", "Non Shooting Foul"]
}

# Assign PLAYER_2 of the original action row with the player that did the additional action.
def handle_original_action(row, original_actions):
    primary_action_ids = actions[actions.index.isin(original_actions)].PRIMARY_ACTION_ID
    secondary_action_ids = actions[actions.index.isin(original_actions)].SECONDARY_ACTION_ID
    df.loc[(df.GAME_ID == row.GAME_ID) & (df.TIME == row.TIME) & df.PRIMARY_ACTION.isin(primary_action_ids) & df.SECONDARY_ACTION.isin(secondary_action_ids), "PLAYER_2"] = row.PLAYER_1


df["PLAYER_2"] = ""
for additional_action, original_actions in additional_box_score_actions.items():
    additional_df = df[df.MOVE.apply(lambda x: additional_action in x.split(" > "))]
    additional_df.apply(lambda x: handle_original_action(x, original_actions), axis=1)

# Remove duplicate rows.
df = df[
    ~df.MOVE.apply(lambda x: "|".join(additional_box_score_actions.keys()) in x.split(" > ")) &  # Rows with PLAYER_2 actions.
    (df.PRIMARY_ACTION != 0) &  # Rows that their action wasn't identified.
    ~(df.MOVE.str.startswith("Shot") & df.apply(
        lambda row: df[(df.GAME_ID == row.GAME_ID) & (df.TIME == row.TIME) & (df.PRIMARY_ACTION == primary_actions.index("SHOT"))].shape[0] > 1
        , axis=1)) &  # Rows with move strings that start with "Shot" and have another row for the shot.
    ~((df.PRIMARY_ACTION == primary_actions.index("REBOUND")) & ~df.MOVE.str.startswith("Misc")) &  # Non misc rows that were mistagged as rebounds (because of the "offensive rebound" play type).
    ~df.MOVE.str.startswith("Turnover >")  # Remove second row of the same turnover.
]

# Create possession counter column by comparing the team of the current row to the team of the next row.
df = df.sort_values(["GAME_ID", "PERIOD", "TIME"], ascending=[False, True, False]).reset_index(drop=True)
df["POSSESSIONS"] = (df.TEAM != df.TEAM.shift(1))
df.POSSESSIONS = df.groupby("GAME_ID").POSSESSIONS.cumsum()

# Mark end of possession
df["END_OF_POSSESSION"] = (df.POSSESSIONS != df.POSSESSIONS.shift(-1)).astype(int)

# Set first play type of each possession
df["FIRST_PLAY_TYPE"] = df.groupby(["GAME_ID", "POSSESSIONS"])["PLAY_TYPE"].transform("first")

# Mark events & count points
df["MADE2"] = 0
df["MISS2"] = 0
df["MADE3"] = 0
df["MISS3"] = 0
df["MADE_FT"] = 0
df["MISS_FT"] = 0
df["OFF_REB"] = 0
df["DEF_REB"] = 0
df["TOV"] = 0
df["FOUL"] = 0

for row in actions.iterrows():
    vals = row[1]
    if vals["LABEL"] is not None:
        df.loc[(df["PRIMARY_ACTION"] == vals["PRIMARY_ACTION_ID"]) & (df["SECONDARY_ACTION"] == vals["SECONDARY_ACTION_ID"]), vals["LABEL"]] += 1

df["POINTS_SCORED"] = df.apply(lambda r: r["MADE_FT"] + (2 * r["MADE2"]) + (3 * r["MADE3"]), axis=1)


def ParseTimeDifference(d):
    # If d is negative - turn to positive
    # If d is positive - start of new qtr
    secs = d.total_seconds()
    return secs * -1 if secs < 0 else 0

def qtr_first_action(r):
    action_time = r["TIME"]
    period = r["PERIOD"]
    start_time = action_time.replace(hour=period, minute=10, second=0)
    return ParseTimeDifference(action_time - start_time)

# Calculate time between actions
df["LEN_OF_PLAY"] = df["TIME"].diff().transform(lambda d: ParseTimeDifference(d))
qtr_starts = df.groupby(["GAME_ID", "PERIOD"]).head(1)
for i, d in qtr_starts.iterrows():
    df.loc[i, "LEN_OF_PLAY"] = qtr_first_action(d)

team_info["ROUNDS"] = 0

# Stat belong to
def CheckTeam(r):
    t = r["TEAM"]
    if r["DEF_REB"] == 1 or r["FOUL"] == 1:
        h = r["HOME_TEAM"]
        a = r["AWAY_TEAM"]
        return h if a in t else a
    return t


df["STAT_BELONG_TO"] = df.apply(CheckTeam, axis=1)

# Count round for each team
team_rounds = team_info.set_index('FULL').to_dict('dict')["ROUNDS"]

df.sort_values("DATE")

for g in df.groupby("GAME_ID"):
    game = g[1]
    h = game["HOME_TEAM"].iloc[0]
    a = game["AWAY_TEAM"].iloc[0]
    indexes = game.index
    team_rounds[h] += 1
    team_rounds[a] += 1
    df.loc[indexes, "HOME_TEAM_ROUND"] = team_rounds[h]
    df.loc[indexes, "AWAY_TEAM_ROUND"] = team_rounds[a]

# Format and save
df.drop("MOVE", axis=1, inplace=True)
df.DATE = df.DATE.dt.date
df.TIME = df.TIME.dt.time
df.groupby("GAME_ID").filter(lambda g: len(g) >= 200).to_csv("{}-play-by-play.csv".format(LEAGUE_NAME.lower().replace(" ", "-")), index=False)

unique_players.to_csv("{}-players.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))
pd.Series(primary_actions).to_csv("Primary action ids.csv")

actions.drop("LABEL", axis=1, inplace=True)
actions.to_csv("actions.csv")
 
