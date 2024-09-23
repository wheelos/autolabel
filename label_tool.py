import sys
import os
import yaml
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QAction, QVBoxLayout,
    QHBoxLayout, QWidget, QSizePolicy, QToolBar, QMessageBox, QStyle, QActionGroup
)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPen
from PyQt5.QtCore import Qt, QUrl, QPoint, QRect, QThread, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setScaledContents(True)  # 允许自动缩放图像

        self.coord_label = QLabel(self)
        self.coord_label.setStyleSheet(
            "color: red; background-color: rgba(255, 255, 255, 128);"
        )
        self.coord_label.setFont(QFont("Arial", 12))
        self.coord_label.hide()
        self.coord_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # 设置尺寸策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.coord_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # 绘图相关属性
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.rectangles = []
        self.points = []  # 存储 (point, point_type)
        self.current_tool = None  # 'rectangle' or 'point'
        self.point_type = None  # 'target' or 'non-target'

        # 操作栈，用于撤销操作
        self.actions = []

    def mousePressEvent(self, event):
        if self.current_tool == 'rectangle' and event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
        elif self.current_tool == 'point' and self.point_type and event.button() == Qt.LeftButton:
            self.points.append((event.pos(), self.point_type))
            # 记录操作
            self.actions.append(('point', (event.pos(), self.point_type)))
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self.drawing and self.current_tool == 'rectangle':
            self.end_point = event.pos()
            self.update()

        if self.pixmap():
            pixmap = self.pixmap()
            label_size = self.size()
            pixmap_size = pixmap.size()

            if pixmap_size.width() == 0 or pixmap_size.height() == 0:
                super().mouseMoveEvent(event)
                return

            # 计算缩放比例
            x_ratio = pixmap_size.width() / label_size.width()
            y_ratio = pixmap_size.height() / label_size.height()

            # 获取实际坐标
            x = int(pos.x() * x_ratio)
            y = int(pos.y() * y_ratio)

            # 确保坐标在图像范围内
            if 0 <= x < pixmap_size.width() and 0 <= y < pixmap_size.height():
                self.coord_label.setText(f"坐标: ({x}, {y})")
                # 防止坐标标签超出图像边界
                label_x = pos.x()
                label_y = pos.y()
                label_width = self.coord_label.width()
                label_height = self.coord_label.height()
                if label_x + label_width > label_size.width():
                    label_x = label_size.width() - label_width
                if label_y + label_height > label_size.height():
                    label_y = label_size.height() - label_height
                self.coord_label.move(label_x, label_y)
                self.coord_label.adjustSize()
                self.coord_label.show()
            else:
                self.coord_label.hide()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drawing and self.current_tool == 'rectangle':
            self.end_point = event.pos()
            self.rectangles.append((self.start_point, self.end_point))
            # 记录操作
            self.actions.append(('rectangle', (self.start_point, self.end_point)))
            self.drawing = False
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制已保存的矩形
        pen = QPen(Qt.green, 2, Qt.SolidLine)
        painter.setPen(pen)
        for rect in self.rectangles:
            rect_normalized = QRect(rect[0], rect[1]).normalized()
            painter.drawRect(rect_normalized)

        # 绘制正在绘制的矩形
        if self.drawing and self.current_tool == 'rectangle':
            pen = QPen(Qt.red, 2, Qt.DashLine)
            painter.setPen(pen)
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)

        # 绘制选取的点
        for point, point_type in self.points:
            if point_type == 'target':
                pen = QPen(Qt.green, 5)
            else:
                pen = QPen(Qt.red, 5)
            painter.setPen(pen)
            painter.drawPoint(point)

    def leaveEvent(self, event):
        self.coord_label.hide()
        super().leaveEvent(event)

    def undo_last_action(self):
        if self.actions:
            last_action = self.actions.pop()
            if last_action[0] == 'rectangle' and self.rectangles:
                self.rectangles.pop()
            elif last_action[0] == 'point' and self.points:
                self.points.pop()
            self.update()
        else:
            QMessageBox.information(self, "提示", "没有可撤销的操作！")

    def clear_all(self):
        self.rectangles.clear()
        self.points.clear()
        self.actions.clear()
        self.update()

    def save_image(self):
        if self.pixmap():
            # 创建一个与原始图像相同大小的 QPixmap
            pixmap = self.pixmap().copy()
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 计算缩放比例
            label_size = self.size()
            pixmap_size = pixmap.size()
            x_ratio = pixmap_size.width() / label_size.width()
            y_ratio = pixmap_size.height() / label_size.height()

            # 绘制矩形
            pen = QPen(Qt.green, 2)
            painter.setPen(pen)
            for rect in self.rectangles:
                start = QPoint(int(rect[0].x() * x_ratio), int(rect[0].y() * y_ratio))
                end = QPoint(int(rect[1].x() * x_ratio), int(rect[1].y() * y_ratio))
                rect_normalized = QRect(start, end).normalized()
                painter.drawRect(rect_normalized)

            # 绘制点
            for point, point_type in self.points:
                p = QPoint(int(point.x() * x_ratio), int(point.y() * y_ratio))
                if point_type == 'target':
                    pen = QPen(Qt.green, 5)
                else:
                    pen = QPen(Qt.red, 5)
                painter.setPen(pen)
                painter.drawPoint(p)

            painter.end()

            # 保存图像
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存图像", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;BMP Files (*.bmp)"
            )
            if file_path:
                pixmap.save(file_path)
        else:
            QMessageBox.warning(self, "警告", "没有可保存的图像！")


class VideoWidget(QVideoWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.coord_label = QLabel(self)
        self.coord_label.setStyleSheet(
            "color: red; background-color: rgba(255, 255, 255, 128);"
        )
        self.coord_label.setFont(QFont("Arial", 12))
        self.coord_label.hide()
        self.coord_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # 设置尺寸策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.coord_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if 0 <= pos.x() < self.width() and 0 <= pos.y() < self.height():
            self.coord_label.setText(f"坐标: ({pos.x()}, {pos.y()})")
            # 防止坐标标签超出视频边界
            label_x = pos.x()
            label_y = pos.y()
            label_width = self.coord_label.width()
            label_height = self.coord_label.height()
            if label_x + label_width > self.width():
                label_x = self.width() - label_width
            if label_y + label_height > self.height():
                label_y = self.height() - label_height
            self.coord_label.move(label_x, label_y)
            self.coord_label.adjustSize()
            self.coord_label.show()
        else:
            self.coord_label.hide()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.coord_label.hide()
        super().leaveEvent(event)


class CommandThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.command = command

    def run(self):
        try:
            result = subprocess.run(self.command, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                output = result.stdout
                self.finished.emit(True, output)
            else:
                error_output = result.stderr
                self.finished.emit(False, error_output)
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoLabel")
        self.resize(800, 600)

        # 创建一个中央小部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 创建主布局为水平布局
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # 创建工具栏（左侧）
        self.tool_bar = QToolBar("工具栏", self)
        self.addToolBar(Qt.LeftToolBarArea, self.tool_bar)
        self.tool_bar.setOrientation(Qt.Vertical)
        self.tool_bar.setMovable(False)

        # 添加工具按钮

        # 矩形工具
        self.rect_tool_action = QAction("矩形工具", self)
        self.rect_tool_action.setCheckable(True)
        self.rect_tool_action.triggered.connect(self.select_rectangle_tool)
        self.tool_bar.addAction(self.rect_tool_action)

        # 点工具
        self.point_tool_action = QAction("点工具", self)
        self.point_tool_action.setCheckable(True)
        self.point_tool_action.triggered.connect(self.select_point_tool)
        self.tool_bar.addAction(self.point_tool_action)

        # 工具组，用于互斥选择
        self.tool_actions = [
            self.rect_tool_action,
            self.point_tool_action
        ]

        # 添加点类型动作，但初始时禁用
        self.target_point_action = QAction("目标点", self)
        self.target_point_action.setCheckable(True)
        self.target_point_action.setEnabled(False)

        self.non_target_point_action = QAction("非目标点", self)
        self.non_target_point_action.setCheckable(True)
        self.non_target_point_action.setEnabled(False)

        # 创建动作组
        self.point_type_action_group = QActionGroup(self)
        self.point_type_action_group.addAction(self.target_point_action)
        self.point_type_action_group.addAction(self.non_target_point_action)
        self.point_type_action_group.setExclusive(True)
        self.point_type_action_group.triggered.connect(self.point_type_selected)

        # 添加到工具栏
        self.tool_bar.addAction(self.target_point_action)
        self.tool_bar.addAction(self.non_target_point_action)

        # 创建一个自定义标签用于显示图像
        self.image_label = ImageLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        # 创建一个自定义视频播放器
        self.video_widget = VideoWidget()
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)

        # 设置尺寸策略
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 默认显示图像标签
        self.main_layout.addWidget(self.image_label)

        # 创建顶部工具栏
        self.create_top_toolbar()

        # 标记当前显示的是图像还是视频
        self.is_image = True

        # 当前打开的文件路径
        self.current_file = None

    def create_top_toolbar(self):
        # 创建顶部工具栏
        self.top_toolbar = QToolBar("顶部工具栏", self)
        self.addToolBar(Qt.TopToolBarArea, self.top_toolbar)
        self.top_toolbar.setMovable(False)

        # 添加打开文件按钮，使用标准的目录图标
        open_icon = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        self.open_action = QAction(open_icon, "打开文件", self)
        self.open_action.triggered.connect(self.open_file)
        self.top_toolbar.addAction(self.open_action)

        # 使用标准撤销图标
        undo_icon = self.style().standardIcon(QStyle.SP_ArrowBack)
        self.undo_action = QAction(undo_icon, "撤销", self)
        self.undo_action.triggered.connect(self.undo_action_triggered)
        self.top_toolbar.addAction(self.undo_action)

        # 使用标准保存图标
        save_icon = self.style().standardIcon(QStyle.SP_DialogSaveButton)
        self.save_action = QAction(save_icon, "保存", self)
        self.save_action.triggered.connect(self.save_action_triggered)
        self.top_toolbar.addAction(self.save_action)

        # 更换执行按钮的图标，使用标准的运行图标
        execute_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.execute_action = QAction(execute_icon, "执行", self)
        self.execute_action.triggered.connect(self.execute_action_triggered)
        self.top_toolbar.addAction(self.execute_action)

    def update_tool_selection(self, selected_action):
        for action in self.tool_actions:
            action.setChecked(action == selected_action)
        if selected_action == self.point_tool_action:
            # 启用点类型动作
            for action in self.point_type_action_group.actions():
                action.setEnabled(True)
        else:
            # 禁用点类型动作
            for action in self.point_type_action_group.actions():
                action.setEnabled(False)
                action.setChecked(False)
            self.image_label.point_type = None

    def select_rectangle_tool(self):
        self.image_label.current_tool = 'rectangle'
        self.update_tool_selection(self.rect_tool_action)

    def select_point_tool(self):
        self.image_label.current_tool = 'point'
        self.update_tool_selection(self.point_tool_action)

    def point_type_selected(self, action):
        if action == self.target_point_action:
            self.image_label.point_type = 'target'
        elif action == self.non_target_point_action:
            self.image_label.point_type = 'non-target'

    def undo_action_triggered(self):
        self.image_label.undo_last_action()

    def save_action_triggered(self):
        self.image_label.save_image()

    def execute_action_triggered(self):
        # 确保有打开的文件
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先打开一个文件！")
            return

        # 将点的坐标转换为实际图像坐标
        point_coords = []
        point_labels = []
        label_size = self.image_label.size()
        pixmap_size = self.image_label.pixmap().size()
        x_ratio = pixmap_size.width() / label_size.width()
        y_ratio = pixmap_size.height() / label_size.height()

        for point, point_type in self.image_label.points:
            x = int(point.x() * x_ratio)
            y = int(point.y() * y_ratio)
            point_coords.append([x, y])
            if point_type == 'target':
                point_labels.append(1)
            else:
                point_labels.append(0)

        # 构建配置文件内容，使用标准字典
        content = {
            'task_type': 'video_segment' if not self.is_image else 'image_segment',
            'model': {
                'checkpoint': 'autolabel/checkpoints/sam2_hiera_large.pt',
                'model_cfg': 'sam2_hiera_l.yaml'
            },
            'source': self.get_relative_source_path(self.current_file),
            'prompt': {
                'point_coords': point_coords,
                'point_labels': point_labels
                # 如果需要添加 box，可以在这里添加
                # 'box': [425, 600, 700, 875]
            }
        }

        # 获取当前脚本所在的目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(base_dir, 'autolabel', 'config')

        # 如果目录不存在，则创建
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        # 文件路径
        file_path = os.path.join(config_dir, 'image_segment_gen.yaml')

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    content,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False
                )
            # QMessageBox.information(self, "成功", f"文件已生成：{file_path}")

            # 生成配置文件后，执行命令
            command = f'autolabel -c={file_path}'
            self.command_thread = CommandThread(command)
            self.command_thread.finished.connect(self.on_command_finished)
            self.command_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法生成文件：{e}")

    def on_command_finished(self, success, output):
        if success:
            QMessageBox.information(self, "成功", "命令执行成功！\n" + output)
        else:
            QMessageBox.critical(self, "错误", "命令执行失败！\n" + output)

    def get_relative_source_path(self, file_path):
        # 假设 autolabel/images/ 目录在 base_dir 下
        base_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            relative_path = os.path.relpath(file_path, base_dir)
            return relative_path.replace("\\", "/")  # 兼容Windows路径
        except ValueError:
            # 如果无法计算相对路径，返回绝对路径
            return file_path.replace("\\", "/")

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "Image/Video Files (*.png *.jpg *.bmp *.mp4 *.avi *.mov)"
        )
        if file_name:
            if file_name.lower().endswith(('.png', '.jpg', '.bmp')):
                self.open_image(file_name)
            elif file_name.lower().endswith(('.mp4', '.avi', '.mov')):
                self.open_video(file_name)
            else:
                QMessageBox.warning(self, "警告", "不支持的文件格式！")
        else:
            QMessageBox.warning(self, "警告", "未选择任何文件！")

    def open_image(self, file_name):
        pixmap = QPixmap(file_name)
        if pixmap.isNull():
            # 处理无法加载的图像
            self.image_label.setText("无法加载图像")
        else:
            self.image_label.setPixmap(pixmap)
            # 重置绘制状态
            self.image_label.rectangles = []
            self.image_label.points = []
            self.image_label.actions = []  # 清空操作栈
            self.image_label.update()
        self.is_image = True
        self.media_player.stop()
        if self.video_widget.isVisible():
            self.main_layout.removeWidget(self.video_widget)
            self.video_widget.hide()
        if not self.image_label.isVisible():
            self.main_layout.addWidget(self.image_label)
            self.image_label.show()
        self.current_file = file_name  # 记录当前文件路径

    def open_video(self, file_name):
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_name)))
        self.media_player.play()
        self.is_image = False
        self.image_label.hide()
        if self.image_label in self.main_layout.children():
            self.main_layout.removeWidget(self.image_label)
        if not self.video_widget.isVisible():
            self.main_layout.addWidget(self.video_widget)
            self.video_widget.show()

        # 禁用绘图工具
        for action in self.tool_actions:
            action.setChecked(False)
        self.image_label.current_tool = None
        # 禁用点类型动作
        for action in self.point_type_action_group.actions():
            action.setEnabled(False)
            action.setChecked(False)
        self.image_label.point_type = None
        self.current_file = file_name  # 记录当前文件路径

    def closeEvent(self, event):
        # 确保在关闭应用程序时，正确释放媒体播放器资源
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
