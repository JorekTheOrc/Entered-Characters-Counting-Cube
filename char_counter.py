import sys
import os
import random
import math
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect, QRectF, pyqtSignal, QObject, QDateTime, QSettings, QStandardPaths, QUrl
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath, QIcon, QPixmap, QDesktopServices
from pynput import keyboard, mouse

# НАСТРОЙКА: Сброс статистики CPM/WPM в ноль при простое (в миллисекундах)
SPEED_RESET_TIMEOUT_MS = 10000

# Словарь переводов для локализации интерфейса
TRANSLATIONS = {
    "ru": {
        "masher_mode": "Учитывать клики мышью",
        "lock": "Заблокировать",
        "unlock": "Разблокировать",
        "pause": "Приостановить подсчет",
        "resume": "Продолжить подсчет",
        "reset": "Сбросить счетчик",
        "hide_tray": "Скрыть в трей",
        "show_app": "Показать куб",
        "open_log": "Открыть лог статистики",
        "exit": "Выход",
        "language": "Язык \\ Language",
        "start": "Старт",
        "elapsed": "Прошло",
        "speed": "Скорость",
    },
    "en": {
        "masher_mode": "Count mouse clicks",
        "lock": "Lock",
        "unlock": "Unlock",
        "pause": "Pause Counting",
        "resume": "Resume Counting",
        "reset": "Reset Counter",
        "hide_tray": "Hide to tray",
        "show_app": "Show Cube",
        "open_log": "Open Stats Log",
        "exit": "Exit",
        "language": "Language \\ Язык",
        "start": "Start",
        "elapsed": "Elapsed",
        "speed": "Speed",
    }
}


# Класс для "искрящихся" частиц (эффект взрыва)
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4.0, 4.0)
        self.vy = random.uniform(-4.0, 4.0)
        self.radius = random.uniform(1.2, 3.2)
        self.color = random.choice([
            QColor(255, 69, 0),    # Красно-оранжевый
            QColor(255, 140, 0),   # Темно-оранжевый
            QColor(255, 215, 0),   # Золотой
            QColor(255, 255, 255), # Белый
            QColor(255, 105, 180)  # Розовый акцент
        ])
        self.alpha = 255
        self.decay = random.uniform(8.0, 15.0)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= self.decay
        if self.alpha < 0:
            self.alpha = 0


# Класс для создания эффекта ряби (круговой волны)
class Ripple:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.radius = 2.0
        self.alpha = 255
        self.speed = 2.5

    def update(self):
        self.radius += self.speed
        self.alpha -= 10
        if self.alpha < 0:
            self.alpha = 0


# Поток-монитор устройств ввода
class InputMonitor(QObject):
    char_typed = pyqtSignal()
    mouse_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.button_masher_mode = False
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.win_pressed = False
        
        self.pressed_keys = set()
        
        self.key_listener = keyboard.Listener(
            on_press=self.on_press, 
            on_release=self.on_release
        )
        self.mouse_listener = mouse.Listener(
            on_click=self.on_click
        )
        
    def start(self):
        self.key_listener.start()
        self.mouse_listener.start()
        
    def on_click(self, x, y, button, pressed):
        if pressed and self.button_masher_mode:
            self.mouse_clicked.emit()
        
    def on_press(self, key):
        if key in self.pressed_keys:
            return
        self.pressed_keys.add(key)

        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.ctrl_pressed = True
            return
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.alt_pressed = True
            return
        if key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            self.win_pressed = True
            return
            
        if key in (keyboard.Key.enter, keyboard.Key.backspace, keyboard.Key.tab, keyboard.Key.esc,
                   keyboard.Key.delete, keyboard.Key.insert, keyboard.Key.page_up, keyboard.Key.page_down,
                   keyboard.Key.home, keyboard.Key.end, keyboard.Key.left, keyboard.Key.right,
                   keyboard.Key.up, keyboard.Key.down):
            return

        if key == keyboard.Key.space:
            if not (self.ctrl_pressed or self.alt_pressed or self.win_pressed):
                self.char_typed.emit()
            return

        if not (self.ctrl_pressed or self.alt_pressed or self.win_pressed):
            if hasattr(key, 'char') and key.char is not None:
                if ord(key.char) >= 32:
                    self.char_typed.emit()
                    
    def on_release(self, key):
        self.pressed_keys.discard(key)

        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.ctrl_pressed = False
        elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.alt_pressed = False
        elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            self.win_pressed = False


# Главный виджет куба
class CubeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("CharCounterApp", "CharCounter")
        
        # Путь к файлу лога в AppData
        app_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
        self.log_file_path = os.path.join(app_data_dir, "stats_log.txt")

        # Раздельный учет нажатий
        self.count = 0
        self.keys_count = 0
        self.clicks_count = 0
        self._logged_exit = False
        
        self.particles = []
        self.ripples = []
        self.shake_frames = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0
        self.counting_enabled = True
        self.locked = False
        self.button_masher_mode = False
        self.lang = "ru"
        
        self.display_mode = "counter"
        self.launch_time = QDateTime.currentDateTime()
        self.keystroke_times = []  
        
        self.heat = 0.0
        self.last_type_time = QDateTime.currentDateTime()
        
        self.border_alpha = 200
        self.hue = 0.0             
        self.base_speed = 0.3      
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(110, 110)
        
        # Позиционирование по умолчанию
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 130, screen.height() - 170)
        
        # Загрузка сохраненных настроек
        self.load_settings()
        
        # Запись старта в лог
        self.log_session_start()
        
        self.drag_position = QPoint()
        self.click_start_pos = QPoint()
        self.drag_occurred = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_step)
        self.timer.start(16)
        
        self.monitor = InputMonitor()
        self.monitor.button_masher_mode = self.button_masher_mode
        self.monitor.char_typed.connect(self.handle_key_typed)
        self.monitor.mouse_clicked.connect(self.handle_mouse_click)
        self.monitor.start()

        # Инициализация системного трея
        self.init_tray()

    def get_mode_name(self):
        modes = {
            "counter": "Счетчик \\ Counter",
            "time": "Время \\ Time",
            "speed": "Скорость \\ Speed"
        }
        return modes.get(self.display_mode, self.display_mode)

    def log_session_start(self):
        now_str = QDateTime.currentDateTime().toString("dd.MM.yyyy hh:mm:ss")
        masher_str = "Включен \\ Enabled" if self.button_masher_mode else "Выключен \\ Disabled"
        
        line = (
            f"[{now_str}] >>> ЗАПУСК ПРОГРАММЫ \\ PROGRAM LAUNCH\n"
            f"  • Выбранный режим \\ Selected mode: {self.get_mode_name()}\n"
            f"  • Учет кликов мыши \\ Mouse click tracking: {masher_str}\n"
            f"{'-'*60}\n"
        )
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"Ошибка записи лога старта: {e}")

    def log_session_end(self):
        if self._logged_exit:
            return
        self._logged_exit = True
        
        now = QDateTime.currentDateTime()
        now_str = now.toString("dd.MM.yyyy hh:mm:ss")
        masher_str = "Включен \\ Enabled" if self.button_masher_mode else "Выключен \\ Disabled"
        
        elapsed_sec = self.launch_time.secsTo(now)
        hours = elapsed_sec // 3600
        minutes = (elapsed_sec % 3600) // 60
        seconds = elapsed_sec % 60
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        line = (
            f"[{now_str}] <<< ЗАВЕРШЕНИЕ РАБОТЫ \\ SESSION END\n"
            f"  • Время работы \\ Uptime: {duration_str}\n"
            f"  • Нажатий клавиш \\ Keystrokes: {self.keys_count}\n"
            f"  • Кликов мыши \\ Mouse clicks: {self.clicks_count}\n"
            f"  • Всего действий за сессию \\ Total session actions: {self.count}\n"
            f"  • Финальный режим \\ Final mode: {self.get_mode_name()}\n"
            f"  • Учет кликов мыши \\ Mouse click tracking: {masher_str}\n"
            f"{'='*60}\n\n"
        )
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"Ошибка записи лога выхода: {e}")

    def open_stats_log(self):
        if not os.path.exists(self.log_file_path):
            open(self.log_file_path, "w", encoding="utf-8").close()
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.log_file_path))

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.create_tray_icon())
        
        tray_menu = QMenu()
        self.toggle_action = QAction(self.tr_text("show_app"), self)
        self.toggle_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(self.toggle_action)

        open_log_action = QAction(self.tr_text("open_log"), self)
        open_log_action.triggered.connect(self.open_stats_log)
        tray_menu.addAction(open_log_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction(self.tr_text("exit"), self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def create_tray_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.setPen(QPen(QColor(0, 200, 255), 2))
        painter.drawRoundedRect(3, 3, 26, 26, 6, 6)
        
        painter.setFont(QFont("Consolas", 12, QFont.Bold))
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(QRect(0, 0, 32, 32), Qt.AlignCenter, "#")
        painter.end()
        
        return QIcon(pixmap)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.toggle_action.setText(self.tr_text("show_app"))
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self.toggle_action.setText(self.tr_text("hide_tray"))

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_visibility()

    def load_settings(self):
        self.lang = self.settings.value("lang", "ru", type=str)
        self.button_masher_mode = self.settings.value("masher_mode", False, type=bool)
        self.locked = self.settings.value("locked", False, type=bool)
        self.counting_enabled = self.settings.value("counting_enabled", True, type=bool)
        
        self.count = 0
        self.keys_count = 0
        self.clicks_count = 0
        
        pos = self.settings.value("pos")
        if pos and isinstance(pos, QPoint):
            self.move(pos)

    def save_settings(self):
        self.settings.setValue("lang", self.lang)
        self.settings.setValue("masher_mode", self.button_masher_mode)
        self.settings.setValue("locked", self.locked)
        self.settings.setValue("counting_enabled", self.counting_enabled)
        self.settings.setValue("pos", self.pos())

    def tr_text(self, key):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["ru"]).get(key, key)

    def set_language(self, lang):
        self.lang = lang
        self.save_settings()
        if hasattr(self, 'toggle_action'):
            self.toggle_action.setText(self.tr_text("show_app") if not self.isVisible() else self.tr_text("hide_tray"))
        self.update()

    def handle_key_typed(self):
        if not self.counting_enabled:
            return
        self.keys_count += 1
        self.register_input_action(is_key=True)

    def handle_mouse_click(self):
        if not self.counting_enabled:
            return
        self.clicks_count += 1
        self.trigger_ripple()
        self.register_input_action(is_key=False)

    def register_input_action(self, is_key=True):
        if self.timer.interval() != 16:
            self.timer.setInterval(16)
        
        now = QDateTime.currentDateTime()
        self.count = self.keys_count + self.clicks_count
        
        self.keystroke_times.append(now)
        self.heat = min(self.heat + 0.6, 10.0)
        self.last_type_time = now
        
        if self.display_mode == "counter" and is_key:
            self.shake_frames = 10
            cx = self.width() // 2
            cy = self.height() // 2
            
            num_sparks = 10 + int(self.heat * 3.0)
            for _ in range(num_sparks):
                p = Particle(cx, cy)
                self.particles.append(p)
            
        self.update()

    def trigger_ripple(self):
        if not self.counting_enabled:
            return
        
        if self.timer.interval() != 16:
            self.timer.setInterval(16)
            
        cx = self.width() // 2
        cy = self.height() // 2
        self.ripples.append(Ripple(cx, cy))
        self.update()

    def animate_step(self):
        now = QDateTime.currentDateTime()
        
        if self.last_type_time.msecsTo(now) > SPEED_RESET_TIMEOUT_MS:
            self.keystroke_times = []
        else:
            self.keystroke_times = [t for t in self.keystroke_times if t.msecsTo(now) <= 60000]
        
        if self.last_type_time.msecsTo(now) > 2000:
            if self.heat > 0:
                self.heat = max(0.0, self.heat - 0.04)
                
        if self.heat > 5.0:
            if random.random() < (self.heat - 5.0) * 0.03:
                ex = random.uniform(20, self.width() - 20)
                ey = random.uniform(20, self.height() - 20)
                p = Particle(ex, ey)
                p.radius = random.uniform(1.0, 2.0)
                p.vx = random.uniform(-1.5, 1.5)
                p.vy = random.uniform(-1.5, 1.5)
                self.particles.append(p)

        active_particles = []
        for p in self.particles:
            p.update()
            if p.alpha > 0:
                active_particles.append(p)
        self.particles = active_particles

        active_ripples = []
        for r in self.ripples:
            r.update()
            if r.alpha > 0:
                active_ripples.append(r)
        self.ripples = active_ripples
        
        if self.shake_frames > 0 and self.display_mode == "counter":
            max_offset = 3
            self.shake_offset_x = random.randint(-max_offset, max_offset)
            self.shake_offset_y = random.randint(-max_offset, max_offset)
            self.shake_frames -= 1
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0
            
        current_speed = self.base_speed + (self.heat * 0.5)
        self.hue = (self.hue + current_speed) % 360
        
        self.update()

    def get_font_size(self):
        length = len(str(self.count))
        if length <= 2: return 28
        elif length == 3: return 22
        elif length == 4: return 17
        elif length == 5: return 13
        else: return 10

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_rect = QRect(12, 12, self.width() - 24, self.height() - 24)
        
        if self.counting_enabled:
            border_color = QColor.fromHsv(int(self.hue), 240, 255, self.border_alpha)
        else:
            border_color = QColor(120, 120, 120, 150)
            
        bg_color = QColor(15, 15, 15, 210) if self.counting_enabled else QColor(20, 20, 20, 150)
        
        pen_width = 2
        painter.setPen(QPen(border_color, pen_width))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(bg_rect, 15, 15)
        
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(bg_rect), 15, 15)
        
        painter.save()
        painter.setClipPath(clip_path)
        
        for r in self.ripples:
            ripple_color = QColor(border_color)
            ripple_color.setAlpha(int(r.alpha))
            painter.setPen(QPen(ripple_color, 2))
            painter.setBrush(Qt.NoBrush)
            r_rect = QRectF(r.cx - r.radius, r.cy - r.radius, r.radius * 2, r.radius * 2)
            painter.drawRoundedRect(r_rect, 10, 10)
            
        for p in self.particles:
            color = QColor(p.color)
            color.setAlpha(int(p.alpha))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(p.x - p.radius), int(p.y - p.radius), int(p.radius * 2), int(p.radius * 2))
            
        painter.restore()
        
        text_color = QColor(255, 255, 255) if self.counting_enabled else QColor(150, 150, 150)
        painter.setPen(QPen(text_color))

        if self.display_mode == "counter":
            font = QFont("Consolas", self.get_font_size(), QFont.Bold)
            painter.setFont(font)
            text_rect = bg_rect.translated(self.shake_offset_x, self.shake_offset_y)
            painter.drawText(text_rect, Qt.AlignCenter, str(self.count))
                
        elif self.display_mode == "time":
            font = QFont("Consolas", 8, QFont.Bold)
            painter.setFont(font)
            
            elapsed_seconds = self.launch_time.secsTo(QDateTime.currentDateTime())
            hours = elapsed_seconds // 3600
            minutes = (elapsed_seconds % 3600) // 60
            seconds = elapsed_seconds % 60
            
            elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            launch_str = self.launch_time.toString("hh:mm:ss")
            
            time_text = f"{self.tr_text('start')}:\n{launch_str}\n{self.tr_text('elapsed')}:\n{elapsed_str}"
            painter.drawText(bg_rect, Qt.AlignCenter, time_text)
            
        else:
            font = QFont("Consolas", 9, QFont.Bold)
            painter.setFont(font)
            
            cpm = len(self.keystroke_times)
            wpm = int(cpm / 5)  
            
            speed_text = f"{self.tr_text('speed')}:\n{cpm} CPM\n{wpm} WPM"
            painter.drawText(bg_rect, Qt.AlignCenter, speed_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_start_pos = event.globalPos()
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.drag_occurred = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if (event.globalPos() - self.click_start_pos).manhattanLength() > 5:
                self.drag_occurred = True
                
            if not self.locked:
                self.move(event.globalPos() - self.drag_position)
                self.save_settings()
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.drag_occurred:
                self.toggle_display_mode()
            event.accept()
        elif event.button() == Qt.MiddleButton:
            self.toggle_visibility()
            event.accept()

    def toggle_display_mode(self):
        if self.display_mode == "counter":
            self.display_mode = "time"
        elif self.display_mode == "time":
            self.display_mode = "speed"
        else:
            self.display_mode = "counter"
        self.update()

    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)
        
        masher_action = QAction(self.tr_text("masher_mode"), self)
        masher_action.setCheckable(True)
        masher_action.setChecked(self.button_masher_mode)
        masher_action.triggered.connect(self.toggle_masher_mode)
        contextMenu.addAction(masher_action)
        
        contextMenu.addSeparator()
        
        lock_text = self.tr_text("unlock") if self.locked else self.tr_text("lock")
        lock_action = QAction(lock_text, self)
        lock_action.triggered.connect(self.toggle_lock)
        contextMenu.addAction(lock_action)
        
        pause_text = self.tr_text("resume") if not self.counting_enabled else self.tr_text("pause")
        pause_action = QAction(pause_text, self)
        pause_action.triggered.connect(self.toggle_counting)
        contextMenu.addAction(pause_action)
        
        reset_action = QAction(self.tr_text("reset"), self)
        reset_action.triggered.connect(self.reset_counter)
        contextMenu.addAction(reset_action)

        hide_tray_action = QAction(self.tr_text("hide_tray"), self)
        hide_tray_action.triggered.connect(self.hide)
        contextMenu.addAction(hide_tray_action)

        open_log_action = QAction(self.tr_text("open_log"), self)
        open_log_action.triggered.connect(self.open_stats_log)
        contextMenu.addAction(open_log_action)
        
        lang_menu = contextMenu.addMenu(self.tr_text("language"))
        
        ru_lang_action = QAction("Русский", self)
        ru_lang_action.setCheckable(True)
        ru_lang_action.setChecked(self.lang == "ru")
        ru_lang_action.triggered.connect(lambda: self.set_language("ru"))
        
        en_lang_action = QAction("English", self)
        en_lang_action.setCheckable(True)
        en_lang_action.setChecked(self.lang == "en")
        en_lang_action.triggered.connect(lambda: self.set_language("en"))
        
        lang_menu.addAction(ru_lang_action)
        lang_menu.addAction(en_lang_action)
        
        contextMenu.addSeparator()
        
        exit_action = QAction(self.tr_text("exit"), self)
        exit_action.triggered.connect(self.quit_app)
        contextMenu.addAction(exit_action)
        
        contextMenu.exec_(self.mapToGlobal(event.pos()))

    def toggle_masher_mode(self, checked):
        self.button_masher_mode = checked
        self.monitor.button_masher_mode = checked
        self.save_settings()

    def toggle_lock(self):
        self.locked = not self.locked
        self.save_settings()

    def toggle_counting(self):
        self.counting_enabled = not self.counting_enabled
        self.save_settings()
        self.update()

    def reset_counter(self):
        self.count = 0
        self.keys_count = 0
        self.clicks_count = 0
        self.heat = 0.0
        self.update()

    def quit_app(self):
        self.on_shutdown()
        QApplication.quit()

    def closeEvent(self, event):
        self.on_shutdown()
        event.accept()

    def on_shutdown(self):
        """Гарантированное сохранение настроек и запись в лог при выходе."""
        self.save_settings()
        self.log_session_end()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    widget = CubeWidget()
    
    # Гарантированное сохранение при системном завершении работы / выключении ПК
    app.aboutToQuit.connect(widget.on_shutdown)
    
    widget.show()
    sys.exit(app.exec_())