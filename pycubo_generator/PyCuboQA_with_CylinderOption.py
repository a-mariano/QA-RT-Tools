import numpy as np
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk, font
import pydicom
from pydicom.dataset import FileDataset, Dataset
import datetime
import os

# Imports para plotagem
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Função: cria RTSTRUCT com estrutura BODY
def criar_rtstruct_body(volume, spacing, patient_name, patient_id, patient_position, output_dir,
                        study_uid, series_uid, frame_uid):
    dt = datetime.datetime.now()
    sop_instance_uid = pydicom.uid.generate_uid()
    file_meta = pydicom.Dataset()
    file_meta.MediaStorageSOPClassUID = pydicom.uid.RTStructureSetStorage
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

    ds = FileDataset("RTSTRUCT.dcm", {}, file_meta=file_meta, preamble=b"\x00" * 128)
    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.FrameOfReferenceUID = frame_uid
    ds.Modality = "RTSTRUCT"
    ds.SeriesNumber = 999
    ds.StructureSetLabel = "BODY_ONLY"

    depth, height, width = volume.shape
    pixel_spacing = spacing[1]
    slice_thickness = spacing[0]

    ds.ReferencedFrameOfReferenceSequence = [Dataset()]
    ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID = frame_uid
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence = [Dataset()]
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].ReferencedSOPClassUID = "1.2.840.10008.5.1.4.1.2.2.1"
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].ReferencedSOPInstanceUID = study_uid
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence = [Dataset()]
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID = series_uid

    contour_image_seq = []
    for z in range(depth):
        item = Dataset()
        item.ReferencedSOPClassUID = pydicom.uid.CTImageStorage
        item.ReferencedSOPInstanceUID = pydicom.uid.generate_uid()
        contour_image_seq.append(item)
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence = contour_image_seq

    roi_number = 1
    ds.StructureSetROISequence = [Dataset()]
    ds.StructureSetROISequence[0].ROINumber = roi_number
    ds.StructureSetROISequence[0].ReferencedFrameOfReferenceUID = frame_uid
    ds.StructureSetROISequence[0].ROIName = "BODY"
    ds.StructureSetROISequence[0].ROIGenerationAlgorithm = "MANUAL"

    mid_z = depth // 2
    start_x = 50
    end_x = width - 50
    start_y = 50
    end_y = height - 50
    z_coord = mid_z * slice_thickness

    contour_dataset = Dataset()
    contour_dataset.ContourGeometricType = "CLOSED_PLANAR"
    contour_dataset.NumberOfContourPoints = 4
    contour_dataset.ContourData = [
        start_x * pixel_spacing, start_y * pixel_spacing, z_coord,
        end_x * pixel_spacing, start_y * pixel_spacing, z_coord,
        end_x * pixel_spacing, end_y * pixel_spacing, z_coord,
        start_x * pixel_spacing, end_y * pixel_spacing, z_coord,
    ]
    contour_dataset.ContourImageSequence = [Dataset()]
    contour_dataset.ContourImageSequence[0].ReferencedSOPClassUID = pydicom.uid.CTImageStorage
    contour_dataset.ContourImageSequence[0].ReferencedSOPInstanceUID = contour_image_seq[mid_z].ReferencedSOPInstanceUID

    ds.ROIContourSequence = [Dataset()]
    ds.ROIContourSequence[0].ReferencedROINumber = roi_number
    ds.ROIContourSequence[0].ContourSequence = [contour_dataset]

    ds.RTROIObservationsSequence = [Dataset()]
    ds.RTROIObservationsSequence[0].ObservationNumber = 1
    ds.RTROIObservationsSequence[0].ReferencedROINumber = roi_number
    ds.RTROIObservationsSequence[0].ROIObservationLabel = "BODY"
    ds.RTROIObservationsSequence[0].RTROIInterpretedType = "EXTERNAL"
    ds.RTROIObservationsSequence[0].ROIInterpreter = ""

    rt_path = os.path.join(output_dir, "RTSTRUCT_BODY.dcm")
    ds.save_as(rt_path, write_like_original=False)
    return rt_path

# Função: gera volume com cilindro de água dentro de ar
def gerar_volume_com_cilindro_mm(diameter_mm, length_mm, pixel_size, slice_thickness):
    lado_xy_mm = diameter_mm + 100.0
    altura_z_mm = length_mm + 50.0

    nz = int(round(altura_z_mm / slice_thickness))
    ny = int(round(lado_xy_mm / pixel_size))
    nx = int(round(lado_xy_mm / pixel_size))

    volume = np.ones((nz, ny, nx), dtype=np.int16) * -1000

    radius_vox = (diameter_mm / 2.0) / pixel_size
    height_vox = int(round(length_mm / slice_thickness))

    start_z = (nz - height_vox) // 2
    z_end = start_z + height_vox

    cy = ny // 2
    cx = nx // 2

    for z in range(start_z, z_end):
        yy, xx = np.ogrid[:ny, :nx]
        mask = ((yy - cy)**2 + (xx - cx)**2) <= radius_vox**2
        volume[z][mask] = 0

    spacing = [float(slice_thickness), float(pixel_size), float(pixel_size)]
    return volume, spacing

# Função: gera volume cúbico de água dentro de ar
def gerar_volume_com_cubo_mm(mm_x, mm_y, mm_z, pixel_size, slice_thickness):
    lado_xy_mm   = max(mm_x, mm_y) + 100.0
    altura_z_mm  = mm_z + 50.0

    nz = int(round(altura_z_mm / slice_thickness))
    ny = int(round(lado_xy_mm / pixel_size))
    nx = int(round(lado_xy_mm / pixel_size))

    volume = np.ones((nz, ny, nx), dtype=np.int16) * -1000

    cz = int(round(mm_z / slice_thickness))
    cy = int(round(mm_y / pixel_size))
    cx = int(round(mm_x / pixel_size))

    start_z = (nz - cz) // 2
    start_y = (ny - cy) // 2
    start_x = (nx - cx) // 2

    volume[start_z:start_z+cz, start_y:start_y+cy, start_x:start_x+cx] = 0

    spacing = [float(slice_thickness), float(pixel_size), float(pixel_size)]
    return volume, spacing

# Função: exporta DICOM e RTSTRUCT
def exportar_dicom(volume, voxel_spacing, patient_name, patient_id, patient_position, output_dir):
    dt = datetime.datetime.now()
    study_uid = pydicom.uid.generate_uid()
    series_uid = pydicom.uid.generate_uid()
    frame_uid  = pydicom.uid.generate_uid()

    depth, height, width = volume.shape
    os.makedirs(output_dir, exist_ok=True)

    for z in range(depth):
        file_meta = pydicom.Dataset()
        file_meta.MediaStorageSOPClassUID = pydicom.uid.CTImageStorage
        inst_uid = pydicom.uid.generate_uid()
        file_meta.MediaStorageSOPInstanceUID = inst_uid
        file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

        ds = FileDataset('', {}, file_meta=file_meta, preamble=b"\x00" * 128)

        ds.PatientName     = patient_name
        ds.PatientID       = patient_id
        ds.PatientPosition = patient_position
        ds.PatientBirthDate = ''
        ds.PatientSex       = ''

        ds.StudyInstanceUID    = study_uid
        ds.SeriesInstanceUID   = series_uid
        ds.FrameOfReferenceUID = frame_uid
        ds.SOPInstanceUID      = inst_uid
        ds.SOPClassUID         = file_meta.MediaStorageSOPClassUID

        ds.StudyDate = dt.strftime('%Y%m%d')
        ds.StudyTime = dt.strftime('%H%M%S')
        ds.StudyID   = '1'
        ds.StudyDescription = '3D Phantom - PyCubo'

        ds.SeriesNumber      = 1
        ds.SeriesDate        = dt.strftime('%Y%m%d')
        ds.SeriesTime        = dt.strftime('%H%M%S')
        ds.SeriesDescription = '3D Phantom'

        ds.Modality             = 'CT'
        ds.Manufacturer         = 'PyCubo'
        ds.ManufacturerModelName = ''
        ds.DeviceSerialNumber   = ''
        ds.SoftwareVersions     = ''

        ds.ImageType = ['ORIGINAL', 'PRIMARY', 'AXIAL']
        ds.ImagePositionPatient    = [0.0, 0.0, float(z) * voxel_spacing[0]]
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        ds.Rows    = height
        ds.Columns = width
        ds.InstanceNumber = z + 1

        ds.SliceLocation        = float(z) * voxel_spacing[0]
        ds.SpacingBetweenSlices = float(voxel_spacing[0])

        ds.PixelSpacing           = [float(voxel_spacing[1]), float(voxel_spacing[2])]
        ds.SliceThickness         = float(voxel_spacing[0])
        ds.ReconstructionDiameter = float(width * voxel_spacing[2])

        ds.SamplesPerPixel         = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelRepresentation      = 1
        ds.HighBit                  = 15
        ds.BitsStored               = 16
        ds.BitsAllocated            = 16

        ds.RescaleIntercept = 0
        ds.RescaleSlope     = 1

        ds.WindowCenter = 0
        ds.WindowWidth  = 4000
        ds.KVP = 120
        ds.PixelAspectRatio = '1\\1'
        ds.ContentDate      = dt.strftime('%Y%m%d')
        ds.ContentTime      = dt.strftime('%H%M%S')

        ds.PixelData = volume[z, :, :].tobytes()
        filename = os.path.join(output_dir, f'slice_{z:03}.dcm')
        ds.save_as(filename, write_like_original=False)

    criar_rtstruct_body(volume, voxel_spacing, patient_name, patient_id, patient_position,
                        output_dir, study_uid, series_uid, frame_uid)
    return output_dir

def salvar_dicom():
    global current_volume, current_spacing
    if current_volume is None or current_spacing is None:
        messagebox.showwarning("Aviso", "Gere o volume primeiro antes de exportar.")
        return

    patient_name     = entry_name.get().strip()
    patient_id       = entry_id.get().strip()
    patient_position = combobox_position.get().strip()
    if not patient_name or not patient_id or not patient_position:
        messagebox.showwarning("Aviso", "Insira Patient Name, Patient ID e Patient Position.")
        return

    output_dir = filedialog.askdirectory(title="Selecione pasta de saída para DICOMs")
    if not output_dir:
        return

    try:
        exportar_dicom(
            current_volume,
            current_spacing,
            patient_name,
            patient_id,
            patient_position,
            output_dir
        )
        messagebox.showinfo("Sucesso", "DICOMs exportados com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao exportar DICOM ou RT Structure: {e}")

def atualizar_imagem():
    global current_volume, current_spacing
    try:
        pixel_size = float(entry_ps.get())
        thickness  = float(entry_st.get())

        shape = shape_var.get()
        if shape == "Cubo":
            mm_x = float(entry_lx.get())
            mm_y = float(entry_ly.get())
            mm_z = float(entry_lz.get())
            volume, spacing = gerar_volume_com_cubo_mm(mm_x, mm_y, mm_z, pixel_size, thickness)
        else:
            diameter = float(entry_diam.get())
            length_c = float(entry_cl.get())
            volume, spacing = gerar_volume_com_cilindro_mm(diameter, length_c, pixel_size, thickness)

        current_volume  = volume
        current_spacing = spacing

        nz, ny, nx = volume.shape
        z_mid      = nz // 2
        y_mid      = ny // 2
        x_mid      = nx // 2

        slice_axial   = volume[z_mid, :, :]
        slice_coronal = volume[:, y_mid, :]
        slice_sagital = volume[:, :, x_mid]

        fig.clear()
        axs = fig.subplots(1, 3)

        axs[0].imshow(slice_axial, cmap='gray', vmin=-1000, vmax=500)
        axs[0].set_title(f'Axial (Z={z_mid})')
        axs[0].axis('off')
        axs[0].set_aspect('equal')

        axs[1].imshow(slice_coronal, cmap='gray', vmin=-1000, vmax=500)
        axs[1].set_title(f'Coronal')
        axs[1].axis('off')
        axs[1].set_aspect(thickness / pixel_size)

        axs[2].imshow(slice_sagital, cmap='gray', vmin=-1000, vmax=500)
        axs[2].set_title(f'Sagital')
        axs[2].axis('off')
        axs[2].set_aspect(thickness / pixel_size)

        fig.tight_layout()
        canvas.draw()

    except ValueError:
        messagebox.showwarning("Aviso", "Valores inválidos. Insira números positivos.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao atualizar imagem: {e}")

# Interface Tkinter
root = tk.Tk()
root.title("PyCubo QA - Gerador de Phantom 3D")
root.minsize(850, 550)

default_font = font.Font(family="TkDefaultFont", size=12)
style = ttk.Style()
style.configure('TButton', font=default_font, padding=6)

frame_principal = tk.LabelFrame(root, text="Parâmetros", font=default_font,
                                bd=2, relief="groove", padx=10, pady=10)
frame_principal.pack(fill="x", padx=15, pady=10)

# Seleção da forma
shape_var = tk.StringVar(value="Cubo")
tk.Label(frame_principal, text="Forma do Phantom:", font=default_font).grid(row=0, column=0, sticky="e", pady=5)
rb_cubo = tk.Radiobutton(frame_principal, text="Cubo", variable=shape_var, value="Cubo", font=default_font)
rb_cubo.grid(row=0, column=1, pady=5, sticky="w")
rb_cilindro = tk.Radiobutton(frame_principal, text="Cilindro", variable=shape_var, value="Cilindro", font=default_font)
rb_cilindro.grid(row=0, column=2, pady=5, sticky="w")

# Entradas para Cubo
tk.Label(frame_principal, text="Largura X (mm):", font=default_font).grid(row=1, column=0, sticky="e", padx=(0,5), pady=5)
entry_lx = tk.Entry(frame_principal, width=8, font=default_font)
entry_lx.insert(0, "300")
entry_lx.grid(row=1, column=1, padx=(0,15), pady=5)

tk.Label(frame_principal, text="Altura Y (mm):", font=default_font).grid(row=1, column=2, sticky="e", padx=(0,5), pady=5)
entry_ly = tk.Entry(frame_principal, width=8, font=default_font)
entry_ly.insert(0, "300")
entry_ly.grid(row=1, column=3, padx=(0,15), pady=5)

tk.Label(frame_principal, text="Comprimento Z (mm):", font=default_font).grid(row=1, column=4, sticky="e", padx=(0,5), pady=5)
entry_lz = tk.Entry(frame_principal, width=8, font=default_font)
entry_lz.insert(0, "300")
entry_lz.grid(row=1, column=5, pady=5)

# Entradas para Cilindro
tk.Label(frame_principal, text="Diâmetro (mm):", font=default_font).grid(row=2, column=0, sticky="e", padx=(0,5), pady=5)
entry_diam = tk.Entry(frame_principal, width=8, font=default_font)
entry_diam.insert(0, "200")
entry_diam.grid(row=2, column=1, padx=(0,15), pady=5)

tk.Label(frame_principal, text="Comprimento (mm):", font=default_font).grid(row=2, column=2, sticky="e", padx=(0,5), pady=5)
entry_cl = tk.Entry(frame_principal, width=8, font=default_font)
entry_cl.insert(0, "500")
entry_cl.grid(row=2, column=3, padx=(0,15), pady=5)

# Entradas comuns
tk.Label(frame_principal, text="Tamanho do pixel (mm):", font=default_font).grid(row=3, column=0, sticky="e", padx=(0,5), pady=5)
entry_ps = tk.Entry(frame_principal, width=8, font=default_font)
entry_ps.insert(0, "1")
entry_ps.grid(row=3, column=1, padx=(0,15), pady=5)

tk.Label(frame_principal, text="Espessura do corte (mm):", font=default_font).grid(row=3, column=2, sticky="e", padx=(0,5), pady=5)
entry_st = tk.Entry(frame_principal, width=8, font=default_font)
entry_st.insert(0, "1")
entry_st.grid(row=3, column=3, padx=(0,15), pady=5)

# Patient Name / Patient ID
tk.Label(frame_principal, text="Patient Name:", font=default_font).grid(row=4, column=0, sticky="e", padx=(0,5), pady=5)
entry_name = tk.Entry(frame_principal, width=20, font=default_font)
entry_name.grid(row=4, column=1, columnspan=2, pady=5)

tk.Label(frame_principal, text="Patient ID:", font=default_font).grid(row=4, column=3, sticky="e", padx=(0,5), pady=5)
entry_id = tk.Entry(frame_principal, width=15, font=default_font)
entry_id.grid(row=4, column=4, columnspan=2, pady=5)

# Patient Position
tk.Label(frame_principal, text="Patient Position:", font=default_font).grid(row=5, column=0, sticky="e", padx=(0,5), pady=(5,10))
posicoes = ["HFS","HFP","FFS","FFP","HFDR","HFDL","FFDR","FFDL"]
combobox_position = ttk.Combobox(frame_principal, values=posicoes, width=8, font=default_font, state="readonly")
combobox_position.set("HFS")
combobox_position.grid(row=5, column=1, padx=(0,15), pady=(5,10))

buttons_frame = tk.Frame(root)
buttons_frame.pack(fill="x", padx=15, pady=(0,10))

btn_gerar = ttk.Button(buttons_frame, text="Gerar Volume", command=atualizar_imagem)
btn_gerar.pack(side="left", padx=(0, 10))

btn_exportar = ttk.Button(buttons_frame, text="Exportar como DICOM", command=salvar_dicom)
btn_exportar.pack(side="left")

canvas_frame = tk.Frame(root, bd=1, relief="solid")
canvas_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

fig = Figure(figsize=(10, 4))
canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
canvas.get_tk_widget().pack(fill="both", expand=True)

current_volume = None
current_spacing = None

atualizar_imagem()

root.mainloop()
