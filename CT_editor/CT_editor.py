import os
import sys
import pydicom
from pydicom.uid import generate_uid
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QSlider, QLabel, QLineEdit, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class DICOMEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DICOM CT & RTSS Viewer/Editor")
        self.ct_slices = []       # List of CT slices: (InstanceNumber, dataset, filepath)
        self.rtss_list = []       # List of RTSTRUCTs: (dataset, filepath)
        self.current_rtss = None

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Toolbar buttons
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._make_button("Open Folder", self.load_folder))
        btn_layout.addWidget(self._make_button("Regenerate UIDs", self.regenerate_uids))
        btn_layout.addWidget(self._make_button("Save Series", self.save_series))
        layout.addLayout(btn_layout)

        # Patient info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Patient Name:"))
        self.name_edit = QLineEdit()
        info_layout.addWidget(self.name_edit)
        info_layout.addWidget(QLabel("Patient ID:"))
        self.id_edit = QLineEdit()
        info_layout.addWidget(self.id_edit)
        layout.addLayout(info_layout)

        # RTSTRUCT selector
        struct_layout = QHBoxLayout()
        struct_layout.addWidget(QLabel("Structure Set:"))
        self.rtss_combo = QComboBox()
        self.rtss_combo.currentIndexChanged.connect(self._on_rtss_change)
        struct_layout.addWidget(self.rtss_combo)
        layout.addLayout(struct_layout)

        # Display canvas
        self.figure = Figure(figsize=(6,6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Slice slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Slice:"))
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setMinimum(0)
        self.slice_slider.valueChanged.connect(self._on_slice_change)
        slider_layout.addWidget(self.slice_slider)
        layout.addLayout(slider_layout)

    def _make_button(self, text, slot):
        btn = QPushButton(text)
        btn.clicked.connect(slot)
        return btn

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select DICOM Directory")
        if not folder:
            return
        self.ct_slices.clear()
        self.rtss_list.clear()
        self.rtss_combo.clear()
        self.current_rtss = None

        # Read DICOM files
        for root, _, files in os.walk(folder):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    ds = pydicom.dcmread(fp)
                except Exception:
                    continue
                mod = getattr(ds, 'Modality', '')
                if mod == 'CT':
                    inst = getattr(ds, 'InstanceNumber', 0)
                    self.ct_slices.append((inst, ds, fp))
                elif mod == 'RTSTRUCT':
                    label = getattr(ds, 'StructureSetLabel', os.path.basename(fp))
                    self.rtss_list.append((ds, fp))
                    self.rtss_combo.addItem(label)

        if not self.ct_slices:
            QMessageBox.warning(self, "Error", "Nenhum CT encontrado na pasta selecionada.")
            return

        # Sort CT slices and init slider
        self.ct_slices.sort(key=lambda x: x[0])
        self.slice_slider.setMaximum(len(self.ct_slices) - 1)
        self.slice_slider.setValue(0)

        # Pre-fill patient info
        first_ds = self.ct_slices[0][1]
        self.name_edit.setText(str(first_ds.PatientName))
        self.id_edit.setText(str(first_ds.PatientID))

        # Default RTSTRUCT
        if self.rtss_list:
            self.current_rtss = self.rtss_list[0]
        self._redraw()

    def _on_rtss_change(self, idx):
        self.current_rtss = self.rtss_list[idx] if 0 <= idx < len(self.rtss_list) else None
        self._redraw()

    def _on_slice_change(self, _: int):
        self._redraw()

    def _redraw(self):
        if not self.ct_slices:
            return
        idx = self.slice_slider.value()
        _, ct_ds, _ = self.ct_slices[idx]
        img = ct_ds.pixel_array

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.imshow(img, cmap='gray', origin='upper', interpolation='none')

        # Overlay structure contours
        if self.current_rtss:
            rtss_ds, _ = self.current_rtss
            spacing = ct_ds.PixelSpacing
            origin = ct_ds.ImagePositionPatient
            z_plane = origin[2]
            for roi in rtss_ds.ROIContourSequence:
                for contour in roi.ContourSequence:
                    pts = np.array(contour.ContourData).reshape(-1, 3)
                    mask = np.isclose(pts[:, 2], z_plane, atol=1e-3)
                    if np.any(mask):
                        pts2d = pts[mask][:, :2]
                        x_pix = (pts2d[:, 0] - origin[0]) / spacing[1]
                        y_pix = (pts2d[:, 1] - origin[1]) / spacing[0]
                        ax.plot(x_pix, y_pix, '-r')

        ax.set_xlim(0, img.shape[1])
        ax.set_ylim(img.shape[0], 0)
        ax.axis('off')
        self.canvas.draw()

    def regenerate_uids(self):
        # Generate new Study and Series UIDs
        new_study = generate_uid()
        new_series = generate_uid()

        # Map old CT SOPInstanceUID -> new and store first CT SOP Class
        ct_uid_map = {}
        first_ct_ds = self.ct_slices[0][1]
        ct_sop_class = first_ct_ds.file_meta.MediaStorageSOPClassUID
        frame_uid = first_ct_ds.FrameOfReferenceUID

        for inst, ds, _ in self.ct_slices:
            old_sop = ds.SOPInstanceUID
            new_sop = generate_uid()
            ct_uid_map[old_sop] = new_sop
            ds.StudyInstanceUID      = new_study
            ds.SeriesInstanceUID     = new_series
            ds.SOPInstanceUID        = new_sop
            ds.file_meta.MediaStorageSOPInstanceUID = new_sop
            ds.PatientName           = self.name_edit.text()
            ds.PatientID             = self.id_edit.text()

        # Update each RTSTRUCT
        for rtss_ds, path in self.rtss_list:
            rtss_ds.PatientName      = self.name_edit.text()
            rtss_ds.PatientID        = self.id_edit.text()
            rtss_ds.StudyInstanceUID = new_study
            rtss_ds.SeriesInstanceUID= generate_uid()
            rtss_ds.SOPInstanceUID   = generate_uid()
            rtss_ds.file_meta.MediaStorageSOPInstanceUID = rtss_ds.SOPInstanceUID

            # References
            for ref in rtss_ds.ReferencedFrameOfReferenceSequence:
                ref.FrameOfReferenceUID = frame_uid
                for rs in ref.RTReferencedStudySequence:
                    # Use CT Image Storage class for study reference
                    rs.ReferencedSOPClassUID    = ct_sop_class
                    rs.ReferencedSOPInstanceUID = new_study
                    for series in rs.RTReferencedSeriesSequence:
                        series.SeriesInstanceUID = new_series
                        for item in series.ContourImageSequence:
                            item.ReferencedSOPClassUID   = ct_sop_class
                            old_ref = item.ReferencedSOPInstanceUID
                            item.ReferencedSOPInstanceUID = ct_uid_map.get(old_ref, old_ref)

        QMessageBox.information(self, "UIDs", "UIDs e referências atualizados com sucesso.")

    def save_series(self):
        out_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not out_dir:
            return
        for _, ds, path in self.ct_slices:
            ds.save_as(os.path.join(out_dir, os.path.basename(path)))
        for rtss_ds, path in self.rtss_list:
            rtss_ds.save_as(os.path.join(out_dir, os.path.basename(path)))
        QMessageBox.information(self, "Salvo", f"Arquivos salvos em: {out_dir}")


def main():
    app = QApplication(sys.argv)
    window = DICOMEditor()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
