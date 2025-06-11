import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QSizePolicy, QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize
import subprocess

class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radiotherapy Tools Launcher")
        self.setGeometry(100, 100, 600, 400)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Título principal
        title = QLabel("Radiotherapy Tools Launcher")
        font_title = QFont()
        font_title.setPointSize(18)
        font_title.setBold(True)
        title.setFont(font_title)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        icons_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
        font_btn = QFont()
        font_btn.setPointSize(14)

        # Grupo: Manipulação de DICOM
        gb_dicom = QGroupBox("Manipulação de DICOM")
        layout_dicom = QHBoxLayout()
        gb_dicom.setLayout(layout_dicom)

        # Botões do grupo DICOM
        btn_dicom = QPushButton("DicomRT Editor")
        btn_dicom.setFont(font_btn)
        btn_dicom.setIcon(QIcon(os.path.join(icons_path, "dicomrt_icon.png")))
        btn_dicom.setIconSize(QSize(96, 96))
        btn_dicom.setMinimumHeight(100)
        btn_dicom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_dicom.clicked.connect(self.launch_dicom_editor)

        btn_ct = QPushButton("Gerador de CT\n(PyCubo)")
        btn_ct.setFont(font_btn)
        btn_ct.setIcon(QIcon(os.path.join(icons_path, "pycubo_icon.png")))
        btn_ct.setIconSize(QSize(96, 96))
        btn_ct.setMinimumHeight(100)
        btn_ct.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_ct.clicked.connect(self.launch_ct_generator)

        btn_cteditor = QPushButton("CT Editor")
        btn_cteditor.setFont(font_btn)
        btn_cteditor.setIcon(QIcon(os.path.join(icons_path, "cteditor_icon.png")))
        btn_cteditor.setIconSize(QSize(96, 96))
        btn_cteditor.setMinimumHeight(100)
        btn_cteditor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_cteditor.clicked.connect(self.launch_ct_editor)

        # Adiciona espaciadores e botões horizontalmente
        layout_dicom.addWidget(btn_dicom)
        layout_dicom.addWidget(btn_ct)
        layout_dicom.addWidget(btn_cteditor)

        main_layout.addWidget(gb_dicom)

        # Grupo: Comparação de dose (vazio por enquanto)
        gb_cmp = QGroupBox("Comparação de dose")
        layout_cmp = QHBoxLayout()
        gb_cmp.setLayout(layout_cmp)
        placeholder = QLabel("Nenhuma ferramenta disponível")
        placeholder.setAlignment(Qt.AlignCenter)
        layout_cmp.addWidget(placeholder)

        main_layout.addWidget(gb_cmp)
        main_layout.addStretch()

    def launch_dicom_editor(self):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dicomrt_editor", "main_window.py")
        subprocess.Popen([sys.executable, script])

    def launch_ct_generator(self):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pycubo_generator", "PyCuboQA.py")
        subprocess.Popen([sys.executable, script])

    def launch_ct_editor(self):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CT_editor", "CT_editor.py")
        subprocess.Popen([sys.executable, script])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec_())
