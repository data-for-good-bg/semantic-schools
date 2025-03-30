import streamlit as st
import pandas as pd
import geopandas as gpd
import altair as alt
from io import StringIO
import folium
from streamlit_folium import st_folium, folium_static
import branca.colormap as cm

import datalib
import chartlib

st.set_page_config(
    page_title='ДЗИ Данни',
    layout='wide'
)

raw_data = datalib.load_dzi_data()
subject_data = datalib.extract_subject_data(raw_data)


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
        'Филтър по области',
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


with st.expander(label='**Карта с училища**', expanded=True):
    st.write('### Географско разпределение на училищата спрямо техните резултати от ДЗИ')
    st.write('Цветът на маркерите показва средния успех, а размерът - броя ученици. Избраните училища са с черна граница.')

    data = datalib.load_dzi_data_with_coords()
    grouped = data.groupby(['year', 'region', 'mun', 'place', 'school_id', 'school', 'subject_group', 'slongitude', 'slatitude']).agg(
        total_people=('people', 'sum'),
        avg_score=('score', 'mean')
    ).reset_index()

    # Get unique years and create a selector
    years = sorted(grouped['year'].unique().tolist(), reverse=True)
    selected_year = st.selectbox(
        'Изберете година',
        years,
        0,  # Default to the most recent year (first in the reversed list)
    )

    # Filter data by selected year
    grouped = grouped[grouped['year'] == selected_year]

    # Get unique subject groups and create a selector
    subject_groups = grouped['subject_group'].unique().tolist()
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

    # Input field for school IDs to highlight
    school_ids_input = st.text_input(
        'Въведете ID на училища от интерес (разделени със запетая)',
        value='200112, 100110, 200221, 200234, 200216, 200230, 200605, 1302623, 2400130, 2218071, 2208075, 2212097',
        help='Пример: 200112, 100110, 200221'
    )

    # Parse school IDs from input
    schools_with_special_styling = []
    if school_ids_input:
        try:
            # Split by comma and convert to strings (keeping them as strings since that's how they're stored)
            schools_with_special_styling = [
                school_id.strip()
                for school_id in school_ids_input.split(',') if school_id.strip()
            ]
            st.success(f'Избрани училища от интерес: {len(schools_with_special_styling)}')
        except ValueError:
            st.error('Грешка: Моля, въведете ID-та, разделени със запетая')

    # Add markers for each school
    for _, row in grouped.iterrows():
        # Scale marker size based on number of students
        radius = min_radius + (row['total_people'] / max_students) * (max_radius - min_radius)

        # Common parameters for all markers
        popup_text = (
            f"Училище: {row['school_id']} {row['school']}<br>"
            f"Област: {row['region']}, Община: {row['mun']}, {row['place']}<br>"
            f"Брой ученици: {int(row['total_people'])}<br>"
            f"Среден успех: {row['avg_score']:.2f}"
        )

        common_params = {
            'location': [row['slatitude'], row['slongitude']],
            'radius': radius,
            'tooltip': f"{row['school_id']} {row['school']} ",
            'popup': folium.Popup(popup_text, max_width=300),
            'fill': True,
            'fill_opacity': 0.6,
            'opacity': 1,
            'weight': 2,
        }

        # Additional parameters based on styling
        style_params = {}
        if row['school_id'] in schools_with_special_styling:
            # Special styling with black border
            style_params = {
                'color': 'black',
                'fill_color': colormap(row['avg_score']),
                'weight': 2,  # Thicker border for highlighted schools
            }
        else:
            # Normal styling for non-highlighted schools
            style_params = {
                'color': colormap(row['avg_score']),
            }

        # Merge parameters and create marker
        marker_params = {**common_params, **style_params}
        marker = folium.CircleMarker(**marker_params)

        # Add to the appropriate feature group
        if row['school_id'] in schools_with_special_styling:
            marker.add_to(highlighted_schools)
        else:
            marker.add_to(regular_schools)

    # Add feature groups to the map
    highlighted_schools.add_to(m)
    regular_schools.add_to(m)

    # Add layer control to toggle school groups
    folium.LayerControl().add_to(m)

    # Display the map
    # st_folium(m, use_container_width=True) #width=700)
    folium_static(m)
