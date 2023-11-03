import sys
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QFrame, QScrollArea, QDialog
from PyQt5.QtGui import QPalette, QColor, QFont

from explore import execute_query_in_database

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

        # Connect the button click event to a function
        self.execute_button.clicked.connect(self.executeQuery)

        # Create a scroll area to make the layout scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Ensure the widget inside the scroll area resizes properly

        # Create a widget to hold the vertical layout
        layout_bottom_widget = QWidget()
        self.layout_bottom = QVBoxLayout(layout_bottom_widget)
       
        # Set the layout widget as the widget for the scroll area
        scroll_area.setWidget(layout_bottom_widget)

        # Create a main layout for the main window
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout_top)
        main_layout.addWidget(scroll_area)  # Add the scroll area to the main layout

        self.setLayout(main_layout)

        # Beautify the window with styles
        self.setWindowTitle("SQL Query App")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.label.setFont(QFont("Arial", 12))
        self.execute_button.setStyleSheet("background-color: #007acc; color: #ffffff;")
    

    def executeQuery(self):
        # Get the SQL query from the input field
        query = self.sql_input.text()
        try:
            # results contains dictionary of table names and their records
            results = execute_query_in_database(query)
            
            # for debug purpose only
            for table_name in results:
                print(table_name,": ",results[table_name],"\n\n")
            
            #this is hardcoded for now
            result = list(results.values())[0]
            self.generateBlockAccessedButtons(result)
            
        except Exception as e:
            self.showErrorMessage("Error Executing Query", str(e))

    def showErrorMessage(self, title, message):
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle(title)
            error_dialog.setText(message)
            error_dialog.exec_()
    
    def generateBlockAccessedButtons(self, results):
            # Clear existing buttons when executing a new query
            self.clearButtons()
            # Create buttons and store records in the dictionary
            recordGroups = []
            curBlock = -1
            for record in results:
                elements = [int(x) for x in record[0][1:-1].split(',')]
                if curBlock != elements[0]:
                    curBlock = elements[0]
                    recordGroups = []
                    temp = QPushButton(f"Block {curBlock}")
                    self.layout_bottom.addWidget(temp)
                    temp.clicked.connect(lambda _, block=curBlock: self.showRecordsForBlock(block))
                recordGroups.append(record)
                self.record_dict[curBlock] = recordGroups
                
    def showRecordsForBlock(self, block):
        if block in self.record_dict:
            records = self.record_dict[block]
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Records for Block {block}")
            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text = "\n".join([str(record) for record in records])
            text_edit.setPlainText(text)
            layout.addWidget(text_edit)
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

