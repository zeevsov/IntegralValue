import pandas as pd
import itertools

LEAGUE_NAME = "Israeli League"

possessions_df = pd.read_csv("{}-possessions.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))

play_types = ["PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION", "POST_UP",
              "SPOT_UP", "OFF_SCREEN", "HAND_OFF", "TRANSITION", "CUT", "OFFENSIVE_REBOUND", "OFF_THE_BALL"]
stat_columns = ["MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT", "OFF_REB", "DEF_REB", "TOV", "FOUL", "FGA", "FGM",
                "3PT_IN_POSS", "FT_IN_POSS"]
shared_columns = ["POSSESSIONS", "POINTS"] + \
                 stat_columns + \
                 play_types + \
                 ["{}_POINTS".format(t) for t in play_types] + \
                 ["{}_{}".format(playtype, stat) for playtype, stat in list(itertools.product(play_types, stat_columns))]

off_lineups_columns = ["LINEUP", "OFF_RTG", "OFF_TIME"] + shared_columns

def_lineups_columns = ["LINEUP", "DEF_RTG", "DEF_TIME"] + ["OPPONENT_{}".format(s) for s in shared_columns]

def GetLineupsDFs(r, side):
    r_lineups = []
    side_df = possessions_df[possessions_df["{}_TEAM_ROUND".format(side)] == r]
    teams = side_df.groupby("{}_TEAM".format(side))
    for t in teams:
        team_poss = t[1]

        offense_possesions = team_poss[team_poss["TEAM_ON_OFFENSE"] == team_poss["{}_TEAM".format(side)]]
        defense_possesions = team_poss[team_poss["TEAM_ON_OFFENSE"] != team_poss["{}_TEAM".format(side)]]
        # If corrupted game
        if len(offense_possesions) == 0 or len(defense_possesions) == 0:
            continue

        team_off_lineups = pd.DataFrame(columns=off_lineups_columns)
        team_def_lineups = pd.DataFrame(columns=def_lineups_columns)

        # region Offensive stats
        team_off_lineups["LINEUP"] = pd.Series(offense_possesions["{}_LINEUP".format(side)].unique())

        off_lineups = offense_possesions.groupby("{}_LINEUP".format(side))
        offense = off_lineups.sum().reset_index()
        team_off_lineups["POSSESSIONS"] = off_lineups.nunique().reset_index()["POSSESSION_ID"]

        team_off_lineups[["OFF_TIME", "3PT_IN_POSS", "FT_IN_POSS",
                          "PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION", "POST_UP", "SPOT_UP",
                          "OFF_SCREEN", "HAND_OFF", "TRANSITION", "CUT", "OFFENSIVE_REBOUND", "OFF_THE_BALL", "POINTS",
                          "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT", "OFF_REB", "DEF_REB", "TOV", "FOUL"]] = \
            offense[["LENGTH_OF_POSSESSION", "3PT_IN_POSS", "FT_IN_POSS",
                     "PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION", "POST_UP", "SPOT_UP",
                     "OFF_SCREEN", "HAND_OFF", "TRANSITION", "CUT", "OFFENSIVE_REBOUND", "OFF_THE_BALL", "POINTS_SCORED",
                     "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT", "MISS_FT", "OFF_REB", "DEF_REB", "TOV", "FOUL"]]

        team_off_lineups["OFF_RTG"] = 100 * team_off_lineups["POINTS"] / team_off_lineups["POSSESSIONS"]
        team_off_lineups["FGM"] = team_off_lineups["MADE2"] + team_off_lineups["MADE3"]
        team_off_lineups["FGA"] = team_off_lineups["FGM"] + team_off_lineups["MISS2"] + team_off_lineups["MISS3"]

        for tp in play_types:
            poss_with_playtype = off_lineups.apply(lambda l: l[l[tp] != 0].sum()).reset_index()

            team_off_lineups["{}_POINTS".format(tp)] = poss_with_playtype["POINTS_SCORED"]
            for stat in stat_columns:
                team_off_lineups["{}_{}".format(tp, stat)] = poss_with_playtype[stat]

            team_off_lineups["{}_PPP".format(tp)] = team_off_lineups["{}_POINTS".format(tp)] / team_off_lineups[tp]
            team_off_lineups["{}_TOV_RATE".format(tp)] = team_off_lineups["{}_TOV".format(tp)] / team_off_lineups[tp]
            team_off_lineups["{}_FT_RATE".format(tp)] = team_off_lineups["{}_FT_IN_POSS".format(tp)] / team_off_lineups[tp]
            team_off_lineups["{}_eFG%".format(tp)] = (team_off_lineups["{}_FGM".format(tp)] + 0.5 * team_off_lineups["{}_MADE3".format(tp)]) / team_off_lineups["{}_FGA".format(tp)]
        # endregion

        # region Defensive stats
        team_def_lineups["LINEUP"] = pd.Series(defense_possesions["{}_LINEUP".format(side)].unique())

        def_lineups = defense_possesions.groupby("{}_LINEUP".format(side))
        defense = def_lineups.sum().reset_index()
        team_def_lineups["OPPONENT_POSSESSIONS"] = def_lineups.nunique().reset_index()["POSSESSION_ID"]

        team_def_lineups[["DEF_TIME", "OPPONENT_3PT_IN_POSS", "OPPONENT_FT_IN_POSS",
                          "OPPONENT_PICK_ROLL_BALL_HANDLER", "OPPONENT_PICK_ROLL_MAN", "OPPONENT_ISOLATION",
                          "OPPONENT_POST_UP", "OPPONENT_SPOT_UP", "OPPONENT_OFF_SCREEN", "OPPONENT_HAND_OFF",
                          "OPPONENT_TRANSITION", "OPPONENT_CUT", "OPPONENT_OFFENSIVE_REBOUND", "OPPONENT_OFF_THE_BALL", "OPPONENT_POINTS",
                          "OPPONENT_MADE2", "OPPONENT_MISS2", "OPPONENT_MADE3", "OPPONENT_MISS3", "OPPONENT_MADE_FT",
                          "OPPONENT_MISS_FT", "OPPONENT_OFF_REB", "OPPONENT_DEF_REB", "OPPONENT_TOV", "OPPONENT_FOUL"]] = \
            defense[["LENGTH_OF_POSSESSION", "3PT_IN_POSS", "FT_IN_POSS",
                     "PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION",
                     "POST_UP", "SPOT_UP", "OFF_SCREEN", "HAND_OFF",
                     "TRANSITION", "CUT", "OFFENSIVE_REBOUND", "OFF_THE_BALL", "POINTS_SCORED",
                     "MADE2", "MISS2", "MADE3", "MISS3", "MADE_FT",
                     "MISS_FT", "OFF_REB", "DEF_REB", "TOV", "FOUL"]]

        team_def_lineups["DEF_RTG"] = 100 * team_def_lineups["OPPONENT_POINTS"] / team_def_lineups["OPPONENT_POSSESSIONS"]
        team_def_lineups["OPPONENT_FGM"] = team_def_lineups["OPPONENT_MADE2"] + team_def_lineups["OPPONENT_MADE3"]
        team_def_lineups["OPPONENT_FGA"] = team_def_lineups["OPPONENT_FGM"] + team_def_lineups["OPPONENT_MISS2"] + team_def_lineups["OPPONENT_MISS3"]

        for tp in play_types:
            poss_with_playtype = def_lineups.apply(lambda l: l[l[tp] != 0].sum()).reset_index()
            team_def_lineups["OPPONENT_{}_POINTS".format(tp)] = poss_with_playtype["POINTS_SCORED"]
            for stat in stat_columns:
                team_def_lineups["OPPONENT_{}_{}".format(tp, stat)] = poss_with_playtype[stat]

            team_def_lineups["OPPONENT_{}_PPP".format(tp)] = team_def_lineups["OPPONENT_{}_POINTS".format(tp)] / team_def_lineups["OPPONENT_{}".format(tp)]
            team_def_lineups["OPPONENT_{}_TOV_RATE".format(tp)] = team_def_lineups["OPPONENT_{}_TOV".format(tp)] / team_def_lineups["OPPONENT_{}".format(tp)]
            team_def_lineups["OPPONENT_{}_FT_RATE".format(tp)] = team_def_lineups["OPPONENT_{}_FT_IN_POSS".format(tp)] / team_def_lineups["OPPONENT_{}".format(tp)]
            team_def_lineups["OPPONENT_{}_eFG%".format(tp)] = (team_def_lineups["OPPONENT_{}_FGM".format(tp)] +
                                                               0.5 * team_def_lineups["OPPONENT_{}_MADE3".format(tp)]) / \
                                                              team_def_lineups["OPPONENT_{}_FGA".format(tp)]
        # endregion

        team_lineups = pd.merge(team_off_lineups, team_def_lineups, on="LINEUP", how="outer").fillna(0)
        team_lineups["NET_RTG"] = team_lineups["OFF_RTG"] - team_lineups["DEF_RTG"]
        team_lineups["SECONDS"] = team_lineups["OFF_TIME"] + team_lineups["DEF_TIME"]
        team_lineups["OFF_REB%"] = team_lineups["OFF_REB"] / (team_lineups["OFF_REB"] + team_lineups["OPPONENT_DEF_REB"])
        team_lineups["DEF_REB%"] = team_lineups["DEF_REB"] / (team_lineups["DEF_REB"] + team_lineups["OPPONENT_OFF_REB"])
        team_lineups["DATE"] = team_poss.iloc[0]["DATE"]
        team_lineups["GAME_ID"] = team_poss.iloc[0]["GAME_ID"]
        team_lineups["TEAM"] = team_poss.iloc[0]["{}_TEAM".format(side)]

        r_lineups.append(team_lineups.fillna(0))

    return pd.concat(r_lineups) if len(r_lineups) != 0 else pd.DataFrame()

def GetSubLineups(round_lineups, nplayers):
    nplineups = pd.DataFrame()
    teams = round_lineups.groupby("TEAM")
    for t in teams:
        team_lineups = t[1]

        # Get all possible n-player lineups
        lineups = team_lineups["LINEUP"]
        players = set(itertools.chain.from_iterable([l.split('/') for l in lineups.tolist()]))
        npcombinations = itertools.combinations(players, nplayers)
        for npl in npcombinations:
            # Find lineups with all of the players
            tmp_df = team_lineups[lineups.apply(lambda l: all(p in l for p in npl))]
            if not tmp_df.empty:
                nplineup = tmp_df.sum()
                nplineup["LINEUP"] = '/'.join(str(p) for p in sorted(npl))

                # Re-calculate fields
                safe_divide = lambda x, y: x / y if y != 0 else 0
                nplineup["OFF_RTG"] = 100 * safe_divide(nplineup["POINTS"], nplineup["POSSESSIONS"])
                nplineup["DEF_RTG"] = 100 * safe_divide(nplineup["OPPONENT_POINTS"], nplineup["OPPONENT_POSSESSIONS"])
                nplineup["NET_RTG"] = nplineup["OFF_RTG"] - nplineup["DEF_RTG"]
                nplineup["OFF_REB%"] = safe_divide(nplineup["OFF_REB"], nplineup["OFF_REB"] + nplineup["OPPONENT_DEF_REB"])
                nplineup["DEF_REB%"] = safe_divide(nplineup["DEF_REB"], nplineup["DEF_REB"] + nplineup["OPPONENT_OFF_REB"])
                nplineup["DATE"] = tmp_df.iloc[0]["DATE"]
                nplineup["GAME_ID"] = tmp_df.iloc[0]["GAME_ID"]
                nplineup["TEAM"] = tmp_df.iloc[0]["TEAM"]

                for tp in play_types:
                    nplineup["{}_PPP".format(tp)] = safe_divide(nplineup["{}_POINTS".format(tp)], nplineup[tp])
                    nplineup["{}_TOV_RATE".format(tp)] = safe_divide(nplineup["{}_TOV".format(tp)], nplineup[tp])
                    nplineup["{}_FT_RATE".format(tp)] = safe_divide(nplineup["{}_FT_IN_POSS".format(tp)], nplineup[tp])
                    nplineup["{}_eFG%".format(tp)] = safe_divide(nplineup["{}_FGM".format(tp)] + 0.5 * nplineup["{}_MADE3".format(tp)],
                                                                 nplineup["{}_FGA".format(tp)])

                    nplineup["OPPONENT_{}_PPP".format(tp)] = safe_divide(nplineup["OPPONENT_{}_POINTS".format(tp)], nplineup["OPPONENT_{}".format(tp)])
                    nplineup["OPPONENT_{}_TOV_RATE".format(tp)] = safe_divide(nplineup["OPPONENT_{}_TOV".format(tp)], nplineup["OPPONENT_{}".format(tp)])
                    nplineup["OPPONENT_{}_FT_RATE".format(tp)] = safe_divide(nplineup["OPPONENT_{}_FT_IN_POSS".format(tp)], nplineup["OPPONENT_{}".format(tp)])
                    nplineup["OPPONENT_{}_eFG%".format(tp)] = safe_divide(nplineup["OPPONENT_{}_FGM".format(tp)] + 0.5 * nplineup["OPPONENT_{}_MADE3".format(tp)],
                                                                          nplineup["OPPONENT_{}_FGA".format(tp)])

                nplineups = nplineups.append(nplineup, ignore_index=True)
    return nplineups


lowest = min(possessions_df["HOME_TEAM_ROUND"].min(), possessions_df["AWAY_TEAM_ROUND"].min())
highest = max(possessions_df["HOME_TEAM_ROUND"].max(), possessions_df["AWAY_TEAM_ROUND"].max())

rounds_dfs = []

for r in range(int(lowest), int(highest+1)):
    home_teams_lineups = GetLineupsDFs(r, "HOME")
    away_teams_lineups = GetLineupsDFs(r, "AWAY")

    round_lineups = pd.concat([home_teams_lineups, away_teams_lineups]).reset_index()
    round_lineups.drop("index", axis=1, inplace=True)
    round_4p_lineups = GetSubLineups(round_lineups, 4)
    round_3p_lineups = GetSubLineups(round_lineups, 3)
    round_2p_lineups = GetSubLineups(round_lineups, 2)
    round_1p_lineups = GetSubLineups(round_lineups, 1)

    round_lineups.to_csv("{}-5p-lineups-round{}.csv".format(LEAGUE_NAME.lower().replace(" ", "-"), r), index=False)
    round_4p_lineups.to_csv("{}-4p-lineups-round{}.csv".format(LEAGUE_NAME.lower().replace(" ", "-"), r), index=False)
    round_3p_lineups.to_csv("{}-3p-lineups-round{}.csv".format(LEAGUE_NAME.lower().replace(" ", "-"), r), index=False)
    round_2p_lineups.to_csv("{}-2p-lineups-round{}.csv".format(LEAGUE_NAME.lower().replace(" ", "-"), r), index=False)
    round_1p_lineups.to_csv("{}-1p-lineups-round{}.csv".format(LEAGUE_NAME.lower().replace(" ", "-"), r), index=False)
