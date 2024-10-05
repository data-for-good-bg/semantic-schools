import pandas as pd

from collections import defaultdict


_SUBJECT_TO_GROUP_MAPPING = {
    'БЕЛ': 'БЕЛ',

    'МАТ': 'СТЕМ',
    'БЗО': 'СТЕМ',
    'ИНФ': 'СТЕМ',
    'ИТ': 'СТЕМ',
    'ХООС': 'СТЕМ',
    'ФА': 'СТЕМ'
}


def load_dzi_data() -> pd.DataFrame:
    raw_data = pd.read_csv('dzi-data.csv')
    raw_data['subject_group'] = raw_data['subject'].map(_SUBJECT_TO_GROUP_MAPPING).fillna('ДРУГИ')

    return raw_data


# def get_subjects_by_subjectgroup(data: pd.DataFrame, subject_group: str) -> list[str]:
#     unique_combinations = data[['subject', 'subject_group']].drop_duplicates()
#     filtered = unique_combinations.loc[unique_combinations['subject_group'] == subject_group]
#     as_list = sorted(filtered['subject'].unique().tolist())
#     return as_list


# def group_by_year_region_subjectgroup(data: pd.DataFrame) -> pd.DataFrame:
#     return data.groupby(['year', 'region', 'subject_group']).agg(
#         total_people=('people', 'sum'),
#         avg_score=('score', 'mean')
#     ).reset_index()


def group_by_year_subjectgroup(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby(['year', 'subject_group']).agg(
        total_people=('people', 'sum'),
        avg_score=('score', 'mean')
    ).reset_index()


# def filter_by_subjectgroup(data: pd.DataFrame, value: str) -> pd.DataFrame:
#     return data.loc[data['subject_group'] == value]


def extract_subject_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    return raw_data[['year', 'subject', 'subject_group']].drop_duplicates(ignore_index=True)


def extract_subjects_of_group_per_years(subject_data: pd.DataFrame, subject_group) -> list[tuple[str, str]]:

    subjects_to_years = defaultdict(list)
    for year in sorted(subject_data['year'].unique().tolist()):
        subjects = subject_data[(subject_data['year'] == year) & (subject_data['subject_group'] == subject_group)]['subject'].unique().tolist()
        subjects_str = ', '.join(sorted(subjects))
        subjects_to_years[subjects_str].append(str(year))

    result = []
    for subjects_str, years in subjects_to_years.items():
        years_str = ', '.join(sorted(years))
        result.append((years_str, subjects_str))

    return result