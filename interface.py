import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtSvg import QGraphicsSvgItem

import psycopg2
from explore import *

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Connection Details")
        self.setGeometry(200, 200, 400, 200)

        self.host_input = QLineEdit()
        self.name_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        # Confirm Button
        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.accept)

        layout = QFormLayout(self)
        layout.addRow("Database Host:", self.host_input)
        layout.addRow("Database Name:", self.name_input)
        layout.addRow("Database User:", self.user_input)
        layout.addRow("Database Password:", self.password_input)
        layout.addWidget(confirm_button)

        # Placeholders
        self.host_input.setPlaceholderText("Example: localhost")
        self.name_input.setPlaceholderText("Example: TPC-H")
        self.user_input.setPlaceholderText("Example: postgres")

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

        main_layout = QVBoxLayout(self)

        self.label = QLabel("SQL Query Explorer 🔎")
        self.label.setFixedHeight(30)
        self.label.setStyleSheet("font: bold 20px monospace;")
        main_layout.addWidget(self.label)

        # -------------LEFT SIDE-----------------------
        self.layout_left = QVBoxLayout()

        label_sql_input = QLabel("Enter an SQL Query:")
        self.layout_left.addWidget(label_sql_input)

        self.sql_input = QTextEdit()
        self.layout_left.addWidget(self.sql_input)

        # Execute Button
        self.execute_button = QPushButton("Execute Query")
        self.layout_left.addWidget(self.execute_button)
        self.execute_button.clicked.connect(self.executeQuery)

        self.layout_left.addSpacing(30)

        label_blocks = QLabel("Blocks Accessed (Grouped by Tables)")
        self.layout_left.addWidget(label_blocks)

        # Tab to hold tabs for each table
        self.tab_widget = QTabWidget()
        self.layout_left.addWidget(self.tab_widget)
        self.tab_widget.currentChanged.connect(self.tabChanged)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        blocks_layout_widget = QWidget()
        self.layout_blocks = QVBoxLayout(blocks_layout_widget)

        # Set the layout widget as the widget for the scroll area
        scroll_area.setWidget(blocks_layout_widget)
        self.layout_left.addWidget(scroll_area, 1)  # Use stretch factor to control size

        # -------------MIDDLE-----------------------
        self.layout_middle = QVBoxLayout()
        self.layout_middle.setAlignment(Qt.AlignTop)

        label_execution = QLabel("Execution Plan")
        self.layout_middle.addWidget(label_execution)

        self.plan_tree_widget = QTreeWidget()
        self.plan_tree_widget.setHeaderLabel("Results:")
        self.layout_middle.addWidget(self.plan_tree_widget)

        # -------------RIGHT SIDE----------------------
        self.layout_right = QVBoxLayout()
        self.layout_right.setAlignment(Qt.AlignTop)

        label_blocks = QLabel("Query Expression Tree")
        self.layout_right.addWidget(label_blocks)

        self.graphics_view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        self.layout_right.addWidget(self.graphics_view, 1)

        # Zoom Buttons
        self.zoom_in_button = QPushButton("Zoom In ➕")
        self.zoom_out_button = QPushButton("Zoom Out ➖")
        self.layout_right.addWidget(self.zoom_in_button)
        self.layout_right.addWidget(self.zoom_out_button)

        self.zoom_in_button.clicked.connect(self.zoomIn)
        self.zoom_out_button.clicked.connect(self.zoomOut)

        # Combine left, middle and right layouts
        splitter = QSplitter()
        main_layout.addWidget(splitter)

        widget_left = QWidget()
        widget_left.setLayout(self.layout_left)
        splitter.addWidget(widget_left)

        widget_middle = QWidget()
        widget_middle.setLayout(self.layout_middle)
        splitter.addWidget(widget_middle)

        widget_right = QWidget()
        widget_right.setLayout(self.layout_right)
        splitter.addWidget(widget_right)

        self.setWindowTitle("SQL Query App")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #f0f0f0; color: #000000;")
        self.label.setFont(QFont("Arial", 12))
        self.execute_button.setStyleSheet("background-color: #007acc; color: #ffffff;")
        self.setLayout(main_layout)

        
    def displayExecutionPlan(self, plan):
        self.plan_tree_widget.clear()
        root_item = build_tree_widget_item(plan)
        self.plan_tree_widget.addTopLevelItem(root_item)
        self.plan_tree_widget.expandAll()  
    
    def visualizeQueryPlan(self):
        query = self.sql_input.toPlainText()
        try:
            plan = get_execution_plan(query)
            display_tree_image(plan)
            self.displayExecutionPlan(plan)
            svg_item = QGraphicsSvgItem("plan-svg.svg")
            self.scene.clear()
            self.scene.addItem(svg_item)
            self.graphics_view.fitInView(svg_item, Qt.KeepAspectRatio)
        except Exception as e:
            self.showErrorMessage("Error Visualizing Query Plan", str(e))
    def zoomIn(self):
        self.graphics_view.scale(1.2, 1.2)

    def zoomOut(self):
        self.graphics_view.scale(0.8, 0.8)
    def executeQuery(self):
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
            self.visualizeQueryPlan()

        except Exception as e:
            self.showErrorMessage("Error Executing Query", str(e))

    def tabChanged(self, index):
        if index >= 0:
            table_name = self.tab_widget.tabText(index)
            if table_name in self.results:
                result = self.results[table_name]
                self.generateBlockAccessedButtons(result, table_name)
            else:
                self.tab_widget.setCurrentIndex(0)

    def showErrorMessage(self, title, message):
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle(title)
            error_dialog.setText(message)
            error_dialog.exec_()
    
    def generateBlockAccessedButtons(self, results, table_name):
        self.clearButtons()
        self.record_dict = {}
        for record in results:
            elements = [int(x) for x in record[0][1:-1].split(',')]

            if elements[0] not in self.record_dict:
                self.record_dict[elements[0]] = [record]
            else:
                self.record_dict[elements[0]].append(record)
        for block in self.record_dict:
            self.record_dict[block] = sorted(self.record_dict[block], key=lambda x: int(x[0].split(',')[1][:-1]))

        header = get_columns_for_table(table_name)
        
        for key in sorted(self.record_dict.keys()):
            temp = QPushButton(f"Block {key}")
            self.layout_blocks.addWidget(temp)
            temp.clicked.connect(lambda _, block=key: self.showRecordsForBlock(block, header))
            
    def showRecordsForBlock(self, block, header):
  
        if block in self.record_dict:
            records = self.record_dict[block]

     
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Records for Block {block}")
            layout = QVBoxLayout()

            table = QTableWidget(len(records), len(records[0]))
            
            table.setHorizontalHeaderLabels(header)

            for row, record in enumerate(records):
                for col, field in enumerate(record):
                    item = QTableWidgetItem(str(field))
                    table.setItem(row, col, item)

    
            table.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable editing
            table.setShowGrid(True)
            table.setLineWidth(1)  
            table.setStyleSheet("color: black;")
            table.horizontalHeader().setStyleSheet("QHeaderView::section { border: 1px solid black; background-color: lightgrey;}")

            table.verticalHeader().setStyleSheet("QHeaderView::section { border: 1px solid black;background-color: lightgrey; }")
            layout.addWidget(table)
            table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(400)

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

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    app.setPalette(palette)

    connected = False
    while not connected:
        window = SQLQueryApp()
        window.show()

        dialog = ConfigDialog()
        result = dialog.exec_()

        if result == QDialog.Accepted:
            db_host, db_name, db_user, db_password = dialog.get_connection_details()
            try:
                psycopg2.connect(
                    host=db_host,
                    database=db_name,
                    user=db_user,
                    password=db_password
                )
                connected = True  
            except Exception as e:
                QMessageBox.critical(None, "Connection Error", f"Error connecting to the database: {str(e)}")

    sys.exit(app.exec_())


   

