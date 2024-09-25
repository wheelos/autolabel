import sys
import os
import yaml
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QAction, QVBoxLayout,
    QHBoxLayout, QWidget, QSizePolicy, QToolBar, QMessageBox, QStyle, QActionGroup
)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPen, QColor, QImage
from PyQt5.QtCore import Qt, QUrl, QPoint, QRect, QThread, pyqtSignal, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

import numpy as np
import torch
from PIL import Image

# 导入您的模型和相关模块
from autolabel.source.source_factory import SourceFactory
from autolabel.model.model_factory import ModelFactory
from autolabel.prompt.prompt import Prompt
from autolabel.task.image_segment_task import ImageSegmentTask
from autolabel.task.image_detection_task import ImageDetectionTask
from autolabel.task.video_segment_tracking_task import VideoSegmentTrackingTask

from sam2.sam2_image_predictor import SAM2ImagePredictor

# 后台线程，用于模型预测
class PredictThread(QThread):
    result_ready = pyqtSignal(np.ndarray)

    def __init__(self, image_predictor, point_coords=None, point_labels=None, box=None):
        super().__init__()
        self.image_predictor = image_predictor
        self.point_coords = point_coords
        self.point_labels = point_labels
        self.box = box

    def run(self):
        try:
            # 进行模型预测
            with torch.no_grad():
                masks, scores, logits = self.image_predictor.predict(
                    point_coords=self.point_coords,
                    point_labels=self.point_labels,
                    box=self.box,
                    multimask_output=False
                )
                if masks is not None and len(masks) > 0:
                    mask = masks[0]
                    # 将 mask 转换为 uint8 格式
                    mask = (mask * 255).astype(np.uint8)
                    # 发射信号，将结果传递回主线程
                    self.result_ready.emit(mask)
                else:
                    self.result_ready.emit(None)
        except Exception as e:
            print(f"预测时发生错误：{e}")
            self.result_ready.emit(None)
class ImageLabel(QLabel):
    update_mask_signal = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setScaledContents(False)

        self.coord_label = QLabel(self)
        self.coord_label.setStyleSheet(
            "color: red; background-color: rgba(255, 255, 255, 128);"
        )
        self.coord_label.setFont(QFont("Arial", 12))
        self.coord_label.hide()
        self.coord_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.coord_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.rectangles = []
        self.points = []
        self.current_tool = None
        self.point_type = None

        self.actions = []
        self.predictor = None
        self.mask = None
        self.combined_mask = None
        self.is_previewing = True  # 控制是否实时预览
        self.clicked_points = []

        self.debounce_timer = QTimer()
        self.debounce_timer.setInterval(500)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.perform_prediction)

        self.update_mask_signal.connect(self.on_update_mask)

    def get_pixmap_rect(self):
        pixmap = self.pixmap()
        if not pixmap:
            return QRect()

        label_width = self.width()
        label_height = self.height()
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        if pixmap_width <= 0 or pixmap_height <= 0:
            return QRect()

        ratio = min(label_width / pixmap_width, label_height / pixmap_height)
        new_width = pixmap_width * ratio
        new_height = pixmap_height * ratio

        x_offset = (label_width - new_width) / 2
        y_offset = (label_height - new_height) / 2

        return QRect(int(x_offset), int(y_offset), int(new_width), int(new_height))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_tool == 'point' and self.point_type:
            # 选择点，停止实时预览并生成分割结果
            self.is_previewing = False

            x, y = self.current_mouse_pos
            self.clicked_points.append((x, y))

            # 更新模型预测结果
            self.run_model_with_clicked_points()

        elif self.current_tool == 'rectangle' and event.button() == Qt.LeftButton:
            # 选择矩形，准备绘制
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()

        super().mousePressEvent(event)

    def run_model_with_clicked_points(self):
        if self.predictor is None or not self.clicked_points:
            return

        point_coords = np.array(self.clicked_points, dtype=np.float32)
        point_labels = np.ones(len(self.clicked_points), dtype=np.int32)

        self.predict_thread = PredictThread(self.predictor, point_coords=point_coords, point_labels=point_labels)
        self.predict_thread.result_ready.connect(self.update_combined_mask)
        self.predict_thread.start()

    def update_combined_mask(self, mask):
        if mask is None:
            QMessageBox.critical(self, "错误", "分割过程中出现错误！")
            return

        # 将新的分割结果与之前的结果叠加，确保分割结果不会丢失
        if self.combined_mask is None:
            self.combined_mask = mask
        else:
            self.combined_mask = np.maximum(self.combined_mask, mask)

        # 停止预览并更新显示
        self.is_previewing = False
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self.drawing and self.current_tool == 'rectangle':
            self.end_point = event.pos()
            self.update()

        if self.pixmap():
            pixmap_rect = self.get_pixmap_rect()

            if pixmap_rect.contains(pos):
                x = (pos.x() - pixmap_rect.x()) * self.pixmap().width() / pixmap_rect.width()
                y = (pos.y() - pixmap_rect.y()) * self.pixmap().height() / pixmap_rect.height()
                x = int(x)
                y = int(y)

                if 0 <= x < self.pixmap().width() and 0 <= y < self.pixmap().height():
                    self.coord_label.setText(f"坐标: ({x}, {y})")
                    label_x = pos.x()
                    label_y = pos.y()
                    if label_x + self.coord_label.width() > self.width():
                        label_x = self.width() - self.coord_label.width()
                    if label_y + self.coord_label.height() > self.height():
                        label_y = self.height() - self.coord_label.height()
                    self.coord_label.move(label_x, label_y)
                    self.coord_label.adjustSize()
                    self.coord_label.show()
                else:
                    self.coord_label.hide()

                self.current_mouse_pos = (x, y)
                # 只有在预览状态下才允许实时分割
                if self.is_previewing:
                    self.debounce_timer.start()
            else:
                self.coord_label.hide()
        super().mouseMoveEvent(event)

    def perform_prediction(self):
        if self.predictor is None or not self.is_previewing:
            return

        point_coords = self.current_mouse_pos

        self.predict_thread = PredictThread(self.predictor, point_coords=np.array([point_coords], dtype=np.float32), point_labels=np.array([1], dtype=np.int32))
        self.predict_thread.result_ready.connect(self.on_update_mask)
        self.predict_thread.start()

    def on_update_mask(self, mask):
        if mask is not None:
            self.mask = mask
            self.update()
        else:
            QMessageBox.critical(self, "错误", "分割过程中出现错误！")

    def mouseReleaseEvent(self, event):
        if self.drawing and self.current_tool == 'rectangle':
            self.end_point = event.pos()
            pixmap_rect = self.get_pixmap_rect()
            start_x = (self.start_point.x() - pixmap_rect.x()) * self.pixmap().width() / pixmap_rect.width()
            start_y = (self.start_point.y() - pixmap_rect.y()) * self.pixmap().height() / pixmap_rect.height()
            end_x = (self.end_point.x() - pixmap_rect.x()) * self.pixmap().width() / pixmap_rect.width()
            end_y = (self.end_point.y() - pixmap_rect.y()) * self.pixmap().height() / pixmap_rect.height()
            start_point = QPoint(int(start_x), int(start_y))
            end_point = QPoint(int(end_x), int(end_y))
            self.rectangles.append((start_point, end_point))
            self.actions.append(('rectangle', (start_point, end_point)))
            self.drawing = False
            self.update()

            box = [start_x, start_y, end_x, end_y]
            # 执行分割后，停止实时预览
            self.run_model_with_box(box)

        super().mouseReleaseEvent(event)

    def run_model_with_box(self, box):
        if self.predictor is None or not box:
            return

        # 停止预览，执行分割
        self.is_previewing = False

        self.predict_thread = PredictThread(self.predictor, box=box)
        self.predict_thread.result_ready.connect(self.update_combined_mask)
        self.predict_thread.start()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pixmap_rect = self.get_pixmap_rect()

        if self.combined_mask is not None:
            combined_mask_image = QImage(self.combined_mask.data, self.combined_mask.shape[1], self.combined_mask.shape[0], self.combined_mask.shape[1], QImage.Format_Grayscale8)
            combined_mask_image = combined_mask_image.scaled(pixmap_rect.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            painter.setOpacity(0.5)
            painter.drawImage(pixmap_rect.topLeft(), combined_mask_image)
            painter.setOpacity(1.0)

        if self.is_previewing and self.mask is not None:
            mask_image = QImage(self.mask.data, self.mask.shape[1], self.mask.shape[0], self.mask.shape[1], QImage.Format_Grayscale8)
            mask_image = mask_image.scaled(pixmap_rect.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            painter.setOpacity(0.5)
            painter.drawImage(pixmap_rect.topLeft(), mask_image)
            painter.setOpacity(1.0)

        pen = QPen(Qt.green, 2, Qt.SolidLine)
        painter.setPen(pen)
        for rect in self.rectangles:
            start_x = pixmap_rect.x() + rect[0].x() * pixmap_rect.width() / self.pixmap().width()
            start_y = pixmap_rect.y() + rect[0].y() * pixmap_rect.height() / self.pixmap().height()
            end_x = pixmap_rect.x() + rect[1].x() * pixmap_rect.width() / self.pixmap().width()
            end_y = pixmap_rect.y() + rect[1].y() * pixmap_rect.height() / self.pixmap().height()
            start_point = QPoint(int(start_x), int(start_y))
            end_point = QPoint(int(end_x), int(end_y))
            rect_normalized = QRect(start_point, end_point).normalized()
            painter.drawRect(rect_normalized)

        if self.drawing and self.current_tool == 'rectangle':
            pen = QPen(Qt.red, 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(QRect(self.start_point, self.end_point).normalized())

        for point, point_type in self.points:
            pen = QPen(Qt.green if point_type == 'target' else Qt.red, 5)
            painter.setPen(pen)
            x = pixmap_rect.x() + point.x() * pixmap_rect.width() / self.pixmap().width()
            y = pixmap_rect.y() + point.y() * pixmap_rect.height() / self.pixmap().height()
            painter.drawPoint(int(x), int(y))

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
        self.mask = None
        self.combined_mask = None
        self.clicked_points = []
        self.is_previewing = True  # 清除所有操作后重新启用预览
        self.update()

    def save_image(self):
        if self.pixmap():
            pixmap = QPixmap(self.pixmap())
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            if self.combined_mask is not None:
                mask_image = QImage(self.combined_mask.data, self.combined_mask.shape[1], self.combined_mask.shape[0], self.combined_mask.shape[1], QImage.Format_Grayscale8)
                painter.setOpacity(0.5)
                painter.drawImage(0, 0, mask_image)
                painter.setOpacity(1.0)

            painter.end()

            file_path, _ = QFileDialog.getSaveFileName(self, "保存图像", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;BMP Files (*.bmp)")
            if file_path:
                pixmap.save(file_path)
        else:
            QMessageBox.warning(self, "警告", "没有可保存的图像！")




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("上位机程序")
        self.resize(1200, 800)

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
        self.rect_tool_action = QAction("矩形工具", self)
        self.rect_tool_action.setCheckable(True)
        self.rect_tool_action.triggered.connect(self.select_rectangle_tool)
        self.tool_bar.addAction(self.rect_tool_action)

        self.point_tool_action = QAction("点工具", self)
        self.point_tool_action.setCheckable(True)
        self.point_tool_action.triggered.connect(self.select_point_tool)
        self.tool_bar.addAction(self.point_tool_action)

        # 工具组，用于互斥选择
        self.tool_actions = [self.rect_tool_action, self.point_tool_action]

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
        self.tool_bar.addSeparator()
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

        # 使用标准执行图标
        execute_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.execute_action = QAction(execute_icon, "执行", self)
        self.execute_action.triggered.connect(self.execute_action_triggered)
        self.top_toolbar.addAction(self.execute_action)

        # 添加清除按钮
        clear_icon = self.style().standardIcon(QStyle.SP_DialogResetButton)
        self.clear_action = QAction(clear_icon, "清除", self)
        self.clear_action.triggered.connect(self.clear_action_triggered)
        self.top_toolbar.addAction(self.clear_action)

    def update_tool_selection(self, selected_action):
        for action in self.tool_actions:
            action.setChecked(action == selected_action)
        if selected_action == self.point_tool_action:
            for action in self.point_type_action_group.actions():
                action.setEnabled(True)
        else:
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

    def clear_action_triggered(self):
        self.image_label.clear_all()

    def execute_action_triggered(self):
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先打开一个文件！")
            return

        point_coords = []
        point_labels = []
        for point, point_type in self.image_label.points:
            x = point.x()
            y = point.y()
            point_coords.append([x, y])
            point_labels.append(1 if point_type == 'target' else 0)

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
            }
        }

        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(base_dir, 'autolabel', 'config')

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        file_path = os.path.join(config_dir, 'image_segment_gen.yaml')

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(content, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

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
        base_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            relative_path = os.path.relpath(file_path, base_dir)
            return relative_path.replace("\\", "/")
        except ValueError:
            return file_path.replace("\\", "/")

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "Image/Video Files (*.png *.jpg *.bmp *.mp4 *.avi *.mov)"
        )
        if file_name:
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
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
            self.image_label.setText("无法加载图像")
        else:
            self.image_label.setPixmap(pixmap)
            self.image_label.clear_all()
            self.image_label.update()

            image = Image.open(file_name)
            image = np.array(image.convert('RGB'))

            model_checkpoint = 'autolabel/checkpoints/sam2_hiera_large.pt'
            model_cfg = 'sam2_hiera_l.yaml'

            model = ModelFactory.create(model_checkpoint, model_cfg, 'image_segment')
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model.to(device)

            self.image_label.predictor = SAM2ImagePredictor(model)
            self.image_label.predictor.set_image(image)

        self.is_image = True
        self.media_player.stop()
        if self.video_widget.isVisible():
            self.main_layout.removeWidget(self.video_widget)
            self.video_widget.hide()
        if not self.image_label.isVisible():
            self.main_layout.addWidget(self.image_label)
            self.image_label.show()
        self.current_file = file_name

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

        for action in self.tool_actions:
            action.setChecked(False)
        self.image_label.current_tool = None

        for action in self.point_type_action_group.actions():
            action.setEnabled(False)
            action.setChecked(False)
        self.image_label.point_type = None
        self.current_file = file_name

    def closeEvent(self, event):
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())
        super().closeEvent(event)
class VideoWidget(QVideoWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.coord_label = QLabel(self)
        self.coord_label.setStyleSheet(
            "color: yellow; background-color: rgba(0, 0, 0, 128);"
        )
        self.coord_label.setFont(QFont("Arial", 12))
        self.coord_label.hide()
        self.coord_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # 设置尺寸策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.coord_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # 鼠标坐标
        self.current_mouse_pos = (0, 0)

        # 防抖定时器，避免频繁调用
        self.debounce_timer = QTimer()
        self.debounce_timer.setInterval(500)  # 每500ms最多执行一次
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.update_mouse_coords)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self.current_mouse_pos = (pos.x(), pos.y())

        # 显示鼠标坐标
        self.coord_label.setText(f"坐标: ({pos.x()}, {pos.y()})")
        # 防止坐标标签超出视频窗口边界
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

        # 启动防抖定时器
        self.debounce_timer.start()

        super().mouseMoveEvent(event)

    def update_mouse_coords(self):
        """可以在这里添加与鼠标坐标相关的功能，例如更新状态栏等。"""
        pass

    def leaveEvent(self, event):
        self.coord_label.hide()
        super().leaveEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())