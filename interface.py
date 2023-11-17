import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, \
    QHBoxLayout, QFrame, QScrollArea, QDialog, QTabWidget, QSplitter, QTableWidget, QTableWidgetItem, QSizePolicy,QFormLayout
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtSvg import QGraphicsSvgItem
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene

from explore import build_tree_widget_item, convert_query_to_ctid_query, display_tree_image, execute_query_in_database, get_columns_for_table, get_execution_plan,get_table_names

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Connection Details")
        self.setGeometry(200, 200, 400, 200)

        # Input fields for database connection details
        self.host_input = QLineEdit()
        self.name_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        # Button to confirm the input
        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.accept)

        # Create a layout for the dialog
        layout = QFormLayout(self)
        layout.addRow("Database Host:", self.host_input)
        layout.addRow("Database Name:", self.name_input)
        layout.addRow("Database User:", self.user_input)
        layout.addRow("Database Password:", self.password_input)
        layout.addWidget(confirm_button)

    def get_connection_details(self):
        return (
            self.host_input.text(),
            self.name_input.text(),
            self.user_input.text(),
            self.password_input.text()
        )

class SQLQueryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.record_dict = {}  # Dictionary to store records for each block
        self.initUI()

    def initUI(self):
        # Creating a main layout for the main window
        main_layout = QVBoxLayout(self)

        # Create a label for the app
        self.label = QLabel("SQL Query Explorer 🔎")
        self.label.setFixedHeight(30)
        self.label.setStyleSheet("font: bold 20px monospace;")
        main_layout.addWidget(self.label)

         # -------------LEFT SIDE-----------------------
        # Create a vertical layout for the left box
        self.layout_left = QVBoxLayout()

        # Create a label for the SQL input
        label_sql_input = QLabel("Enter an SQL Query:")
        self.layout_left.addWidget(label_sql_input)

        # Create an input field for SQL query
        self.sql_input = QTextEdit()
        # self.sql_input.setFixedHeight(200)
        self.layout_left.addWidget(self.sql_input)

        # Create a button to execute the SQL query
        self.execute_button = QPushButton("Execute Query")
        self.layout_left.addWidget(self.execute_button)
        self.execute_button.clicked.connect(self.executeQuery)

        # Create a button to visualize the execution plan
        # self.visualize_plan_button = QPushButton("Visualize Execution Plan")
        # self.layout_left.addWidget(self.visualize_plan_button)
        # self.visualize_plan_button.clicked.connect(self.visualizeQueryPlan)

        # Add some spacing 
        self.layout_left.addSpacing(30)

        # Create a label for the block accessed input
        label_blocks = QLabel("Blocks Accessed (Grouped by Tables)")
        self.layout_left.addWidget(label_blocks)

        # Create a tab widget to hold tabs for each table
        self.tab_widget = QTabWidget()
        self.layout_left.addWidget(self.tab_widget)
        self.tab_widget.currentChanged.connect(self.tabChanged)
        
        # Create a scroll area to make the layout scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget to hold the blocks
        blocks_layout_widget = QWidget()
        self.layout_blocks = QVBoxLayout(blocks_layout_widget)

        # Set the layout widget as the widget for the scroll area
        scroll_area.setWidget(blocks_layout_widget)
        self.layout_left.addWidget(scroll_area, 1)  # Use stretch factor to control size

        #-----------------------------------------------
        # -------------MIDDLE-----------------------
        # Create a vertical layout for the right box
        self.layout_middle = QVBoxLayout()
        self.layout_middle.setAlignment(Qt.AlignTop)

        # Create a label for the block accessed input
        label_execution = QLabel("Execution Plan")
        self.layout_middle.addWidget(label_execution)

        # Initialize the QTreeWidget
        self.plan_tree_widget = QTreeWidget()
        self.plan_tree_widget.setHeaderLabel("Results:")
        self.layout_middle.addWidget(self.plan_tree_widget)
        #-----------------------------------------------

        # -------------RIGHT SIDE-----------------------
    # Create a vertical layout for the right box
        self.layout_right = QVBoxLayout()
        self.layout_right.setAlignment(Qt.AlignTop)

        # Create a label for the block accessed input
        label_blocks = QLabel("Query Expression Tree")
        self.layout_right.addWidget(label_blocks)

        # # Create widget for graph
        # self.svg_widget = QSvgWidget(self)
        # self.layout_right.addWidget(self.svg_widget, 1)
        
        # Replace QSvgWidget with QGraphicsView for the query expression tree
        self.graphics_view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        self.layout_right.addWidget(self.graphics_view, 1)
            # Add zoom in and zoom out buttons
        self.zoom_in_button = QPushButton("Zoom In ➕")
        self.zoom_out_button = QPushButton("Zoom Out ➖")
        self.layout_right.addWidget(self.zoom_in_button)
        self.layout_right.addWidget(self.zoom_out_button)

        self.zoom_in_button.clicked.connect(self.zoomIn)
        self.zoom_out_button.clicked.connect(self.zoomOut)

        # Load svg graph into widget
        # self.svg_widget.load("plan-svg.svg")

        #-----------------------------------------------

        # Add a QSplitter to the main layout
        splitter = QSplitter()
        main_layout.addWidget(splitter)

        # Add the left, middle and right layouts to the QSplitter as widgets
        widget_left = QWidget()
        widget_left.setLayout(self.layout_left)
        splitter.addWidget(widget_left)

        widget_middle = QWidget()
        widget_middle.setLayout(self.layout_middle)
        splitter.addWidget(widget_middle)

        widget_right = QWidget()
        widget_right.setLayout(self.layout_right)
        splitter.addWidget(widget_right)



        # Beautify the window with styles
        self.setWindowTitle("SQL Query App")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #f0f0f0; color: #000000;")
        self.label.setFont(QFont("Arial", 12))
        self.execute_button.setStyleSheet("background-color: #007acc; color: #ffffff;")
        self.setLayout(main_layout)

        
    def displayExecutionPlan(self, plan):
        # clear previous results
        self.plan_tree_widget.clear()

        # Generate the tree items from the plan
        root_item = build_tree_widget_item(plan)

        self.plan_tree_widget.addTopLevelItem(root_item)
        
        # Add the tree widget to the UI layout
        # self.layout_middle.addWidget(self.plan_tree_widget)
        
        # Update the UI
        self.plan_tree_widget.expandAll()  # expand all tree nodes
    
    def visualizeQueryPlan(self):
        query = self.sql_input.toPlainText()
        try:
            plan = get_execution_plan(query)
            display_tree_image(plan)

            # Display the Execution Plan in a separate dialog
            # dialog = ExecutionPlanDialog(plan, self)
            # dialog.exec_()
            svg_item = QGraphicsSvgItem("plan-svg.svg")
            self.scene.clear()
            self.scene.addItem(svg_item)
            self.graphics_view.fitInView(svg_item, Qt.KeepAspectRatio)
        except Exception as e:
            self.showErrorMessage("Error Visualizing Query Plan", str(e))
    def zoomIn(self):
        # Implement zoom in functionality
        self.graphics_view.scale(1.2, 1.2)

    def zoomOut(self):
        # Implement zoom out functionality
        self.graphics_view.scale(0.8, 0.8)
    def executeQuery(self):
        # Get the SQL query from the input field
        query = self.sql_input.toPlainText()
        try:
            # results contains a dictionary of table names and their records
            self.results = execute_query_in_database(query)
            self.tab_widget.clear()
            for table_name in self.results:
                # Create a new tab for each table
                tab = QWidget()
                self.tab_widget.addTab(tab, table_name)
                self.tab_widget.setCurrentWidget(tab)

            # visualise the query plan (QET and execution plan)
            self.visualizeQueryPlan()

        except Exception as e:
            self.showErrorMessage("Error Executing Query", str(e))



    def tabChanged(self, index):
        # Get the current tab index and perform actions based on it
        if index >= 0:
            table_name = self.tab_widget.tabText(index)
            # Get the result for the current table
            if table_name in self.results:
                result = self.results[table_name]
                self.generateBlockAccessedButtons(result, table_name)
            else:
                # Set the current tab to index 0 (or another default index)
                self.tab_widget.setCurrentIndex(0)

    def showErrorMessage(self, title, message):
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle(title)
            error_dialog.setText(message)
            error_dialog.exec_()
    
    def generateBlockAccessedButtons(self, results, table_name):
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

        header = get_columns_for_table(table_name)
        
        # Create buttons for each block and connect them to the showRecordsForBlock function
        for key in sorted(self.record_dict.keys()):
            temp = QPushButton(f"Block {key}")
            self.layout_blocks.addWidget(temp)
            temp.clicked.connect(lambda _, block=key: self.showRecordsForBlock(block, header))
            
    def showRecordsForBlock(self, block, header):
        # Display records for a specific block in a QDialog
        if block in self.record_dict:
            records = self.record_dict[block]

            # Create a dialog window
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Records for Block {block}")
            layout = QVBoxLayout()

            # Display records in a QTextEdit widget
            # text_edit = QTextEdit()
            # text = "\n".join([str(record) for record in records])

            # Display records in a QTableWidget
            table = QTableWidget(len(records), len(records[0]))
            
            # Set the header labels
            table.setHorizontalHeaderLabels(header)

            for row, record in enumerate(records):
                for col, field in enumerate(record):
                    item = QTableWidgetItem(str(field))
                    table.setItem(row, col, item)

            # Set table properties
            table.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable editing
            table.setShowGrid(True)
            table.setLineWidth(1)  # Set line width for the grid
            # text_edit.setPlainText(text)
            table.setStyleSheet("color: black;")
            # Set the border color for horizontal header
            table.horizontalHeader().setStyleSheet("QHeaderView::section { border: 1px solid black; background-color: lightgrey;}")

            # Set the border color for vertical header
            table.verticalHeader().setStyleSheet("QHeaderView::section { border: 1px solid black;background-color: lightgrey; }")
            layout.addWidget(table)
            table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(400)

            # Set the layout for the dialog
            dialog.setLayout(layout)
            dialog.exec_()
                    
    def clearButtons(self):
        # Remove existing buttons from the layout
        while self.layout_blocks.count() > 0:
            item = self.layout_blocks.itemAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            self.layout_blocks.removeItem(item)

db_host = ""
db_name = ""
db_user = ""
db_password = ""

def startWindow():
    global db_host, db_name, db_user, db_password  # Use the global keyword
    app = QApplication(sys.argv)

    # Set a custom palette for a professional look
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    app.setPalette(palette)

    window = SQLQueryApp()
    window.show()

    dialog = ConfigDialog()
    result = dialog.exec_()

    if result == QDialog.Accepted:
        db_host, db_name, db_user, db_password = dialog.get_connection_details()
        print(f"Database Host: {db_host}")
        print(f"Database Name: {db_name}")
        print(f"Database User: {db_user}")
        print(f"Database Password: {db_password}")


    sys.exit(app.exec_())

