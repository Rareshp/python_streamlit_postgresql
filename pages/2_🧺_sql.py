import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import pandas as pd
import datetime

from postgresql_definitions import * # this is for table definition
from sqlalchemy import select, insert, update, delete

import plotly.express as px

# --- Function definitions ---
def int_separators(option):
    return f"{option:,d}"

# @st.cache_data
def load_data():
    return conn.query("SELECT * FROM my_table order by timestamp desc;", ttl="5s")

def find_most_recent_in_df(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    recent_indices = df.groupby('tag_name')['timestamp'].idxmax()
    return df.loc[recent_indices]

# https://docs.streamlit.io/knowledge-base/using-streamlit/how-to-get-row-selections
def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)

def find_aggregate_occurrences_in_df(df, selections, agg_function):
    # selections is columns after timestamp
    # agg_function: min, max
    result_list = []

    for tag_name in selections:
        # Apply the specified aggregation function
        agg_value = getattr(df[tag_name], agg_function)()
        agg_occurrences = df[df[tag_name] == agg_value]

        # Add each occurrence to the result list
        for index, row in agg_occurrences.iterrows():
            result_list.append({
                'timestamp': row['timestamp'],
                tag_name: agg_value
            })

    return pd.DataFrame(result_list)

# ----------------------------

conn = st.connection("postgresql", type="sql")

today = datetime.datetime.now()
yesterday = (today - datetime.timedelta(1))
two_days_ago = (yesterday - datetime.timedelta(1))

# this is used for dataframe display
column_config={
    #  "id": st.column_config.NumberColumn("Id"),
    #  "tag_name": "Tag name",
    "num_value": st.column_config.NumberColumn(
        "Numeric value",
        format="%d",
    ),
    "str_value": st.column_config.TextColumn(
        "String Value",
        help="Used for strings: selections and comments"
    ),
    "timestamp": st.column_config.DatetimeColumn(
        "Date",
        format="DD-MM-YYYY",
        #  step=86400 # whole day
    ),
}

# ----------------------------

st.header("Postgres interactions")

if 'e-data' not in st.session_state or 'p-data' not in st.session_state:
    st.warning("Please go back to input page to fill the forms!")
    switch = st.button("↩️  Input page")
    if switch:
        switch_page("input")
else:

    tab_insert, tab_read, tab_change, tab_calc = st.tabs(["Insert", "Read", "Change", "Calculations"])

    with tab_insert:
        data = {**st.session_state["e-data"], **st.session_state["p-data"], **st.session_state["calculated"]}

        insert_list = []
        date = st.date_input("Select date to insert at", yesterday, format="DD-MM-YYYY")
        
        for tag in data.keys():
            if type(data[tag]) == int or type(data[tag]) == bool:
                insert_list.append(
                        {
                            "tag_name": tag,
                            "num_value": int(data[tag]),
                            "timestamp": date
                        }
                )
            elif type(data[tag]) == str:
                insert_list.append(
                        {
                            "tag_name": tag,
                            "str_value": data[tag],
                            "timestamp": date
                        }
                )
        with st.form("add_tags"):
            submit_button = st.form_submit_button(label="Submit Data")
            if submit_button:
                with conn.session as session:
                    session.execute(insert(my_table), insert_list)
                    # NOTE, you can also insert with manual query instead, but it also needs a for loop
                    #  conn.execute( text("INSERT INTO my_table (x, y) VALUES (:x, :y)"), insert_list,)
                    session.commit()
                st.success("Data sent")

        with st.expander("Data to be sumbited"):
            st.write(insert_list)

    with tab_read:
        df2 = load_data()

        start_date = st.date_input("Start date:", yesterday, format="DD-MM-YYYY")
        end_date   = st.date_input("End date:",   today, format="DD-MM-YYYY")

        # instead of hard coding a tag list, let's query them, excluding comments
        tag_names = conn.query("""
            SELECT DISTINCT tag_name FROM my_table
            WHERE tag_name NOT LIKE '%comment%'
              AND tag_name NOT LIKE '%category%'
            order by tag_name asc;
        """, ttl="10m")

        selections = st.multiselect("Choose tags", tag_names)

        if st.button("Load"):
            if selections == []:
                st.warning("Selection is empty!")

            # Construct the dynamic SQL query to retrieve data
            # NOTE: postgresql has a crostab, but it is easier to pivot the dataframe
            sql_query = f"""
                SELECT timestamp, tag_name, num_value FROM my_table
                WHERE tag_name IN ('{"', '".join([f'{tag}' for tag in selections])}')
                AND timestamp BETWEEN '{start_date}' and '{end_date}';
            """

            df = conn.query(sql_query, ttl="1m")


            if df.empty:
                st.warning("Unable to retrieve any data. Maybe change start / end dates?")
            else:
                # we need to convert the timestamps first
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.date
                # NOTE: we can also slice the dataframe like so, but is best to query less data!
                #  sl = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]

                # Use pivot_table to handle duplicate entries by aggregating num_value
                pivot_df = df.pivot_table(index='timestamp', columns='tag_name', values='num_value', aggfunc='sum')
                # this is line is needed for plotly later to avoid:
                # ValueError: Value of 'x' is not the name of a column in 'data_frame'. Expected one of [] but received: timestamp
                pivot_df.reset_index(inplace=True)

                # Display the resulting dataframe
                st.write("All data")
                st.dataframe(pivot_df,  use_container_width=True)

                # NOTE: you can also highlight min and max directly, but it requires newer packages
                # also, having separate dataframes allows for easier csv downloads

                #  st.dataframe(
                    #  pivot_df.style.highlight_max(axis=0, props='background-color:green;')
                                   #  .highlight_min(axis=0, props='background-color:yellow;')
                #  )

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("Min values")
                    # Easier to do it like this, but I want to display all occurences and timestamp
                    #  st.dataframe(pivot_df.min(numeric_only=True), use_container_width=True)

                    # NOTE: one could use this for individual dataframes:
                    # see: https://stackoverflow.com/questions/58682893/select-a-pandas-dataframe-row-where-column-has-minimum-value
                    #  for tag_name in selections:
                        #  st.dataframe((pivot_df[pivot_df[tag_name]==pivot_df[tag_name].min()][['timestamp', tag_name]]))

                    st.dataframe(find_aggregate_occurrences_in_df(pivot_df, selections, 'min'), hide_index=True)

                with col2:
                    st.write("Max values")
                    # st.dataframe(pivot_df.max(numeric_only=True), use_container_width=True)
                    #  for tag_name in selections:
                        #  st.dataframe((pivot_df[pivot_df[tag_name]==pivot_df[tag_name].max()][['timestamp', tag_name]]))

                    st.dataframe(find_aggregate_occurrences_in_df(pivot_df, selections, 'max'), hide_index=True)

                with col3:
                    # NOTE: pandas mean is arithmetic average
                    st.write("Average values")
                    st.dataframe(pivot_df.mean(numeric_only=True), use_container_width=True)

                fig_bar = px.bar(pivot_df, x='timestamp', y=pivot_df.columns[1:], title='Side-by-Side Bar Chart',
                        labels={'value': 'Num Value', 'variable': 'Tag Name'}, barmode='group')
                fig = px.line(pivot_df, x='timestamp', y=pivot_df.columns[1:], title='Line Chart with Multiple Y-Axes',
                        labels={'value': 'Num Value', 'variable': 'Tag Name'},
                        line_shape='linear', render_mode='svg')

                st.plotly_chart(fig_bar, use_container_width=True)
                st.plotly_chart(fig, use_container_width=True)

    with tab_change:
        df2 = load_data()
        st.subheader("Changing data")
        #  st.dataframe(df2, column_config=column_config, hide_index=True)
        #  selected_id = st.selectbox( "Select what row to delete", options=df2['id'].tolist(), format_func=int_separators)

        actions = ["Modify row", "Delete row"]
        action = st.selectbox("Choose action", actions)

        # st.dataframe(df2, column_config=column_config, hide_index=True)
        st.write("Use the checkmarks to select rows:")
        selection  = dataframe_with_selections(df2)
        changed_df = st.data_editor(selection)
        changed_dict = changed_df.to_dict('records')

        if action == actions[0]:
            #  Update 'nan' to None and convert timestamp strings to datetime objects
            for record in changed_dict:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    if key == 'timestamp':
                        record[key] = pd.to_datetime(value).to_pydatetime()

            submit_changes = st.button(label="Submit Data")
            if submit_changes:
                with conn.session as session:
                    session.execute(update(my_table), changed_dict)
                    session.commit()
                st.success("Data sent:")
                st.success(changed_dict)
                st.success("You may have to reload the page to see the changes")

        if action == actions[1]:
            id_list = [record['id'] for record in changed_dict if 'id' in record]
            if st.button("Delete"):
                with conn.session as session:
                    session.execute(delete(my_table).where(my_table.id.in_(id_list)))
                    #  session.execute(text("DELETE FROM my_table where id=:id"), {"id": selected_id})
                    session.commit()
                st.success("Row successfully deleted!")

    with tab_calc:
        st.write("Let's make some calculations")

        # hard coded tags for the example
        sql_query = f"""
            SELECT timestamp, tag_name, num_value FROM my_table
            WHERE tag_name IN ('E1', 'E2')
        """
        df1  = find_most_recent_in_df(conn.query(sql_query + f" AND timestamp BETWEEN '{yesterday}'    and '{today}'; ",     ttl="1m"))
        df2  = find_most_recent_in_df(conn.query(sql_query + f" AND timestamp BETWEEN '{two_days_ago}' and '{yesterday}'; ", ttl="1m"))

        st.dataframe(df1)
        st.dataframe(df2)

        # Create a set of unique tag names
        # of course, this can be manually defined before running the query
        unique_tags = sorted(set(df1['tag_name']).union(set(df2['tag_name'])))

        result_list = []

        for tag_name in unique_tags:
            # Extract num_values for the current tag name from each DataFrame
            num_value_df1 = df1.loc[df1['tag_name'] == tag_name, 'num_value'].values
            num_value_df2 = df2.loc[df2['tag_name'] == tag_name, 'num_value'].values

            # If tag_name is present in both DataFrames, calculate the difference
            if len(num_value_df1) > 0 and len(num_value_df2) > 0:
                diff_value = num_value_df1[0] - num_value_df2[0]

                # Append the result to the list as a dictionary
                result_list.append({'tag_name': tag_name + '_index', 'difference': diff_value})
        # Iterate over each unique tag name

        st.write("Simple difference")
        st.dataframe(result_list)

        modifiers = {
            'E1_index': 1.225,
            'E2_index': 2**0.5 * 3
        }

        st.write("Difference with modifiers applied")
        m_result_list = result_list.copy()
        for i in range(len(m_result_list)):
            m_result_list[i]['difference'] = m_result_list[i]['difference'] * modifiers[m_result_list[i]['tag_name']]
        st.dataframe(m_result_list)


