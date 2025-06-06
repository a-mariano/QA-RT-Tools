import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QSizePolicy
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
import subprocess
from PyQt5.QtCore import QSize

class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radiotherapy Tools Launcher")
        self.setGeometry(100, 100, 400, 300)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Título
        title = QLabel("Selecione uma Ferramenta")
        font = QFont()
        font.setPointSize(16)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        icons_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
        
        # DicomRT Editor Button
        btn_dicom = QPushButton("DicomRT Editor")
        btn_dicom.setFixedWidth(400)  
        font_btn = QFont()
        font_btn.setPointSize(14)          # define o tamanho da fonte (por exemplo, 14 pt)
        btn_dicom.setFont(font_btn)
        icon_dicom = QIcon(os.path.join(icons_path, "dicomrt_icon.png"))
        btn_dicom.setIcon(icon_dicom)
        btn_dicom.setIconSize(QSize(96, 96))
        btn_dicom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn_dicom.setMinimumHeight(80)
        btn_dicom.clicked.connect(self.launch_dicom_editor)
        layout.addWidget(btn_dicom)
        
        # CT Generator Button
        btn_ct = QPushButton("Gerador de CT \n (PyCubo)")
        btn_ct.setFixedWidth(400)  
        btn_ct.setFont(font_btn)
        icon_ct = QIcon(os.path.join(icons_path, "pycubo_icon.png"))
        btn_ct.setIcon(icon_ct)
        btn_ct.setIconSize(QSize(96, 96))
        btn_ct.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn_ct.setMinimumHeight(80)
        btn_ct.clicked.connect(self.launch_ct_generator)
        layout.addWidget(btn_ct)
    
    def launch_dicom_editor(self):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dicomrt_editor", "main_window.py")
        subprocess.Popen([sys.executable, script])
    
    def launch_ct_generator(self):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pycubo_generator", "PyCuboQA.py")
        subprocess.Popen([sys.executable, script])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec_())
