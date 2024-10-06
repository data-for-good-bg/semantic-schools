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

    values_chart, percent_chart = chartlib.create_line_charts_for_people_aggregated_data(people_data)
    values_chart = values_chart.properties(width=400)
    percent_chart = percent_chart.properties(width=400)

    st.markdown((
        '* _Матурата по БЕЛ е задължителна, поради това може да се приеме, че броят явили се на изпит по БЕЛ представя броят зрелостници._'
        '\n* _Броят ученици, без допълнителен зрелостен изпит е получен като разликата между броя явили се по БЕЛ и броя явили се по всички други предмети. **Може да е подвеждащ?!**_'
    ))
    _write_subject_data_per_years('СТЕМ')
    _write_subject_data_per_years('Чужди езици')
    _write_subject_data_per_years('Дипломни прокети')
    _write_subject_data_per_years('ДРУГИ')

    st.write(values_chart | percent_chart)


with st.expander(label='**Поглед по области**', expanded=True):

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

    st.markdown((
        '* _Матурата по БЕЛ е задължителна, поради това може да се приеме, че броят явили се на изпит по БЕЛ представя броят зрелостници._'
        '\n* _Броят ученици, без допълнителен зрелостен изпит е получен като разликата между броя явили се по БЕЛ и броя явили се по всички други предмети. **Може да е подвеждащ?!**_'
    ))

    _write_subject_data_per_years('СТЕМ')
    _write_subject_data_per_years('Чужди езици')
    _write_subject_data_per_years('Дипломни прокети')
    _write_subject_data_per_years('ДРУГИ')

    value_tabs, percent_tab = st.tabs(['Бройки', 'Проценти'])
    value_tabs.write(values_chart)
    percent_tab.write(percent_chart)
