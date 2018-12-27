from get_preset import GetLineupsByPreset
from get_tabs import GetAllStatsScores, GetBestSwitchingTabs
import numpy as np
import itertools
import scipy.stats
import pandas as pd
import json

LEAGUE_NAME = "Israeli League"

'''
The presets to check, in order of importance
'''
presets = ["Lineup", "Offensive Lineup", "Defensive Lineup", "Offensive Rebounding Lineup", "Defensive Rebounding Lineup",
           "Pick & Roll Offense", "Pick & Roll Defense", "3Pt Shooting", "3Pt Defense", "Fast Paced"]

'''
The relevant percentiles to check (in the order in which they will be checked), and the descriptive words for each
'''
percentiles_description = {
    80: ["Excellent", "Superb"],
    20: ["Poor", "Unsuccessful"],
    70: ["Good", "Well Performing"],
    30: ["Insufficient", "Underperforming"],
}

tab_name_to_title = {
    "Shooting": "Shooting",
    "Off-The-Ball": "Movement without the ball",
    "Pick & Roll": "Pick & Roll Game",
    "Transition": "Transition Play",
    "Shooting Defense": "when Defending Shooters",
    "Off-The-Ball Defense": "Off-The-Ball Defense",
    "Pick & Roll Defense": "Pick & Roll Defense",
    "Transition Defense": "Transition Defense",
}

stat_keywords_to_description = {
    "MEDIAN": {1: "Vulnerable", -1: "Durable"},
    "%": {1: "Not reliable", -1: "Satisfying"},
    "PPP": {1: "Not reliable", -1: "Satisfying"},
    "RATE": {1: "Not reliable", -1: "Satisfying"},
    "FREQ": {1: "Vulnerable", -1: "Durable"},
}

'''
Returns a dictionary with the lineup's percentile within each preset.
e.g.:
scores = {
    "Lineup": 65.0,
    "Offensive Lineup": 71.5,
    "Defensive Lineup": 60.52,
    ...
}
'''


def GetPercentilesFromPresetLineups(lineup, preset_lineups):
    scores = {}
    for preset in preset_lineups.keys():
        lineups = preset_lineups[preset]
        if lineup not in lineups["LINEUP"].unique():
            continue

        curr_lineup = lineups[lineups["LINEUP"] == lineup].iloc[0]
        scores[preset] = scipy.stats.percentileofscore(lineups["PRESET_SCORE"], curr_lineup["PRESET_SCORE"])
    return scores


def GetText(lineup, team_presets, tabs_stat_scores):
    # Check if lineup is BEST in presets
    for preset in presets:
        preset_lineups = team_presets[preset]

        # Check if lineup doesn't qualify for current preset - ignore it
        if lineup not in preset_lineups["LINEUP"].unique():
            continue

        # If lineup is the best in the preset - return preset title as the text
        if preset_lineups.iloc[0]["LINEUP"] == lineup:
            return "Best " + preset

    # Check if lineup is WORST in presets
    for preset in presets:
        preset_lineups = team_presets[preset]

        # Check if lineup doesn't qualify for current preset - ignore it
        if lineup not in preset_lineups["LINEUP"].unique():
            continue

        # If lineup is the worst in the preset - return preset title as the text
        if preset_lineups.iloc[-1]["LINEUP"] == lineup:
            return "Worst " + preset

    # Check percentiles
    team_presets_lineups = team_presets
    lineup_percentiles = GetPercentilesFromPresetLineups(lineup, team_presets_lineups)
    if len(lineup_percentiles) != 0:
        for percentile, preset in itertools.product(percentiles_description.keys(), lineup_percentiles.keys()):
            # If lineup matches percentile condition (for percent above 50 - if lineup percentile is at least the checked percent, and vice-versa)
            if 50 < percentile <= lineup_percentiles[preset] or lineup_percentiles[preset] <= percentile < 50:
                # Swap "Best" from preset title with a random word describing the percentile
                descriptions = percentiles_description[percentile]
                word = np.random.choice(descriptions)
                return word + " " + preset

    # Last resort - check dynamic tabs
    lineup_scores = tabs_stat_scores[tabs_stat_scores["LINEUP"] == lineup].iloc[0]
    tab = GetBestSwitchingTabs(1, lineup_scores)[0]
    tab_name = tab[0]
    tab_selected_stats = tab[2]

    if tab_selected_stats[0][1] == 0:
        # If the first stat's score is 0, than all stats are 0 (because they are order in descending order of the absolute value).
        # This means that the best tab's score is 0 which means that the lineup didn't qualify for any stat on any switching tab
        return "Not Enough Data"

    # For defense tabs ignore freq and median stats
    if "Defense" in tab_name:
        tmp = []
        for stat in tab_selected_stats:
            if "MEDIAN" not in stat[0] and "FREQ" not in stat[0]:
                tmp.append(stat)
        tab_selected_stats = tmp

    # Generate text
    selected_stat = tab_selected_stats[0]
    for kw in stat_keywords_to_description:
        if kw in selected_stat[0]:
            val = selected_stat[1] / abs(selected_stat[1])
            return "{} {}".format(stat_keywords_to_description[kw][val], tab_name_to_title[tab_name])


def GetAllLineupsText(lineups_df):
    # Get all teams presets
    team_presets = {}
    teams = lineups_df["TEAM"].unique()
    for team in teams:
        team_presets[team] = {}
        for preset in presets:
            team_presets[team][preset] = GetLineupsByPreset(lineups_df, team, preset)

    # Get all tabs stat scores for lineups which need it
    tabs_stat_scores = GetAllStatsScores(lineups_df)

    lineups_text = {}

    for l in lineups_df.iterrows():
        lineup_stats = l[1]
        lineup = lineup_stats["LINEUP"]
        team = lineup_stats["TEAM"]
        lineups_text[lineup] = GetText(lineup, team_presets[team], tabs_stat_scores)

    return lineups_text


def GenerateJSON():
    lineups_df = pd.read_csv("israeli-league-lineups.csv")
    lineups_text = GetAllLineupsText(lineups_df)
    with open("{}-text.json".format(LEAGUE_NAME.lower().replace(" ", "-")), "w") as f:
        json.dump(lineups_text, f)

GenerateJSON()
