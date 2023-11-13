import psycopg2
from config import db_host, db_name, db_user, db_password
# from graphviz import Digraph
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
        execution_plan_query = f"EXPLAIN (analyze, buffers, costs on, FORMAT JSON) {query};"
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
    
    # dot = Digraph(comment='Query Execution Plan')

    # Start adding nodes and edges
    add_nodes_edges(plan)

    # Save the output
    # dot.render(filename, view=True)
    
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

