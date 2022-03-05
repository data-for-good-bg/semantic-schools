### Processing of data extract for STEM performance analysis

import pandas as pd


## User-defined functions


def sub_to_eng(sub_bg):
    """Convert subject name from BG to ENG"""
    if sub_bg == "БЕЛ":
        return "bel"
    elif sub_bg == "СТЕМ":
        return "stem"
    else:
        return "other"


## Data processing

# read the raw data which is the result of ../sparql/matura-stem.rq
matura_raw = pd.read_csv("<data filepath>.csv")  # Insert data filepath
matura_clean = matura_raw.copy()

# convert subjects from BG to ENG
matura_clean["sub_eng"] = [sub_to_eng(x) for x in matura_clean["sub_group"]]

# split number of pupils and average grade by subject group
matura_clean = matura_clean.pivot(
    index=["province", "town", "school_wiki_id", "school", "year"],
    columns="sub_eng",
    values=["tot_pup", "average_grade"],
).reset_index()
matura_clean.columns = matura_clean.columns.map("_".join).str.strip("_")

# add STEM's share of second matura and difference in grades between STEM and BEL
matura_clean["tot_pup_second"] = (
    matura_clean["tot_pup_stem"] + matura_clean["tot_pup_other"]
)
matura_clean["share_stem"] = (
    matura_clean["tot_pup_stem"] / matura_clean["tot_pup_second"]
)
matura_clean["grade_diff_stem_bel"] = (
    matura_clean["average_grade_stem"] - matura_clean["average_grade_bel"]
)

# add ranks based on STEM grade and difference in grades with BEL
matura_clean["rank_average_grade_stem"] = matura_clean.groupby("province")[
    "average_grade_stem"
].rank(method="min", ascending=False)
matura_clean["rank_grade_diff_stem_bel"] = matura_clean.groupby("province")[
    "grade_diff_stem_bel"
].rank(method="min", ascending=False)
matura_clean = matura_clean.sort_values(["province", "rank_average_grade_stem"])

# rearrange columns
matura_clean = matura_clean[
    [
        "province",
        "town",
        "school_wiki_id",
        "school",
        "year",
        "tot_pup_bel",
        "tot_pup_second",
        "tot_pup_other",
        "tot_pup_stem",
        "share_stem",
        "average_grade_bel",
        "average_grade_other",
        "average_grade_stem",
        "grade_diff_stem_bel",
        "rank_average_grade_stem",
        "rank_grade_diff_stem_bel",
    ]
]

matura_clean.to_excel(
    "<output filepath>.xlsx", index=False, freeze_panes=(1, 4)
)  # Insert output filepath

