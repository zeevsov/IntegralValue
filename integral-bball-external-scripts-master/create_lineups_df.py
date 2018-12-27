import pandas as pd
import os
import itertools

LEAGUE_NAME = "Israeli League"


def get_presets(lineups_df):
    return [
        {
            "PRESET": "#1 Lineup",
            "LINEUP": lineups_df["Net Rating"].idxmax()
        },
        {
            "PRESET": "#1 Offensive",
            "LINEUP": lineups_df["Offensive Rating"].idxmax()
        },
        {
            "PRESET": "#1 Defensive",
            "LINEUP": lineups_df["Defensive Rating"].idxmin()
        },
        {
            "PRESET": "#1 Rebound",
            "LINEUP": lineups_df["Net Rating"].idxmax()
        },
        {
            "PRESET": "#1 Shooting",
            "LINEUP": lineups_df["Net Rating"].idxmax()
        },
        {
            "PRESET": "#1 3PT Defense",
            "LINEUP": lineups_df["Net Rating"].idxmax()
        },
        {
            "PRESET": "#1 Pick & Roll",
            "LINEUP": lineups_df["Net Rating"].idxmax()
        },
        {
            "PRESET": "#1 Pick & Roll Defense",
            "LINEUP": lineups_df["Net Rating"].idxmax()
        },
        {
            "PRESET": "#1 Fast Paced",
            "LINEUP": lineups_df["Net Rating"].idxmax()
        },
        {
            "PRESET": "#1 Against Big Man Lineup",
            "LINEUP": lineups_df["Net Rating"].idxmax()
        }
    ]

for i in range(1,6):
    # Load round dfs.
    round_df_filenames = filter(lambda x: "{}-{}p-lineups-round".format(LEAGUE_NAME.lower().replace(" ", "-"), i) in x, os.listdir())
    round_dfs = map(pd.read_csv, round_df_filenames)
    rounds_df = pd.concat(round_dfs)

    # Create lineup df with sums of stats from round dfs.
    play_types = ["PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION", "POST_UP",
                  "SPOT_UP", "OFF_SCREEN", "HAND_OFF", "TRANSITION", "CUT", "OFFENSIVE_REBOUND", "OFF_THE_BALL"]
    stat_columns = ["POINTS", "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT", "OFF_REB", "DEF_REB", "TOV", "FOUL", "FGA", "FGM",
                    "3PT_IN_POSS", "FT_IN_POSS"]

    sum_columns = ["POSSESSIONS"] + \
                  stat_columns + \
                  play_types + \
                  ["{}_{}".format(playtype, stat) for playtype, stat in list(itertools.product(play_types, stat_columns))]

    sum_columns += ["OPPONENT_" + column for column in sum_columns]
    sum_columns += ["SECONDS"]  # This is not separated to offense and defense

    rounds_lineups = rounds_df[sum_columns + ["LINEUP", "GAME_ID", "TEAM"]].groupby("LINEUP")
    lineups_df = rounds_lineups.sum()
    lineups_df.columns = lineups_df.columns.str.replace("MADE2", "2PM")
    lineups_df.columns = lineups_df.columns.str.replace("MADE3", "3PM")
    lineups_df.columns = lineups_df.columns.str.replace("MADE_FT", "FTM")
    lineups_df.rename(columns={"{}".format(t): "{}_POSSESSIONS".format(t) for t in play_types}, inplace=True)
    lineups_df.rename(columns={"OPPONENT_{}".format(t): "OPPONENT_{}_POSSESSIONS".format(t) for t in play_types}, inplace=True)
    lineups_df.drop("GAME_ID", axis=1, inplace=True)

    # Add basic info about lineups
    lineups_df.loc[rounds_lineups.groups, "GAMES_PLAYED"] = rounds_lineups["GAME_ID"].nunique()
    lineups_df.loc[rounds_lineups.groups, "TEAM"] = rounds_lineups.apply(lambda g: g.iloc[0]["TEAM"])

    # Add stats that are calculated from sums.
    lineups_df["OFF_RTG"] = (lineups_df["POINTS"] / lineups_df["POSSESSIONS"] * 100).fillna(0)
    lineups_df["DEF_RTG"] = (lineups_df["OPPONENT_POINTS"] / lineups_df["OPPONENT_POSSESSIONS"] * 100).fillna(0)
    lineups_df["NET_RTG"] = (lineups_df["OFF_RTG"] - lineups_df["DEF_RTG"]).fillna(0)
    lineups_df["PACE"] = (lineups_df["POSSESSIONS"] + lineups_df["OPPONENT_POSSESSIONS"]) / lineups_df["SECONDS"] * 48 * 60

    for playtype, sides in list(itertools.product([""] + [p + "_" for p in play_types], {"": "OPPONENT_", "OPPONENT_": ""}.items())):
        team = sides[0]
        opp = sides[1]
        lineups_df[team + playtype + "2PA"] = lineups_df[team + playtype + "2PM"] + lineups_df[team + playtype + "MISS2"]
        lineups_df[team + playtype + "3PA"] = lineups_df[team + playtype + "3PM"] + lineups_df[team + playtype + "MISS3"]
        lineups_df[team + playtype + "FTA"] = lineups_df[team + playtype + "FTM"] + lineups_df[team + playtype + "MISS_FT"]
        lineups_df[team + playtype + "FG%"] = lineups_df[team + playtype + "FGM"] / lineups_df[team + playtype + "FGA"]
        lineups_df[team + playtype + "3PT%"] = lineups_df[team + playtype + "3PM"] / lineups_df[team + playtype + "3PA"]
        lineups_df[team + playtype + "FT%"] = lineups_df[team + playtype + "FTM"] / lineups_df[team + playtype + "FTA"]
        lineups_df[team + playtype + "eFG%"] = (lineups_df[team + playtype + "FGM"] + (0.5 * lineups_df[team + playtype + "3PM"])) / lineups_df[team + playtype + "FGA"]
        lineups_df[team + playtype + "TS%"] = lineups_df[team + playtype + "POINTS"] / (2 * (lineups_df[team + playtype + "FGA"] + 0.44 * lineups_df[team + playtype + "FTA"]))
        lineups_df[team + playtype + "OFF_REB%"] = lineups_df[team + playtype + "OFF_REB"] / (lineups_df[team + playtype + "OFF_REB"] + lineups_df[opp + playtype + "DEF_REB"])
        lineups_df[team + playtype + "DEF_REB%"] = lineups_df[team + playtype + "DEF_REB"] / (lineups_df[team + playtype + "DEF_REB"] + lineups_df[opp + playtype + "OFF_REB"])
        lineups_df[team + playtype + "3PT_FREQ"] = lineups_df[team + playtype + "3PT_IN_POSS"] / lineups_df[team + playtype + "POSSESSIONS"]
        lineups_df[team + playtype + "FT_RATE"] = lineups_df[team + playtype + "FT_IN_POSS"] / lineups_df[team + playtype + "POSSESSIONS"]
        lineups_df[team + playtype + "TOV_RATE"] = lineups_df[team + playtype + "TOV"] / lineups_df[team + playtype + "POSSESSIONS"]
        lineups_df[team + playtype + "PPP"] = lineups_df[team + playtype + "POINTS"] / lineups_df[team + playtype + "POSSESSIONS"]
        lineups_df[team + playtype + "FREQ"] = lineups_df[team + playtype + "POSSESSIONS"] / sum([lineups_df[team + pt + "_POSSESSIONS"] for pt in play_types])


    # Add median/variance stats.
    min_relevant_games = 5

    median_groupby = rounds_df[(rounds_df["POSSESSIONS"] >= 3) & (rounds_df["OPPONENT_POSSESSIONS"] >= 3)].groupby("LINEUP")
    median_groupby = median_groupby.filter(lambda g: len(g) >= min_relevant_games).groupby("LINEUP")
    lineups_df.loc[median_groupby.groups, "NET_RTG_MEDIAN"] = median_groupby["NET_RTG"].median()
    lineups_df.loc[median_groupby.groups, "NET_RTG_MEAN"] = median_groupby["NET_RTG"].mean()
    lineups_df.loc[median_groupby.groups, "NET_RTG_SEM"] = median_groupby["NET_RTG"].sem()

    median_groupby = rounds_df[rounds_df["POSSESSIONS"] >= 3].groupby("LINEUP")
    median_groupby = median_groupby.filter(lambda g: len(g) >= min_relevant_games).groupby("LINEUP")
    lineups_df.loc[median_groupby.groups, "OFF_RTG_MEDIAN"] = median_groupby["OFF_RTG"].median()
    lineups_df.loc[median_groupby.groups, "OFF_RTG_MEAN"] = median_groupby["OFF_RTG"].mean()
    lineups_df.loc[median_groupby.groups, "OFF_RTG_SEM"] = median_groupby["OFF_RTG"].sem()

    median_groupby = rounds_df[rounds_df["OPPONENT_POSSESSIONS"] >= 3].groupby("LINEUP")
    median_groupby = median_groupby.filter(lambda g: len(g) >= min_relevant_games).groupby("LINEUP")
    lineups_df.loc[median_groupby.groups, "DEF_RTG_MEDIAN"] = median_groupby["DEF_RTG"].median()
    lineups_df.loc[median_groupby.groups, "DEF_RTG_MEAN"] = median_groupby["DEF_RTG"].mean()
    lineups_df.loc[median_groupby.groups, "DEF_RTG_SEM"] = median_groupby["DEF_RTG"].sem()

    median_groupby = rounds_df[rounds_df["OFF_REB"] + rounds_df["OPPONENT_DEF_REB"] >= 3].groupby("LINEUP")
    median_groupby = median_groupby.filter(lambda g: len(g) >= min_relevant_games).groupby("LINEUP")
    lineups_df.loc[median_groupby.groups, "OFF_REB%_MEDIAN"] = median_groupby["OFF_REB%"].median()

    median_groupby = rounds_df[rounds_df["DEF_REB"] + rounds_df["OPPONENT_OFF_REB"] >= 3].groupby("LINEUP")
    median_groupby = median_groupby.filter(lambda g: len(g) >= min_relevant_games).groupby("LINEUP")
    lineups_df.loc[median_groupby.groups, "DEF_REB%_MEDIAN"] = median_groupby["DEF_REB%"].median()

    median_groupby = rounds_df[rounds_df["OPPONENT_POSSESSIONS"] >= 3].groupby("LINEUP")
    median_groupby = median_groupby.filter(lambda g: len(g) >= min_relevant_games).groupby("LINEUP")
    lineups_df.loc[median_groupby.groups, "DEF_RTG_MEDIAN"] = median_groupby["DEF_RTG"].median()

    for playtype, team in itertools.product(play_types, ["", "OPPONENT_"]):
        median_groupby = rounds_df[rounds_df[team + playtype] >= 3].groupby("LINEUP")
        median_groupby = median_groupby.filter(lambda g: len(g) >= min_relevant_games).groupby("LINEUP")
        lineups_df.loc[median_groupby.groups, team + playtype + "_PPP_MEDIAN"] = median_groupby[team + playtype + "_PPP"].median()
        lineups_df.loc[median_groupby.groups, team + playtype + "_PPP_MEAN"] = median_groupby[team + playtype + "_PPP"].mean()
        lineups_df.loc[median_groupby.groups, team + playtype + "_PPP_SEM"] = median_groupby[team + playtype + "_PPP"].sem()
        lineups_df.loc[median_groupby.groups, team + playtype + "_TOV_RATE_MEDIAN"] = median_groupby[team + playtype + "_TOV_RATE"].median()
        lineups_df.loc[median_groupby.groups, team + playtype + "_FT_RATE_MEDIAN"] = median_groupby[team + playtype + "_FT_RATE"].median()

        median_groupby = rounds_df[rounds_df[team + playtype + "_FGA"] >= 3].groupby("LINEUP")
        median_groupby = median_groupby.filter(lambda g: len(g) >= min_relevant_games).groupby("LINEUP")
        lineups_df.loc[median_groupby.groups, team + playtype + "_eFG%_MEDIAN"] = median_groupby[team + playtype + "_eFG%"].median()

    # Save
    lineups_df.fillna(0).to_csv("{}-{}p-lineups.csv".format(LEAGUE_NAME.lower().replace(" ", "-"), i))
