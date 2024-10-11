import pandas as pd
import altair as alt
from typing import Callable, Optional


CustomizeChart = Callable[[alt.Chart], alt.Chart]

def create_subjectgroup_charts(data: pd.DataFrame, customize: Optional[CustomizeChart]) -> tuple[alt.Chart, alt.Chart, alt.Chart]:
    """
    The `data` dataframe is expected to contain columns `year`, `subject_group`,
    `total_people`, `total_people_percent` and `score`.

    The result will be:
     * two mark_line charts representing how total_people
       and total_people_percent change over the years.
     * another mark_line chart representing the average score change over the
       years

    The `customize` callable will be executed on each of the charts,
    it could be used to apply additional properties, encodings, etc.

    The DataFrame could contain more columns, which means `customize`
    could also use .facet() or .repeat() to create multiple charts.

    All result charts:
     * will display each subject_group with different color.
     * come with a drop-down menu which will highlight
       the selected subject_group.
    """

    def _customize(chart: alt.Chart) -> alt.Chart:
        if customize:
            return customize(chart)
        else:
            chart

    subject_groups = data['subject_group'].unique().tolist()
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

    values_chart = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            alt.X('year:O', title='Година'),
            alt.Y('total_people:Q', axis=alt.Axis(format='.0f'), title='Брой явили се ученици'),
            color=color
        )
        .add_params(selection_subject_group)
    )

    percent_chart = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            alt.X('year:O', title='Година'),
            alt.Y('total_people_percent:Q', axis=alt.Axis(format='.0%'), title='Процент от общият брой ученици'),
            color=color
        )
        .add_params(selection_subject_group)
    )

    score_chart = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            alt.X('year:O', title='Година'),
            alt.Y('score:Q', axis=alt.Axis(format='.2f'), title='Среден успех', scale=alt.Scale(domainMin=2.0, domainMax=6.0)),
            color=color
        )
        .add_params(
            selection_subject_group
        )
    )

    return _customize(values_chart), _customize(percent_chart), _customize(score_chart)


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
