import logging
import sys, os
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QLineEdit, QPushButton, QGridLayout, QFormLayout, QDialog, QBoxLayout, QComboBox, QListView, QTableView, QTableWidget, QTableWidgetItem, QMessageBox, QDialogButtonBox, QVBoxLayout, QInputDialog
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QSound, QMediaPlayer, QMediaContent
from PyQt5.QtGui import QStandardItemModel

import threading, time
import json
from cryptoalerts import Futures

#logging.basicConfig(format="%(message)s", level=logging.INFO)
log_file = 'logs.log'
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %I:%M:%S %p',
                    level=logging.INFO,
                    handlers=[
                        #logging.FileHandler(log_file),
                        logging.StreamHandler()
                    ])

class APIInputDialog(QDialog):
    config_dir = ""
    def __init__(self, config_dir, parent=None):
        super().__init__(parent=parent)
        self.config_dir = config_dir
        
        self.setWindowTitle("Enter your Binance API keys")

        btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(btn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
                
        self.layout         = QVBoxLayout()
        self.api_msg        = QLabel("Your api key: ")
        self.api_textbox    = QLineEdit(self)
        self.secret_msg     = QLabel("Your secret key: ")
        self.secret_textbox = QLineEdit(self)
        
        self.api_textbox.setMinimumWidth(340)
        self.secret_textbox.setMinimumWidth(340)
        
        self.layout.addWidget(self.api_msg)
        self.layout.addWidget(self.api_textbox)
        self.layout.addWidget(self.secret_msg)
        self.layout.addWidget(self.secret_textbox)
        self.layout.addWidget(self.buttonBox)
        
        self.setLayout(self.layout)
        
        ok_btn = self.buttonBox.button(QDialogButtonBox.Ok)
        ok_btn.clicked.connect(lambda: self.dump_keys())
    
    def dump_keys(self):
        api_key     = self.api_textbox.text()
        secret_key  = self.secret_textbox.text()
        if api_key and secret_key:
            api_keys = {
                "api_key": api_key,
                "api_secret": secret_key
                }
            with open(os.path.join(self.config_dir, "config.json"), "w") as f:
                json.dump(api_keys, f)

class PriceAlertDialog(QDialog):
    def __init__(self, price=0, symbol="btcusdt", typ="below", parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("PRICE ALERT!")

        btn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(btn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.msg = QLabel(f"An alert was triggered for {symbol.upper()}, because the price was {typ.lower()} {price}.")
        self.layout.addWidget(self.msg)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
            
    def set_ticker(self, symbol, price, typ):
        self.msg.setText(f"An alert was triggered for {symbol.upper()}, because the price was {typ.lower()} {price}.")
        
    def play_sound(self):
        self.alert_sound = QSound("C:/Users/nikar/Desktop/Day Trading/BinanceFutures/alert.wav")
        self.alert_sound.setLoops(3)
        self.alert_sound.play()


class MainWindow(QWidget):
    __exit = False
    futures = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        self.title  = "CryptoAlerts"
        self.left   = 50
        self.top    = 50
        self.width  = 600
        self.height = 400
        self.ticker = "btcusdt"
        self.dlg    = PriceAlertDialog()
        self.dlg.setWindowModality(Qt.WindowModality.WindowModal)
        
        self.InitUI()

        self.create_config()
        
        self.check_alerts = threading.Thread(target=self.check_prices)
        if self.futures:
            self.check_alerts.start()
    
    def create_config(self):
        """ Create new folder and config.json file in local appdata directory to store the api keys
        """
        config_dir = os.path.join(os.getenv("LOCALAPPDATA"), "CryptoAlerts")
        if not os.path.exists(config_dir) or not os.path.exists(os.path.join(config_dir, "config.json")):
            try:
                os.mkdir(config_dir)
            except:
                print(f"Couldn't create a directory in {config_dir}")
                
            input_d = APIInputDialog(config_dir)
            acc = input_d.exec()
            if acc == QDialog.Accepted:
                self.futures = Futures(True)
        else:
            self.futures = Futures(True)

    def InitUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.ticker_textbox = QLineEdit()
        self.ticker_textbox.returnPressed.connect(self.change_ticker)

        # Alert textbox
        self.alert_pricebox = QLineEdit()

        # Alert button
        alert_b = QPushButton("Set Alert")
        alert_b.clicked.connect(self.add_to_list)
        
        # Remove alert
        alert_rem_b = QPushButton("Remove Alert")
        alert_rem_b.clicked.connect(self.remove_from_list)

        # Alert dropdown
        self.alert_dropdown = QComboBox()
        self.alert_dropdown.addItem("Below")
        self.alert_dropdown.addItem("Above")

        # Alert layout
        alert_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        alert_layout.addWidget(self.alert_dropdown)
        alert_layout.addWidget(self.alert_pricebox)
        alert_layout.addWidget(alert_b)
        alert_layout.addWidget(alert_rem_b)

        self.ticker_price = QLabel("")
        self.ticker_l = QLabel(self.ticker.upper())

        # List of alerts
        self.alert_list = QTableWidget()
        self.alert_list.setColumnCount(4)
        self.alert_list.setHorizontalHeaderLabels(["Ticker", "Alert Price", "Type", "Triggered"])
                
        # Main layout
        tickerlayout = QFormLayout()
        tickerlayout.addRow("Ticker", self.ticker_textbox)
        tickerlayout.addRow(self.ticker_l, self.ticker_price)
        tickerlayout.addRow("Alert when price is", alert_layout)
        tickerlayout.addRow(self.alert_list)

        grid = QGridLayout()

        self.setLayout(tickerlayout)


    def remove_from_list(self):
        """Removes a symbol from the list (which disables the alert)
        """
        for row in self.alert_list.selectedItems():
            self.alert_list.removeRow(row.row())
    
    def check_prices(self):
        """Constantly goes through a list of symbols and checks if price has reached a given number (runs in a thread)
        """
        while True:
            if self.__exit:
                break
            
            self.set_ticker_price()
            
            for row in range(self.alert_list.rowCount()):
                if self.alert_list.item(row, 3).text() == "False":
                    symbol      = self.alert_list.item(row, 0).text().lower()
                    alert_price = self.alert_list.item(row, 1).text()
                    alert_type  = self.alert_list.item(row, 2).text()
                    price       = self.futures.get_price(symbol)
                        
                    if alert_type == "Below" and price < float(alert_price):
                        self.alert_list.item(row, 3).setText("True")
                        self.dlg.set_ticker(symbol, alert_price, alert_type)
                        self.dlg.play_sound()
                        self.dlg.exec()
                    elif alert_type == "Above" and price > float(alert_price):
                        self.alert_list.item(row, 3).setText("True")
                        self.dlg.set_ticker(symbol, alert_price, alert_type)
                        self.dlg.play_sound()
                        self.dlg.exec()
                    
            time.sleep(0.5)

    def add_to_list(self):
        """Adds an item to the list
        """
        self.alert_list.insertRow(self.alert_list.rowCount())
            
        tck = QTableWidgetItem()
        tck.setText(self.ticker.upper())
        price = QTableWidgetItem()
        price.setText(self.alert_pricebox.text())
        typ = QTableWidgetItem()
        alert_type = self.alert_dropdown.itemText(self.alert_dropdown.currentIndex())
        typ.setText(alert_type)
        triggered = QTableWidgetItem()
        triggered.setText("False")

        self.alert_list.setItem(self.alert_list.rowCount()-1, 0, tck)
        self.alert_list.setItem(self.alert_list.rowCount()-1, 1, price)
        self.alert_list.setItem(self.alert_list.rowCount()-1, 2, typ)
        self.alert_list.setItem(self.alert_list.rowCount()-1, 3, triggered)

    def change_ticker(self):
        self.ticker = self.ticker_textbox.text()
        self.ticker_l.setText(self.ticker.upper())
    
    def set_ticker_price(self):
        self.ticker_price.setText(str(self.futures.get_price(self.ticker)))
    
    def closeEvent(self, event):
        # Breaks the while loop to end the thread
        self.__exit = True
        
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # Start the event loop.
    app.exec_()