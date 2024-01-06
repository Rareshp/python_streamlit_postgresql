# python_streamlit_postgresql
This is a demo application using streamlit for creating Forms (example using [streamlit-pydantic](https://github.com/LukasMasuch/streamlit-pydantic) and manual definitions). Form data may be used in other calculations too. Inspired by a real world project and also [Sven-Bo tutorials](https://github.com/Sven-Bo/google-sheets-data-entry-form-with-streamlit/blob/main/vendor_app.py).

After forms are filled in, the operator may:
- insert the form data into Postgresql at a given date
- modify or delete rows insert previously
- read data to gain insights

## Setup
### Postgresql
I opted for Postgresql instead of a simpler sqlite, because of production reasons and need to add Timescale later.

#### Docker
For the sake of this demo you can simply use the following docker command; feel free to use dockercompose instead.
```sh
docker run --name postgres -it -p 5432:5432 -e POSTGRES_USER=postgres_user -e POSTGRES_PASSWORD=postgres_password -e POSTGRES_DB=myDataBase postgres
```

Then, you need access to the psql cli:
```sh
docker exec -it postgres psql -U postgres_user -d myDataBase
```

If you see this, everything is good:
```
psql (16.1 (Debian 16.1-1.pgdg120+1))
Type "help" for help.

myDataBase=#
```

You can stop the docker container with this command. Replace "stop" with "start" if you want to start it again.
```sh
docker stop postgres
```

#### Tables
For this demo, I used one simple table. You can create it in psql with this command:
```sql
CREATE TABLE my_table (
        id BIGSERIAL PRIMARY KEY,
        tag_name VARCHAR(80) NOT NULL,
        num_value INTEGER,
        str_value VARCHAR,
        timestamp timestamp DEFAULT (CURRENT_TIMESTAMP) NOT NULL
);
```

The `postgresql_definitions.py` is used for SQLAlchemy.

### Python 
Install the requirements from the requirements.txt file.

For streamlit to be able to connect to Postgresql, you need to make `.streamlit/secrets.toml` file. For the sake of this demo, the file would look like this:
```
[connections.postgresql]
dialect = "postgresql"
host = "localhost"
port = "5432"
database = "myDataBase"
username = "postgres_user"
password = "postgres_password"
```

Then run the streamlit app with:
```sh
streamlit run main.py
```

## Showcase
The forms are used to insert data:
![Screenshot of e-form created with pydantic](./images/e-form.png)
![Screenshot of p-form created manually. Has optional downtime reasons](./images/p-form.png)

Then, we can insert the data at some given date:
![SQL - inserting data](./images/sql-insert.png)

After some inserts data may look like this:
```
myDataBase=# select * from my_table;
 id |     tag_name      | num_value |   str_value    |      timestamp      
----+-------------------+-----------+----------------+---------------------
 42 | E1                |         0 |                | 2024-01-04 00:00:00
 43 | E2                |         0 |                | 2024-01-04 00:00:00
 44 | E3                |         0 |                | 2024-01-04 00:00:00
 45 | E4                |         0 |                | 2024-01-04 00:00:00
 46 | E4_state          |         1 |                | 2024-01-04 00:00:00
 47 | E_comment         |           | no comment     | 2024-01-04 00:00:00
 48 | FIQ               |       130 |                | 2024-01-04 00:00:00
 49 | FIQ_running_hours |        83 |                | 2024-01-04 00:00:00
 50 | P_comment         |           | no comment     | 2024-01-04 00:00:00
 51 | E_sum             |        54 |                | 2024-01-04 00:00:00
 52 | E1                |        12 |                | 2024-01-05 00:00:00
 53 | E2                |        10 |                | 2024-01-05 00:00:00
 54 | E3                |         2 |                | 2024-01-05 00:00:00
 55 | E4                |         6 |                | 2024-01-05 00:00:00
 56 | E4_state          |         1 |                | 2024-01-05 00:00:00
 57 | E_comment         |           | First comment! | 2024-01-05 00:00:00
 58 | FIQ               |       140 |                | 2024-01-05 00:00:00
 59 | FIQ_running_hours |        75 |                | 2024-01-05 00:00:00
 60 | P_comment         |           | P form comment | 2024-01-05 00:00:00
 61 | E_sum             |        30 |                | 2024-01-05 00:00:00
(20 rows)
```

I have also made a page where we can modify or delete rows as well:
![](./images/sql-modify-rows.png)

Finally, this data can be read to perform some calculations such as getting the delta between 2 days, or more complicated calculations:
![Calculations](./images/sql-calculations.png)

... or the data can be used to calculate min, max, mean or be displayed on graphs (using plotly):
![Metrics](./images/sql-metrics.png)

![Graphs](./images/sql-metrics-plotly.png)
