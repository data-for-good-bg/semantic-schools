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

# change the font size of tab titles
st.markdown("""
<style>
    .stTabs [data-baseweb="tab"] {
        & p { font-size: 18px }
    }
</style>""", unsafe_allow_html=True)



def _write_subject_group_data_per_years(subject_group: str):
    html_text = StringIO()

    html_text.write(f'<ul style="font-size: 12px">{subject_group} предмети са:\n')
    for years_str, subjects_str in datalib.extract_subjects_of_group_per_years(subject_data, subject_group):
        html_text.write(f'  <li>За години {years_str} : {subjects_str}</li>')

    html_text.write('</ul></span>')
    st.html(html_text.getvalue())


def _write_all_subject_groups():
    st.markdown((
        '* _Матурата по БЕЛ е задължителна, поради това може да се приеме, че броят явили се на изпит по БЕЛ представя броят зрелостници._'
        '\n* _Броят ученици, без допълнителен зрелостен изпит е получен като разликата между броя явили се по БЕЛ и броя явили се по всички други предмети. **Може да е подвеждащ?!**_'
    ))
    _write_subject_group_data_per_years('СТЕМ')
    _write_subject_group_data_per_years('Чужди езици')
    _write_subject_group_data_per_years('Дипломни прокети')
    _write_subject_group_data_per_years('ДРУГИ')


st.write('# ДЗИ Данни')
with st.expander(label='**Поглед за цяла Бълагрия**', expanded=False):

    aggregated_data = datalib.extract_subjectgroup_aggregated_data(
        raw_data, ['year']
    )

    def _customize(chart: alt.Chart) -> alt.Chart:
        return chart.properties(width=400)

    values_chart, percent_chart, score_chart = chartlib.create_subjectgroup_charts(aggregated_data, _customize)

    _write_all_subject_groups()

    st.write((values_chart | percent_chart) & score_chart)


with st.expander(label='**Поглед по области**', expanded=False):
    _write_all_subject_groups()

    aggregated_data = datalib.extract_subjectgroup_aggregated_data(raw_data, ['year', 'region'])

    regions = aggregated_data['region'].unique().tolist()
    st.write('##### Филтър по области')
    selected_regions = st.multiselect(
        '',
        options=regions,
        default=regions,
        label_visibility='hidden'
    )

    st.write('##### Графики')
    summary_tab, value_tab, percent_tab, score_tab = st.tabs([
        '1\. Явили се, обща картина',
        '2\. Явили се ученици, по област, брой',
        '3\. Явили се ученици, по област, в проценти',
        '4\. Среден успех, по област'
    ])

    if selected_regions:

        # filter the data by region
        aggregated_data = aggregated_data[aggregated_data['region'].isin(selected_regions)]


        def _customize(chart: alt.Chart) -> alt.Chart:
            facet_field_def = alt.FacetFieldDef(
                field='region', type='nominal',
                title='Област (осите в различните графики може да имат различен обхват)')
            facet_columns = 4
            return (chart
                .facet(facet=facet_field_def, columns=facet_columns)
                .resolve_scale(y='independent', x='independent')
            )

        values_chart, percent_chart, score_chart = chartlib.create_subjectgroup_charts(aggregated_data, _customize)

        # selector for subject_group
        subject_groups = aggregated_data['subject_group'].unique().tolist()
        selected_subject_group = summary_tab.selectbox(
            'Вид матура',
            subject_groups,
            subject_groups.index('БЕЛ'),
        )

        summary_chart = chartlib.create_total_people_chart(
            aggregated_data[aggregated_data['subject_group'] == selected_subject_group]
        )

        summary_tab.write(summary_chart)
        value_tab.write(values_chart)
        percent_tab.write(percent_chart)
        score_tab.write(score_chart)
