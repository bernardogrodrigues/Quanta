import sys, os

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QToolBar, QLabel, QListWidget, QSplitter, QSizePolicy, QComboBox, QMenu, QToolTip,
    QDockWidget, QDialog, QMenuBar
)
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QColor, QAction, QPen
from PyQt6.QtCore import Qt, QSize
import pyqtgraph as pqtg
from datetime import datetime
import numpy as np
from cs import CandlestickItem
from risk import VolatilityItem

from api import getTimeSeries

BG_COLOR = "#151820" # dark background's color 

LIGHT_COLOR = "#8c4ee9" # lighter color of theme

class GUI(QWidget):
    '''
    Quanta da Wish Risk Analysis GUI application.
    (Disclaimer: "risk" and "volatility" are highly correlated terms in this project,
    often used interchangeably; same for "graph" and "chart" - I know it's confusing.)

    Attributes:
        main_widgets (dict): Dictionary containing main widgets.
        buttons (dict): Dictionary containing the buttons.
    '''
    def __init__(self):
        super().__init__()
        
        # Set Main widgets
        self.main_widgets = {"main_window": QMainWindow(),
                             "central_widget": QWidget(),
                             "ohlc_chart": pg.PlotWidget(),
                             "risk_chart": pg.PlotWidget(),
                             "tool_bar": QToolBar()}

        # Set title label
        self.title_label = QLabel("Quanta da Wish Risk Analysis")
        self.setStyleSheet(f"color: {LIGHT_COLOR}; \
                            padding-left: 0px; \
                            padding-right: 60px;")

        # Buttons for plotting charts and clearing plot {"name":(QButton("text"), action)}
        self.buttons = {"EUR/USD": (QPushButton("EUR/USD"), lambda: self.plotOHLCData("EURUSD")),
                        "GBP/USD": (QPushButton("GBP/JPY"), lambda: self.plotOHLCData("GBPJPY")),
                        "EUR/JPY": (QPushButton("EUR/JPY"), lambda: self.plotOHLCData("EURJPY")),
                        "Clear Plot": (QPushButton("Clear Plot"), lambda: self.clearPlot())}
        
        # Initialize layout and add elements to it
        self.setupGUI()

    def setupGUI(self):
        """
        Set up the GUI
        """

        # Styling window
        self.setStyleSheet(f"background: {BG_COLOR};")
        self.main_widgets["main_window"].setStyleSheet(f"background: {BG_COLOR};")
        self.main_widgets["main_window"].setCentralWidget(self.main_widgets["central_widget"])

        # Styling charts
        graphs = [self.main_widgets["ohlc_chart"], self.main_widgets["risk_chart"]]
        
        # Customize axis labels and colors
        label_style = {'color': 'purple', 'font-size': '12px', 'font-weight': 'bold'}
        axis_color = LIGHT_COLOR
        
        # set up axis
        for graph in graphs:
            graph.setBackground(BG_COLOR)
            graph.showGrid(x=True, y=True, alpha=0.5)

            # Set y axis label and pen
            y_axis = graph.getAxis('left')
            y_axis.setLabel("Currency pair price" if graph is self.main_widgets["ohlc_chart"] else "Periodic Volatility", **label_style)
            y_axis.setPen(LIGHT_COLOR)

            # Set x axis as a date axis item, set label, set pen, but hide x axis if it is the top graph
            if graph is self.main_widgets["ohlc_chart"]:
                graph.getAxis("bottom").hide()
            else:
                graph.setAxisItems({'bottom':pqtg.DateAxisItem()})
                x_axis = graph.getAxis('bottom')
                x_axis.setLabel('Date', **label_style)
                x_axis.setPen(axis_color)
            
        # Set the height of the risk chart
        self.main_widgets["risk_chart"].setFixedHeight(200)

        # Link the views of OHLC and Risk graphs
        ohlc_viewbox = self.main_widgets["ohlc_chart"].getViewBox()
        risk_viewbox = self.main_widgets["risk_chart"].getViewBox()
        ohlc_viewbox.setXLink(risk_viewbox)

        # Forex price y_axis
        self.y_value_label_forex = pg.TextItem(text='Price', color=(0,255,0), anchor=(1, 0))
        self.main_widgets["ohlc_chart"].addItem(self.y_value_label_forex, ignoreBounds = True)

        # Risk y_axis
        self.y_value_label_risk = pg.TextItem(text='Volatility', color=(0,255,0), anchor=(1, 0))
        self.main_widgets["risk_chart"].addItem(self.y_value_label_risk, ignoreBounds = True)

        # main window resize
        self.main_widgets["main_window"].resize(800,600)


        ####BUTTONS####
        for button in self.buttons:
            self.setupButton(button, self.buttons[button][1])

        self.setupLayout()
            
    def setupLayout(self) -> None:
        """
        Sets up the layout for the central widget, including the main vertical layout,
        toolbar, search bar, search results, portfolio list, and plot graph.
        (Disclaimer: this function is not entirely my responsability)

        The layout structure consists of:
            1. Main Vertical Layout: Vertical layout for organizing various components.
            2. Toolbar: Added to the main vertical layout.
            3. Search Bar and Search Results Boxed Up Vertically: Widgets are boxed up vertically using the boxUpWidgetsVertically method.
            4. Left Splitter: Splits the boxed-up search bar and results container from the plot graph.
            5. Main Splitter: Splits the left splitter (search bar and results container) from the plot graph.
            6. Sizes for the Left Splitter: Initial sizes set for the left and right sides of the splitter.

        Parameters:
            None

        Returns:
            None
        """

        # Set up the main layout
        layout = QVBoxLayout(self.main_widgets["central_widget"])

        # Add the main splitter to the main layout
        layout.addWidget(self.main_widgets["ohlc_chart"])
        # Add the main splitter to the main layout
        layout.addWidget(self.main_widgets["risk_chart"])

        # Add buttons to GUI
        TOOLBAR_ITEMS = []
        for button_key in self.buttons:
            TOOLBAR_ITEMS.append(self.buttons[button_key][0])

        # Add items layout
        for item in TOOLBAR_ITEMS:
            layout.addWidget(item)
        

    def boxUpWidgetsVertically(self, widgets: list) -> QWidget:
        """
        Boxes up a list of widgets vertically within a QWidget.
        (D.: same thing as last one)

        Parameters:
            widgets (list): List of widgets to be organized vertically.

        Returns:
            QWidget: A container widget with a vertical layout containing the specified widgets.
        """

        # Box up widgets vertically
        container = QWidget()
        container_layout = QVBoxLayout(container)

        # Add widgets to layout container
        for widget in widgets:
            container_layout.addWidget(widget)

        return container

    def setupButton(self, button_key: str, action: callable, l_padding: int = 0, r_padding: int = 0) -> None:
        """
        Customizes button object according to:
            - Action it entails
            - Some padding
        
        Parameters:
            - button_key (str): button name used to access (as a key) self.buttons dictionary attribute
            - action (function): function called upon pressing the button
            - l_padding / r_padding (int | float): button padding

        Returns:
            - None
        """
    
        # Style button
        self.buttons[button_key][0].setStyleSheet(f"""
                QPushButton {{
                background: rgba(180, 180, 255, 255);
                padding-left: {str(l_padding)}px;
                padding-right: {str(r_padding)}px;
                border: none;
                font-size: 130 px;
            }}
        """) 

        # Set function called upon clicking     
        self.buttons[button_key][0].clicked.connect(action)


    def plotOHLCData(self, symbol: str) -> None:
        """
        Plots an asset's OHLC graph, based on its given OHLC data
        (totally not copypasted)
        """
        # Obtain ohlc data by api query
        ohlc_data = getTimeSeries(symbol, 'DAILY', output = "full")
        
        if ohlc_data is not None:
            # OHLC GRAPH
            # Create a CandlestickItem with the fetched candlestick data
            candlestick_item = CandlestickItem(ohlc_data)
            # Add the CandlestickItem to the plot widget
            self.main_widgets["ohlc_chart"].addItem(candlestick_item)

            # RISK(Volatility) GRAPH
            # Extract volatility data and convert 'date' values to numerical
            risk_item = VolatilityItem(ohlc_data)
            self.main_widgets["risk_chart"].addItem(risk_item)
    
    def clearPlot(self) -> None:
        """
        Clears the plotting widgets
        """
        self.main_widgets["ohlc_chart"].clear()
        self.main_widgets["risk_chart"].clear()

        # Reload y_axis after clearing
        self.main_widgets["ohlc_chart"].addItem(self.y_value_label_forex, ignoreBounds = True)
        self.main_widgets["risk_chart"].addItem(self.y_value_label_risk, ignoreBounds = True)

    def show(self):
        self.main_widgets["main_window"].show()



if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setApplicationName('Quanta (da Wish)')

    # Define your custom color palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))  # Text color
    # Apply the custom color palette to the application
    app.setPalette(palette)

    ui = GUI()
    ui.show()

    sys.exit(app.exec())