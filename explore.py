import psycopg2
from psycopg2 import connect
import re

from PyQt5.QtWidgets import  QTreeWidgetItem
try:
    from graphviz import Digraph
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

def get_execution_plan(query):
    from interface import db_host, db_name, db_user, db_password
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
        execution_plan_query = f"EXPLAIN (analyze, buffers, costs on, FORMAT JSON) {query};"
        cursor.execute(execution_plan_query)

        # Fetch the plan
        plan = cursor.fetchall()

        # Close cursor and connection
        cursor.close()
        conn.close()

        return plan[0][0][0]['Plan']  # Assume there is at least one plan
    except Exception as e:
        raise RuntimeError(f"Error getting the execution plan: {e}")

def build_tree_widget_item(plan):
        """
        Recursively create QTreeWidgetItem based on the plan node.
        """
        item = QTreeWidgetItem([plan['Node Type']])
        for key, value in plan.items():
            if key == 'Plans':
                for child in value:
                    child_item = build_tree_widget_item(child)
                    item.addChild(child_item)
            elif key != 'Node Type':
                # Add other details as child items
                child_item = QTreeWidgetItem(["{}: {}".format(key, value)])
                item.addChild(child_item)
                if(key=='Shared Hit Blocks' or key=='Shared Read Blocks'):
                    child_item = QTreeWidgetItem(["{} Size: {}kB".format(key, value*8)])
                    item.addChild(child_item)
        return item

def display_tree_image(plan, filename='plan-svg'):
    """
    This function visualizes the execution plan using Graphviz launched in a PDF format.
    """

    if not GRAPHVIZ_AVAILABLE:
        print("Graphviz is not available. Skipping visualization.")
        return

    try:
        counter = 0
        def add_nodes_edges(plan, parent=None):
            nonlocal counter
            counter+=1
            if parent is None:  # Create the root node
                parent = str(plan['Node Type'])+"_"+str(counter)
                dot.node(parent, label=str(plan['Node Type']), shape='box')
            counter+=1
            for child in plan.get('Plans', []):
                child_node = str(child['Node Type'])+"_"+str(counter)
                dot.node(child_node, label=str(child['Node Type']), shape='box')
                dot.edge(parent, child_node)
                add_nodes_edges(child, parent=child_node)
    
        dot = Digraph(comment='Query Execution Plan', format='svg')

        # Start adding nodes and edges
        add_nodes_edges(plan)

        # Save the output
        dot.render(filename, view=False)
    except Exception as e:
        print(f"An error occurred while creating the visualization: {e}")

    
def execute_query_in_database(query):
    from interface import db_host,db_name,db_user,db_password
    print(db_host)
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
        isErrorFirstPass = False
        for table_name in ctid_queries:
            ctid_query  = ctid_queries[table_name]
            try:
                cursor.execute(ctid_query)
            except psycopg2.Error as e:
                isErrorFirstPass = True
                continue
            # Fetch and format the results for each query
            result = cursor.fetchall()
            results[table_name] = result
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        # If first pass error, we check 2nd pass for aggregate function
        if isErrorFirstPass:
            # Establish a database connection
            conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password
            )
            # Create a cursor object
            cursor = conn.cursor()
            ctid_queries = convert_query_to_ctid_query(query, checkAggregate = isErrorFirstPass)
            for table_name in ctid_queries:
                ctid_query  = ctid_queries[table_name]
                try:
                    cursor.execute(ctid_query)
                except psycopg2.Error as e:
                    raise RuntimeError(f"Error executing the query: {e}")
                # Fetch and format the results for each query
                result = cursor.fetchall()
                results[table_name] = result
            # Close the cursor
            cursor.close()
            conn.close()
            
        # Close the connection
        conn.close()
            
        return results
    except Exception as e:
        raise RuntimeError(f"Error executing the query: {e}")

def get_columns_for_table(table_name):
    from interface import db_host,db_name,db_user,db_password
    # Initialize the list of columns, starting with the ctid
    columns = ["ctid"]
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
        # Query to get all column names for the table
        column_query = f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' ORDER BY ordinal_position"
        # Execute and fetch the query
        cursor.execute(column_query)
        columns_result = cursor.fetchall()
        # Extract column names from the result
        for col in columns_result:
            columns.append(col[0])
            
        # Close the cursor
            cursor.close()
            conn.close()
    except Exception as e:
        raise RuntimeError(f"Error retrieveing table headers")
    return columns

def get_table_names(query):
    # Regular expression to match table names mentioned after "FROM" or "JOIN"
    table_pattern = r'\b(FROM|JOIN)\s+([a-zA-Z_][a-zAZ0-9_\.]+(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_\.]+)*)'

    # Find all matches of the table pattern in the SQL query
    matches = re.findall(table_pattern, query, flags=re.IGNORECASE)

    # Extract only the table names
    table_names = [table.replace(' ', '').split(',') for _, table in matches]
    table_names = [item for sublist in table_names for item in sublist]
    table_names = [name.strip() for name in table_names]
    table_names = list(set(table_names))

    return table_names    

def convert_query_to_ctid_query(query, checkAggregate = False):
    if "ctid" in query.lower():
        raise RuntimeError(f"\"ctid\" is a reserved word, please remove it from the query")
    
    table_names = get_table_names(query)
    ctid_queries = {}
    query = query.strip()
    select_index = query.upper().find("SELECT")
    
    for table_name in table_names:
        #erase ";" if any
        if query[-1]==";":
            new_query = query[:-1]
        else:
            new_query = query
            
        # Regular expression to identify UNION, UNION ALL, INTERSECT, or EXCEPT
        set_operation_regex = r'\b(UNION\s+ALL|UNION|INTERSECT|EXCEPT)\b'
        
        # Save the Set Operation
        operators = re.findall(set_operation_regex, query, flags=re.IGNORECASE)
        
        # Split the query based on the pattern
        sub_queries = re.split(set_operation_regex, new_query, flags=re.IGNORECASE)
        sub_queries = [sub_query.strip() for sub_query in sub_queries]
        
        modified_sub_queries = []
        
        # Add ctid to every sub query
        for sub_query in sub_queries:
            select_index = sub_query.upper().find("SELECT")
            insert_position = select_index + len("SELECT")
                
            #add (table_name).ctid to the query
            sub_query = sub_query[:insert_position] + " " + table_name + ".ctid AS ctid" + ", " + sub_query[insert_position:]
            
            #add ctid to the group by clause
            group_by_index = sub_query.upper().find("GROUP BY")
            if group_by_index != -1:
                insert_position = group_by_index + len("GROUP BY")
                sub_query = sub_query[:insert_position] + " " + "ctid" + ", " + sub_query[insert_position:]
            else:
                # If first pass error, we check 2nd pass for aggregate function by adding group by ctid
                if checkAggregate:
                    aggregate_pattern = re.compile(r'\b(COUNT|SUM|AVG|MAX|MIN)\(', re.IGNORECASE)
                    match = aggregate_pattern.search(query)
                    # Insert group by clause before having, order by, or limit
                    if match:
                        if sub_query.upper().find("HAVING") != -1:
                            insert_position = sub_query.upper().rfind("HAVING")-1
                        elif  sub_query.upper().find("ORDER BY") != -1:
                            insert_position = sub_query.upper().rfind("ORDER BY")-1
                        elif sub_query.upper().find("LIMIT") != -1: 
                            insert_position = sub_query.upper().rfind("LIMIT")-1
                        else:
                            insert_position = len(sub_query)
                        sub_query = sub_query[:insert_position] + " " + "GROUP BY" + " " + table_name + ".ctid" + sub_query[insert_position:]
                        
            modified_sub_queries.append(sub_query)
        
        # Merge all the sub queries
        merge_query = ""
        for i in range (len(operators)):
            merge_query = merge_query + modified_sub_queries[i] + " " + operators[i] + " "
        merge_query = merge_query + modified_sub_queries[-1]
        
        #project the ctid column
        merge_query = "SELECT ctid FROM (" + merge_query + ")" 

        #retrieve all the tuples in a given table based on ctid
        merge_query = "SELECT ctid, * FROM " + table_name + " WHERE ctid IN (" + merge_query + ")" 
        
        ctid_queries[table_name] = merge_query

    return ctid_queries


    


