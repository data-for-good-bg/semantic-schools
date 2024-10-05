import pandas as pd
import altair as alt


def create_charts_for_subjet_group(data: pd.DataFrame, subject_col: str, subject_percent_col: str) -> tuple[alt.Chart, alt.Chart]:
    poeple_per_year_chart_base = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            alt.X(f'{subject_col}:Q', title='Брой явили се ученици'),
            alt.Y('year:O', title='Година'),
            alt.Color('year:N', title='Година')
        )
    )
    value_text_chart = (
        poeple_per_year_chart_base
        .mark_text(align='right', dx=-3)
        .encode(alt.Text(subject_col), alt.Color())
    )
    poeple_per_year_chart = poeple_per_year_chart_base + value_text_chart

    people_per_year_percent_chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            alt.X(f'{subject_percent_col}:Q', axis=alt.Axis(format='.0%'), title=f'Брой ученици избрали {subject_col}, като % от общия брой'),
            alt.Y('year:O', title='Година'),
            alt.Color('year:N', title='Година')
        )
    )
    people_per_year_percent_chart = people_per_year_percent_chart + (
        people_per_year_percent_chart
        .mark_text(align='right', dx=-3)
        .encode(alt.Text(subject_percent_col, format='.0%'), alt.Color())
    )

    return poeple_per_year_chart, people_per_year_percent_chart