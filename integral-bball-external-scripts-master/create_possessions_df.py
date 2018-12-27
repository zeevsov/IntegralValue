import pandas as pd

LEAGUE_NAME = "Israeli League"

df = pd.read_csv("{}-play-by-play.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))

play_types = pd.DataFrame(["No Play Type", "P&R Ball Handler", "P&R Roll Man", "Post-Up", "Spot-Up", "Hand-Off",
                           "Off-Screen", "Transition", "Cut", "ISO", "Offensive Rebound"], columns=["PLAY_TYPES"])
play_types = play_types.reset_index().rename(columns={"index": "PLAY_ID"}).set_index("PLAY_TYPES")


def create_possession_row(poss):
    poss_columns = ["DATE", "GAME_ID", "HOME_TEAM_ROUND", "AWAY_TEAM_ROUND", "PERIOD",
                    "POSSESSION_ID", "TEAM_ON_OFFENSE", "TEAM_ON_DEFENSE", "OFFENSE_LINEUP", "DEFENSE_LINEUP",
                    "AWAY_TEAM", "AWAY_SCORE", "HOME_TEAM", "HOME_SCORE", "AWAY_LINEUP", "HOME_LINEUP",
                    "PRIMARY_PLAY", "PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION", "POST_UP",
                    "SPOT_UP", "OFF_SCREEN", "HAND_OFF", "TRANSITION", "CUT", "OFFENSIVE_REBOUND", "OFF_THE_BALL",
                    "POINTS_SCORED", "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT",
                    "OFF_REB", "DEF_REB", "TOV", "FOUL", "LENGTH_OF_POSSESSION",
                    "3PT_IN_POSS", "FT_IN_POSS", "FGM", "FGA"]
    row = pd.Series(index=poss_columns)

    # Copy basic info
    row[["DATE", "GAME_ID", "HOME_TEAM_ROUND", "AWAY_TEAM_ROUND", "PERIOD", "POSSESSION_ID", "AWAY_TEAM",
         "HOME_TEAM", "AWAY_LINEUP", "HOME_LINEUP", "PRIMARY_PLAY"]] = \
        poss.iloc[0][["DATE", "GAME_ID", "HOME_TEAM_ROUND", "AWAY_TEAM_ROUND", "PERIOD", "POSSESSIONS", "AWAY_TEAM",
                      "HOME_TEAM", "AWAY_LINEUP", "HOME_LINEUP", "FIRST_PLAY_TYPE"]]

    # Check off/def team
    is_home_off = row["HOME_TEAM"] in poss["TEAM"].iat[0]
    row["TEAM_ON_OFFENSE"] = row["HOME_TEAM"] if is_home_off else row["AWAY_TEAM"]
    row["TEAM_ON_DEFENSE"] = row["AWAY_TEAM"] if is_home_off else row["HOME_TEAM"]
    row["OFFENSE_LINEUP"] = row["HOME_LINEUP"] if is_home_off else row["AWAY_LINEUP"]
    row["DEFENSE_LINEUP"] = row["AWAY_LINEUP"] if is_home_off else row["HOME_LINEUP"]

    # Mark plays
    plays = poss["PLAY_TYPE"].unique()
    row["PICK_ROLL_BALL_HANDLER"] = int(play_types.loc["P&R Ball Handler"]["PLAY_ID"] in plays)
    row["PICK_ROLL_MAN"] = int(play_types.loc["P&R Roll Man"]["PLAY_ID"] in plays)
    row["ISOLATION"] = int(play_types.loc["ISO"]["PLAY_ID"] in plays)
    row["POST_UP"] = int(play_types.loc["Post-Up"]["PLAY_ID"] in plays)
    row["SPOT_UP"] = int(play_types.loc["Spot-Up"]["PLAY_ID"] in plays)
    row["OFF_SCREEN"] = int(play_types.loc["Off-Screen"]["PLAY_ID"] in plays)
    row["HAND_OFF"] = int(play_types.loc["Hand-Off"]["PLAY_ID"] in plays)
    row["TRANSITION"] = int(play_types.loc["Transition"]["PLAY_ID"] in plays)
    row["CUT"] = int(play_types.loc["Cut"]["PLAY_ID"] in plays)
    row["OFFENSIVE_REBOUND"] = int(play_types.loc["Offensive Rebound"]["PLAY_ID"] in plays)
    row["OFF_THE_BALL"] = row["OFF_SCREEN"] | row["CUT"]

    # Sum fields
    row[["POINTS_SCORED", "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT", "OFF_REB", "DEF_REB", "TOV", "FOUL",
         "LENGTH_OF_POSSESSION"]] = \
        poss[["POINTS_SCORED", "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT", "OFF_REB", "DEF_REB", "TOV",
              "FOUL", "LEN_OF_PLAY"]].sum()

    row["3PT_IN_POSS"] = int(row["MADE3"] + row["MISS3"] > 0)
    row["FT_IN_POSS"] = int(row["MADE_FT"] + row["MISS_FT"] > 0)
    row["FGM"] = row["MADE2"] + row["MADE3"]
    row["FGA"] = row["FGM"] + row["MISS2"] + row["MISS3"]

    # Calc score at beginning of possession
    row["AWAY_SCORE"] = poss["AWAY_SCORE"].iat[-1] - (0 if is_home_off else row["POINTS_SCORED"])
    row["HOME_SCORE"] = poss["HOME_SCORE"].iat[-1] - (row["POINTS_SCORED"] if is_home_off else 0)
    return row


possessions_df = df.groupby(["GAME_ID", "POSSESSIONS"]).apply(create_possession_row)

possessions_df[["PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION", "POST_UP",
                "SPOT_UP", "OFF_SCREEN", "HAND_OFF", "TRANSITION", "CUT", "OFFENSIVE_REBOUND",
                "POINTS_SCORED", "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT",
                "OFF_REB", "DEF_REB", "TOV", "FOUL"]] = \
    possessions_df[["PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION", "POST_UP",
                    "SPOT_UP", "OFF_SCREEN", "HAND_OFF", "TRANSITION", "CUT", "OFFENSIVE_REBOUND",
                    "POINTS_SCORED", "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT",
                    "OFF_REB", "DEF_REB", "TOV", "FOUL"]].apply(pd.to_numeric)

possessions_df.to_csv("{}-possessions.csv".format(LEAGUE_NAME.lower().replace(" ", "-")), index=False)
