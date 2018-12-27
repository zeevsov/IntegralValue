import pandas as pd
import json
import math

LEAGUE_NAME = "Israeli League"

players_stats = pd.read_csv("{}-players-stats.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))

A = 3
B = 1

categories_info = {
    "Shooting":
        {
            "qualify": lambda pl: (pl["FGA"] > 29) & (pl["3PA"] > 9),
            "score": lambda pl: A * pl["FGA"] + B * pl["eFG%"],
            "ascending": True
        },
    "Play Creation":
        {
            "qualify": lambda pl: (pl["ORIGIN_PICK_ROLL_BALL_HANDLER"] > 10) & (pl["ORIGIN_ISOLATION"] > 7),
            "score": lambda pl: A * pl["PICK_ROLL_BALL_HANDLER_PPP"] + B * pl["PICK_ROLL_BALL_HANDLER_FREQ"] +
                               A * pl["ISOLATION_PPP"] + B * pl["ISOLATION_FREQ"],
            "ascending": True
        },
    "Defense":
        {
            "qualify": lambda pl: pl["OPPONENT_POSSESSIONS"] > 29,
            "score": lambda pl: pl["TEAM_DEF_RTG"],
            "ascending": False
        },
    "Offensive Rebounding":
        {
            "qualify": lambda pl: (pl["TEAM_OFF_REB"] + pl["OPPONENT_DEF_REB"]) >= 10,
            "score": lambda pl: pl["OFF_REB"] / (pl["TEAM_OFF_REB"] + pl["OPPONENT_DEF_REB"]),
            "ascending": True
        },
    "Defensive Rebounding":
        {
            "qualify": lambda pl: (pl["TEAM_DEF_REB"] + pl["OPPONENT_OFF_REB"]) >= 10,
            "score": lambda pl: pl["DEF_REB"] / (pl["TEAM_DEF_REB"] + pl["OPPONENT_OFF_REB"]),
            "ascending": True
        },
    "Post Up":
        {
            "qualify": lambda pl: pl["ORIGIN_POST_UP"] >= 15,
            "score": lambda pl: pl["POST_UP_PPP"],
            "ascending": True
        },
    "Pick & Roll":
        {
            "qualify": lambda pl: pl["ORIGIN_PICK_ROLL_BALL_HANDLER"] >= 15,
            "score": lambda pl: pl["PICK_ROLL_BALL_HANDLER_PPP"],
            "ascending": True
        },
}

def GetColor(p):
    if math.isnan(p):
        return "Gray"

    if p >= 70:
        return "Green"

    if p >= 30:
        return "Yellow"

    return "Red"


def GetAllCatPcts(players_df):
    pcts = pd.DataFrame()
    pcts["ID"] = players_df["ID"]
    for cat in categories_info:
        cat_info = categories_info[cat]
        qualifier = cat_info["qualify"]
        score = cat_info["score"]

        qualified_players = players_df[qualifier(players_df)]
        pcts[cat] = qualified_players.apply(lambda pl: score(pl), axis=1).rank(pct=True, ascending=cat_info["ascending"]) * 100

    return pcts


def GetStatsStrength(players_df):
    cat_pcts = GetAllCatPcts(players_df)
    players_strengths = {}

    for i in cat_pcts.iterrows():
        player_pcts = i[1]
        player_stats_strength = [(cat, abs(50 - player_pcts[cat]) if player_pcts[cat] else -1, GetColor(player_pcts[cat])) for cat in player_pcts.index if cat != "ID"]
        player_stats_strength.sort(key=lambda pss: pss[1] if not math.isnan(pss[1]) else -1, reverse=True)
        players_strengths[player_pcts["ID"]] = player_stats_strength[0:3]

    return players_strengths


def GenerateJSON():
    players_df = pd.read_csv("{}-players-stats.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))
    player_strengths = GetStatsStrength(players_df)
    with open("{}-strengths.json".format(LEAGUE_NAME.lower().replace(" ", "-")), "w") as f:
        json.dump(player_strengths, f)
