from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QTabWidget, QStatusBar,
    QFileDialog, QMessageBox, QSplitter, QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from gui.dialogs.about_dialog import AboutDialog
from PySide6 import QtCore

from gui.widgets.log_panel import LogPanel
from gui.tabs.tab_card import TabCard
from gui.tabs.chip_info import TabChipInfo
from gui.tabs.tab_protection import TabProtection

from gui.themes import THEMES

from core.pcsc_manager import PCSCManager
from controllers.app_controller import AppController
from core.settings_manager import SettingsManager
from core.language_manager import LanguageManager, init_language
from core.card_worker import CardWorker
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from core.resource import resource_path


class MainWindow(QMainWindow):
    requestReadCard = Signal()

    def __init__(self):
        super().__init__()

        self.settings = SettingsManager()
        lang_code = self.settings.get("language", "es")
        self.lang = LanguageManager(lang_code)
        init_language(lang_code)
        self.pcsc = PCSCManager()

        self.controller = AppController(
            self.pcsc,
            self.settings,
            logger=self.log,
        )
        self.controller.main = self

        self.setWindowTitle("SLE Suite PRO")
        self.resize(1100, 750)

        theme = self.settings.get("theme", "dark")
        self.current_theme = theme
        self.setStyleSheet(THEMES.get(theme, THEMES["dark"]))

        self._build_menu_bar()
        self._build_central_widgets()
        self._build_status_bar()

        self.thread = QThread(self)
        self.worker = CardWorker(self.controller)
        self.worker.moveToThread(self.thread)
        self.thread.start()

        self.worker.log.connect(self.log)
        self.worker.error.connect(self.on_worker_error)
        self.worker.finished.connect(self.on_worker_finished)

        self.requestReadCard.connect(self.worker.read_card)

        self.controller.log = lambda msg: self.worker.log.emit(msg)
        icon_path = resource_path("assets/logo.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.refresh_readers()
        QTimer.singleShot(200, lambda: AboutDialog(self, self.tr).exec())

    def closeEvent(self, event):
        try:
            self.thread.quit()
            self.thread.wait()
        except Exception:
            pass
        super().closeEvent(event)

    def on_worker_error(self, msg):
        self.log(f"ERROR: {msg}")
        self.lbl_status.setText(self.tr("msg.error"))
        self.btn_read.setEnabled(True)

    def on_worker_finished(self, result):
        self.btn_read.setEnabled(True)

        if isinstance(result, list):
            try:
                self.tab_card.load_data(result)
                self.tab_card.update_state(connected=True, card_loaded=True)
                idx = self.tabs.indexOf(self.tab_card)
                if idx != -1:
                    self.tabs.setCurrentIndex(idx)
                self.log(self.tr("msg.card_ok"))
            except Exception as exc:
                self.log(f"{self.tr('msg.error')} {exc}")

            try:
                self.tab_protection.load_from_card(self.controller.card)
            except Exception as exc:
                self.log(f"{self.tr('msg.protection_tab_error')}: {exc}")

            try:
                self.tab_chipinfo.load_chip(self.controller.card)
                self.update_psc_state()
                self.lbl_psc_state.setVisible(True)
            except Exception as exc:
                self.log(f"{self.tr('msg.chipinfo_tab_error')}: {exc}")

        elif result is True:
            self.update_psc_state()
            self.log(self.tr("msg.operation_done"))

    def tr(self, key: str) -> str:
        return self.lang.tr(key)

    def _build_menu_bar(self):
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

    def _build_central_widgets(self):
        root = QWidget()
        root_layout = QVBoxLayout()
        root.setLayout(root_layout)
        self.setCentralWidget(root)

        top = QHBoxLayout()

        self.lbl_reader = QLabel(self.tr("label.reader"))
        top.addWidget(self.lbl_reader)

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
        
        self.lbl_psc_state = QLabel(self.tr("label.psc_state_unknown"))
        self.lbl_psc_state.setStyleSheet("color: orange; font-weight: bold; padding-left: 10px;")
        top.addWidget(self.lbl_psc_state)
        self.lbl_psc_state.setVisible(False)

        top.addStretch()
        root_layout.addLayout(top)

        splitter = QSplitter(Qt.Vertical)
        self.splitter = splitter

        top_container = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_container.setLayout(top_layout)

        self.tabs = QTabWidget()
        self.tab_card = TabCard(self)
        self.tab_chipinfo = TabChipInfo(self)
        self.tab_protection = TabProtection(self)

        self.tabs.addTab(self.tab_card, self.tr("tab.card"))
        self.tabs.addTab(self.tab_chipinfo, self.tr("tab.chipinfo"))
        self.tabs.addTab(self.tab_protection, self.tr("tab.protection"))

        top_layout.addWidget(self.tabs)

        is_dark = (self.current_theme == "dark")
        self.log_panel = LogPanel(is_dark=is_dark)

        splitter.addWidget(top_container)
        splitter.addWidget(self.log_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)
        self.update_psc_state()

    def _build_status_bar(self):
        status = QStatusBar()
        self.setStatusBar(status)

        self.lbl_status = QLabel(self.tr("status.reader_none"))
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
        status.addWidget(self.lbl_status)

        self.btn_clear_log = QPushButton(self.tr("btn.clear_log"))
        self.btn_clear_log.clicked.connect(self.log_panel.clear_log)
        status.addPermanentWidget(self.btn_clear_log)

    def read_card(self):
        if not self.controller.conn:
            self.log(self.tr("msg.connect_reader_first"))
            return

        self.log(self.tr("msg.reading_card"))
        self.btn_read.setEnabled(False)
        self.requestReadCard.emit()

    def log(self, msg: str):
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
            self.lbl_status.setText(self.tr("status.reader_none"))
            self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
            self.log(self.tr("msg.no_readers"))

    def connect_reader(self):
        idx = self.reader_combo.currentIndex()
        if idx < 0:
            return

        readers = self.controller.list_readers()
        if not readers or idx >= len(readers):
            return

        reader = readers[idx]

        try:
            atr = self.controller.connect_reader(reader)
            atr_str = " ".join(f"{x:02X}" for x in atr)
            self.log(f"{self.tr('msg.connected_to')} {reader} | ATR: {atr_str}")

            self.tab_card.update_state(connected=True, card_loaded=False)

            self.lbl_status.setText(f"{self.tr('status.reader')}: {reader}")
            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")

            self.btn_connect.setVisible(False)
            self.btn_refresh.setVisible(False)
            self.btn_disconnect.setVisible(True)
            self.btn_read.setVisible(True)

        except Exception as exc:
            self.log(f"{self.tr('msg.error_connect')} {exc}")

    def disconnect_reader(self):
        self.controller.disconnect_reader()
        self.log(self.tr("msg.reader_disconnected_ok"))
        self.tab_card.update_state(connected=False, card_loaded=False)

        self.btn_connect.setVisible(True)
        self.btn_disconnect.setVisible(False)
        self.btn_read.setVisible(False)
        self.btn_refresh.setVisible(True)

        self.lbl_status.setText(self.tr("status.reader_none"))
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
        self.update_psc_state()
        self.lbl_psc_state.setVisible(False)

    def action_import_bin(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("menu.import_bin"),
            "",
            self.tr("msg.binary_files"),
        )
        if not path:
            return

        try:
            with open(path, "rb") as fh:
                data = fh.read()

            self.tab_card.load_data(list(data))
            self.log(f"{self.tr('msg.import_ok')}: {path}")
        except Exception as exc:
            self.log(f"{self.tr('msg.error')} {exc}")

    def action_export_bin(self):
        if not self.controller.memory:
            self.log(self.tr("msg.no_memory_export"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("menu.export_bin"),
            "",
            self.tr("msg.binary_files"),
        )
        if not path:
            return

        try:
            data = self.controller.export_memory()
            with open(path, "wb") as fh:
                fh.write(data)
            self.log(f"{self.tr('msg.export_ok')}: {path}")
        except Exception as exc:
            self.log(f"{self.tr('msg.error')} {exc}")

    def update_theme(self, theme: str):
        self.current_theme = theme
        self.setStyleSheet(THEMES.get(theme, THEMES["dark"]))
        self.settings.set("theme", theme)
        is_dark = (theme == "dark")
        self.log_panel.set_dark_mode(is_dark)
        self.log(f"{self.tr('msg.theme_changed')}: {theme}")

    def update_language(self, lang: str):
        self.settings.set("language", lang)
        self.lang.load(lang)
        init_language(lang)

        QMessageBox.information(
            self,
            self.tr("msg.information"),
            self.tr("msg.restart_needed"),
        )


    def retranslate_ui(self):
        self.setWindowTitle("SLE Suite PRO")

        self.lbl_reader.setText(self.tr("label.reader"))
        self.btn_refresh.setText(self.tr("btn.search"))
        self.btn_connect.setText(self.tr("btn.connect"))
        self.btn_disconnect.setText(self.tr("btn.disconnect"))
        self.btn_read.setText(self.tr("btn.read"))

        if self.controller.connected_reader is None:
            self.lbl_status.setText(self.tr("status.reader_none"))

        idx = self.tabs.indexOf(self.tab_card)
        if idx != -1:
            self.tabs.setTabText(idx, self.tr("tab.card"))

        idx = self.tabs.indexOf(self.tab_chipinfo)
        if idx != -1:
            self.tabs.setTabText(idx, self.tr("tab.chipinfo"))

        idx = self.tabs.indexOf(self.tab_protection)
        if idx != -1:
            self.tabs.setTabText(idx, self.tr("tab.protection"))

        self.menuBar().clear()
        self._build_menu_bar()

    def action_about(self):
        dlg = AboutDialog(self, self.tr)
        dlg.exec()


    def update_psc_state(self):
        card = self.controller.card
        if not card:
            self.lbl_psc_state.setText(self.tr("label.psc_state_unknown"))
            self.lbl_psc_state.setStyleSheet("color: orange; font-weight: bold; padding-left: 10px;")
            return

        if card.is_authenticated:
            self.lbl_psc_state.setText(self.tr("label.psc_state_logged"))
            self.lbl_psc_state.setStyleSheet("color: #00e600; font-weight: bold; padding-left: 10px;")
        else:
            self.lbl_psc_state.setText(self.tr("label.psc_state_required"))
            self.lbl_psc_state.setStyleSheet("color: red; font-weight: bold; padding-left: 10px;")

    def ask_psc_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(self.tr("msg.psc_dialog_title"))
        dlg.setText(self.tr("msg.psc_dialog_text"))
        dlg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        inp = QLineEdit()
        dlg.layout().addWidget(inp)

        ret = dlg.exec()
        if ret != QMessageBox.Ok:
            return None

        txt = inp.text().strip().replace(" ", "")
        if len(txt) != 4:
            return None

        try:
            return [int(txt[0:2], 16), int(txt[2:4], 16)]
        except Exception:
            return None
