import sys
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, \
    QHBoxLayout, QFrame, QScrollArea, QDialog, QTabWidget
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QTreeWidget

from explore import *

class ExecutionPlanDialog(QDialog):
    def __init__(self, plan, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Execution Plan")
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout(self)

        # Create a label for the Execution Plan
        label = QLabel("Execution Plan:")
        layout.addWidget(label)

        # Initialize the QTreeWidget
        plan_tree_widget = QTreeWidget()
        plan_tree_widget.setHeaderLabel("Execution Plan")

        # Generate the tree items from the plan
        root_item = build_tree_widget_item(plan)
        plan_tree_widget.addTopLevelItem(root_item)

        # Add the tree widget to the layout
        layout.addWidget(plan_tree_widget)

        # Optionally expand all tree nodes
        plan_tree_widget.expandAll()

class SQLQueryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.record_dict = {}  # Dictionary to store records for each block
        self.initUI()

    def initUI(self):
        layout_top = QVBoxLayout()

        # Create a label for the SQL query input
        self.label = QLabel("SQL Query:")
        layout_top.addWidget(self.label)

        # Create an input field for SQL query
        self.sql_input = QLineEdit()
        layout_top.addWidget(self.sql_input)

        # Create a button to execute the SQL query
        self.execute_button = QPushButton("Execute Query")
        layout_top.addWidget(self.execute_button)
        self.execute_button.clicked.connect(self.executeQuery)

        # Create a button to visualize the execution plan
        self.visualize_plan_button = QPushButton("Visualize Execution Plan")
        layout_top.addWidget(self.visualize_plan_button)
        self.visualize_plan_button.clicked.connect(self.visualizeQueryPlan)

        # Add some spacing between the button and the main layout
        layout_top.addSpacing(10)

        # Create a tab widget to hold tabs for each table
        self.tab_widget = QTabWidget()
        layout_top.addWidget(self.tab_widget)
        self.tab_widget.currentChanged.connect(self.tabChanged)

        # Create a scroll area to make the layout scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget to hold the vertical layout
        layout_bottom_widget = QWidget()
        self.layout_bottom = QVBoxLayout(layout_bottom_widget)

        # Set the layout widget as the widget for the scroll area
        scroll_area.setWidget(layout_bottom_widget)

        # Create a main layout for the main window
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(layout_top)
        main_layout.addWidget(scroll_area, 1)  # Use stretch factor to control size

        # Beautify the window with styles
        self.setWindowTitle("SQL Query App")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #f0f0f0; color: #000000;")
        self.label.setFont(QFont("Arial", 12))
        self.execute_button.setStyleSheet("background-color: #007acc; color: #000000;")

        
    def displayExecutionPlan(self, plan):
        # Initialize the QTreeWidget
        self.plan_tree_widget = QTreeWidget()
        self.plan_tree_widget.setHeaderLabel("Execution Plan")
        
        # Generate the tree items from the plan
        root_item = build_tree_widget_item(plan)
        self.plan_tree_widget.addTopLevelItem(root_item)
        
        # Add the tree widget to the UI layout
        self.layout_bottom.addWidget(self.plan_tree_widget)
        
        # Update the UI
        self.plan_tree_widget.expandAll()  # Optionally expand all tree nodes
    
    def visualizeQueryPlan(self):
        query = self.sql_input.text()
        try:
            plan = get_execution_plan(query)
            display_tree_image(plan)

            # Display the Execution Plan in a separate dialog
            dialog = ExecutionPlanDialog(plan, self)
            dialog.exec_()
        except Exception as e:
            self.showErrorMessage("Error Visualizing Query Plan", str(e))

    def executeQuery(self):
        # Get the SQL query from the input field
        query = self.sql_input.text()
        try:
            # results contains a dictionary of table names and their records
            self.results = execute_query_in_database(query)
            self.tab_widget.clear()
            for table_name in self.results:
                # Create a new tab for each table
                tab = QWidget()
                self.tab_widget.addTab(tab, table_name)
                self.tab_widget.setCurrentWidget(tab)


        except Exception as e:
            self.showErrorMessage("Error Executing Query", str(e))

    def tabChanged(self, index):
        # Get the current tab index and perform actions based on it
        if index >= 0:
            table_name = self.tab_widget.tabText(index)            
            # Get the result for the current table
            result = self.results[table_name]
            self.generateBlockAccessedButtons(result)

    def showErrorMessage(self, title, message):
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle(title)
            error_dialog.setText(message)
            error_dialog.exec_()
    
    def generateBlockAccessedButtons(self, results):
        # Clear existing buttons when executing a new query
        self.clearButtons()
        self.record_dict = {}
        # Create buttons and store records in the dictionary
        for record in results:
            # Get the block number from the first element of the tuple
            elements = [int(x) for x in record[0][1:-1].split(',')]

            # Append the record to the record_dict with block number as the key
            if elements[0] not in self.record_dict:
                self.record_dict[elements[0]] = [record]
            else:
                self.record_dict[elements[0]].append(record)

        # Sort records for each block based on the second part of the tuple's first element
        for block in self.record_dict:
            self.record_dict[block] = sorted(self.record_dict[block], key=lambda x: int(x[0].split(',')[1][:-1]))

        # Create buttons for each block and connect them to the showRecordsForBlock function
        for key in sorted(self.record_dict.keys()):
            temp = QPushButton(f"Block {key}")
            self.layout_bottom.addWidget(temp)
            temp.clicked.connect(lambda _, block=key: self.showRecordsForBlock(block))
            
    def showRecordsForBlock(self, block):
        # Display records for a specific block in a QDialog
        if block in self.record_dict:
            records = self.record_dict[block]

            # Create a dialog window
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Records for Block {block}")
            layout = QVBoxLayout()

            # Display records in a QTextEdit widget
            text_edit = QTextEdit()
            text = "\n".join([str(record) for record in records])
            text_edit.setPlainText(text)
            layout.addWidget(text_edit)

            # Set the layout for the dialog
            dialog.setLayout(layout)
            dialog.exec_()
                    
    def clearButtons(self):
        # Remove existing buttons from the layout
        while self.layout_bottom.count() > 0:
            item = self.layout_bottom.itemAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            self.layout_bottom.removeItem(item)
                     
            
def startWindow():
    app = QApplication(sys.argv)

    # Set a custom palette for a professional look
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    app.setPalette(palette)

    window = SQLQueryApp()
    window.show()
    sys.exit(app.exec_())

