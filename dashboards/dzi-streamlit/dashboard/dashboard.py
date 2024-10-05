import streamlit as st
import pandas as pd
import altair as alt
from io import StringIO

import datalib
import chartlib


raw_data = datalib.load_dzi_data()

st.set_page_config(
    page_title='ДЗИ Данни',
    layout='wide'
)
st.write('# ДЗИ Данни')

with st.expander(label='**Поглед за цяла Бълагрия**', expanded=True):

    data = datalib.group_by_year_subjectgroup(raw_data)
    data_pivoted = data.pivot_table(index=['year'], columns='subject_group', values='total_people', fill_value=0)
    data_pivoted['СТЕМ-ПР'] = data_pivoted['СТЕМ']/data_pivoted['БЕЛ']
    data_pivoted['ДРУГИ-ПР'] = data_pivoted['ДРУГИ']/data_pivoted['БЕЛ']
    data_pivoted['БЕЗ'] = data_pivoted['БЕЛ'] - data_pivoted['СТЕМ'] - data_pivoted['ДРУГИ']
    data_pivoted['БЕЗ-ПР'] = data_pivoted['БЕЗ']/data_pivoted['БЕЛ']
    data_pivoted = data_pivoted.reset_index()

    subject_data = datalib.extract_subject_data(raw_data)

    def _write_subject_data_per_years(subject_group: str):
        html_text = StringIO()

        #md_text.write('<span style="font-size: 10px;">\n')
        html_text.write(f'<ul style="font-size: 12px">{subject_group} предмети са:\n')
        for years_str, subjects_str in datalib.extract_subjects_of_group_per_years(subject_data, subject_group):
            html_text.write(f'  <li>За години {years_str} : {subjects_str}</li>')

        html_text.write('</ul></span>')
        st.html(html_text.getvalue())


    st.write('## ДЗИ по Български език и литература (БЕЛ)')
    st.write('Тъй като държавният зрелостен изпит по БЕЛ е задължителен, броят ученици явили се по БЕЛ съотвества на броят зрелостници в съответната година.')

    chart1, _ = chartlib.create_charts_for_subjet_group(data_pivoted, 'БЕЛ', 'БЕЛ')
    st.altair_chart(chart1)

    st.write('## ДЗИ по СТЕМ предмети')
    _write_subject_data_per_years('СТЕМ')

    chart1, chart2 = chartlib.create_charts_for_subjet_group(data_pivoted, 'СТЕМ', 'СТЕМ-ПР')
    col1, col2 = st.columns(2)
    col1.altair_chart(chart1)
    col2.altair_chart(chart2)


    st.write('## ДЗИ по други предмети')
    _write_subject_data_per_years('ДРУГИ')

    chart1, chart2 = chartlib.create_charts_for_subjet_group(data_pivoted, 'ДРУГИ', 'ДРУГИ-ПР')
    col1, col2 = st.columns(2)
    col1.altair_chart(chart1)
    col2.altair_chart(chart2)

    st.write('## Данни за брой ученици без втора матура')
    st.markdown((
        '_TODO_ - провери отново закона\n\n'
        '_Бележка: След учебна година 2021/2022 учениците имат право да се '
        'явят на до 3 допълнителни матури._\n\n_Графиките в тази секция може да '
        'са подвеждащи, тъй като няма данни за това колко ученика са се явили '
        'на повече от един допълнителен зрелостен изпит. Графиките представят '
        'разликата на явилите се по БЕЛ и явилите се на всички други предмети._'
    ))

    chart1, chart2 = chartlib.create_charts_for_subjet_group(data_pivoted, 'БЕЗ', 'БЕЗ-ПР')
    col1, col2 = st.columns(2)
    col1.altair_chart(chart1)
    col2.altair_chart(chart2)
