import streamlit as st
import altair as alt
from io import StringIO
import folium
from streamlit_folium import folium_static
import branca.colormap as cm

from lib import data
from lib import chart


# change the font size of tab titles
st.markdown("""
<style>
    .stTabs [data-baseweb="tab"] {
        & p { font-size: 18px }
    }
</style>""", unsafe_allow_html=True)

raw_data = data.load_dzi_data()
subject_data = data.extract_subject_data(raw_data)

st.write('# ДЗИ Данни')


def _divider():
    st.markdown(
        "<hr style='border: 1px solid #F04500;'/>",
        unsafe_allow_html=True
    )


def _write_subject_group_data_per_years(subject_group: str):
    html_text = StringIO()

    html_text.write(f'<ul style="font-size: 12px">{subject_group} предмети са:\n')
    for years_str, subjects_str in data.extract_subjects_of_group_per_years(subject_data, subject_group):
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
    _write_subject_group_data_per_years('Дипломни проекти')
    _write_subject_group_data_per_years('ДРУГИ')


with st.container():
    aggregated_data = data.extract_subjectgroup_aggregated_data(
        raw_data, ['year']
    )

    percent_chart, score_chart = chart.create_subjectgroup_charts(aggregated_data, customize=None)

    st.markdown("""
    Тук ще живее текст.
    """)

    # Shares by subject group
    _divider()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("""Тук ще живее текст.""")

    with col2:
        st.altair_chart(percent_chart, use_container_width=True)

    _divider()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("""Тук ще живее текст.""")

    with col2:
        st.altair_chart(score_chart, use_container_width=True)

with st.container():
    st.markdown("""Тук ще живее текст.""")

    location_data = data.create_wide_table(
        raw_data, ['year', 'region', 'mun'],
        {"total_people" : "sum", "score" : "mean"},
        ['БЕЛ', 'СТЕМ']
    )

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

_divider()

with st.container():
    st.markdown('### Поглед от близо')

    aggregated_data = data.extract_subjectgroup_aggregated_data(raw_data, ['year', 'region', 'mun'])

    regions = sorted(aggregated_data['region'].unique().tolist())

    cols = st.columns(2)
    for idx, col in enumerate(cols):
        with col:
            selected_region = st.selectbox(
                label=f'Област на община за сравнение {idx+1}',
                index=0,
                options=regions,
                placeholder='Изберете област',
            )
            region_data = aggregated_data[aggregated_data['region'] == selected_region]
            muns = sorted(region_data['mun'].unique().tolist())
            selected_mun = st.selectbox(
                label=f'Община за сравнение {idx+1}',
                index=idx,
                options=muns
            )
            if selected_region and selected_mun:
                selected_mun_data = region_data[aggregated_data['mun'] == selected_mun]
                percent_chart, score_chart = chart.create_subjectgroup_charts(selected_mun_data, None)

                st.altair_chart(percent_chart & score_chart, use_container_width=True)

_divider()

with st.container():
    st.markdown('### Карта на училищата визуализирани спрямо техните резултати от ДЗИ')
    st.write('Цветът на маркерите показва средния успех, а размерът - броя ученици')

    data = data.load_dzi_data_with_coords()
    grouped = data.groupby(['year', 'region', 'mun', 'place', 'school_id', 'school', 'subject_group', 'slongitude', 'slatitude']).agg(
        total_people=('people', 'sum'),
        avg_score=('score', 'mean')
    ).reset_index()

    col1, col2 = st.columns(2)
    # Get unique years and create a selector
    years = sorted(grouped['year'].unique().tolist(), reverse=True)

    with col1:
        selected_year = st.selectbox(
            'Изберете година',
            years,
            0,  # Default to the most recent year (first in the reversed list)
        )

    # Filter data by selected year
    grouped = grouped[grouped['year'] == selected_year]

    # Get unique subject groups and create a selector
    subject_groups = grouped['subject_group'].unique().tolist()

    with col2:
        selected_subject_group = st.selectbox(
            'Изберете вид матура',
            subject_groups,
            subject_groups.index('БЕЛ') if 'БЕЛ' in subject_groups else 0,
        )

    # Filter data by selected subject group
    grouped = grouped[grouped['subject_group'] == selected_subject_group]

    # Create base map centered on Bulgaria
    m = folium.Map(location=[42.7339, 25.4858], zoom_start=7)

    # Create color map for scores
    score_min = grouped['avg_score'].min()
    score_max = grouped['avg_score'].max()
    colormap = cm.LinearColormap(
        colors=['red', 'yellow', 'green'],
        vmin=score_min,
        vmax=score_max
    )

    # Add colormap to map
    colormap.add_to(m)
    colormap.caption = 'Среден успех'

    # Calculate marker sizes based on total_people
    max_students = grouped['total_people'].max()
    min_radius = 5
    max_radius = 15

    # Create feature groups for different school categories
    highlighted_schools = folium.FeatureGroup(name='Училища от интерес')
    regular_schools = folium.FeatureGroup(name='Всички останали училища')

    # Add markers for each school
    for _, row in grouped.iterrows():
        # Scale marker size based on number of students
        radius = min_radius + (row['total_people'] / max_students) * (max_radius - min_radius)

        # Common parameters for all markers
        popup_text = f"""
        <b>{row['school']}</b><br>
        ID: {row['school_id']}<br>
        Област: {row['region']}<br>
        Община: {row['mun']}<br>
        Населено място: {row['place']}<br>
        Брой ученици: {int(row['total_people'])}<br>
        Среден успех: {row['avg_score']:.2f}
        """

        # Create marker with appropriate styling
        marker_params = {
            'radius': radius,
            'popup': folium.Popup(popup_text, max_width=300),
            'fill': True,
            'fill_color': colormap(row['avg_score']),
            'color': 'gray',
            'weight': 1,
            'fill_opacity': 0.7,
        }

        # Create the circle marker
        circle = folium.CircleMarker(
            location=[row['slatitude'], row['slongitude']],
            **marker_params
        )

        # Add to appropriate feature group
        circle.add_to(regular_schools)

    # Add feature groups to map
    regular_schools.add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Display the map
    folium_static(m, width=1000, height=600)
