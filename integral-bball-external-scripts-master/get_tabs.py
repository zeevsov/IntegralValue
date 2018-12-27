import scipy.stats
import itertools
import pandas as pd
import json

LEAGUE_NAME = "Israeli League"
num_of_tabs = 4
num_of_stats = 4

play_types = ["PICK_ROLL_BALL_HANDLER", "PICK_ROLL_MAN", "ISOLATION", "POST_UP",
              "SPOT_UP", "OFF_SCREEN", "HAND_OFF", "TRANSITION", "CUT", "OFFENSIVE_REBOUND", "OFF_THE_BALL"]

'''
stats_qualifiers: Holds lineup-qualifying condition for each stats
stats_qualifiers = {
    stat1: qualifier1,
    stat2: qualifier2,
    stat3: qualifier3,
    ...
}
'''
stats_qualifiers = {
    "POINTS": lambda lineup: lineup["POSSESSIONS"] >= 30,
    "FGA": lambda lineup: lineup["FGA"] >= 10,
    "FGM": lambda lineup: lineup["FGA"] >= 10,
    "FTA": lambda lineup: lineup["FTA"] >= 10,
    "FTM": lambda lineup: lineup["FTA"] >= 10,
    "3PA": lambda lineup: lineup["3PA"] >= 10,
    "3PM": lambda lineup: lineup["3PA"] >= 10,
    "OFF_REB": lambda lineup: lineup["OFF_REB"] + lineup["OPPONENT_DEF_REB"] >= 10,
    "DEF_REB": lambda lineup: lineup["DEF_REB"] + lineup["OPPONENT_OFF_REB"] >= 10,
    "TOV": lambda lineup: lineup["POSSESSIONS"] >= 30,
    "OFF_RTG": lambda lineup: lineup["POSSESSIONS"] >= 30,
    "DEF_RTG": lambda lineup: lineup["OPPONENT_POSSESSIONS"] >= 30,
    "NET_RTG": lambda lineup: lineup["POSSESSIONS"] + lineup["OPPONENT_POSSESSIONS"] >= 30,
    "FG%": lambda lineup: lineup["FGA"] >= 10,
    "FT%": lambda lineup: lineup["FTA"] >= 10,
    "3PT%": lambda lineup: lineup["3PA"] >= 10,
    "eFG%": lambda lineup: lineup["FGA"] >= 10,
    "TS%": lambda lineup: lineup["FGA"] >= 10,
    "OFF_REB%": lambda lineup: lineup["OFF_REB"] + lineup["OPPONENT_DEF_REB"] >= 10,
    "DEF_REB%": lambda lineup: lineup["DEF_REB"] + lineup["OPPONENT_OFF_REB"] >= 10,
    "3PT_FREQ": lambda lineup: lineup["POSSESSIONS"] >= 30,
    "FT_RATE": lambda lineup: lineup["POSSESSIONS"] >= 30,
    "PACE": lambda lineup: lineup["POSSESSIONS"] + lineup["OPPONENT_POSSESSIONS"] >= 30,

    "OPPONENT_POINTS": lambda lineup: lineup["OPPONENT_POSSESSIONS"] >= 30,
    "OPPONENT_FGA": lambda lineup: lineup["OPPONENT_FGA"] >= 10,
    "OPPONENT_FGM": lambda lineup: lineup["OPPONENT_FGA"] >= 10,
    "OPPONENT_FTA": lambda lineup: lineup["OPPONENT_FTA"] >= 10,
    "OPPONENT_FTM": lambda lineup: lineup["OPPONENT_FTA"] >= 10,
    "OPPONENT_3PA": lambda lineup: lineup["OPPONENT_3PA"] >= 10,
    "OPPONENT_3PM": lambda lineup: lineup["OPPONENT_3PA"] >= 10,
    "OPPONENT_OFF_REB": lambda lineup: lineup["DEF_REB"] + lineup["OPPONENT_OFF_REB"] >= 10,
    "OPPONENT_DEF_REB": lambda lineup: lineup["OFF_REB"] + lineup["OPPONENT_DEF_REB"] >= 10,
    "OPPONENT_TOV": lambda lineup: lineup["OPPONENT_POSSESSIONS"] >= 30,
    "OPPONENT_FG%": lambda lineup: lineup["OPPONENT_FGA"] >= 10,
    "OPPONENT_FT%": lambda lineup: lineup["OPPONENT_FTA"] >= 10,
    "OPPONENT_3PT%": lambda lineup: lineup["OPPONENT_3PA"] >= 10,
    "OPPONENT_eFG%": lambda lineup: lineup["OPPONENT_FGA"] >= 10,
    "OPPONENT_TS%": lambda lineup: lineup["OPPONENT_FGA"] >= 10,
    "OPPONENT_3PT_FREQ": lambda lineup: lineup["OPPONENT_POSSESSIONS"] >= 30,
    "OPPONENT_FT_RATE": lambda lineup: lineup["OPPONENT_POSSESSIONS"] >= 30,
}

def CreateLambda(stat, min):
    return lambda lineup: lineup[stat] >= min


for o, t in itertools.product(["", "OPPONENT_"], play_types):
    prefix = "{}{}_".format(o, t)
    stats_qualifiers[prefix + "POSSESSIONS"] = CreateLambda(o + "POSSESSIONS", 30)
    stats_qualifiers[prefix + "POINTS"] = CreateLambda(prefix + "POSSESSIONS", 15)
    stats_qualifiers[prefix + "FGA"] = CreateLambda(prefix + "FGA", 10)
    stats_qualifiers[prefix + "FGM"] = CreateLambda(prefix + "FGA", 10)
    stats_qualifiers[prefix + "3PA"] = CreateLambda(prefix + "3PA", 10)
    stats_qualifiers[prefix + "3PM"] = CreateLambda(prefix + "3PA", 10)
    stats_qualifiers[prefix + "FTA"] = CreateLambda(prefix + "FTA", 10)
    stats_qualifiers[prefix + "FTM"] = CreateLambda(prefix + "FTA", 10)
    stats_qualifiers[prefix + "TOV"] = CreateLambda(prefix + "POSSESSIONS", 15)
    stats_qualifiers[prefix + "PPP"] = CreateLambda(prefix + "POSSESSIONS", 15)
    stats_qualifiers[prefix + "FG%"] = CreateLambda(prefix + "FGA", 10)
    stats_qualifiers[prefix + "eFG%"] = CreateLambda(prefix + "FGA", 10)
    stats_qualifiers[prefix + "TS%"] = CreateLambda(prefix + "FGA", 10)
    stats_qualifiers[prefix + "FT_RATE"] = CreateLambda(prefix + "POSSESSIONS", 15)
    stats_qualifiers[prefix + "TOV_RATE"] = CreateLambda(prefix + "POSSESSIONS", 15)
    stats_qualifiers[prefix + "3PT_FREQ"] = CreateLambda(prefix + "POSSESSIONS", 15)
    stats_qualifiers[prefix + "FREQ"] = CreateLambda(prefix + "POSSESSIONS", 15)
    stats_qualifiers[prefix + "PPP_MEDIAN"] = CreateLambda(prefix + "POSSESSIONS", 15)

'''
constant/changing_tabs: Holds the relevant stats for each tab
changing_tabs = {
    tab_name1: {
        constant: [stat1, stat2]
        changing: [stat3, stat4, stat5,...],
    }
    tab_name2: {
        constant: [stat3]
        changing: [stat1, stat2, stat4, stat5,...],
    }
    ...
}
'''
constant_tabs = {
    "General": {
        "constant": ["NET_RTG", "OFF_RTG", "DEF_RTG"],
        "changing": [s for s in filter(lambda stat: "MEDIAN" not in stat, stats_qualifiers.keys()) if s not in ["NET_RTG", "OFF_RTG", "DEF_RTG"]]
    },
    "Offense": {
        "constant": ["OFF_RTG"],
        "changing": ["POINTS", "FGA", "FGM", "FTA", "FTM", "3PA", "3PM", "OFF_REB", "OPPONENT_DEF_REB", "TOV", "FG%", "FT%", "3PT%", "eFG%", "TS%",
                     "OFF_REB%", "3PT_FREQ", "FT_RATE"]
    },
    "Defense": {
        "constant": ["DEF_RTG"],
        "changing": ["OPPONENT_POINTS", "OPPONENT_FGA", "OPPONENT_FGM", "OPPONENT_FTA", "OPPONENT_FTM", "OPPONENT_3PA", "OPPONENT_3PM",
                     "OPPONENT_OFF_REB", "DEF_REB", "OPPONENT_TOV", "OPPONENT_FG%", "OPPONENT_FT%", "OPPONENT_3PT%", "OPPONENT_eFG%", "OPPONENT_TS%",
                     "DEF_REB%", "OPPONENT_3PT_FREQ", "OPPONENT_FT_RATE"]
    },
}
changing_tabs = {
    "Shooting": {
        "constant": [],
        "changing": ["OFF_RTG", "FG%", "eFG%", "TS%", "3PT%", "3PT_FREQ", "FT%"]
    },
    "Shooting Defense": {
        "constant": [],
        "changing": ["DEF_RTG", "OPPONENT_FG%", "OPPONENT_eFG%", "OPPONENT_TS%", "OPPONENT_3PT%", "OPPONENT_3PT_FREQ", "OPPONENT_FT%"]
    },
    "Pick & Roll": {
        "constant": [],
        "changing": ["PICK_ROLL_BALL_HANDLER_PPP", "PICK_ROLL_BALL_HANDLER_FREQ", "PICK_ROLL_BALL_HANDLER_eFG%", "PICK_ROLL_BALL_HANDLER_FT_RATE",
                     "PICK_ROLL_BALL_HANDLER_TOV_RATE", "PICK_ROLL_BALL_HANDLER_PPP_MEDIAN"],
    },
    "Pick & Roll Defense": {
        "constant": [],
        "changing": ["OPPONENT_PICK_ROLL_BALL_HANDLER_PPP", "OPPONENT_PICK_ROLL_BALL_HANDLER_FREQ", "OPPONENT_PICK_ROLL_BALL_HANDLER_eFG%",
                     "OPPONENT_PICK_ROLL_BALL_HANDLER_FT_RATE", "OPPONENT_PICK_ROLL_BALL_HANDLER_TOV_RATE",
                     "OPPONENT_PICK_ROLL_BALL_HANDLER_PPP_MEDIAN"],
    },
    "Transition": {
        "constant": [],
        "changing": ["TRANSITION_PPP", "TRANSITION_FREQ", "TRANSITION_eFG%", "TRANSITION_FT_RATE", "TRANSITION_TOV_RATE", "TRANSITION_PPP_MEDIAN"],
    },
    "Transition Defense": {
        "constant": [],
        "changing": ["OPPONENT_TRANSITION_PPP", "OPPONENT_TRANSITION_FREQ", "OPPONENT_TRANSITION_eFG%", "OPPONENT_TRANSITION_FT_RATE",
                     "OPPONENT_TRANSITION_TOV_RATE", "OPPONENT_TRANSITION_PPP_MEDIAN"]
    },
     "Off-The-Ball": {
        "constant": [],
        "changing": ["OFF_THE_BALL_PPP", "OFF_THE_BALL_FREQ", "OFF_THE_BALL_eFG%", "OFF_THE_BALL_TOV_RATE", "OFF_THE_BALL_PPP_MEDIAN"],
     },
     "Off-The-Ball Defense": {
        "constant": [],
        "changing": ["OPPONENT_OFF_THE_BALL_PPP", "OPPONENT_OFF_THE_BALL_FREQ", "OPPONENT_OFF_THE_BALL_eFG%", "OPPONENT_OFF_THE_BALL_TOV_RATE",
                     "OPPONENT_OFF_THE_BALL_PPP_MEDIAN"]
     },
}

def GetAllStatsScores(lineups_df):
    scores = pd.DataFrame()
    scores["LINEUP"] = lineups_df["LINEUP"]
    for stat in stats_qualifiers:
        qualifier = stats_qualifiers[stat]
        qualified_lineups = lineups_df[qualifier(lineups_df)]
        scores[stat] = 50 - (qualified_lineups[stat].rank(pct=True) * 100)

    return scores.fillna(0)


def GetConstantTabs(lineup_scores, lineup_stats):
    tabs = {}
    for tab in constant_tabs:
        tab_stats = constant_tabs[tab]

        # Fill with constant stats
        selected_stats = [(s, lineup_scores[s]) for s in tab_stats["constant"]]

        # Fill remaining stats - select highest scored
        rem_stats = num_of_stats - len(selected_stats)
        other_stats = [(s, lineup_scores[s]) for s in tab_stats["changing"]]
        other_stats.sort(key=lambda tuple: abs(tuple[1]), reverse=True)
        selected_stats = selected_stats + other_stats[0:rem_stats]

        tabs[tab] = [(s0, lineup_stats[s0], s1) for s0, s1 in selected_stats]
    return tabs


'''
returns:
[(tab1_name, tab1_score, tab1_selected_stats), (tab2_name, tab2_score, tab2_selected_stats), ...]
'''
def GetBestSwitchingTabs(num_of_tabs, lineup_scores):
    tab_scores = []

    # Calculate each of the changing tabs' score
    for tab in changing_tabs:
        tab_stats = changing_tabs[tab]

        # take constant stats first (if exists) and then the highest scored
        selected_stats = [(s, lineup_scores[s]) for s in tab_stats["constant"]]
        rem_stats = num_of_stats - len(selected_stats)
        other_stats = [(s, lineup_scores[s]) for s in tab_stats["changing"]]
        other_stats.sort(key=lambda tuple: abs(tuple[1]), reverse=True)
        selected_stats = selected_stats + other_stats[0:rem_stats]

        # re-sort in case there were constant tabs which are not the best
        other_stats.sort(key=lambda tuple: abs(tuple[1]), reverse=True)

        # Calculate score = stat1^4 + stat2^3 + stat3^2 + stat4^1
        score = sum([selected_stats[i][1] ** (num_of_stats - i) for i in range(0, num_of_stats)])

        tab_scores.append((tab, score, selected_stats))

    tab_scores.sort(key=lambda ts: ts[1], reverse=True)
    selected_tabs = tab_scores[0:num_of_tabs]
    return selected_tabs


'''
return object structure:
{
    lineup1: 
    {
        tab1_name: [(stat1, value1, score1), (stat2, value2, score2), (stat3, value3, score3), (stat4, value4, score4)]
        tab2_name: [(stat1, value1, score1), (stat2, value2, score2), (stat3, value3, score3), (stat4, value4, score4)]
        tab3_name: [(stat1, value1, score1), (stat2, value2, score2), (stat3, value3, score3), (stat4, value4, score4)]
        tab4_name: [(stat1, value1, score1), (stat2, value2, score2), (stat3, value3, score3), (stat4, value4, score4)]
    }
    lineup2:
    ...
}
'''
def GetTabs(lineups_df):
    tabs = {}

    # Get all lineups score for each stat
    stats_scores = GetAllStatsScores(lineups_df)

    for l in stats_scores.iterrows():
        lineup_scores = l[1]
        lineup_stats = lineups_df.iloc[l[0]]
        # Set constant tabs
        lineup_tabs = GetConstantTabs(lineup_scores, lineup_stats)

        # Set changing tabs
        rem_tabs = num_of_tabs - len(lineup_tabs)
        selected_tabs = GetBestSwitchingTabs(rem_tabs, lineup_scores)
        for tab_name, tac_score, selected_stats in selected_tabs:
            lineup_tabs[tab_name] = [(s0, lineup_stats[s0], s1) for s0, s1 in selected_stats]

        tabs[lineup_scores["LINEUP"]] = lineup_tabs

    return tabs

def GenerateJSON():
    lineups_df = pd.read_csv("{}-5p-lineups.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))
    tabs = GetTabs(lineups_df)
    with open("{}-tabs.json".format(LEAGUE_NAME.lower().replace(" ", "-")), "w") as f:
        json.dump(tabs, f)
