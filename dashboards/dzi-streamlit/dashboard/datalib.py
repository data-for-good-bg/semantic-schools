import pandas as pd

from collections import defaultdict


_SUBJECT_GROUP_TO_SUBJECT_MAPPING = {
    'БЕЛ': { 'БЕЛ' },
    'СТЕМ': { 'БЗО', 'ИНФ', 'ИТ', 'МАТ', 'ФА', 'ХООС' },
    'Чужди езици': { 'АЕ', 'АЕ-Б1', 'АЕ-Б1.1', 'АЕ-Б2',
                     'ИСПЕ', 'ИСПЕ-Б1', 'ИСПЕ-Б1.1', 'ИСПЕ-Б2',
                     'ИТЕ', 'ИТЕ-Б1', 'ИТЕ-Б1.1', 'ИТЕ-Б2',
                     'НЕ', 'НЕ-Б1', 'НЕ-Б1.1', 'НЕ-Б2',
                     'РЕ', 'РЕ-Б1', 'РЕ-Б1.1', 'РЕ-Б2',
                     'ФРЕ', 'ФРЕ-Б1', 'ФРЕ-Б1.1', 'ФРЕ-Б2'
                    },
    'Дипломни прокети': {'ДИППК', 'ДИППК-Д.ПР', 'ДИППК-П.Р', 'ДИППК-ПР', 'ДИППК-ТЕСТ'}
}

_SUBJECT_TO_GROUP_MAPPING = {
    subject : subject_group
    for subject_group, subjects in _SUBJECT_GROUP_TO_SUBJECT_MAPPING.items()
    for subject in subjects
}

# _SUBJECT_TO_GROUP_MAPPING = {
#     'БЕЛ': 'БЕЛ',

#     'МАТ': 'СТЕМ',
#     'БЗО': 'СТЕМ',
#     'ИНФ': 'СТЕМ',
#     'ИТ': 'СТЕМ',
#     'ХООС': 'СТЕМ',
#     'ФА': 'СТЕМ',
# }


def load_dzi_data() -> pd.DataFrame:
    raw_data = pd.read_csv('dzi-data.csv')
    raw_data['subject_group'] = raw_data['subject'].map(_SUBJECT_TO_GROUP_MAPPING).fillna('ДРУГИ')

    return raw_data


# def get_subjects_by_subjectgroup(data: pd.DataFrame, subject_group: str) -> list[str]:
#     unique_combinations = data[['subject', 'subject_group']].drop_duplicates()
#     filtered = unique_combinations.loc[unique_combinations['subject_group'] == subject_group]
#     as_list = sorted(filtered['subject'].unique().tolist())
#     return as_list


def group_by_year_region_subjectgroup(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby(['year', 'region', 'subject_group']).agg(
        total_people=('people', 'sum'),
        avg_score=('score', 'mean')
    ).reset_index()


def group_by_year_subjectgroup(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby(['year', 'subject_group']).agg(
        total_people=('people', 'sum'),
        avg_score=('score', 'mean')
    ).reset_index()



def extract_people_aggregated_data(input_data: pd.DataFrame, id_columns: list[str]) -> pd.DataFrame:
    """
    The input dataframe should contain the columns pointed in `id_columns` and
    also `total_people` and `subject_group` columns. The dataframe may have
    any other columns, which will be dropped as part of group-by operation,
    see below.

    The assumption is that the total_people value for 'БЕЛ' subject_group
    represents the total number of studends, thus the function calculates
    ratios against this value.

    The result dataframe will contain data gruped by [*id_columns, 'subject_group']
    with columns:
    * all columns from `id_columns` list
    * the subject_group column
    * tatal_people will be the aggregated sum calculated by the group-by
    * total_people_percent will be the percent from subject_group 'БЕЛ'

    The result dataframe will contain also a new row with
      `subject_group` equal 'БЕЗ' value for each `id_columns` combination.
      The `total_people` will be the difference between the value for `БЕЛ`
      and all other subject groups, the `total_people_percent` will be the
      corresponding percent from `БЕЛ` value.

    """

    # group the data by the specified id_columns and subjec_group
    data = input_data.groupby([*id_columns, 'subject_group']).agg(
        total_people=('people', 'sum'),
        # avg_score=('score', 'mean')
    ).reset_index()

    # extract unique subject groups
    subject_groups = data['subject_group'].unique().tolist()

    # pivot subject groups as columns
    data_pivoted = data.pivot_table(index=id_columns, columns='subject_group', values='total_people', fill_value=0)

    # add column БЕЗ
    data_pivoted['БЕЗ'] = data_pivoted['БЕЛ']
    for subject_group in subject_groups:
        if subject_group != 'БЕЛ':
            data_pivoted['БЕЗ'] = data_pivoted['БЕЗ'] - data_pivoted[subject_group]
    subject_groups.append('БЕЗ')

    # for each subject group add percent column
    for subject_group in subject_groups:
        data_pivoted[f'{subject_group}-ПР'] = data_pivoted[subject_group]/data_pivoted['БЕЛ']

    data_pivoted = data_pivoted.reset_index()

    # melt subject_groups percent columns to rows
    value_vars = [f'{subject_group}-ПР' for subject_group in subject_groups]
    data_with_percent_value = data_pivoted.melt(id_vars=id_columns, value_vars=value_vars, value_name='total_people_percent')
    # remove the -ПР suffix from values
    data_with_percent_value['subject_group'] = data_with_percent_value['subject_group'].apply(lambda v: v.replace('-ПР', ''))

    # melt subject_groups columns to rows
    data_with_abs_value = data_pivoted.melt(id_vars=id_columns, value_vars=subject_groups, value_name='total_people')

    # merge the two dataframes
    result = data_with_abs_value.merge(data_with_percent_value, on=[*id_columns, 'subject_group'], how='inner')

    return result


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