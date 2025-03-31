import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import branca.colormap as cm

from lib import data

st.write('# НВО Данни')


# Load NVO data with coordinates
nvo_examinations = data.load_nvo_examinations()

# Create an expander for the map and filters
with st.expander(label='### Визуализация на училищата спрямо промяната в резултатите от НВО', expanded=True):

    st.write('### Визуализация на училищата спрямо промяната в резултатите от НВО')
    # Extract grade level from subject

    years = sorted(nvo_examinations['year'].unique(), reverse=True)
    # exclude the latest year
    years = years[0:-1]
    latest_year = years[0] if years else None

    grade_levels = sorted(nvo_examinations['grade_level'].unique())

    subjects = sorted(nvo_examinations['subject'].unique())

    # Create columns for filters
    col1, col2, col3 = st.columns(3)

    # Year selector
    with col1:
        selected_year = int(st.selectbox(
            'Изберете година',
            options=years,
            index=0,  # Default to the latest year
            key='nvo_year_selector'
        ))

    # Grade level selector
    with col2:
        selected_grade = int(st.selectbox(
            'Изберете клас',
            options=grade_levels,
            index=0,  # Default to the first grade level
            key='nvo_grade_selector'
        ))

    # Subject selector
    with col3:
        selected_subject = st.selectbox(
            'Изберете предмет',
            options=subjects,
            index=0,  # Default to the first subject
            key='nvo_subject_selector'
        )

    # This is now our grade_data (already filtered by grade and subject)
    grade_data = data.load_nvo_data_with_coords(selected_grade, selected_subject)

    # Filter data for the selected year
    selected_year_data = grade_data[grade_data['year'] == selected_year]

    # Find the previous year's data
    previous_year = selected_year - 1

    previous_year_data = grade_data[
        (grade_data['year'] == previous_year)
    ]

    # Merge current and previous year data
    merged_data = selected_year_data.merge(
        previous_year_data[['school_id', 'score', 'people']],
        on='school_id',
        how='left',
        suffixes=('', '_prev')
    )

    # Fill with 0 when `people` in the previous year is NaN
    merged_data['people_prev'] = merged_data['people_prev'].fillna(0)

    # Calculate delta
    merged_data['delta'] = merged_data['score'] - merged_data['score_prev']

    # Handle schools that don't have previous year data
    merged_data['delta'] = merged_data['delta'].fillna(0)

    # Show summary statistics
    st.write("### Обобщена статистика")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            'Максимален резултат',
            f"{selected_year_data['score'].max():.2f}",
            f"{selected_year_data['score'].max() - previous_year_data['score'].max():.2f}"
        )
        st.metric(
            "Среден резултат",
            f"{selected_year_data['score'].mean():.2f}",
            f"{selected_year_data['score'].mean() - previous_year_data['score'].mean():.2f}"
        )
        st.metric(
            "Минимален резултат",
            f"{selected_year_data['score'].min():.2f}",
            f"{selected_year_data['score'].min() - previous_year_data['score'].min():.2f}",
        )

    with col2:
        improved_count = (merged_data['delta'] > 0).sum()
        total_count = len(merged_data)
        st.metric(
            "Училища с подобрение",
            f"{improved_count} ({improved_count/total_count*100:.1f}%)"
        )
        decreased_count = (merged_data['delta'] < 0).sum()
        st.metric(
            "Училища с влошаване",
            f"{decreased_count} ({decreased_count/total_count*100:.1f}%)"
        )
        unchanged_count = (merged_data['delta'] == 0).sum()
        st.metric(
            "Училища без промяна",
            f"{unchanged_count} ({unchanged_count/total_count*100:.1f}%)"
        )

    with col3:
        st.metric(
            "Най-голямо подобрение",
            f"{merged_data['delta'].max():.2f}"
        )
        st.metric(
            "Най-голямо влошаване",
            f"{merged_data['delta'].min():.2f}"
        )


    # Create base map centered on Bulgaria
    m = folium.Map(location=[42.7339, 25.4858], zoom_start=7)

    # Create color map for delta scores
    delta_min = merged_data['delta'].min()
    delta_max = merged_data['delta'].max()

    # Ensure colormap range is symmetric around zero
    abs_max = max(abs(delta_min), abs(delta_max))
    colormap = cm.LinearColormap(
        colors=['red', 'yellow', 'green'],
        vmin=-abs_max,
        vmax=abs_max
    )

    # Add colormap to map
    colormap.add_to(m)
    colormap.caption = 'Промяна в резултата спрямо предходната година'

    # Calculate marker sizes based on absolute delta
    merged_data['abs_delta'] = merged_data['delta'].abs()
    max_abs_delta = merged_data['abs_delta'].max()
    min_radius = 5
    max_radius = 15

    # Create feature groups for different school categories
    highlighted_schools = folium.FeatureGroup(name='Училища от интерес')

    # Define bucket size for delta values
    bucket_size = 20

    # Create buckets for delta values
    delta_min_rounded = int(delta_min // bucket_size) * bucket_size
    delta_max_rounded = int(delta_max // bucket_size + 1) * bucket_size
    delta_buckets = {}

    # Create feature groups for each bucket
    for i in range(delta_min_rounded, delta_max_rounded + bucket_size, bucket_size):
        bucket_name = f'Училища с промяна {i} до {i+bucket_size}'
        delta_buckets[i] = folium.FeatureGroup(name=bucket_name)

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
    for _, row in merged_data.iterrows():
        # Skip schools with missing coordinates
        if pd.isna(row['slongitude']) or pd.isna(row['slatitude']):
            continue

        radius = min_radius + (row['abs_delta'] / max_abs_delta) * (max_radius - min_radius)

        # Create popup text
        popup_text = f"""
        <b>{row['school']}</b><br>
        ID: {row['school_id']}<br>
        Област: {row['region']}<br>
        Община: {row['mun']}<br>
        Населено място: {row['place']}<br>
        Резултат {selected_year}: {row['score']:.2f} т., брой ученици: {int(row['people'])}<br>
        Резултат {previous_year}: {row['score_prev']:.2f} т., брой ученици: {int(row['people_prev'])}<br>
        Промяна: {row['delta']:.2f}
        """

        # Determine if this school should be highlighted
        is_highlighted = str(row['school_id']) in schools_with_special_styling

        # Create marker with appropriate styling
        marker_params = {
            'radius': radius,
            'popup': folium.Popup(popup_text, max_width=300),
            'tooltip': f"{row['school']} ({row['delta']:.2f} == {row['score']:.2f} - {row['score_prev']:.2f})",
            'fill': True,
            'fill_color': colormap(row['delta']),
            'color': 'black' if is_highlighted else 'gray',
            'weight': 2 if is_highlighted else 1,
            'fill_opacity': 0.7,
        }

        # Create the circle marker
        circle = folium.CircleMarker(
            location=[row['slatitude'], row['slongitude']],
            **marker_params
        )

        # Add to appropriate feature group
        if is_highlighted:
            circle.add_to(highlighted_schools)
        else:
            # Find the appropriate bucket for this school based on delta
            bucket_key = int(row['delta'] // bucket_size) * bucket_size
            # Ensure the bucket exists (in case of rounding issues)
            if bucket_key not in delta_buckets:
                bucket_key = min(delta_buckets.keys(), key=lambda x: abs(x - bucket_key))
            circle.add_to(delta_buckets[bucket_key])

    # Add feature groups to map
    # Add all delta buckets to the map
    for bucket_key in sorted(delta_buckets.keys()):
        delta_buckets[bucket_key].add_to(m)

    # Add highlighted schools last so they appear on top
    highlighted_schools.add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Display the map
    st.write(f'Карта на промяната в резултатите между {previous_year} и {selected_year} година за {selected_subject}')
    folium_static(m, width=1000, height=600)

    # Add explanatory text
    st.markdown("""
    **Легенда:**
    - **Цвят на кръга**: Показва промяната в резултата спрямо предходната година (зелено = подобрение, червено = влошаване)
    - **Размер на кръга**: Показва големината на промяната (по-голям кръг = по-голяма промяна)
    """)
