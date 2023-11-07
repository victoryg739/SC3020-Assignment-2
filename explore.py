import psycopg2
import re
from config import db_host, db_name, db_user, db_password
from graphviz import Digraph
from PyQt5.QtWidgets import  QTreeWidgetItem


def get_execution_plan(query):
    """
    This function gets the execution plan for the given SQL query
    and returns it as a string.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()

        # Use EXPLAIN to get the plan
        execution_plan_query = f"EXPLAIN (FORMAT JSON) {query};"
        cursor.execute(execution_plan_query)

        # Fetch the plan
        plan = cursor.fetchall()

        # Close cursor and connection
        cursor.close()
        conn.close()

        return plan[0][0][0]['Plan']  # Assume there is at least one plan
    except psycopg2.Error as e:
        raise RuntimeError(f"Error getting the execution plan: {e}")

def build_tree_widget_item(plan):
    """
    This function creates a QTreeWidgetItem based on the plan node.
    """
    item = QTreeWidgetItem([plan['Node Type']])
    for child in plan.get('Plans', []):
        child_item = build_tree_widget_item(child)
        item.addChild(child_item)
    return item

def display_tree_image(plan, filename='plan'):
    """
    This function visualizes the execution plan using Graphviz launched in a PDF format.
    """
    def add_nodes_edges(plan, parent=None):
        if parent is None:  # Create the root node
            parent = str(plan['Node Type'])
            dot.node(parent, label=parent)
        for child in plan.get('Plans', []):
            child_node = str(child['Node Type'])
            dot.node(child_node, label=child_node)
            dot.edge(parent, child_node)
            add_nodes_edges(child, parent=child_node)
    
    dot = Digraph(comment='Query Execution Plan')

    # Start adding nodes and edges
    add_nodes_edges(plan)

    # Save the output
    dot.render(filename, view=True)
    
def execute_query_in_database(query):
    try:
        results = {}
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
        ctid_queries = convert_query_to_ctid_query(query)
        
        for table_name in ctid_queries:
            query  = ctid_queries[table_name]
            cursor.execute(query)
            # Fetch and format the results for each query
            result = cursor.fetchall()
            results[table_name] = result
            
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        # for table_name in results:
        #     print(table_name,": ",results[table_name],"\n\n")
            
        return results
    except psycopg2.Error as e:
        raise RuntimeError(f"Error executing the query: {e}")

def get_table_names(query):
    # Regular expression to match table names mentioned after "FROM" or "JOIN"
    table_pattern = r'\b(FROM|JOIN)\s+([a-zA-Z_][a-zAZ0-9_\.]+(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_\.]+)*)'

    # Find all matches of the table pattern in the SQL query
    matches = re.findall(table_pattern, query, flags=re.IGNORECASE)

    # Extract only the table names, not the "FROM" or "JOIN" keywords
    table_names = [table.replace(' ', '').split(',') for _, table in matches]
    table_names = [item for sublist in table_names for item in sublist]
    table_names = [name.strip() for name in table_names]
    table_names = list(set(table_names))

    return table_names    

def convert_query_to_ctid_query(query):
    if "ctid" in query.lower():
        raise RuntimeError(f"\"ctid\" is a reserved word, please remove it from the query")
    
    table_names = get_table_names(query)
    ctid_queries = {}
    select_index = query.upper().find("SELECT")
    
    if select_index != -1:
        insert_position = select_index + len("SELECT")
        
        for table_name in table_names:
            #erase ";" if any
            if query[-1]==";":
                new_query = query[:-1]
            else:
                new_query = query
            #add (table_name).ctid to the query
            new_query = new_query[:insert_position] + " " + table_name + ".ctid AS ctid" + ", " + new_query[insert_position:]

            #project the ctid column
            new_query = "SELECT ctid FROM (" + new_query + ")" 

            #retrieve all the tuples in a given table based on ctid
            new_query = "SELECT ctid, * FROM " + table_name + " WHERE ctid IN (" + new_query + ")" 

            ctid_queries[table_name] = new_query
                
        return ctid_queries
    else:
        raise RuntimeError(f"Error executing the query")

    


