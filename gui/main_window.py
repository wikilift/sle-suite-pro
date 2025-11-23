                    

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QTabWidget, QStatusBar,
    QFileDialog, QMessageBox
)

from gui.widgets.log_panel import LogPanel
from gui.tabs.tab_card import TabCard

from gui.themes import THEMES

from core.pcsc_manager import PCSCManager
from controllers.app_controller import AppController
from core.settings_manager import SettingsManager
from core.language_manager import LanguageManager
from gui.tabs.chip_info import TabChipInfo
from PySide6 import QtCore 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

                                                              
              
                                                              
        self.settings = SettingsManager()
        self.lang = LanguageManager(self.settings.get("language", "es"))
        self.pcsc = PCSCManager()

        self.controller = AppController(
            self.pcsc,
            self.settings,
            logger=self.log
        )

                                                              
                       
                                                              
        self.setWindowTitle("SLE Suite PRO")
        self.resize(1100, 750)

        theme = self.settings.get("theme", "dark")
        self.setStyleSheet(THEMES.get(theme, THEMES["dark"]))

                    
        self.build_menu()

                                                              
                     
                                                              
        root = QWidget()
        layout = QVBoxLayout()
        root.setLayout(layout)
        self.setCentralWidget(root)

                                                              
                 
                                                              
        top = QHBoxLayout()

        top.addWidget(QLabel(self.tr("label.reader")))

        self.reader_combo = QComboBox()
        top.addWidget(self.reader_combo)

        self.btn_refresh = QPushButton(self.tr("btn.search"))
        self.btn_refresh.clicked.connect(self.refresh_readers)
        top.addWidget(self.btn_refresh)

        self.btn_connect = QPushButton(self.tr("btn.connect"))
        self.btn_connect.clicked.connect(self.connect_reader)
        top.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton(self.tr("btn.disconnect"))
        self.btn_disconnect.clicked.connect(self.disconnect_reader)
        self.btn_disconnect.setVisible(False)
        top.addWidget(self.btn_disconnect)

        self.btn_read = QPushButton(self.tr("btn.read"))
        self.btn_read.clicked.connect(self.read_card)
        self.btn_read.setVisible(False)
        top.addWidget(self.btn_read)

        top.addStretch()
        layout.addLayout(top)

                                                              
              
                                                              
        self.tabs = QTabWidget()
        self.tab_card = TabCard(self)
                                       
        self.tab_chipinfo = TabChipInfo(self)

        self.tabs.addTab(self.tab_card, self.tr("tab.card"))
                                                                  
        self.tabs.addTab(self.tab_chipinfo, self.tr("tab.chipinfo"))

        layout.addWidget(self.tabs)

                                                              
                      
                                                              
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)

       

        status = QStatusBar()
        self.setStatusBar(status)

        self.lbl_status = QLabel(self.tr("status.reader_none"))
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
        status.addWidget(self.lbl_status)

                              
        self.refresh_readers()

                                                                
                   
                                                                
    def tr(self, key):
        return self.lang.tr(key)

                                                                
                 
                                                                
    def build_menu(self):
        menu = self.menuBar()

              
        file_menu = menu.addMenu(self.tr("menu.file"))
        file_menu.addAction(self.tr("menu.import_bin")).triggered.connect(self.action_import_bin)
        file_menu.addAction(self.tr("menu.export_bin")).triggered.connect(self.action_export_bin)
        file_menu.addSeparator()
        file_menu.addAction(self.tr("menu.exit")).triggered.connect(self.close)

                  
        settings_menu = menu.addMenu(self.tr("menu.settings"))

               
        theme_menu = settings_menu.addMenu(self.tr("menu.theme"))
        theme_menu.addAction(self.tr("theme.light")).triggered.connect(lambda: self.update_theme("light"))
        theme_menu.addAction(self.tr("theme.dark")).triggered.connect(lambda: self.update_theme("dark"))

                                           
        lang_menu = settings_menu.addMenu(self.tr("menu.language"))

        for lang_code in self.settings.available_langs:
            lang_menu.addAction(lang_code).triggered.connect(
                lambda checked, c=lang_code: self.update_language(c)
            )
              
        help_menu = menu.addMenu(self.tr("menu.help"))
        help_menu.addAction(self.tr("menu.about")).triggered.connect(self.action_about)


                                                                
                   
                                                                
    def log(self, msg):
        self.log_panel.log(msg)

                                                                
                       
                                                                
    def refresh_readers(self):
        self.reader_combo.clear()
        readers = self.controller.list_readers()

        if readers:
            for r in readers:
                self.reader_combo.addItem(str(r))

            self.btn_connect.setEnabled(True)
            self.log(self.tr("msg.readers_found"))

        else:
            self.btn_connect.setEnabled(False)
            self.btn_read.setVisible(False)

            
            self.lbl_status = QLabel(self.tr("status.reader_none"))
            self.lbl_status.setStyleSheet("color: red; font-weight: bold;")

            self.log(self.tr("msg.no_readers"))

    def connect_reader(self):
        idx = self.reader_combo.currentIndex()
        if idx < 0:
            return
        

        reader = self.controller.list_readers()[idx]

        try:
            atr = self.controller.connect_reader(reader)
            self.log(f"{self.tr('msg.connected_to')} {reader} | ATR: {' '.join(f'{x:02X}' for x in atr)}")
            
            self.tab_card.update_state(connected=True, card_loaded=False)

            self.lbl_status.setText(f"{self.tr('status.reader')}: {reader}")

            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")

                                           
            self.btn_connect.setVisible(False)
            self.btn_refresh.setVisible(False)

                                       
            self.btn_disconnect.setVisible(True)
            self.btn_read.setVisible(True)

        except Exception as e:
            self.log(f"{self.tr('msg.error_connect')} {e}")

    def disconnect_reader(self):
        self.controller.disconnect_reader()
        self.log(self.tr("msg.reader_disconnected"))
        self.tab_card.update_state(connected=False, card_loaded=False)



        

        self.btn_connect.setVisible(True)
        self.btn_disconnect.setVisible(False)
        self.btn_read.setVisible(False)
        self.btn_refresh.setVisible(True)

        self.lbl_status.setText(self.tr("status.reader_none"))
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")

                                                                
                     
                                                                
    def read_card(self):
        if not self.controller.conn:
            self.log(self.tr("msg.connect_reader_first"))
            return

        ctype = self.controller.detect_card_type()
        self.log(f"{self.tr('msg.card_type')}: {ctype}")
        

        try:
            data = self.controller.load_card(ctype)
            self.tab_chipinfo.load_chip(self.controller.card)
            self.tab_card.load_data(data)

            self.tabs.setCurrentIndex(self.tabs.indexOf(self.tab_card))
            self.log(self.tr("msg.card_ok"))
            self.tab_card.update_state(connected=True, card_loaded=True)


        except Exception as e:
            self.log(f"{self.tr('msg.error_card_read')} {e}")

                                                                
               
                                                                
    def action_import_bin(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("menu.import_bin"),
            "",
            "Binary Files (*.bin)"
        )
        if not path:
            return

        try:
            with open(path, "rb") as f:
                data = f.read()

            self.tab_card.load_data(list(data))
            self.log(f"{self.tr('msg.import_ok')}: {path}")

        except Exception as e:
            self.log(f"{self.tr('msg.error')} {e}")

    def action_export_bin(self):
        if not self.controller.memory:
            self.log(self.tr("msg.no_card_loaded"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("menu.export_bin"),
            "",
            "Binary Files (*.bin)"
        )
        if not path:
            return

        try:
            data = self.controller.export_memory()
            with open(path, "wb") as f:
                f.write(data)

            self.log(f"{self.tr('msg.export_ok')}: {path}")

        except Exception as e:
            self.log(f"{self.tr('msg.error')} {e}")

                                                                
              
                                                                
    def update_theme(self, theme):
        self.setStyleSheet(THEMES.get(theme, THEMES["dark"]))
        self.settings.set("theme", theme)
        self.log(f"{self.tr('msg.theme_changed')}: {theme}")

    def update_language(self, lang):
        self.settings.set("language", lang)
        self.lang.load(lang)

        QMessageBox.information(
            self,
            "Info",
            self.tr("msg.restart_needed")
        )
        
        
    def retranslate_ui(self):
        self.setWindowTitle("SLE Suite PRO")

                 
        self.findChildren(QLabel)[0].setText(self.tr("label.reader"))
        self.btn_refresh.setText(self.tr("btn.search"))
        self.btn_connect.setText(self.tr("btn.connect"))
        self.btn_disconnect.setText(self.tr("btn.disconnect"))
        self.btn_read.setText(self.tr("btn.read"))

                
        self.lbl_status.setText(self.tr("status.reader_none"))

              
        idx = self.tabs.indexOf(self.tab_card)
        self.tabs.setTabText(idx, self.tr("tab.card"))

        idx = self.tabs.indexOf(self.tab_chipinfo)
        self.tabs.setTabText(idx, self.tr("tab.chipinfo"))

                                          
        self.menuBar().clear()
        self.build_menu()


      

                                                                
          
                                                                
    def action_about(self):
        github_url = "https://github.com/wikilift" 
        
        message_html = (
            "SLE Suite PRO<br>"
            "<br>"
            "(c) 2025 Wikilift<br><br>"
            f'Meet me on: <a href="{github_url}">Wikilift on GitHub</a>'
        )
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About")
        
                                                                   
                                                          
        msg.setTextFormat(QtCore.Qt.TextFormat.RichText) 
        
        msg.setText(message_html)
        
        msg.exec()