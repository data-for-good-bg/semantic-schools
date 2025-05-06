import streamlit as st

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
    'Дипломни проекти': {'ДИППК', 'ДИППК-Д.ПР', 'ДИППК-П.Р', 'ДИППК-ПР', 'ДИППК-ТЕСТ'}
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

    sql = '''
select e."year", r."name" as region, m."name" as mun, p."name" as place, es.school_id, es.subject, es.people, es.score
from examination e
        inner join examination_score es on e.id = es.examination_id
        inner join school s on s.id = es.school_id
        inner join place p on s.place_id = p.id
        inner join municipality m on p.municipality_id = m.id
        inner join region r on m.region_id = r.id
where e."type" = 'ДЗИ'
--   and e."year" = 2017 and s.id = '400036'
order by e."year", region, mun, place, school_id, subject
'''
    conn = st.connection('eddata', type='sql')

    raw_data = conn.query(sql, ttl='1h')
    # raw_data = pd.read_csv('dzi-data.csv')
    raw_data['subject_group'] = raw_data['subject'].map(_SUBJECT_TO_GROUP_MAPPING).fillna('ДРУГИ')

    return raw_data


def load_dzi_data_with_coords() -> pd.DataFrame:
    sql = '''
select e."year", r."name" as region, m."name" as mun, p."name" as place, es.school_id, s."name" as school, es.subject, es.people, es.score,
r.longitude as rlongitude, r.latitude as rlatitude,
m.longitude as mlongitude, m.latitude as mlatitude,
p.longitude as plongitude, p.latitude as platitude,
s.longitude as slongitude, s.latitude as slatitude
from examination e
        inner join examination_score es on e.id = es.examination_id
        inner join school s on s.id = es.school_id
        inner join place p on s.place_id = p.id
        inner join municipality m on p.municipality_id = m.id
        inner join region r on m.region_id = r.id
where e."type" = 'ДЗИ'
order by e."year", region, mun, place, school_id, subject
'''

    conn = st.connection('eddata', type='sql')

    raw_data = conn.query(sql, ttl='1h')

    raw_data['subject_group'] = raw_data['subject'].map(_SUBJECT_TO_GROUP_MAPPING).fillna('ДРУГИ')

    # some schools do not have coordinates, they take the coordinates from the place
    raw_data.loc[raw_data['slongitude'].isna() | raw_data['slatitude'].isna(), ['slongitude', 'slatitude']] = \
        raw_data[['plongitude', 'platitude']].where(raw_data['slongitude'].isna() | raw_data['slatitude'].isna())


    for bad_school_id in ['2217151', '2212553', '2208123', '2218071']:
        raw_data.loc[raw_data['school_id'] == bad_school_id , ['slongitude', 'slatitude']] = \
            raw_data[['plongitude', 'platitude']].where(raw_data['school_id'] == bad_school_id)


    def convert_to_str(v):
        return float(v)

    raw_data['slongitude'] = raw_data['slongitude'].apply(convert_to_str)
    raw_data['slatitude'] = raw_data['slatitude'].apply(convert_to_str)

    return raw_data


def load_nvo_data_with_coords(grade_level: int, subject: str) -> pd.DataFrame:
    sql = '''
select e."year", r."name" as region, m."name" as mun, p."name" as place, es.school_id, s."name" as school, es.subject, es.people, es.score,
r.longitude as rlongitude, r.latitude as rlatitude,
m.longitude as mlongitude, m.latitude as mlatitude,
p.longitude as plongitude, p.latitude as platitude,
s.longitude as slongitude, s.latitude as slatitude
from examination e
        inner join examination_score es on e.id = es.examination_id
        inner join school s on s.id = es.school_id
        inner join place p on s.place_id = p.id
        inner join municipality m on p.municipality_id = m.id
        inner join region r on m.region_id = r.id
where e."type" = 'НВО' and e.grade_level = :grade_level and es.subject = :subject
order by e."year", region, mun, place, school_id, subject
'''

    conn = st.connection('eddata', type='sql')

    params = {'grade_level': grade_level, 'subject': subject}
    raw_data = conn.query(sql, params=params, ttl='1h')

    raw_data['subject_group'] = raw_data['subject'].map(_SUBJECT_TO_GROUP_MAPPING).fillna('ДРУГИ')

    # some schools do not have coordinates, they take the coordinates from the place
    raw_data.loc[raw_data['slongitude'].isna() | raw_data['slatitude'].isna(), ['slongitude', 'slatitude']] = \
        raw_data[['plongitude', 'platitude']].where(raw_data['slongitude'].isna() | raw_data['slatitude'].isna())


    for bad_school_id in ['2217151', '2212553', '2208123', '2218071']:
        raw_data.loc[raw_data['school_id'] == bad_school_id , ['slongitude', 'slatitude']] = \
            raw_data[['plongitude', 'platitude']].where(raw_data['school_id'] == bad_school_id)


    def convert_to_str(v):
        return float(v)

    raw_data['slongitude'] = raw_data['slongitude'].apply(convert_to_str)
    raw_data['slatitude'] = raw_data['slatitude'].apply(convert_to_str)

    return raw_data


def load_nvo_examinations() -> pd.DataFrame:
    sql = '''
select distinct e."year", e.grade_level, es.subject
from examination e
	inner join examination_score es on e.id = es.examination_id
where e."type" = 'НВО'
order by e."year" desc, e.grade_level
'''

    conn = st.connection('eddata', type='sql')
    return conn.query(sql, ttl='1h')


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



def extract_subjectgroup_aggregated_data(input_data: pd.DataFrame, id_columns: list[str]) -> pd.DataFrame:
    """
    The input dataframe should contain the columns pointed in `id_columns` and
    also `total_people`, 'score' and `subject_group` columns. The dataframe may have
    any other columns, which will be dropped as part of group-by operation,
    see below.

    The assumption is that the total_people value for 'БЕЛ' subject_group
    represents the total number of students, thus the function calculates
    ratios against this value.

    The result dataframe will contain data grouped by [*id_columns, 'subject_group']
    with columns:
    * all columns from `id_columns` list
    * the subject_group column
    * total_people will be the aggregated sum calculated by the group-by
    * total_people_percent will be the percent from subject_group 'БЕЛ'
    * score column will contain the weighted average score for the subject group

    The result dataframe will contain also a new row with
      `subject_group` equal 'БЕЗ' value for each `id_columns` combination.
      The `total_people` will be the difference between the value for `БЕЛ`
      and all other subject groups, the `total_people_percent` will be the
      corresponding percent from `БЕЛ` value.

    """

    data = input_data.groupby([*id_columns, 'subject_group']).apply(
        lambda x: pd.Series({
            'score': (x['score'] * x['people']).sum() / x['people'].sum(),
            'total_people': x['people'].sum()
        }),
        include_groups=False
    ).reset_index()

    # extract unique subject groups
    subject_groups = data['subject_group'].unique().tolist()

    # pivot subject groups as columns
    data_pivoted_people = data.pivot_table(index=id_columns, columns='subject_group', values='total_people', fill_value=0)

    # add column БЕЗ, this column could be misleading!
    data_pivoted_people['БЕЗ'] = data_pivoted_people['БЕЛ']
    for subject_group in subject_groups:
        if subject_group != 'БЕЛ':
            data_pivoted_people['БЕЗ'] = data_pivoted_people['БЕЗ'] - data_pivoted_people[subject_group]
    data_pivoted_people['БЕЗ'] = data_pivoted_people['БЕЗ'].apply(lambda v: 0 if v < 0 else v)
    subject_groups.append('БЕЗ')

    # for each subject group add percent column
    for subject_group in subject_groups:
        data_pivoted_people[f'{subject_group}-ПР'] = data_pivoted_people[subject_group]/data_pivoted_people['БЕЛ']

    data_pivoted_people = data_pivoted_people.reset_index()

    # melt subject_groups percent columns to rows
    value_vars = [f'{subject_group}-ПР' for subject_group in subject_groups]
    data_with_percent_value = data_pivoted_people.melt(id_vars=id_columns, value_vars=value_vars, value_name='total_people_percent')
    # remove the -ПР suffix from values
    data_with_percent_value['subject_group'] = data_with_percent_value['subject_group'].apply(lambda v: v.replace('-ПР', ''))

    # melt subject_groups columns to rows
    data_with_abs_value = data_pivoted_people.melt(id_vars=id_columns, value_vars=subject_groups, value_name='total_people')

    data_merged_people = data_with_abs_value.merge(data_with_percent_value, on=[*id_columns, 'subject_group'], how='inner')

    score_data = data[[*id_columns, 'subject_group', 'score']]

    # merge the two dataframes
    result = data_merged_people.merge(score_data, on=[*id_columns, 'subject_group'], how='left')

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

def create_wide_table(
    df_input: pd.DataFrame, index_cols: list, value_aggr: dict, subjects: list
    ) -> pd.DataFrame:
    """
    Creates a wide table with values (i.e. scores, number of pupils) split by
    subject group.
    """
    df_long = extract_subjectgroup_aggregated_data(
        df_input, index_cols
    )

    df_long = df_long[df_long["subject_group"].isin(subjects)]

    df_long = df_long.groupby(index_cols+["subject_group"]).agg(value_aggr).reset_index()

    df_wide = pd.DataFrame(columns=index_cols)
    for x in value_aggr.keys():
        df_pivot = df_long.pivot(index=index_cols, columns='subject_group', values=x)
        df_pivot.columns = [f'{x}_{col}' for col in df_pivot.columns]
        df_wide = df_wide.merge(df_pivot.reset_index(), "outer", index_cols)

    return df_wide

def format_municipal_table(
    df_region: pd.DataFrame
    ) -> pd.DataFrame:
    """Formats the municipality table with some hardcoded rules."""
    df_format = df_region.rename(columns={
        "year" : "Година", "region" : "Област", "mun" : "Община",
        "total_people_БЕЛ" : "Явили се - БЕЛ",
        "total_people_СТЕМ" : "Явили се - СТЕМ",
        "score_БЕЛ" : "Оценка - БЕЛ",
        "score_СТЕМ" : "Оценка - СТЕМ"
        })

    df_format[["Явили се - БЕЛ", "Явили се - СТЕМ"]] = df_format[["Явили се - БЕЛ", "Явили се - СТЕМ"]].astype(int)
    df_format[["Година"]] = df_format[["Година"]].astype(str)

    return df_format