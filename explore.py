import psycopg2
import json


def connect_to_db():
    """
    Connect to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="S9911832F",
            host="localhost"
        )
        return conn
    except Exception as e:
        print(f"Unable to connect to the database. Error: {e}")
        return None

def get_query_plan(sql_query):
    """
    Get the Query Execution Plan (QEP) for a given SQL query.
    """
    conn = connect_to_db()
    if not conn:
        return None
    
    cur = conn.cursor()
    cur.execute(f"EXPLAIN (FORMAT JSON) {sql_query}")
    plan = cur.fetchall()
    conn.close()
    qep = plan[0][0]   # Directly assign without using json.loads
    return qep


def analyze_disk_blocks(qep):
    """
    Analyze the QEP and return the disk blocks accessed by the query.
    This is a heuristic based extraction. Might need further refinement.
    """
    disk_blocks_info = {
        "table": "",
        "blocks_read": 0
    }
    
    # Assuming the table is mentioned in 'Relation Name' in the QEP
    if 'Relation Name' in qep[0]['Plan']:
        disk_blocks_info["table"] = qep[0]['Plan']['Relation Name']

    # Assuming blocks read can be inferred from the 'rows' in the QEP
    if 'rows' in qep[0]['Plan']:
        disk_blocks_info["blocks_read"] = qep[0]['Plan']['rows']

    return disk_blocks_info

def extract_qep_features(qep):
    """
    Extract and return features of the QEP such as buffer size, cost, etc.
    This is a heuristic based extraction. Might need further refinement.
    """
    features = {
        "start_cost": qep[0]['Plan']['Startup Cost'],
        "total_cost": qep[0]['Plan']['Total Cost'],
        "rows": qep[0]['Plan']['Plan Rows'],
        "width": qep[0]['Plan']['Plan Width']
    }

    return features

if __name__ == "__main__":
    sql_query = "SELECT * FROM customer WHERE c_custkey = 1"
    qep = get_query_plan(sql_query)
    print("Disk Blocks Accessed:", analyze_disk_blocks(qep))
    print("QEP Features:", extract_qep_features(qep))
