import streamlit as st

st.title("Home page")

st.markdown("""
## Basic Usage
1. use the sidebar menu to navigate to different pages, from top to bottom
2. on the **input** page, you can fill some forms. Additonally extra calculations can be done in the background
3. then move on to **sql** page. Here you have the following tabs:
   - **Insert** - you can insert the form data into Postgresql, at any given date (of course, one could insert today too)
   - **Read** - based on time and tag filtering, retrieve a dataframe of data and show relevant information:
     - min
     - max
     - mean
     - plotly graphs
   - **Change**
     - you can either modify the dataframe then submit the changes to SQL database
     - or you can delete the selected rows entirely
   - **Calculations**
     - we can retrieve data from SQL and perform calculations on that data
""")
