import pandas as pd
import altair as alt


def create_line_charts_for_people_aggregated_data(people_data: pd.DataFrame) -> tuple[alt.Chart, alt.Chart]:
    """
    The `people_data` dataframe is expected to contain columns `year`, `subject_group`,
    `total_people` and `total_people_percent`.

    The result will be two mark_line charts representing how total_people
    and total_people_percent change over the years.

    The dataframe could contain more columns, the caller may use .facet() or
    .repeat() to create charts for each value of such columns.

    Both charts
     * will display each subject_group with different color.
     * come with a drop-down menu which will highlight
       the selected subject_group.
    """

    ### create charts
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

    values_chart = (
        alt.Chart(people_data)
        .mark_line(point=True)
        .encode(
            alt.X('year:O', title='Година'),
            alt.Y('total_people:Q', axis=alt.Axis(format='.0f'), title='Брой явили се ученици'),
            color=color
        )
        .add_params(
            selection_subject_group
        )
    )

    percent_chart = (
        alt.Chart(people_data)
        .mark_line(point=True)
        .encode(
            alt.X('year:O', title='Година'),
            alt.Y('total_people_percent:Q', axis=alt.Axis(format='.0%'), title='Процент от общият брой ученици'),
            color=color
        )
        .add_params(
            selection_subject_group
        )
    )

    return values_chart, percent_chart
