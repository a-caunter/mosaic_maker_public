app_color = "#30383d"

tab_style = """
            QTabBar::tab {
                background-color: #30383d;
                color: white;
                font: 14px Century Gothic;
                text-align: center;
                padding: 0px;
                border: 1px solid #455361;
                min-width: 150px; /* Adjust width and height as needed */
                min-height: 25px;
                padding: 0px 10px
            }

            QTabBar::tab:hover {
                background-color: #455361;
            }

            QTabBar::tab:selected {
                background-color: #455361;
            }
            """

button_style = """
            QPushButton {
                background-color: #30383d;
                border: 1px solid #64b1d8;
                color: white;
                font: bold 14px Century Gothic;
                padding: 5px;
                text-align: center;
                border-radius: 0px;
                margin: 10px;
            }

            QPushButton:hover {
                background-color: #455361;
            }
            """

tooltip = """
            QToolTip {
                color: white;
                background-color: black;
                border: 1px solid white;
                padding: 0px 5px;
                border-radius: 0px;
                opacity: 200;
            }
            """

combobox_style = """
            QComboBox {
                background-color: #30383d;
                color: white;
                font: 14px Century Gothic;
                border: 1px solid #455361;
                min-height: 25px;
                padding: 3px; 
            }
            QComboBox:hover {
                background-color: #455361;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #455361;
            }
            QComboBox QAbstractItemView {
                background-color: #30383d;
                color: white;
                border: 1px solid #455361;
                selection-background-color: #455361;
            }
        """

label_style = """
            QLabel {
                color: white;
                font: 12px Century Gothic;
            }
            """

line_edit_style = """
            QLineEdit {
                color: white;
                font: 12px Century Gothic;
                background-color: #455361;
                border-radius: 0px;
                padding: 5px;
            }
            """

list_style = """
    QListWidget {
        background-color: #455361;
        color: white;
        font: 12px Century Gothic;
        border: 1px solid #455361;
        padding: 0px;
    }
    QListWidget::item {
        background-color: #30383d;
        color: white;
        padding: 0px;
        border: 1px solid #455361;
    }
    QListWidget::item:hover {
        border: 1px solid white;
    }
    QListWidget::item:selected {
        border: 1px solid #64b1d8;
    }
"""

checkbox_style = """
    QCheckBox {
        background-color: #455361;
        color: white;
        font: 12px Century Gothic;
        border: 1px solid #455361;
        padding: 0px;
    }
"""
