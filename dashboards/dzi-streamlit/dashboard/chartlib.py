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


    values_chart = (
        alt.Chart(people_data)
        .mark_line(point=True)
        .encode(
            alt.X('year:O', title='Година'),
            alt.Y('total_people:Q', axis=alt.Axis(format='.0f'), title='Брой явили се ученици'),
        )
    )

    percent_chart = (
        alt.Chart(people_data)
        .mark_line(point=True)
        .encode(
            alt.X('year:O', title='Година'),
            alt.Y('total_people_percent:Q', axis=alt.Axis(format='.0%'), title='Процент от общият брой ученици'),
        )
    )

    return values_chart, percent_chart
