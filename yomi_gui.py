import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFileDialog, QSizePolicy, QScrollArea, 
                             QFrame, QStackedWidget, QGridLayout, QMessageBox, QCheckBox,
                             QLineEdit, QRadioButton, QButtonGroup, QGroupBox, QComboBox, 
                             QProgressBar)
from PyQt5.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image, ImageOps
import os

def pixelate_image_logic(image_path, output_dir, resolutions, color_filter=None, output_format='png'):
    processed_images = []
    
    if not resolutions:
        resolutions = [32, 64, 128, 256] 
        
    try:
        img = Image.open(image_path).convert('RGBA')
        
        if color_filter == 'grayscale':
            img = img.convert('L').convert('RGB')
        elif color_filter == 'sepia':
            img = ImageOps.colorize(img.convert('L'), '#704214', '#ffffff')

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        original_width, original_height = img.size
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        for res in resolutions:
            small_img = img.resize((res, res), resample=Image.Resampling.NEAREST)
            pixelated_img = small_img.resize((original_width, original_height), resample=Image.Resampling.NEAREST)
            
            output_file_name = f"{base_name}_pixelated_{res}x{res}"
            if color_filter:
                output_file_name += f"_{color_filter}"
            
            output_file = os.path.join(output_dir, f"{output_file_name}.{output_format}")
            
            save_options = {}
            if output_format == 'gif':
                pixelated_img = pixelated_img.convert('P', palette=Image.Palette.ADAPTIVE)
            
            pixelated_img.save(output_file, **save_options)
            processed_images.append(output_file)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    
    return processed_images

class PixelationThread(QThread):
    finished = pyqtSignal(list)
    progress_updated = pyqtSignal(int)
    
    def __init__(self, image_paths, output_dir, resolutions, color_filter, output_format):
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.resolutions = resolutions
        self.color_filter = color_filter
        self.output_format = output_format

    def run(self):
        all_processed_files = []
        total_images = len(self.image_paths)
        for i, path in enumerate(self.image_paths):
            processed_files = pixelate_image_logic(path, self.output_dir, self.resolutions, self.color_filter, self.output_format)
            all_processed_files.extend(processed_files)
            progress = int(((i + 1) / total_images) * 100)
            self.progress_updated.emit(progress)
            
        self.finished.emit(all_processed_files)

class WelcomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.title_label = QLabel("Yomi")
        self.title_label.setObjectName("welcomeTitleLabel")
        
        self.slogan_label = QLabel("Transform any image into pixel-perfect art, fast and offline.")
        self.slogan_label.setObjectName("welcomeSloganLabel")
        
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")

        layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.slogan_label, alignment=Qt.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

class MainPage(QWidget):
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.pixelation_thread = None
        self.setAcceptDrops(True)
        self.initUI()
    
    def initUI(self):
        main_layout = QHBoxLayout(self)

        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignTop)

        self.title_label = QLabel("Yomi")
        self.title_label.setObjectName("titleLabel")
        left_panel.addWidget(self.title_label, alignment=Qt.AlignCenter)

        self.select_button = QPushButton('Select Images')
        self.select_button.setObjectName("selectButton")
        self.select_button.clicked.connect(self.openFileNamesDialog)
        left_panel.addWidget(self.select_button)
        
        color_groupbox = QGroupBox("Color Options")
        color_groupbox.setObjectName("optionsGroup")
        color_layout = QVBoxLayout()
        
        self.color_group = QButtonGroup(self)
        
        self.original_radio = QRadioButton("Original")
        self.original_radio.setChecked(True)
        self.color_group.addButton(self.original_radio)
        self.original_radio.setObjectName("optionRadioButton")
        color_layout.addWidget(self.original_radio)
        
        self.grayscale_radio = QRadioButton("Grayscale")
        self.color_group.addButton(self.grayscale_radio)
        self.grayscale_radio.setObjectName("optionRadioButton")
        color_layout.addWidget(self.grayscale_radio)
        
        self.sepia_radio = QRadioButton("Sepia")
        self.color_group.addButton(self.sepia_radio)
        self.sepia_radio.setObjectName("optionRadioButton")
        color_layout.addWidget(self.sepia_radio)
        
        color_groupbox.setLayout(color_layout)
        left_panel.addWidget(color_groupbox)

        res_groupbox = QGroupBox("Pixel Resolutions")
        res_groupbox.setObjectName("optionsGroup")
        res_layout = QGridLayout()

        self.resolution_checkboxes = []
        resolutions = [32, 64, 128, 256, 512, 1024]
        col = 0
        row = 0
        for res in resolutions:
            cb = QCheckBox(f"{res}x{res}")
            cb.setObjectName("optionCheckBox")
            cb.setChecked(True)
            self.resolution_checkboxes.append(cb)
            res_layout.addWidget(cb, row, col)
            col += 1
            if col == 3:
                col = 0
                row += 1
        
        custom_res_label = QLabel("Custom Resolution:")
        res_layout.addWidget(custom_res_label, row + 1, 0, 1, 1)
        
        self.custom_res_input = QLineEdit()
        self.custom_res_input.setPlaceholderText("e.g. 75")
        self.custom_res_input.setObjectName("customResInput")
        res_layout.addWidget(self.custom_res_input, row + 1, 1, 1, 2)
        
        res_groupbox.setLayout(res_layout)
        left_panel.addWidget(res_groupbox)

        save_groupbox = QGroupBox("File Settings")
        save_groupbox.setObjectName("optionsGroup")
        save_layout = QVBoxLayout()
        
        output_dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel("Output Folder:")
        self.output_dir_line = QLineEdit("pixelated_images")
        self.output_dir_line.setPlaceholderText("pixelated_images")
        self.output_dir_line.setObjectName("customResInput")
        self.output_dir_button = QPushButton("Browse...")
        self.output_dir_button.clicked.connect(self.select_output_directory)
        output_dir_layout.addWidget(self.output_dir_label)
        output_dir_layout.addWidget(self.output_dir_line)
        output_dir_layout.addWidget(self.output_dir_button)
        save_layout.addLayout(output_dir_layout)
        
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpeg", "gif"])
        self.format_combo.setObjectName("formatComboBox")
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        save_layout.addLayout(format_layout)
        
        save_groupbox.setLayout(save_layout)
        left_panel.addWidget(save_groupbox)

        self.original_image_label = QLabel()
        self.original_image_label.setObjectName("originalImageLabel")
        self.original_image_label.setText("Drag and Drop Images Here or Select")
        self.original_image_label.setAlignment(Qt.AlignCenter)
        self.original_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.original_image_label.setScaledContents(True)
        left_panel.addWidget(self.original_image_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("progressBar")
        left_panel.addWidget(self.progress_bar)
        
        self.pixelate_button = QPushButton('Pixelate')
        self.pixelate_button.setObjectName("pixelateButton")
        self.pixelate_button.clicked.connect(self.start_pixelation)
        self.pixelate_button.setEnabled(False) 
        left_panel.addWidget(self.pixelate_button)
        
        main_layout.addLayout(left_panel, 1)

        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignTop)
        
        results_title_label = QLabel("Results")
        results_title_label.setObjectName("resultsTitleLabel")
        right_panel.addWidget(results_title_label, alignment=Qt.AlignCenter)

        self.results_scroll_area = QScrollArea()
        self.results_scroll_area.setWidgetResizable(True)
        self.results_scroll_area.setObjectName("resultsScrollArea")

        self.results_widget = QWidget()
        self.results_widget.setObjectName("resultsWidget")
        self.results_layout = QGridLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.results_scroll_area.setWidget(self.results_widget)
        right_panel.addWidget(self.results_scroll_area)

        main_layout.addLayout(right_panel, 2)

    def select_output_directory(self):
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self, "Select Output Folder", "", options=options)
        if directory:
            self.output_dir_line.setText(directory)

    def openFileNamesDialog(self):
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp)", options=options)
        if file_names:
            self.set_images(file_names)

    def set_images(self, file_paths):
        self.image_paths = file_paths
        if self.image_paths:
            self.update_image_preview()
            self.pixelate_button.setEnabled(True)
            self.clear_results()

    def update_image_preview(self):
        if not self.image_paths:
            self.original_image_label.setText("Drag and Drop Images Here or Select")
            self.original_image_label.setPixmap(QPixmap())
            self.pixelate_button.setEnabled(False)
            return

        if len(self.image_paths) > 1:
            preview_scroll_area = QScrollArea()
            preview_scroll_area.setWidgetResizable(True)
            preview_widget = QWidget()
            preview_layout = QHBoxLayout(preview_widget)
            preview_layout.setAlignment(Qt.AlignLeft)
            
            for path in self.image_paths:
                if os.path.exists(path):
                    pixmap = QPixmap(path)
                    label = QLabel()
                    label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    preview_layout.addWidget(label)
            
            preview_scroll_area.setWidget(preview_widget)
            
            old_label = self.original_image_label
            self.layout().itemAt(0).replaceWidget(old_label, preview_scroll_area)
            old_label.hide()
            self.original_image_label = preview_scroll_area
        else: 
            self.original_image_label.setText("")
            if isinstance(self.original_image_label, QScrollArea):
                new_label = QLabel()
                new_label.setObjectName("originalImageLabel")
                new_label.setAlignment(Qt.AlignCenter)
                new_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                new_label.setScaledContents(True)
                self.layout().itemAt(0).replaceWidget(self.original_image_label, new_label)
                self.original_image_label.hide()
                self.original_image_label = new_label
                
            pixmap = QPixmap(self.image_paths[0])
            self.original_image_label.setPixmap(pixmap)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.original_image_label.setProperty('acceptDrops', True)
            self.original_image_label.style().unpolish(self.original_image_label)
            self.original_image_label.style().polish(self.original_image_label)

    def dragLeaveEvent(self, event):
        self.original_image_label.setProperty('acceptDrops', False)
        self.original_image_label.style().unpolish(self.original_image_label)
        self.original_image_label.style().polish(self.original_image_label)

    def dropEvent(self, event: QDropEvent):
        self.original_image_label.setProperty('acceptDrops', False)
        self.original_image_label.style().unpolish(self.original_image_label)
        self.original_image_label.style().polish(self.original_image_label)
        urls = event.mimeData().urls()
        file_paths = []
        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    file_paths.append(file_path)
        if file_paths:
            self.set_images(file_paths)

    def start_pixelation(self):
        if self.image_paths:
            self.pixelate_button.setEnabled(False)
            self.pixelate_button.setText("Processing...")
            self.progress_bar.setVisible(True)
            self.clear_results()
            
            output_folder = self.output_dir_line.text()
            selected_resolutions = []
            for cb in self.resolution_checkboxes:
                if cb.isChecked():
                    res = int(cb.text().split('x')[0])
                    selected_resolutions.append(res)
            
            custom_res_text = self.custom_res_input.text().strip()
            if custom_res_text:
                try:
                    custom_res = int(custom_res_text)
                    if custom_res > 0:
                        selected_resolutions.append(custom_res)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for custom resolution.")
                    self.pixelate_button.setEnabled(True)
                    self.pixelate_button.setText("Pixelate")
                    return
            
            if not selected_resolutions:
                QMessageBox.warning(self, "No Resolutions Selected", "Please select at least one resolution or enter a custom one.")
                self.pixelate_button.setEnabled(True)
                self.pixelate_button.setText("Pixelate")
                return

            color_filter = None
            if self.grayscale_radio.isChecked():
                color_filter = 'grayscale'
            elif self.sepia_radio.isChecked():
                color_filter = 'sepia'
                
            output_format = self.format_combo.currentText().lower()

            self.pixelation_thread = PixelationThread(self.image_paths, output_folder, selected_resolutions, color_filter, output_format)
            self.pixelation_thread.progress_updated.connect(self.progress_bar.setValue)
            self.pixelation_thread.finished.connect(self.display_results)
            self.pixelation_thread.start()

    def display_results(self, processed_files):
        self.pixelate_button.setEnabled(True)
        self.pixelate_button.setText("Pixelate")
        self.progress_bar.setVisible(False)
        
        row, col = 0, 0
        for file_path in processed_files:
            file_name = os.path.basename(file_path)
            
            result_frame = QFrame()
            result_frame.setObjectName("resultFrame")
            result_row = QVBoxLayout(result_frame)
            result_row.setContentsMargins(0, 0, 0, 0)
            
            res_label = QLabel(os.path.basename(file_name))
            res_label.setAlignment(Qt.AlignCenter)
            res_label.setObjectName("resultResolutionLabel")
            
            image_label = QLabel()
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            
            result_row.addWidget(res_label)
            result_row.addWidget(image_label)

            self.results_layout.addWidget(result_frame, row, col)
            
            col += 1
            if col == 3:
                col = 0
                row += 1

    def clear_results(self):
        while self.results_layout.count() > 0:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
    
    def clear_layout(self, layout):
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

class YomiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle('Yomi - Pixel Art Image Converter')
        self.setGeometry(100, 100, 1200, 800)
        
        self.stacked_widget = QStackedWidget(self)
        self.initPages()
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stacked_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.apply_styles()
        self.create_title_bar()
        
        self.welcome_page.start_button.clicked.connect(self.show_main_page)

    def initPages(self):
        self.welcome_page = WelcomePage()
        self.main_page = MainPage()
        
        self.stacked_widget.addWidget(self.welcome_page)
        self.stacked_widget.addWidget(self.main_page)
        
        self.stacked_widget.setCurrentWidget(self.welcome_page)
        
    def show_main_page(self):
        self.stacked_widget.setCurrentWidget(self.main_page)

    def create_title_bar(self):
        self.title_bar = QWidget(self)
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(40)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        
        title_label = QLabel("Yomi")
        title_label.setObjectName("titleBarLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        
        self.minimize_button = QPushButton("—")
        self.minimize_button.setObjectName("minimizeButton")
        self.minimize_button.clicked.connect(self.showMinimized)
        
        self.maximize_button = QPushButton("☐")
        self.maximize_button.setObjectName("maximizeButton")
        self.maximize_button.clicked.connect(self.toggle_maximize)
        
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.close)

        title_layout.addWidget(self.minimize_button)
        title_layout.addWidget(self.maximize_button)
        title_layout.addWidget(self.close_button)

        self.layout().insertWidget(0, self.title_bar)

        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < self.title_bar.height():
            self.start_pos = event.globalPos()
            self.drag_start_pos = self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPos() - self.start_pos
            self.move(self.drag_start_pos + delta)
    
    def mouseReleaseEvent(self, event):
        self.start_pos = None

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def apply_styles(self):
        style = """
            QWidget {
                background-color: #262e3d;
                color: #e6e8eb;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #titleBar {
                background-color: #1e2531;
            }
            #titleBarLabel {
                font-size: 16px;
                color: #55b8e9;
                font-weight: bold;
            }
            #minimizeButton, #maximizeButton, #closeButton {
                border: none;
                background-color: transparent;
                color: #e6e8eb;
                font-size: 18px;
                width: 30px;
                height: 30px;
                border-radius: 5px;
            }
            #minimizeButton:hover, #maximizeButton:hover {
                background-color: #4a5468;
            }
            #closeButton:hover {
                background-color: #e74c3c;
                color: #ffffff;
            }
            #welcomeTitleLabel {
                font-size: 80px;
                font-weight: bold;
                color: #55b8e9;
                text-align: center;
                margin-bottom: 20px;
            }
            #welcomeSloganLabel {
                font-size: 18px;
                font-style: italic;
                color: #8b96a7;
            }
            #startButton, #selectButton, #pixelateButton {
                background-color: #55b8e9;
                color: #ffffff;
                border: none;
                padding: 18px 40px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
            }
            #startButton:hover, #selectButton:hover, #pixelateButton:hover {
                background-color: #439bc9;
            }
            #startButton:pressed, #selectButton:pressed, #pixelateButton:pressed {
                background-color: #3884b2;
            }
            #pixelateButton:disabled {
                background-color: #4a5468;
                color: #8b96a7;
            }
            #titleLabel {
                font-size: 56px;
                font-weight: bold;
                color: #55b8e9;
                margin-bottom: 25px;
            }
            #originalImageLabel {
                border: 2px dashed #4a5468;
                background-color: #3b4556;
                font-size: 15px;
                color: #8b96a7;
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 20px;
            }
            #originalImageLabel[acceptDrops="true"] {
                border: 2px solid #55b8e9;
                background-color: #3e4a5d;
            }
            #resultsTitleLabel {
                font-size: 28px;
                font-weight: bold;
                color: #e6e8eb;
                padding-bottom: 15px;
            }
            #resultsScrollArea {
                border: none;
                background-color: #3b4556;
                border-radius: 12px;
            }
            #resultsWidget {
                background-color: #3b4556;
            }
            .resultFrame {
                background-color: #2c3e50;
                border: 1px solid #4a5468;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            .resultResolutionLabel {
                font-weight: bold;
                color: #e6e8eb;
                font-size: 14px;
            }
            QScrollBar:vertical {
                border: none;
                background: #3b4556;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #5a7a8f;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QGroupBox {
                border: 2px solid #4a5468;
                border-radius: 10px;
                margin-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: #262e3d;
                color: #55b8e9;
            }
            #optionRadioButton, #optionCheckBox {
                spacing: 10px;
                font-weight: normal;
            }
            #customResInput {
                background-color: #3b4556;
                color: #e6e8eb;
                border: 1px solid #4a5468;
                border-radius: 8px;
                padding: 8px;
            }
            #progressBar {
                text-align: center;
                border: 2px solid #4a5468;
                border-radius: 8px;
            }
            #progressBar::chunk {
                background-color: #55b8e9;
                border-radius: 6px;
            }
            #formatComboBox {
                background-color: #3b4556;
                color: #e6e8eb;
                border: 1px solid #4a5468;
                border-radius: 8px;
                padding: 5px;
            }
        """
        self.setStyleSheet(style)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = YomiApp()
    ex.show()
    sys.exit(app.exec_())