import sys
import random
import math
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect, QRectF, pyqtSignal, QObject, QDateTime
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath
from pynput import keyboard, mouse

# НАСТРОЙКА: Сброс статистики CPM/WPM в ноль при простое (в миллисекундах)
SPEED_RESET_TIMEOUT_MS = 10000


# Класс для "искрящихся" частиц (эффект взрыва)
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4.0, 4.0)
        self.vy = random.uniform(-4.0, 4.0)
        self.radius = random.uniform(1.2, 3.2)  # Стандартный размер частиц
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
        if self.button_masher_mode:
            self.char_typed.emit()
            return

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
        self.count = 0
        self.particles = []
        self.ripples = []
        self.shake_frames = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0
        self.counting_enabled = True
        self.locked = False
        self.button_masher_mode = False
        
        # Режимы отображения: "counter" (счетчик), "time" (время), "speed" (скорость)
        self.display_mode = "counter"
        self.launch_time = QDateTime.currentDateTime()
        
        # Переменные для расчета скорости ввода (CPM / WPM)
        self.keystroke_times = []  
        
        # Скрытая шкала активности / накала (Heat)
        self.heat = 0.0            # Диапазон от 0.0 до 10.0
        self.last_type_time = QDateTime.currentDateTime()
        
        # Переменные эффекта "Дыхания" рамки
        self.breathing_angle = 0.0
        self.border_alpha = 200    # Базовая прозрачность неонового свечения
        
        # Переменные цвета
        self.hue = 0.0             
        self.base_speed = 0.3      
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(110, 110)
        
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 130, screen.height() - 170)
        
        self.drag_position = QPoint()
        self.click_start_pos = QPoint()
        self.drag_occurred = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_step)
        self.timer.start(16)      # Стартуем на 60 FPS
        
        self.monitor = InputMonitor()
        self.monitor.char_typed.connect(self.increment_count)
        self.monitor.mouse_clicked.connect(self.trigger_ripple)
        self.monitor.start()

    def increment_count(self):
        if not self.counting_enabled:
            return
        
        # Пробуждаем таймер до полных 60 кадров/сек при первом же клике
        if self.timer.interval() != 16:
            self.timer.setInterval(16)
        
        now = QDateTime.currentDateTime()
        self.count += 1
        
        # Записываем таймстамп нажатия для расчета скорости
        self.keystroke_times.append(now)
        
        # Накапливаем показатель активности (максимум до 10.0)
        self.heat = min(self.heat + 0.6, 10.0)
        self.last_type_time = now
        
        if self.display_mode == "counter":
            self.shake_frames = 10
            
            cx = self.width() // 2
            cy = self.height() // 2
            
            # Количество вылетающих за раз искр по-прежнему увеличивается с ростом накала (от 10 до 40)
            num_sparks = 10 + int(self.heat * 3.0)
            for _ in range(num_sparks):
                p = Particle(cx, cy)
                self.particles.append(p)
            
        self.update()

    def trigger_ripple(self):
        if not self.counting_enabled:
            return
        
        # Мгновенно пробуждаем таймер до 60 FPS при клике мыши
        if self.timer.interval() != 16:
            self.timer.setInterval(16)
            
        cx = self.width() // 2
        cy = self.height() // 2
        self.ripples.append(Ripple(cx, cy))
        self.update()

    def animate_step(self):
        now = QDateTime.currentDateTime()
        
        # Сброс CPM/WPM при простое более 10 секунд
        if self.last_type_time.msecsTo(now) > SPEED_RESET_TIMEOUT_MS:
            self.keystroke_times = []
        else:
            self.keystroke_times = [t for t in self.keystroke_times if t.msecsTo(now) <= 60000]
        
        # Медленное остывание кубика, когда пользователь не печатает
        if self.last_type_time.msecsTo(now) > 2000:
            if self.heat > 0:
                self.heat = max(0.0, self.heat - 0.04)
                
        # ЭФФЕКТ ПРОДОЛЖИТЕЛЬНОЙ ПЕЧАТИ:
        # Если кубик горячий (heat > 5.0), внутри куба спонтанно рождаются дополнительные искорки
        if self.heat > 5.0:
            if random.random() < (self.heat - 5.0) * 0.03:
                ex = random.uniform(20, self.width() - 20)
                ey = random.uniform(20, self.height() - 20)
                p = Particle(ex, ey)
                p.radius = random.uniform(1.0, 2.0)
                p.vx = random.uniform(-1.5, 1.5)
                p.vy = random.uniform(-1.5, 1.5)
                self.particles.append(p)

        # Обновление состояния искр
        active_particles = []
        for p in self.particles:
            p.update()
            if p.alpha > 0:
                active_particles.append(p)
        self.particles = active_particles

        # Обновление состояния ряби
        active_ripples = []
        for r in self.ripples:
            r.update()
            if r.alpha > 0:
                active_ripples.append(r)
        self.ripples = active_ripples
        
        # Обновление тряски текста (амплитуда зафиксирована на стандартном значении 3px)
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
        
        # Выбор цвета рамки с учетом динамического "дыхания" (border_alpha)
        if self.counting_enabled:
            border_color = QColor.fromHsv(int(self.hue), 240, 255, self.border_alpha)
        else:
            border_color = QColor(120, 120, 120, 150)
            
        bg_color = QColor(15, 15, 15, 210) if self.counting_enabled else QColor(20, 20, 20, 150)
        
        # Отрисовка кубика (толщина рамки 2px)
        pen_width = 2
        painter.setPen(QPen(border_color, pen_width))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(bg_rect, 15, 15)
        
        # --- СОЗДАЕМ МАСКУ ОБРЕЗКИ ПО КРАСИВОЙ ФОРМЕ СКРУГЛЕННЫХ УГЛОВ КУБИКА ---
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(bg_rect), 15, 15)  # Маска идеально совпадает со скруглением 15px
        
        painter.save()                 # Сохраняем состояние контекста
        painter.setClipPath(clip_path) # Устанавливаем скругленный клиппинг
        
        # 1. Отрисовка квадратной ряби (теперь плавно обрезается на краях)
        for r in self.ripples:
            ripple_color = QColor(border_color)
            ripple_color.setAlpha(int(r.alpha))
            painter.setPen(QPen(ripple_color, 2))
            painter.setBrush(Qt.NoBrush)
            
            r_rect = QRectF(r.cx - r.radius, r.cy - r.radius, r.radius * 2, r.radius * 2)
            painter.drawRoundedRect(r_rect, 10, 10)
            
        # 2. Отрисовка искр (конфетти) - теперь они тоже аккуратно растворяются у границ кубика,
        # не вылезая за его рамки и не срезаясь невидимым жестким краем окна!
        for p in self.particles:
            color = QColor(p.color)
            color.setAlpha(int(p.alpha))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(p.x - p.radius), int(p.y - p.radius), int(p.radius * 2), int(p.radius * 2))
            
        painter.restore()              # Восстанавливаем состояние контекста (отключаем маску обрезки)
        # --------------------------------------------------------------------------------------------------
        
        # Настройка цвета текста (выровнен идеально по центру во всех режимах)
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
            
            time_text = f"Старт:\n{launch_str}\nПрошло:\n{elapsed_str}"
            painter.drawText(bg_rect, Qt.AlignCenter, time_text)
            
        else:
            font = QFont("Consolas", 9, QFont.Bold)
            painter.setFont(font)
            
            cpm = len(self.keystroke_times)
            wpm = int(cpm / 5)  
            
            speed_text = f"Скорость:\n{cpm} CPM\n{wpm} WPM"
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
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.drag_occurred:
                self.toggle_display_mode()
            event.accept()

    def toggle_display_mode(self):
        if self.display_mode == "counter":
            self.display_mode = "time"
        elif self.display_mode == "time":
            self.display_mode = "speed"
        else:
            self.display_mode = "counter"
        self.update()

    # Контекстное меню по правому клику
    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)
        
        masher_action = QAction("Учитывая все нажатия клавиш и сочетаний", self)
        masher_action.setCheckable(True)
        masher_action.setChecked(self.button_masher_mode)
        masher_action.triggered.connect(self.toggle_masher_mode)
        contextMenu.addAction(masher_action)
        
        contextMenu.addSeparator()
        
        lock_action = QAction("Заблокировать" if not self.locked else "Разблокировать", self)
        lock_action.triggered.connect(self.toggle_lock)
        contextMenu.addAction(lock_action)
        
        pause_action = QAction("Приостановить подсчет" if self.counting_enabled else "Продолжить подсчет", self)
        pause_action.triggered.connect(self.toggle_counting)
        contextMenu.addAction(pause_action)
        
        reset_action = QAction("Сбросить счетчик", self)
        reset_action.triggered.connect(self.reset_counter)
        contextMenu.addAction(reset_action)
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(QApplication.quit)
        contextMenu.addAction(exit_action)
        
        contextMenu.exec_(self.mapToGlobal(event.pos()))

    def toggle_masher_mode(self, checked):
        self.button_masher_mode = checked
        self.monitor.button_masher_mode = checked

    def toggle_lock(self):
        self.locked = not self.locked

    def toggle_counting(self):
        self.counting_enabled = not self.counting_enabled
        self.update()

    def reset_counter(self):
        self.count = 0
        self.heat = 0.0
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = CubeWidget()
    widget.show()
    sys.exit(app.exec_())