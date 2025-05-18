import pandas as pd
import altair as alt
import streamlit as st
from altair import datum
from typing import Callable, Optional


SUBJECT_GROUP_COLOR_MAPPING = {
    'БЕЛ': '#F04500',
    'СТЕМ': '#00991A',
    'Чужди езици': '#7F2985',
    'Дипломни проекти': '#1B40B5',
    'ДРУГИ': '#FFAD00', # TODO: Rename to Други
    'БЕЗ': '#683501' # TODO: Rename to Неявили се
}


CustomizeChart = Callable[[alt.Chart], alt.Chart]


def get_subject_group_altair_color(**kwargs) -> alt.Color:
    scale = alt.Scale(
        domain=list(SUBJECT_GROUP_COLOR_MAPPING.keys()),
        range=list(SUBJECT_GROUP_COLOR_MAPPING.values()),
    )
    return alt.Color(
        'subject_group:N',
        scale=scale,
        **kwargs
    )


@st.cache_data(ttl='1h')
def create_subjectgroup_charts(data: pd.DataFrame) -> tuple[alt.Chart, alt.Chart, alt.Chart]:
    """
    The `data` dataframe is expected to contain columns `year`, `subject_group`,
    `total_people`, `total_people_percent` and `score`.

    The result will be:
     * two mark_line charts representing how total_people
       and total_people_percent change over the years.
     * another mark_line chart representing the average score change over the
       years

    All result charts:
     * will display each subject_group with different color.
     * come with a drop-down menu which will highlight
       the selected subject_group.
    """

    subject_groups_sorted = [
        s for s in data['subject_group'].unique() if s != 'Дипломни проекти'
    ] + ['Дипломни проекти']

    color = get_subject_group_altair_color(
        title=None,
        legend=alt.Legend(orient='top'),
        sort=subject_groups_sorted,
    )

    base_year_chart = (
        alt.Chart(data)
        .encode(
            alt.X('year:O', title=None, axis=alt.Axis(labelAngle=0)),
        )
    )

    percent_bar_chart = (
        base_year_chart
        .mark_bar()
        .encode(
            alt.Y(
                'total_people_percent:Q',
                stack='normalize',
                axis=alt.Axis(format='.0%', tickCount=5, title=None),
            ),
            color=color,
            # https://stackoverflow.com/questions/66347857/sort-a-normalized-stacked-bar-chart-with-altair
            order=alt.Order('color_subject_group_sort_index:Q'),
            tooltip=[
                alt.Tooltip('year:O', title='Година'),
                alt.Tooltip('subject_group:N', title='Вид матура'),
                alt.Tooltip('total_people_percent:Q', title='Процент', format='.1%'),
                alt.Tooltip('total_people:Q', title='Брой ученици', format=',d')
            ]
        )
        .transform_filter(
            datum.subject_group != 'БЕЛ'
        )
    )

    count_chart = (
        base_year_chart
        .mark_line(point=True)
        .encode(
            alt.Y('total_people:Q', title=None),
            tooltip=[
                alt.Tooltip('total_people:Q', title='Общ брой ученици')
            ],
            color=color,
            text='total_people:Q'
        )
        .transform_filter(
            datum.subject_group == 'БЕЛ'
        )
    )

    count_text_chart = (
        count_chart
        .mark_text(
            align='center',
            dy=15,
            fontWeight='bold'
        )
    )

    year_chart = (
        (percent_bar_chart + count_chart + count_text_chart)
        .resolve_scale(y='independent')
        .properties(
            title='% от общия брой ученици'
        )
    )

    score_chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            alt.X('year:O', title=None, axis=alt.Axis(labelAngle=0)),
            alt.XOffset('subject_group:N', sort=subject_groups_sorted),
            alt.Y(
                'score:Q',
                axis=alt.Axis(tickCount=2, format='.2f'),
                title=None,
                scale=alt.Scale(domainMin=0.0, domainMax=6.0)
            ),
            color=color,
            tooltip=[
                alt.Tooltip('year:O', title='Година'),
                alt.Tooltip('subject_group:N', title='Вид матура'),
                alt.Tooltip('score:Q', title='Среден успех', format='.2f'),
                alt.Tooltip('total_people:Q', title='Брой ученици', format=',d')
            ]
        )
        .properties(title='Среден успех')
    )

    return year_chart, score_chart

def create_total_people_chart(data: pd.DataFrame) -> alt.Chart:
    years = data['year'].unique().tolist()
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
        alt.Chart(data)
        .mark_point()
        .encode(
            alt.X('total_people:Q', title='Брой явили се ученици'),
            alt.Y('region:N', title='Област'),
            color=year_color,
        )
        .properties(
            width=800,
        )
        .add_params(
            selection_year
        )
    )

    return summary_chart
