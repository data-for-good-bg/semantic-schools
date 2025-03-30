import streamlit as st

# Configure the main page
st.set_page_config(
    page_title='Данни за Добро - образователни данни',
    layout='wide',
    initial_sidebar_state='collapsed'
)

pg = st.navigation([
    st.Page("./pages/dzi_data.py", title="ДЗИ Данни"),
    st.Page("./pages/nvo_data.py", title="НВО Данни")
])

pg.run()