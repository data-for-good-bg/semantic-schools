import os
import streamlit as st
from io import StringIO
import folium
from streamlit_folium import folium_static
import branca.colormap as cm

from lib.data import (
    create_wide_table, extract_subjects_of_group_per_years, extract_subjectgroup_aggregated_data,
    load_dzi_data_with_coords, load_dzi_data, extract_subject_data, format_municipal_table,
    SG_BEL, SG_STEM, SG_FOREIGN_LANGUAGES, SG_OTHER, SG_DIPL
)
from lib import chart


# change the font size of tab titles
st.markdown("""
<style>
    .stTabs [data-baseweb="tab"] {
        & p { font-size: 18px }
    }
</style>""", unsafe_allow_html=True)

raw_data = load_dzi_data()
subject_data = extract_subject_data(raw_data)

st.write('# Данни за матурите')


def _divider():
    st.markdown(
        "<hr style='border: 1px solid #F04500;'/>",
        unsafe_allow_html=True
    )

with st.container():
    aggregated_data = extract_subjectgroup_aggregated_data(
        raw_data, ['year']
    )

    percent_chart, score_chart = chart.create_subjectgroup_charts(aggregated_data)

    st.markdown(
        """Този анализ представя успехите на зрелостниците и предпочитаните предмети за втора матура в страната.
        Кои са добрите примери сред училищата и общините извън "елитните гимназии" в големите населени места?
        Има ли промени или тенденции през годините, които заслужават вниманието ни?
        Това са въпросите, на които графиките по-долу имат за цел да отговорят.
        Продължи надолу, за да потърсиш отговорите."""
        )

    # Shares by subject group
    _divider()

    st.markdown('### Обща картина за цялата страна')

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("""
        Матурата по български език и литература (БЕЛ) е задължителна за всички и затова дава общия брой на зрелостници.\n
        Предметите за втора матура са групирани в три категории - СТЕМ, Чужди езици и Други (виж бележките най-долу за повече детайли).\n
        СТЕМ предметите са с най-голям дял през 2017, след което отстъпват челната позиция по брой на чуждите езици.\n
        През 2022 е въведен задължителен изпит за професионална квалификация (Дипломен проект) за учениците от професионални гимназии.
        Това води да големи промени в броя явили се на втора матура и в избора на предмет.
        """)

    with col2:
        st.altair_chart(percent_chart, use_container_width=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(
            """Матурите по чужд език бележат най-високи резултати.
            По-високи от матурата по български език и литература и от другите групи предмети за втора матура."""
            )

    with col2:
        st.altair_chart(score_chart, use_container_width=True)

with st.container():

    _divider()

    st.markdown('### Поглед отблизо')

    st.markdown("""
    Тук можеш да разгледаш резултатите по БЕЛ и втора матура по СТЕМ предмети по община.
    Таблицата може да бъде сортирана по всяка една от колоните с клик върху името на колоната.\n
    Например, избери година и сортирай по колоната Явили се - СТЕМ.
    Откриваш ли общини, където броя зрелостници по СТЕМ е относително голям дял от общия брой зрелостници (=Явили се - БЕЛ)?
    Какви са средните оценки там спрямо останалите близки общини по това подреждане?
    """)

    location_data = create_wide_table(
        raw_data, ['year', 'region', 'mun'],
        {"total_people" : "sum", "score" : "mean"},
        [SG_BEL, SG_STEM]
    )

    selected_year = st.selectbox(
        label=" ",
        options=sorted(location_data["year"].unique(), reverse=True),
        label_visibility="collapsed"
        )

    filtered_data = location_data[location_data["year"] == selected_year].reset_index(drop=True)

    formated_data = format_municipal_table(filtered_data)

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
    st.markdown('### Сравнение между области и общини')

    st.markdown("""
    Сравни представянето на две области или общини.
    Сравнението между две области става, като се избере стойност --Всички-- в полетата Община за сравнение.
    Сравнението между общини става, като първо се изберат съответните области.
    """)

    all_region_aggregated_data = extract_subjectgroup_aggregated_data(raw_data, ['year', 'region'])
    all_mun_aggregated_data = extract_subjectgroup_aggregated_data(raw_data, ['year', 'region', 'mun'])

    regions = sorted(all_mun_aggregated_data['region'].unique().tolist())

    all_marker = '-- Всички --'

    cols = st.columns(2)
    for idx, col in enumerate(cols):
        with col:
            selected_region = st.selectbox(
                label=f'Област за сравнение {idx+1}',
                index=idx,
                options=regions,
                placeholder='Избери област',
            )
            select_region_mun_data = all_mun_aggregated_data[all_mun_aggregated_data['region'] == selected_region]
            muns = [all_marker] + sorted(select_region_mun_data['mun'].unique().tolist())
            selected_mun = st.selectbox(
                label=f'Община за сравнение {idx+1}',
                index=0,
                options=muns
            )
            if selected_region and selected_mun:
                if selected_mun == all_marker:
                    selected_mun_data = all_region_aggregated_data[all_region_aggregated_data['region'] == selected_region]
                else:
                    selected_mun_data = select_region_mun_data[select_region_mun_data['mun'] == selected_mun]
                percent_chart, score_chart = chart.create_subjectgroup_charts(selected_mun_data)

                st.altair_chart(percent_chart & score_chart, use_container_width=True)

_divider()

with st.container():
    st.markdown('### Поглед по училища')

    st.markdown("""
    Избери година и вид матура. Откриваш ли райони с преобладаващо по-високи резултати (=по-зелени)?
    Приближи към населено място или училище, което е от интерес. Какво е представянето там?\n
    Цветът на маркерите показва средния успех, а размерът - броя явили се.
    """)

    data = load_dzi_data_with_coords()
    grouped = data.groupby(['year', 'region', 'mun', 'place', 'school_id', 'school', 'subject_group', 'slongitude', 'slatitude']).agg(
        total_people=('people', 'sum'),
        avg_score=('score', 'mean')
    ).reset_index()

    col1, col2 = st.columns(2)
    # Get unique years and create a selector
    years = sorted(grouped['year'].unique().tolist(), reverse=True)

    with col1:
        selected_year = st.selectbox(
            'Избери година',
            years,
            0,  # Default to the most recent year (first in the reversed list)
        )

    # Filter data by selected year
    grouped = grouped[grouped['year'] == selected_year]

    # Get unique subject groups and create a selector
    subject_groups = grouped['subject_group'].unique().tolist()

    with col2:
        selected_subject_group = st.selectbox(
            'Избери вид матура',
            subject_groups,
            subject_groups.index(SG_BEL) if SG_BEL in subject_groups else 0,
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

_divider()

with st.container():
    st.markdown('### Бележки')

    subject_md = StringIO()
    subject_md.write('* Матурата по български език и литература (БЕЛ) е задължителна за всички и затова дава общия брой на зрелостници. \n')
    subject_md.write((
        '* Броят ученици "Неявили се на втора матура" е получен като разликата между броя явили се '
        'по БЕЛ и броя явили се по всички други предмети.\n Реалният брой може да е различен, '
        'тъй като зрелостниците имат право да се явят на повече от един зрелостен изпит.\n'
    ))

    for subject_group in [SG_STEM, SG_DIPL, SG_FOREIGN_LANGUAGES, SG_OTHER]:
        subject_md.write(f'* "{subject_group}" предмети включват:\n')
        for years_str, subjects_str in extract_subjects_of_group_per_years(subject_data, subject_group):
            subject_md.write(f'  * За години {years_str} : {subjects_str}\n')

    st.markdown(subject_md.getvalue())

    st.markdown("""
    Този анализ е изготвен от [Данни за добро](https://data-for-good.bg/).\n

    Данните за броя явили се и оценките от матури са взети от [Портал за отворени данни](https://data.egov.bg/).

    Данните за адреси на училища са предоставени от Министерство на образованието по Закона за достъп до обществена информация.
    """)