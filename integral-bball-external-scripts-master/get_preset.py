import pandas as pd
import scipy.stats
import json

num_of_lineups_to_return = 1
LEAGUE_NAME = "Israeli League"


def BinominalConfidenceInterval(k,n,alpha=0.5):
    """
    alpha confidence intervals for a binomial distribution of k expected successes on n trials
    Clopper Pearson intervals are a conservative estimate.
    """
    lo = scipy.stats.beta.ppf(alpha/2, k, n-k+1)
    hi = scipy.stats.beta.ppf(1 - alpha/2, k+1, n-k)
    return lo, hi

def NormalConfidenceInterval(n, m, se, confidence=0.95):
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return m, m-h, m+h


presets_info = {
    "Lineup":
        {
            "qualify": lambda l: (l["POSSESSIONS"] + l["OPPONENT_POSSESSIONS"]) >= 30,
            "score": lambda l: NormalConfidenceInterval(l["GAMES_PLAYED"], l["NET_RTG_MEAN"], l["NET_RTG_SEM"])[1],
            "ascending": False
        },
    "Offensive Lineup":
        {
            "qualify": lambda l: l["POSSESSIONS"] >= 30,
            "score": lambda l: NormalConfidenceInterval(l["GAMES_PLAYED"], l["OFF_RTG_MEAN"], l["OFF_RTG_SEM"])[1],
            "ascending": False
        },
    "Defensive Lineup":
        {
            "qualify": lambda l: l["OPPONENT_POSSESSIONS"] >= 30,
            "score": lambda l: NormalConfidenceInterval(l["GAMES_PLAYED"], l["DEF_RTG_MEAN"], l["DEF_RTG_SEM"])[1],
            "ascending": True
        },
    "Offensive Rebounding Lineup":
        {
            "qualify": lambda l: (l["OFF_REB"] + l["OPPONENT_DEF_REB"]) >= 10,
            "score": lambda l: BinominalConfidenceInterval(l["OFF_REB"], (l["OFF_REB"] + l["OPPONENT_DEF_REB"]))[0],
            "ascending": False
        },
    "Defensive Rebounding Lineup":
        {
            "qualify": lambda l: (l["DEF_REB"] + l["OPPONENT_OFF_REB"]) >= 10,
            "score": lambda l: BinominalConfidenceInterval(l["DEF_REB"], (l["DEF_REB"] + l["OPPONENT_OFF_REB"]))[0],
            "ascending": False
        },
    "Fast Paced":
        {
            "qualify": lambda l: (l["PACE"] >= 80) & (l["POSSESSIONS"] + l["OPPONENT_POSSESSIONS"] >= 30),
            "score": lambda l: NormalConfidenceInterval(l["GAMES_PLAYED"], l["NET_RTG_MEAN"], l["NET_RTG_SEM"])[1],
            "ascending": False
        },
    "Pick & Roll Offense":
        {
            "qualify": lambda l: l["PICK_ROLL_BALL_HANDLER_POSSESSIONS"] >= 15,
            "score": lambda l: NormalConfidenceInterval(l["GAMES_PLAYED"], l["PICK_ROLL_BALL_HANDLER_PPP_MEAN"], l["PICK_ROLL_BALL_HANDLER_PPP_SEM"])[1],
            "ascending": False
        },
    "Pick & Roll Defense":
        {
            "qualify": lambda l: l["OPPONENT_PICK_ROLL_BALL_HANDLER_POSSESSIONS"] >= 15,
            "score": lambda l: NormalConfidenceInterval(l["GAMES_PLAYED"], l["OPPONENT_PICK_ROLL_BALL_HANDLER_PPP_MEAN"], l["OPPONENT_PICK_ROLL_BALL_HANDLER_PPP_SEM"])[1],
            "ascending": True
        },
    "Transition Offense":
        {
            "qualify": lambda l: l["TRANSITION_POSSESSIONS"] >= 15,
            "score": lambda l: NormalConfidenceInterval(l["GAMES_PLAYED"], l["TRANSITION_PPP_MEAN"], l["TRANSITION_PPP_SEM"])[1],
            "ascending": False
        },
    "Transition Defense":
        {
            "qualify": lambda l: l["OPPONENT_TRANSITION_POSSESSIONS"] >= 15,
            "score": lambda l: NormalConfidenceInterval(l["GAMES_PLAYED"], l["OPPONENT_TRANSITION_PPP_MEAN"], l["OPPONENT_TRANSITION_PPP_SEM"])[1],
            "ascending": True
        },
    "3Pt Shooting":
        {
            "qualify": lambda l: l["3PA"] >= 10,
            "score": lambda l: BinominalConfidenceInterval(l["3PM"], l["3PA"])[0],
            "ascending": False
        },
    "3Pt Defense":
        {
            "qualify": lambda l: l["OPPONENT_3PA"] >= 10,
            "score": lambda l: BinominalConfidenceInterval(l["OPPONENT_3PM"], l["OPPONENT_3PA"])[0],
            "ascending": True
        },
}

def GetBestLineupByPreset(lineups_df, team, preset):
    return GetLineupsByPreset(lineups_df, team, preset).LINEUP.head(num_of_lineups_to_return)

def GetLineupsByPreset(lineups_df, team, preset):
    info = presets_info[preset]
    team_lineups = lineups_df.loc[lineups_df["TEAM"] == team]
    qualified_lineups = team_lineups.where(lambda l: info["qualify"](l)).dropna()
    if not qualified_lineups.empty:
        qualified_lineups["PRESET_SCORE"] = qualified_lineups.apply(lambda l: info["score"](l), axis=1)
        qualified_lineups = qualified_lineups[qualified_lineups.PRESET_SCORE.notnull()]
        qualified_lineups.index = qualified_lineups.PRESET_SCORE.rank(method="first", ascending=info["ascending"]).astype(int)
        qualified_lineups = qualified_lineups.sort_index()
    return qualified_lineups


def GenerateJSON():
    lineups_df = pd.read_csv("{}-lineups.csv".format(LEAGUE_NAME.lower().replace(" ", "-")))
    teams = pd.read_csv("{}-teams.csv".format(LEAGUE_NAME.lower().replace(" ", "-"))).HOME_TEAM
    presets = {
        team: [
            {
                "PRESET": "#{} {}".format(rank, preset_name),
                "LINEUP": lineup
            }
            for preset_name in presets_info.keys() for rank, lineup in GetBestLineupByPreset(lineups_df, team, preset_name).iteritems()
        ]
        for team in teams
    }

    with open("{}-presets.json".format(LEAGUE_NAME.lower().replace(" ", "-")), "w") as f:
        json.dump(presets, f)
