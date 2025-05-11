import pandas as pd
import streamlit as st
import altair as alt
from io import StringIO
import folium
from streamlit_folium import folium_static
import branca.colormap as cm

from lib import data
from lib import chart

raw_data = data.load_dzi_data()
subject_data = data.extract_subject_data(raw_data)

aggregated_data = data.extract_subjectgroup_aggregated_data(
    raw_data, ['year']
)

location_data = data.create_wide_table(
    raw_data, ['year', 'region', 'mun'],
    {"total_people" : "sum", "score" : "mean"},
    ['БЕЛ', 'СТЕМ']
)

percent_chart, score_chart = chart.create_subjectgroup_charts(aggregated_data)

# Title and description
st.title("Данни за матури")

st.markdown("""
Тук ще живее текст.
""")

# Shares by subject group
st.markdown(
    "<hr style='border: 1px solid #F04500;'/>",
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""Тук ще живее текст.""")

with col2:
    st.altair_chart(percent_chart, use_container_width=True)

# Scores by subject group
st.markdown(
    "<hr style='border: 1px solid #F04500;'/>",
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""Тук ще живее текст.""")

with col2:
    st.altair_chart(score_chart, use_container_width=True)

# Pupils and scores by municipality
st.markdown(
    "<hr style='border: 1px solid #F04500;'/>",
    unsafe_allow_html=True
)

st.markdown("""Тук ще живее текст.""")

selected_year = st.selectbox(
    label=" ",
    options=sorted(location_data["year"].unique(), reverse=True),
    label_visibility="collapsed"
    )

filtered_data = location_data[location_data["year"] == selected_year].reset_index(drop=True)

formated_data = data.format_municipal_table(filtered_data)

styled_df = formated_data.style.set_properties(
    **{"color": "#000000"}
).format(precision=2, thousands=",")

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True
)

