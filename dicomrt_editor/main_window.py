import sys
import os
import subprocess
import copy
import numpy as np
import datetime
import pydicom
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QTreeWidgetItem, QLabel, QLineEdit, QMessageBox,
    QAction, QComboBox, QHeaderView, QSpacerItem, QSizePolicy,
    QInputDialog
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

import dicom_utils.reader as dr
import dicom_utils.export_excel as ex
import efs_converter.DCM2EFS as ec
#from utils.PyCuboQA import gerar_volume_com_cubo_mm, exportar_dicom
#from utils.ct_generator import update_rtplan_reference
#from utils.PyCuboQA import gerar_volume_com_cubo_mm, exportar_dicom, update_rtplan_reference

class DicomEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de Tags DICOM (RTPLAN) com Visualizador de MLC, Jaws e Export EFS")
        self.resize(1200, 1080)

        # ===== Menu principal =====
        menu_bar = self.menuBar()

        # --- Menu "Arquivo" com "Salvar Como..." e "Exportar EFS" ---
        file_menu = menu_bar.addMenu("Arquivo")
        action_save_as = QAction("Salvar Como...", self)
        action_save_as.triggered.connect(self.on_save_as)
        file_menu.addAction(action_save_as)
        action_export_efs = QAction("Exportar EFS", self)
        action_export_efs.triggered.connect(self.export_efs)
        file_menu.addAction(action_export_efs)

        # --- Menu "CT" para gerar CT e atualizar RTPLAN ---
        ct_menu = menu_bar.addMenu("CT")
#        action_generate_ct = QAction("Gerar Novo CT Phantom", self)
#        action_generate_ct.triggered.connect(self.menu_generate_ct)
#        ct_menu.addAction(action_generate_ct)
        action_update_rtplan = QAction("Atualizar RTPLAN com CT", self)
        action_update_rtplan.triggered.connect(self.menu_update_rtplan)
        ct_menu.addAction(action_update_rtplan)


        # --- Menu "Ajuda" direcionando ao repositório GitHub ---
        help_menu = menu_bar.addMenu("Ajuda")
        action_github = QAction("Repositório no GitHub", self)
        action_github.triggered.connect(self.open_github_repository)
        help_menu.addAction(action_github)

        # ===== Layout principal =====
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # --- Painel esquerdo (60%): botão "Abrir" + árvore de tags ---
        left_panel = QVBoxLayout()
        layout.addLayout(left_panel, 58)

        self.btn_open = QPushButton("Abrir RTPLAN DICOM")
        self.btn_open.clicked.connect(self.open_dicom)
        left_panel.addWidget(self.btn_open)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tag (Group,Elem)", "VR", "Name", "Value"])
        self.tree.setColumnWidth(0, 300)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.tree.itemClicked.connect(self.on_item_selected)
        left_panel.addWidget(self.tree)

        # --- Painel direito (40%): edição + seleção de modelo + parâmetros + Excel + visualizador + OBS ---
        right_panel = QVBoxLayout()
        layout.addLayout(right_panel, 40)

        # Campos de edição de DataElement
        self.lbl_tag = QLabel("Tag:")
        self.edit_tag = QLineEdit()
        self.edit_tag.setReadOnly(True)

        self.lbl_vr = QLabel("VR:")
        self.edit_vr = QLineEdit()
        self.edit_vr.setReadOnly(True)

        self.lbl_name = QLabel("Name:")
        self.edit_name = QLineEdit()
        self.edit_name.setReadOnly(True)

        self.lbl_value = QLabel("Valor atual:")
        self.edit_value = QLineEdit()
        self.edit_value.setReadOnly(True)

        self.btn_save_value = QPushButton("Salvar valor")
        self.btn_save_value.clicked.connect(self.save_value)
        self.btn_save_value.setEnabled(False)

        for w in [
            self.lbl_tag, self.edit_tag,
            self.lbl_vr, self.edit_vr,
            self.lbl_name, self.edit_name,
            self.lbl_value, self.edit_value,
            self.btn_save_value
        ]:
            right_panel.addWidget(w)

        # Seleção de modelo de MLC (Agility 5mm ou MLCi2 10mm)
        mlc_model_layout = QHBoxLayout()
        mlc_model_layout.addWidget(QLabel("Modelo MLC:"))
        self.mlc_model_combo = QComboBox()
        self.mlc_model_combo.addItem("Agility (5 mm)", 5)
        self.mlc_model_combo.addItem("MLCi2 (10 mm)", 10)
        self.mlc_model_combo.setCurrentIndex(0)
        self.mlc_model_combo.currentIndexChanged.connect(lambda _: self.update_mlc_view())
        mlc_model_layout.addWidget(self.mlc_model_combo)
        right_panel.addLayout(mlc_model_layout)

        # Parâmetros do control point (acima do visualizador)
        top_params_layout = QHBoxLayout()
        left_params_layout = QVBoxLayout()

        font_cp_small = QFont()
        font_cp_small.setPointSize(12)

        self.lbl_gantry = QLabel("Gantry: N/A")
        self.lbl_gantry.setFont(font_cp_small)
        self.lbl_collimator = QLabel("Collimator: N/A")
        self.lbl_collimator.setFont(font_cp_small)
        self.lbl_table = QLabel("Table: N/A")
        self.lbl_table.setFont(font_cp_small)
        self.lbl_mu = QLabel("MU: N/A")
        self.lbl_mu.setFont(font_cp_small)

        for lbl in [self.lbl_gantry, self.lbl_collimator, self.lbl_table, self.lbl_mu]:
            lbl.setAlignment(Qt.AlignLeft)
            left_params_layout.addWidget(lbl)

        top_params_layout.addLayout(left_params_layout)

        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        top_params_layout.addItem(spacer)

        self.lbl_fraction = QLabel("Fraction: N/A")
        font_fraction = QFont()
        font_fraction.setPointSize(14)
        self.lbl_fraction.setFont(font_fraction)
        self.lbl_fraction.setAlignment(Qt.AlignRight)
        top_params_layout.addWidget(self.lbl_fraction)

        right_panel.addLayout(top_params_layout)

        right_panel.addWidget(QLabel("— Visualizador de MLC e Jaws —", alignment=Qt.AlignCenter))

        # Controles de navegação entre beams e CPs
        mlc_nav_layout = QHBoxLayout()
        mlc_nav_layout.addWidget(QLabel("Feixe:"))
        self.beam_combo = QComboBox()
        self.beam_combo.currentIndexChanged.connect(self.on_beam_changed)
        mlc_nav_layout.addWidget(self.beam_combo)

        self.prev_cp_btn = QPushButton("Anterior CP")
        self.prev_cp_btn.clicked.connect(self.on_prev_cp)
        self.prev_cp_btn.setEnabled(False)
        mlc_nav_layout.addWidget(self.prev_cp_btn)

        self.next_cp_btn = QPushButton("Próximo CP")
        self.next_cp_btn.clicked.connect(self.on_next_cp)
        self.next_cp_btn.setEnabled(False)
        mlc_nav_layout.addWidget(self.next_cp_btn)

        self.cp_label = QLabel("CP: 0/0")
        self.cp_label.setFont(font_fraction)
        mlc_nav_layout.addWidget(self.cp_label)

        right_panel.addLayout(mlc_nav_layout)

        # Botões para exportar/importar Excel de Control Points
        btns_excel_layout = QHBoxLayout()
        self.btn_export_excel = QPushButton("Exportar CPs para Excel")
        self.btn_export_excel.clicked.connect(self.export_control_points_to_excel)
        self.btn_import_excel = QPushButton("Importar CPs do Excel")
        self.btn_import_excel.clicked.connect(self.import_control_points_from_excel)
        btns_excel_layout.addWidget(self.btn_export_excel)
        btns_excel_layout.addWidget(self.btn_import_excel)
        right_panel.addLayout(btns_excel_layout)

        # Canvas do matplotlib para desenhar MLC e Jaws
        self.fig = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        right_panel.addWidget(self.canvas)

        self.lbl_obs = QLabel("OBS: ")
        self.lbl_obs.setFont(font_fraction)
        self.lbl_obs.setAlignment(Qt.AlignLeft)
        right_panel.addWidget(self.lbl_obs)

        # ===== Estados internos =====
        self.dataset = None
        self.dicom_path = None
        self.current_item = None
        self.current_element = None
        self.current_beam_idx = 0
        self.current_cp_idx = 0
        self._excel_path = None

    # -------------------------------------------------------------------------
    #    CALLBACK DO MENU DE AJUDA
    # -------------------------------------------------------------------------
    def open_github_repository(self):
        QDesktopServices.openUrl(QUrl("https://github.com/a-mariano/QA-RTplan-Editor"))

    # -------------------------------------------------------------------------
    #    MENU: GERAR NOVO CT PHANTOM
    # -------------------------------------------------------------------------
    def menu_generate_ct(self):
        # Encontra a pasta raiz do projeto (onde fica este main_window.py)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Monta o caminho relativo até utils/PyCuboQA.py
        script = os.path.join(base_dir, "utils", "PyCuboQA.py")

        python_exec = sys.executable
        try:
            subprocess.Popen([python_exec, script])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível iniciar PyCuboQA:\n{e}")


     # -------------------------------------------------------------------------
    #    MENU: ATUALIZAR RTPLAN PARA USAR CT COMO REFERÊNCIA (em memória)
    # -------------------------------------------------------------------------
    def menu_update_rtplan(self):
        if self.dicom_path is None:
            QMessageBox.warning(self, "Atenção", "Abra primeiro um RTPLAN DICOM.")
            return

        # 1) Abre a pasta do CT
        ct_folder = QFileDialog.getExistingDirectory(self,
            "Selecione a pasta com CT DICOMs")
        if not ct_folder:
            return

        # 2) Carrega o primeiro slice de CT
        try:
            ct_files = sorted([
                os.path.join(ct_folder, f)
                for f in os.listdir(ct_folder)
                if f.lower().endswith(".dcm")
            ])
            if not ct_files:
                raise FileNotFoundError("Pasta de CT não contém DICOMs.")
            first_ct = pydicom.dcmread(ct_files[0])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao abrir CT:\n{e}")
            return

        # 3) Extrai informações do CT
        new_patient_name = getattr(first_ct, "PatientName", None)
        new_patient_id   = getattr(first_ct, "PatientID", None)
        new_study_uid    = getattr(first_ct, "StudyInstanceUID", None)
        new_series_uid   = getattr(first_ct, "SeriesInstanceUID", None)
        new_for_uid      = getattr(first_ct, "FrameOfReferenceUID", None)

        if not (new_study_uid and new_series_uid and new_for_uid):
            QMessageBox.critical(self, "Erro",
                "O CT não possui StudyInstanceUID, SeriesInstanceUID ou FrameOfReferenceUID.")
            return

        # 4) Atualiza o RTPLAN carregado (self.dataset) em memória
        try:
            rt = self.dataset  # Alias para abreviar

            # a) PatientName / PatientID
            if new_patient_name is not None:
                rt.PatientName = new_patient_name
            if new_patient_id is not None:
                rt.PatientID = new_patient_id

            # b) StudyInstanceUID / SeriesInstanceUID
            rt.StudyInstanceUID  = new_study_uid
            rt.SeriesInstanceUID = new_series_uid

            # c) FrameOfReferenceUID
            rt.FrameOfReferenceUID = new_for_uid

            # d) SOPInstanceUID (gerar novo, opcional)
            rt.SOPInstanceUID = pydicom.uid.generate_uid()

            # e) REFERENCED STUDY & SERIES (muda para nova série de CT)
            if hasattr(rt, "ReferencedStudySequence"):
                for study_item in rt.ReferencedStudySequence:
                    study_item.ReferencedStudyInstanceUID = new_study_uid
                    if hasattr(study_item, "ReferencedSeriesSequence"):
                        for series_item in study_item.ReferencedSeriesSequence:
                            series_item.SeriesInstanceUID = new_series_uid

            # f) REFERENCED FRAME OF REFERENCE SEQUENCE
            #    (se existir, atualiza para o mesmo FoR do CT)
            if hasattr(rt, "ReferencedFrameOfReferenceSequence"):
                for ref_for_item in rt.ReferencedFrameOfReferenceSequence:
                    ref_for_item.FrameOfReferenceUID = new_for_uid
                    # dentro dele pode haver RTReferencedStudySequence → etc.
                    if hasattr(ref_for_item, "RTReferencedStudySequence"):
                        for rts_item in ref_for_item.RTReferencedStudySequence:
                            rts_item.RTReferencedStudyInstanceUID = new_study_uid
                            if hasattr(rts_item, "RTReferencedSeriesSequence"):
                                for rts_series_item in rts_item.RTReferencedSeriesSequence:
                                    rts_series_item.SeriesInstanceUID = new_series_uid

        except Exception as e:
            QMessageBox.critical(self, "Erro",
                f"Falha ao atualizar RTPLAN em memória:\n{e}")
            return

        # 5) Recarrega a árvore e a visualização para refletir as mudanças
        self.tree.clear()
        dr.populate_tree(self.dataset, self.tree.invisibleRootItem())
        self.init_beam_cp_view()

        QMessageBox.information(self, "RTPLAN Atualizado",
            "RTPLAN agora referencia o novo CT (nome, ID, UIDs e FrameOfReference atualizados).")


    # -------------------------------------------------------------------------
    #    ABRIR E POPULAR DICOM
    # -------------------------------------------------------------------------
    def open_dicom(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecione o arquivo RTPLAN DICOM", "", "DICOM Files (*.dcm *.DCM)"
        )
        if not path:
            return

        try:
            self.dataset = dr.open_dicom_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao ler DICOM:\n{e}")
            return

        self.dicom_path = path
        self.tree.clear()
        dr.populate_tree(self.dataset, self.tree.invisibleRootItem())
        self.setWindowTitle(f"Editor DICOM — {path}")
        self.init_beam_cp_view()

    # -------------------------------------------------------------------------
    #    SELEÇÃO E EDIÇÃO DE DATA_ELEMENT
    # -------------------------------------------------------------------------
    def on_item_selected(self, item: QTreeWidgetItem, column: int):
        self.current_item = item
        elem = getattr(item, "data_element", None)
        if elem is None or elem.VR == "SQ":
            self.current_element = None
            self.edit_tag.setText("")
            self.edit_vr.setText("")
            self.edit_name.setText(item.text(2))
            self.edit_value.setText("")
            self.edit_value.setReadOnly(True)
            self.btn_save_value.setEnabled(False)
            return

        self.current_element = elem
        self.edit_tag.setText(f"({elem.tag.group:04X},{elem.tag.element:04X})")
        self.edit_vr.setText(elem.VR)
        self.edit_name.setText(elem.name)

        val = elem.value
        if isinstance(val, bytes) and len(val) > 64:
            val_str = "<bytes...>"
        else:
            val_str = str(val)
        self.edit_value.setText(val_str)
        self.edit_value.setReadOnly(False)
        self.btn_save_value.setEnabled(True)

    def save_value(self):
        if self.current_element is None:
            return
        new_str = self.edit_value.text().strip()

        try:
            dr.save_data_element(self.current_element, new_str)
        except Exception as e:
            QMessageBox.warning(self, "Erro na conversão", f"Não foi possível converter:\n{e}")
            return

        self.current_item.setText(3, new_str)
        QMessageBox.information(
            self, "OK",
            "Valor atualizado em memória.\nUse “Salvar Como...” para gravar em disco."
        )

    # -------------------------------------------------------------------------
    #    SALVAR DICOM COMO...
    # -------------------------------------------------------------------------
    def on_save_as(self):
        if self.dataset is None:
            QMessageBox.warning(self, "Atenção", "Nenhum arquivo aberto para salvar.")
            return

        path_out, _ = QFileDialog.getSaveFileName(
            self, "Salvar DICOM modificado como", "", "DICOM (*.dcm);;Todos os arquivos (*)"
        )
        if not path_out:
            return

        try:
            dr.save_dicom_file(self.dataset, path_out)
            QMessageBox.information(self, "Arquivo salvo", f"Arquivo gravado em:\n{path_out}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar:\n{e}")

    # -------------------------------------------------------------------------
    #    INICIALIZAÇÃO E NAVEGAÇÃO DE BEAMS/CONTROL POINTS
    # -------------------------------------------------------------------------
    def init_beam_cp_view(self):
        self.beam_combo.clear()
        self.current_beam_idx = 0
        self.current_cp_idx = 0

        beams = dr.get_beams(self.dataset)
        if not beams:
            QMessageBox.warning(
                self,
                "Nenhum Feixe Encontrado",
                "Não foi possível localizar feixes neste arquivo DICOM.\n"
                "Provavelmente não é um RTPLAN válido ou está corrompido."
            )
            self.beam_combo.setEnabled(False)
            self.prev_cp_btn.setEnabled(False)
            self.next_cp_btn.setEnabled(False)
            self.cp_label.setText("CP: 0/0")
            self.ax.clear()
            self.ax.set_title("Sem dados de feixes/MLC")
            self.canvas.draw()
            return

        for idx, beam in enumerate(beams):
            beam_num = getattr(beam, "BeamNumber", idx + 1)
            beam_name = getattr(beam, "BeamName", "")
            label = f"{beam_num}  {beam_name}"
            self.beam_combo.addItem(label, idx)

        self.beam_combo.setEnabled(True)
        self.beam_combo.setCurrentIndex(0)
        self.prev_cp_btn.setEnabled(True)
        self.next_cp_btn.setEnabled(True)

        self.update_mlc_view()

    def on_beam_changed(self, index):
        self.current_beam_idx = index
        self.current_cp_idx = 0
        self.update_mlc_view()

    def on_prev_cp(self):
        if self.dataset is None:
            return
        beams = dr.get_beams(self.dataset)
        cps = dr.get_control_points(beams[self.current_beam_idx])
        if self.current_cp_idx > 0:
            self.current_cp_idx -= 1
            self.update_mlc_view()

    def on_next_cp(self):
        if self.dataset is None:
            return
        beams = dr.get_beams(self.dataset)
        cps = dr.get_control_points(beams[self.current_beam_idx])
        if self.current_cp_idx < len(cps) - 1:
            self.current_cp_idx += 1
            self.update_mlc_view()

    # -------------------------------------------------------------------------
    #    ATUALIZAÇÃO DO VISUALIZADOR DE MLC E JAWS
    # -------------------------------------------------------------------------
    def update_mlc_view(self):
        self.ax.clear()

        beams = dr.get_beams(self.dataset)
        if not beams:
            self.ax.set_title("Sem RTBeamSequence/BeamSequence")
            self.canvas.draw()
            return

        beam = beams[self.current_beam_idx]
        cps = dr.get_control_points(beam)
        total_cps = len(cps)
        self.cp_label.setText(f"CP: {self.current_cp_idx + 1}/{total_cps}")

        cp = cps[self.current_cp_idx]
        bl_seq = dr.get_bl_seq(cp)
        if not bl_seq:
            self.ax.set_title("Sem BeamLimitingDevicePositionSequence")
            self.canvas.draw()
            self.lbl_obs.setText("OBS: Sem BeamLimitingDevicePositionSequence")
            return

        gantry = getattr(cp, "GantryAngle", "N/A")
        collim = getattr(cp, "BeamLimitingDeviceAngle", "N/A")
        table = getattr(cp, "PatientSupportAngle", "N/A")
        fraction = getattr(cp, "CumulativeMetersetWeight", "N/A")
        mu = getattr(beam, "BeamMeterset", "N/A")

        self.lbl_gantry.setText(f"Gantry: {gantry}°")
        self.lbl_collimator.setText(f"Collimator: {collim}°")
        self.lbl_table.setText(f"Table: {table}°")
        self.lbl_mu.setText(f"MU: {mu}")
        self.lbl_fraction.setText(f"Fraction: {fraction}")

        # Encontra item MLC
        mlc_item = dr.find_mlc_item(bl_seq)
        if mlc_item is None:
            self.ax.set_title("Nenhum MLC encontrado neste CP")
            self.canvas.draw()
            self.lbl_obs.setText("OBS: Nenhum MLC encontrado neste CP")
            return

        leaf_positions = dr.get_mlc_positions(mlc_item)
        N2 = len(leaf_positions)
        N = N2 // 2
        left_positions = leaf_positions[:N]
        right_positions = leaf_positions[N:]

        # Jaws X e Y
        x_jaws = dr.find_jaw_positions(bl_seq, axis='X')
        y_jaws = dr.find_jaw_positions(bl_seq, axis='Y')

        obs_msgs = []
        if not x_jaws:
            obs_msgs.append("Sem colimadores X")
        if not y_jaws:
            obs_msgs.append("Sem colimadores Y")
        self.lbl_obs.setText("OBS: " + "; ".join(obs_msgs) if obs_msgs else "OBS: Colimadores detectados")

        xmin, xmax = -200.0, 200.0

        thickness = float(self.mlc_model_combo.currentData())
        total_height = N * thickness
        half_height = total_height / 2.0

        for i in range(N):
            left_val = left_positions[i]
            right_val = right_positions[i]
            y_bottom = (i * thickness) - half_height
            if left_val > xmin:
                width_left = left_val - xmin
                rect_left = Rectangle((xmin, y_bottom), width_left, thickness, facecolor="lightgray", edgecolor="black")
                self.ax.add_patch(rect_left)
            if xmax > right_val:
                width_right = xmax - right_val
                rect_right = Rectangle((right_val, y_bottom), width_right, thickness, facecolor="lightgray", edgecolor="black")
                self.ax.add_patch(rect_right)

        if x_jaws:
            x_left_jaw, x_right_jaw = x_jaws
            x_left_jaw = max(min(x_left_jaw, 200.0), -200.0)
            x_right_jaw = max(min(x_right_jaw, 200.0), -200.0)
            self.ax.axvline(x=x_left_jaw, color="red", linestyle="--", linewidth=1.5, label="X Jaw Esquerda")
            self.ax.axvline(x=x_right_jaw, color="red", linestyle="--", linewidth=1.5, label="X Jaw Direita")

        if y_jaws:
            y_min_jaw, y_max_jaw = y_jaws
            self.ax.axhline(y=y_min_jaw, color="blue", linestyle="--", linewidth=1.5, label=f"Y Jaw {y_min_jaw}mm")
            self.ax.axhline(y=y_max_jaw, color="blue", linestyle="--", linewidth=1.5, label=f"Y Jaw {y_max_jaw}mm")
            new_y_top = max(half_height, y_max_jaw)
            new_y_bottom = min(-half_height, y_min_jaw)
            self.ax.set_ylim(new_y_top, new_y_bottom)
        else:
            self.ax.set_ylim(half_height, -half_height)

        self.ax.set_xlim(xmin, xmax)
        self.ax.set_xlabel("Posição X (mm)")
        self.ax.set_ylabel("Posição Y (mm)")

        beam_label = getattr(beam, "BeamNumber", self.current_beam_idx + 1)
        self.ax.set_title(f"Beam {beam_label} · CP {self.current_cp_idx + 1}/{total_cps}")

        if x_jaws or y_jaws:
            self.ax.legend(loc="upper right", fontsize="small")

        self.ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)
        self.fig.tight_layout()
        self.canvas.draw()

    # -------------------------------------------------------------------------
    #    EXPORTAÇÃO / IMPORTAÇÃO DE EXCEL
    # -------------------------------------------------------------------------
    def export_control_points_to_excel(self):
        ex.export_to_excel(self.dataset)

    def import_control_points_from_excel(self):
        ex.import_from_excel(self.dataset, self.current_beam_idx)

    # -------------------------------------------------------------------------
    #    EXPORTAÇÃO PARA EFS
    # -------------------------------------------------------------------------
    def export_efs(self):
        if self.dataset is None or self.dicom_path is None:
            QMessageBox.warning(self, "Atenção", "Abra um RTPLAN primeiro antes de exportar EFS.")
            return

        output_folder = QFileDialog.getExistingDirectory(self, "Selecione a pasta de destino para arquivos EFS")
        if not output_folder:
            return

        try:
            ec.convert_dcm2efs(self.dicom_path, output_folder)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao gerar EFS", f"Falha ao criar arquivos EFS:\n{e}")
            return

        QMessageBox.information(self, "Exportação Concluída", f"Arquivos .efs gerados em:\n{output_folder}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = DicomEditor()
    editor.show()
    sys.exit(app.exec_())
    