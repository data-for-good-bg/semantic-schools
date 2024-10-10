import streamlit as st
import pandas as pd
import altair as alt
from io import StringIO

import datalib
import chartlib


raw_data = datalib.load_dzi_data()
subject_data = datalib.extract_subject_data(raw_data)

st.set_page_config(
    page_title='ДЗИ Данни',
    layout='wide'
)


def _write_subject_data_per_years(subject_group: str):
    html_text = StringIO()

    html_text.write(f'<ul style="font-size: 12px">{subject_group} предмети са:\n')
    for years_str, subjects_str in datalib.extract_subjects_of_group_per_years(subject_data, subject_group):
        html_text.write(f'  <li>За години {years_str} : {subjects_str}</li>')

    html_text.write('</ul></span>')
    st.html(html_text.getvalue())


st.write('# ДЗИ Данни')
with st.expander(label='**Поглед за цяла Бълагрия**', expanded=False):

    people_data = datalib.extract_people_aggregated_data(
        raw_data, ['year']
    )

    subject_groups = people_data['subject_group'].unique().tolist()
    subject_group_dropdown = alt.binding_select(
        name='Вид матура ',
        options=[None, *subject_groups],
        labels=['Всички', *subject_groups]
    )
    selection_subject_group = alt.selection_point(fields=['subject_group'], bind=subject_group_dropdown)

    color = alt.condition(
        selection_subject_group,
        alt.Color('subject_group:N', title='Вид матура'),
        alt.value('lightgray')
    )

    values_chart, percent_chart = chartlib.create_line_charts_for_people_aggregated_data(people_data)
    values_chart = (
        values_chart
        .encode(color=color)
        .add_params(selection_subject_group)
        .properties(width=400)
    )
    percent_chart = (
        percent_chart
        .encode(color=color)
        .add_params(selection_subject_group)
        .properties(width=400)
    )

    st.markdown((
        '* _Матурата по БЕЛ е задължителна, поради това може да се приеме, че броят явили се на изпит по БЕЛ представя броят зрелостници._'
        '\n* _Броят ученици, без допълнителен зрелостен изпит е получен като разликата между броя явили се по БЕЛ и броя явили се по всички други предмети. **Може да е подвеждащ?!**_'
    ))
    _write_subject_data_per_years('СТЕМ')
    _write_subject_data_per_years('Чужди езици')
    _write_subject_data_per_years('Дипломни прокети')
    _write_subject_data_per_years('ДРУГИ')



    score_data = datalib.extract_score_aggregated_data(
        raw_data, ['year']
    )
    score_data_subjcts = subject_data['subject_group'].unique().tolist()

    # selected_subjects = st.multiselect(
    #     label='Предмет', options=score_data_subjcts, default=['БЕЛ', 'СТЕМ']
    # )

    #score_data = score_data.loc[(score_data['subject_group'].isin(selected_subjects)) ]
    #st.write(score_data)

    score_chart = (
        alt.Chart(score_data)
        .mark_line(point=True)
        .encode(
            alt.X('year:O', title='Година'),
            alt.Y('score:Q', axis=alt.Axis(format='.2f'), title='Среден успех', scale=alt.Scale(domainMin=2.0, domainMax=6.0)),
            color=color
        )
        .properties(
            width=400,
        )
        .add_params(
            selection_subject_group
        )
    )

    st.write((values_chart | percent_chart) & score_chart)



with st.expander(label='**Поглед по области**', expanded=True):
    st.markdown((
        '* _Матурата по БЕЛ е задължителна, поради това може да се приеме, че броят явили се на изпит по БЕЛ представя броят зрелостници._'
        '\n* _Броят ученици, без допълнителен зрелостен изпит е получен като разликата между броя явили се по БЕЛ и броя явили се по всички други предмети. **Може да е подвеждащ?!**_'
    ))

    _write_subject_data_per_years('СТЕМ')
    _write_subject_data_per_years('Чужди езици')
    _write_subject_data_per_years('Дипломни прокети')
    _write_subject_data_per_years('ДРУГИ')


    summary_tab, value_tab, percent_tab = st.tabs(['Обща картина', 'Явили се ученици, брой', 'Явили се ученици, процент'])

    people_data = datalib.extract_people_aggregated_data(raw_data, ['year', 'region'])

    values_chart, percent_chart = chartlib.create_line_charts_for_people_aggregated_data(people_data)

    facet_field_def = alt.FacetFieldDef(field='region', type='nominal', title='Област')
    facet_columns = 4

    values_chart = (
        values_chart
        .facet(facet=facet_field_def, columns=facet_columns)
        .resolve_scale(y='independent', x='independent')
    )

    percent_chart = (
        percent_chart
        .facet(facet=facet_field_def, columns=facet_columns)
        .resolve_scale(y='independent', x='independent')
    )

    subject_groups = people_data['subject_group'].unique().tolist()

    selected_subject_group = summary_tab.selectbox(
        'Вид матура',
        subject_groups,
        subject_groups.index('БЕЛ'),
    )


    years = people_data['year'].unique().tolist()
    year_group_dropdown = alt.binding_select(
        name='Година ',
        options=[None, *years],
        labels=['Всички'] + [f'{y}' for y in years]
    )
    selection_year = alt.selection_point(fields=['year'], bind=year_group_dropdown)

    year_color = alt.condition(
        selection_year,
        alt.Color('year:N', title='Година'),
        alt.value('lightgray')
    )

    summary_chart = (
        alt.Chart(people_data[people_data['subject_group'] == selected_subject_group])
        .mark_point()
        .encode(
            alt.X('total_people:Q'),
            alt.Y('region:N'),
            color=year_color,
        )
        .properties(
            width=800
        )
        .add_params(
            selection_year
        )
    )

    summary_tab.write(summary_chart)
    value_tab.write(values_chart)
    percent_tab.write(percent_chart)