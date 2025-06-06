import os
import numpy as np
import datetime
import pydicom
from pydicom.dataset import FileDataset

def gerar_volume_com_cubo_mm(mm_x, mm_y, mm_z, pixel_size, slice_thickness):
    """
    Cria um volume cúbico 3D onde há um cubo de água (0 HU)
    centralizado num fundo de ar (-1000 HU).
    O lado do volume é igual ao maior dos mm_x, mm_y, mm_z + 100 mm.
    """
    maior_dim = max(mm_x, mm_y, mm_z)
    lado_volume_mm = maior_dim + 100.0  # adiciona 10 cm de margem

    # Quantos voxels em cada direção do volume
    voxels_z = int(round(lado_volume_mm / slice_thickness))
    voxels_y = int(round(lado_volume_mm / pixel_size))
    voxels_x = int(round(lado_volume_mm / pixel_size))

    # Quantos voxels no cubo de água
    vox_cubo_z = int(round(mm_z / slice_thickness))
    vox_cubo_y = int(round(mm_y / pixel_size))
    vox_cubo_x = int(round(mm_x / pixel_size))

    # Volume cúbico preenchido com ar (-1000 HU)
    volume = np.full((voxels_z, voxels_y, voxels_x), -1000, dtype=np.int16)

    # Índices de início para centralizar o cubo
    start_z = (voxels_z - vox_cubo_z) // 2
    start_y = (voxels_y - vox_cubo_y) // 2
    start_x = (voxels_x - vox_cubo_x) // 2

    end_z = start_z + vox_cubo_z
    end_y = start_y + vox_cubo_y
    end_x = start_x + vox_cubo_x

    # Insere cubo de água (0 HU)
    volume[start_z:end_z, start_y:end_y, start_x:end_x] = 0

    voxel_spacing = (slice_thickness, pixel_size, pixel_size)  # Z, Y, X
    return volume, voxel_spacing

def exportar_dicom(volume, voxel_spacing, patient_name, patient_id, output_dir):
    """
    Exporta cada slice axial do volume como um arquivo DICOM no diretório dado,
    usando os tags PatientName e PatientID fornecidos.
    Retorna study UID, series UID e o diretório de saída.
    """
    dt = datetime.datetime.now()
    study_uid = pydicom.uid.generate_uid()
    series_uid = pydicom.uid.generate_uid()

    depth, height, width = volume.shape  # Z, Y, X

    # Garante que a pasta existe
    os.makedirs(output_dir, exist_ok=True)

    for z in range(depth):
        file_meta = pydicom.Dataset()
        file_meta.MediaStorageSOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

        ds = FileDataset('', {}, file_meta=file_meta, preamble=b"\0" * 128)
        ds.ContentDate = dt.strftime('%Y%m%d')
        ds.ContentTime = dt.strftime('%H%M%S')
        ds.PatientName = patient_name
        ds.PatientID = patient_id
        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.Modality = 'CT'
        ds.Rows, ds.Columns = height, width
        ds.InstanceNumber = z + 1
        ds.PixelSpacing = [str(voxel_spacing[1]), str(voxel_spacing[2])]
        ds.SliceThickness = str(voxel_spacing[0])
        ds.ImagePositionPatient = [0.0, 0.0, float(z) * voxel_spacing[0]]
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelRepresentation = 1
        ds.HighBit = 15
        ds.BitsStored = 16
        ds.BitsAllocated = 16
        ds.RescaleIntercept = 0
        ds.RescaleSlope = 1
        ds.WindowCenter = 0
        ds.WindowWidth = 4000
        ds.PixelData = volume[z, :, :].tobytes()

        filename = os.path.join(output_dir, f'slice_{z:03}.dcm')
        ds.save_as(filename)

    return study_uid, series_uid, output_dir

def update_rtplan_reference(rtplan_path, ct_folder, output_rtplan_path):
    """
    Atualiza o RTPLAN DICOM para referenciar a nova CT (pasta de DICOMs).
    Lê o primeiro arquivo DICOM de CT para obter StudyInstanceUID e SeriesInstanceUID,
    então ajusta o RTPLAN e salva em output_rtplan_path.
    """
    rt_ds = pydicom.dcmread(rtplan_path)

    # Localiza primeiro DICOM de CT na pasta
    ct_files = sorted([os.path.join(ct_folder, f) for f in os.listdir(ct_folder) if f.lower().endswith('.dcm')])
    if not ct_files:
        raise FileNotFoundError("Nenhum arquivo DICOM de CT encontrado na pasta.")

    first_ct = pydicom.dcmread(ct_files[0])
    new_study_uid = first_ct.StudyInstanceUID
    new_series_uid = first_ct.SeriesInstanceUID

    # Atualiza StudyInstanceUID e SeriesInstanceUID do RTPLAN
    rt_ds.StudyInstanceUID = new_study_uid
    rt_ds.SeriesInstanceUID = new_series_uid
    rt_ds.SOPInstanceUID = pydicom.uid.generate_uid()

    # Atualiza ReferencedStudySequence e ReferencedSeriesSequence, se existirem
    if hasattr(rt_ds, 'ReferencedStudySequence'):
        for study_item in rt_ds.ReferencedStudySequence:
            study_item.ReferencedStudyInstanceUID = new_study_uid
            if hasattr(study_item, 'ReferencedSeriesSequence'):
                for series_item in study_item.ReferencedSeriesSequence:
                    series_item.SeriesInstanceUID = new_series_uid

    # Salva RTPLAN modificado
    rt_ds.save_as(output_rtplan_path)

    return output_rtplan_path
