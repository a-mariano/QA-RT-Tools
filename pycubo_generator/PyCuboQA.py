
import numpy as np
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk, font
import pydicom
from pydicom.dataset import FileDataset
import datetime
import os

# Matplotlib imports para incorporar no Tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ───────────── Função extra: Criar RTSTRUCT com contorno BODY ─────────────
def criar_rtstruct_body(volume, spacing, patient_name, patient_id, patient_position, output_dir,
                        study_uid, series_uid, frame_uid):
    import pydicom
    from pydicom.dataset import Dataset, FileDataset
    import datetime
    import os

    dt = datetime.datetime.now()
    rtstruct_uid = pydicom.uid.generate_uid()
    sop_instance_uid = pydicom.uid.generate_uid()

    # Arquivo RT Structure Set
    file_meta = pydicom.Dataset()
    file_meta.MediaStorageSOPClassUID = pydicom.uid.RTStructureSetStorage
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

    ds = FileDataset("RTSTRUCT.dcm", {}, file_meta=file_meta, preamble=b"\x00" * 128)
    ds.SpecificCharacterSet = "ISO_IR 100"
    ds.InstanceCreationDate = dt.strftime('%Y%m%d')
    ds.InstanceCreationTime = dt.strftime('%H%M%S')
    ds.SOPClassUID = pydicom.uid.RTStructureSetStorage
    ds.SOPInstanceUID = sop_instance_uid
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.FrameOfReferenceUID = frame_uid
    ds.Modality = "RTSTRUCT"
    ds.Manufacturer = "PyCubo"
    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.PatientBirthDate = ""
    ds.PatientSex = ""
    ds.StudyDate = dt.strftime('%Y%m%d')
    ds.StudyTime = dt.strftime('%H%M%S')
    ds.SeriesNumber = 999
    ds.StructureSetLabel = "BODY_ONLY"
    ds.StructureSetDate = dt.strftime('%Y%m%d')
    ds.StructureSetTime = dt.strftime('%H%M%S')

    # Referência a uma série de imagens
    depth, height, width = volume.shape
    pixel_spacing = spacing[1]
    slice_thickness = spacing[0]

    # Montar ReferencedFrameOfReferenceSequence
    ds.ReferencedFrameOfReferenceSequence = [Dataset()]
    ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID = frame_uid
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence = [Dataset()]
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].ReferencedSOPClassUID = "1.2.840.10008.5.1.4.1.2.2.1"  # Study Root Query Retrieve Information Model - FIND UID
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].ReferencedSOPInstanceUID = study_uid

    # RTReferencedSeriesSequence dentro de RTReferencedStudySequence
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence = [Dataset()]
    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID = series_uid

    # ContourImageSequence para cada slice
    contour_image_seq = []
    for z in range(depth):
        item = Dataset()
        item.ReferencedSOPClassUID = pydicom.uid.CTImageStorage
        item.ReferencedSOPInstanceUID = None  # Será preenchido na sequência abaixo
        contour_image_seq.append(item)

    # Preencher os ReferencedSOPInstanceUID com os mesmos UIDs das imagens CT exportadas
    # Nessas séries, os SOPInstanceUID das imagens CT devem ter sido gerados dentro de exportar_dicom
    # Aqui, assumimos mesmo UID gerado para cada slice
    # (Alternativamente, poderíamos armazenar esses UIDs, mas simplificamos usando gerados aqui)
    for item in contour_image_seq:
        item.ReferencedSOPInstanceUID = pydicom.uid.generate_uid()

    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence = contour_image_seq

    # ROI: BODY
    roi_number = 1
    ds.StructureSetROISequence = [Dataset()]
    ds.StructureSetROISequence[0].ROINumber = roi_number
    ds.StructureSetROISequence[0].ReferencedFrameOfReferenceUID = frame_uid
    ds.StructureSetROISequence[0].ROIName = "BODY"
    ds.StructureSetROISequence[0].ROIGenerationAlgorithm = "MANUAL"

    # ROIContour (uma caixa em uma slice central)
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

    # RTROIObservations
    ds.RTROIObservationsSequence = [Dataset()]
    ds.RTROIObservationsSequence[0].ObservationNumber = 1
    ds.RTROIObservationsSequence[0].ReferencedROINumber = roi_number
    ds.RTROIObservationsSequence[0].ROIObservationLabel = "BODY"
    ds.RTROIObservationsSequence[0].RTROIInterpretedType = "EXTERNAL"
    ds.RTROIObservationsSequence[0].ROIInterpreter = ""

    rt_path = os.path.join(output_dir, "RTSTRUCT_BODY.dcm")
    ds.save_as(rt_path, write_like_original=False)
    return rt_path

def gerar_volume_com_cubo_mm(mm_x, mm_y, mm_z, pixel_size, slice_thickness):
    """
    Cria um volume 3D onde há um cubo (ou paralelepípedo) de água (0 HU)
    centralizado num fundo de ar (–1000 HU), mas seguindo estas regras:

    • Nos eixos X e Y, as dimensões do volume de ar são iguais entre si,
      correspondem a (max(mm_x, mm_y) + 100) mm, ou seja, 10 cm a mais
      do que a maior extensão entre X e Y do fantoma de água.
    • No eixo Z, a dimensão do volume de ar será mm_z + 50 mm (5 cm a mais
      do que o comprimento Z do fantoma de água).

    O volume de água interna pode ser retangular (mm_x × mm_y × mm_z), 
    mas fica centralizado dentro do volume de ar.
    Retorna:
      volume (np.int16 com valores –1000 ou 0) e
      spacing = [slice_thickness, pixel_size, pixel_size].
    """
    # Define dimensões do volume de ar em mm
    lado_xy_mm   = max(mm_x, mm_y) + 100.0   # 10 cm maior entre X e Y
    altura_z_mm  = mm_z + 50.0               # 5 cm maior em Z

    # Converte para número de voxels (arredondando)
    nz = int(round(altura_z_mm / slice_thickness))
    ny = int(round(lado_xy_mm / pixel_size))
    nx = int(round(lado_xy_mm / pixel_size))

    # Cria volume todo de ar (–1000 HU)
    volume = np.ones((nz, ny, nx), dtype=np.int16) * -1000

    # Dimensiona o fantoma de água interno (pode ser retangular)
    cz = int(round(mm_z / slice_thickness))
    cy = int(round(mm_y / pixel_size))
    cx = int(round(mm_x / pixel_size))

    # Determina índices para centralizar o cubo de água
    start_z = (nz - cz) // 2
    start_y = (ny - cy) // 2
    start_x = (nx - cx) // 2

    volume[
        start_z : start_z + cz,
        start_y : start_y + cy,
        start_x : start_x + cx
    ] = 0  # água (0 HU)

    # Spacing na ordem [Z, Y, X] em mm
    spacing = [float(slice_thickness), float(pixel_size), float(pixel_size)]
    return volume, spacing


def exportar_dicom(volume, voxel_spacing, patient_name, patient_id, patient_position, output_dir):
    """
    Exporta cada slice axial do volume como um arquivo DICOM no diretório dado.
    Preenche tags obrigatórios para a maioria dos TPS (StudyDate, SeriesNumber,
    SliceLocation, ReconstructionDiameter, etc.), incluindo PatientPosition.
    """
    dt = datetime.datetime.now()
    study_uid = pydicom.uid.generate_uid()
    series_uid = pydicom.uid.generate_uid()
    frame_uid  = pydicom.uid.generate_uid()  # FrameOfReferenceUID

    depth, height, width = volume.shape  # Z, Y, X
    os.makedirs(output_dir, exist_ok=True)

    for z in range(depth):
        # ─── Metadata do arquivo ───
        file_meta = pydicom.Dataset()
        file_meta.MediaStorageSOPClassUID = pydicom.uid.CTImageStorage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

        ds = FileDataset('', {}, file_meta=file_meta, preamble=b"\x00" * 128)

        # ─── Dados do paciente ───
        ds.PatientName     = patient_name
        ds.PatientID       = patient_id
        ds.PatientPosition = patient_position  # valor selecionado no combobox
        # (opcionais)
        ds.PatientBirthDate = ''
        ds.PatientSex       = ''

        # ─── Study/Série/Instância ───
        ds.StudyInstanceUID    = study_uid
        ds.SeriesInstanceUID   = series_uid
        ds.FrameOfReferenceUID = frame_uid
        ds.SOPInstanceUID      = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID         = file_meta.MediaStorageSOPClassUID

        # Datas e horas
        ds.StudyDate = dt.strftime('%Y%m%d')
        ds.StudyTime = dt.strftime('%H%M%S')
        ds.StudyID   = '1'
        ds.StudyDescription = 'CT Phantom - PyCubo'

        ds.SeriesNumber      = 1
        ds.SeriesDate        = dt.strftime('%Y%m%d')
        ds.SeriesTime        = dt.strftime('%H%M%S')
        ds.SeriesDescription = '3D Cube CT Phantom'

        # ─── Imagem/Orientação ───
        ds.Modality             = 'CT'
        ds.Manufacturer         = 'PyCubo'
        ds.ManufacturerModelName = ''
        ds.DeviceSerialNumber   = ''
        ds.SoftwareVersions     = ''

        ds.ImageType = ['ORIGINAL', 'PRIMARY', 'AXIAL']
        ds.ImagePositionPatient    = [0.0, 0.0, float(z) * voxel_spacing[0]]
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        # Tamanho em pixels
        ds.Rows    = height
        ds.Columns = width
        ds.InstanceNumber = z + 1

        # Posicionamento do corte
        ds.SliceLocation        = float(z) * voxel_spacing[0]
        ds.SpacingBetweenSlices = float(voxel_spacing[0])

        ds.PixelSpacing           = [float(voxel_spacing[1]), float(voxel_spacing[2])]
        ds.SliceThickness         = float(voxel_spacing[0])
        ds.ReconstructionDiameter = float(width * voxel_spacing[2])

        # ─── Parâmetros de pixel ───
        ds.SamplesPerPixel         = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelRepresentation      = 1
        ds.HighBit                  = 15
        ds.BitsStored               = 16
        ds.BitsAllocated            = 16

        ds.RescaleIntercept = 0
        ds.RescaleSlope     = 1

        # Janela padrão
        ds.WindowCenter = 0
        ds.WindowWidth  = 4000

        # kVp (para TPS)
        ds.KVP = 120

        # Outros campos
        ds.PixelAspectRatio = '1\\1'
        ds.ContentDate      = dt.strftime('%Y%m%d')
        ds.ContentTime      = dt.strftime('%H%M%S')

        # ─── Dados de Pixel ───
        ds.PixelData = volume[z, :, :].tobytes()

        # Salva no disco (write_like_original=False garante que as tags sejam gravadas)
        filename = os.path.join(output_dir, f'slice_{z:03}.dcm')
        ds.save_as(filename, write_like_original=False)

    # Após exportar todas as slices, cria o RTSTRUCT
    criar_rtstruct_body(volume, voxel_spacing, patient_name, patient_id, patient_position,
                        output_dir, study_uid, series_uid, frame_uid)
    return output_dir


def salvar_dicom():
    """
    Obtém o volume atual e parâmetros, pede ao usuário diretório de saída
    e chama exportar_dicom().
    """
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
    """
    Lê valores da GUI, gera volume 3D, exibe cortes axial, coronal e sagital
    no Figure Canvas, **mantendo proporção física correta** (cada voxel
    em X × Y tem tamanho pixel_size, cada voxel em Z tem tamanho slice_thickness).
    """
    global current_volume, current_spacing

    try:
        mm_x       = float(entry_lx.get())
        mm_y       = float(entry_ly.get())
        mm_z       = float(entry_lz.get())
        pixel_size = float(entry_ps.get())
        thickness  = float(entry_st.get())

        if mm_x <= 0 or mm_y <= 0 or mm_z <= 0 or pixel_size <= 0 or thickness <= 0:
            raise ValueError

        volume, spacing = gerar_volume_com_cubo_mm(mm_x, mm_y, mm_z, pixel_size, thickness)
        current_volume  = volume
        current_spacing = spacing

        nz, ny, nx = volume.shape
        z_mid      = nz // 2
        y_mid      = ny // 2
        x_mid      = nx // 2

        slice_axial   = volume[z_mid, :, :]    # X × Y
        slice_coronal = volume[:, y_mid, :]    # Z × X
        slice_sagital = volume[:, :, x_mid]    # Z × Y

        # Limpa a figura antes de desenhar
        fig.clear()
        axs = fig.subplots(1, 3)

        # ─── Fatia axial (X × Y) ───
        axs[0].imshow(slice_axial, cmap='gray', vmin=-1000, vmax=500)
        axs[0].set_title(f'Axial (Z={z_mid})\\nDim Cubo: {mm_x:.0f}×{mm_y:.0f}×{mm_z:.0f} mm')
        axs[0].axis('off')
        axs[0].set_aspect('equal')  # pixel X (mm) = pixel Y (mm)

        # ─── Fatia coronal (X × Z) ───
        axs[1].imshow(slice_coronal, cmap='gray', vmin=-1000, vmax=500)
        axs[1].set_title(f'Coronal\\nPixel: {pixel_size} mm, Corte: {thickness} mm')
        axs[1].axis('off')
        # Conversão correta: cada voxel vertical (linha) equivale a thickness mm,
        # cada voxel horizontal (coluna) equivale a pixel_size mm → aspecto = thickness/pixel_size
        axs[1].set_aspect(thickness / pixel_size)

        # ─── Fatia sagital (Y × Z) ───
        axs[2].imshow(slice_sagital, cmap='gray', vmin=-1000, vmax=500)
        axs[2].set_title(f'Sagital')
        axs[2].axis('off')
        axs[2].set_aspect(thickness / pixel_size)

        # Ajusta margens para não cortar nada (rótulos, títulos etc.)
        fig.tight_layout()
        canvas.draw()

    except ValueError:
        messagebox.showwarning("Aviso", "Valores inválidos. Insira números positivos.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao atualizar imagem: {e}")


# ─────────── Interface Tkinter ───────────
root = tk.Tk()
root.title("PyCubo QA - Gerador de CT Phantom")
root.minsize(800, 500)  # tamanho mínimo para a janela

# Define fonte padrão para todos os widgets (labels, entries, combobox, buttons)
default_font = font.Font(family="TkDefaultFont", size=12)

# Cria um estilo simples para os botões ttk
style = ttk.Style()
style.configure('TButton', font=default_font, padding=6)

# Frame principal com borda para dar destaque
frame_principal = tk.LabelFrame(root, text="Parâmetros", font=default_font,
                                bd=2, relief="groove", padx=10, pady=10)
frame_principal.pack(fill="x", padx=15, pady=10)

# ───────── Entradas de parâmetros ─────────
# Largura X (mm)
tk.Label(frame_principal, text="Largura X (mm):", font=default_font).grid(row=0, column=0, sticky="e", padx=(0,5), pady=5)
entry_lx = tk.Entry(frame_principal, width=8, font=default_font)
entry_lx.insert(0, "300")
entry_lx.grid(row=0, column=1, padx=(0,15), pady=5)

# Altura Y (mm)
tk.Label(frame_principal, text="Altura Y (mm):", font=default_font).grid(row=0, column=2, sticky="e", padx=(0,5), pady=5)
entry_ly = tk.Entry(frame_principal, width=8, font=default_font)
entry_ly.insert(0, "300")
entry_ly.grid(row=0, column=3, padx=(0,15), pady=5)

# Comprimento Z (mm)
tk.Label(frame_principal, text="Comprimento Z (mm):", font=default_font).grid(row=0, column=4, sticky="e", padx=(0,5), pady=5)
entry_lz = tk.Entry(frame_principal, width=8, font=default_font)
entry_lz.insert(0, "300")
entry_lz.grid(row=0, column=5, pady=5)

# Tamanho do pixel (mm)
tk.Label(frame_principal, text="Tamanho do pixel (mm):", font=default_font).grid(row=1, column=0, sticky="e", padx=(0,5), pady=5)
entry_ps = tk.Entry(frame_principal, width=8, font=default_font)
entry_ps.insert(0, "1")
entry_ps.grid(row=1, column=1, padx=(0,15), pady=5)

# Espessura de corte (mm)
tk.Label(frame_principal, text="Espessura do corte (mm):", font=default_font).grid(row=1, column=2, sticky="e", padx=(0,5), pady=5)
entry_st = tk.Entry(frame_principal, width=8, font=default_font)
entry_st.insert(0, "3")
entry_st.grid(row=1, column=3, padx=(0,15), pady=5)

# Patient Name / Patient ID
tk.Label(frame_principal, text="Patient Name:", font=default_font).grid(row=2, column=0, sticky="e", padx=(0,5), pady=5)
entry_name = tk.Entry(frame_principal, width=20, font=default_font)
entry_name.grid(row=2, column=1, columnspan=2, pady=5)

tk.Label(frame_principal, text="Patient ID:", font=default_font).grid(row=2, column=3, sticky="e", padx=(0,5), pady=5)
entry_id = tk.Entry(frame_principal, width=15, font=default_font)
entry_id.grid(row=2, column=4, columnspan=2, pady=5)

# Patient Position (DICOM padrão)
tk.Label(frame_principal, text="Patient Position:", font=default_font).grid(row=3, column=0, sticky="e", padx=(0,5), pady=(5,10))
posicoes = [
    "HFS",  # Head First-Supine
    "HFP",  # Head First-Prone
    "FFS",  # Feet First-Supine
    "FFP",  # Feet First-Prone
    "HFDR", # Head First-Decubitus Right
    "HFDL", # Head First-Decubitus Left
    "FFDR", # Feet First-Decubitus Right
    "FFDL"  # Feet First-Decubitus Left
]
combobox_position = ttk.Combobox(frame_principal, values=posicoes, width=8, font=default_font, state="readonly")
combobox_position.set("HFS")
combobox_position.grid(row=3, column=1, padx=(0,15), pady=(5,10))

# ───────── Botões ─────────
buttons_frame = tk.Frame(root)
buttons_frame.pack(fill="x", padx=15, pady=(0,10))

btn_gerar = ttk.Button(buttons_frame, text="Gerar Volume", command=atualizar_imagem)
btn_gerar.pack(side="left", padx=(0, 10))

btn_exportar = ttk.Button(buttons_frame, text="Exportar como DICOM", command=salvar_dicom)
btn_exportar.pack(side="left")

# ───────── Área de plotagem ─────────
canvas_frame = tk.Frame(root, bd=1, relief="solid")
canvas_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

fig = Figure(figsize=(10, 4))
canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
canvas.get_tk_widget().pack(fill="both", expand=True)

# Variáveis globais para volume e spacing
current_volume = None
current_spacing = None

# Gera a primeira visualização ao iniciar
atualizar_imagem()

root.mainloop()
