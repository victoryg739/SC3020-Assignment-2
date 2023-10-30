import psycopg2
from config import db_host, db_name, db_user, db_password

def execute_query_in_database(query):
    try:
        # Establish a database connection
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )

        # Create a cursor object
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(query)

        # Fetch and format the results
        results = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return results

    except psycopg2.Error as e:
        return f"Error: {e}"

