import pydicom
from pydicom.errors import InvalidDicomError
from PyQt5.QtWidgets import QTreeWidgetItem

def open_dicom_file(path):
    try:
        ds = pydicom.dcmread(path)
    except InvalidDicomError:
        ds = pydicom.dcmread(path, force=True)
    return ds

def populate_tree(ds, parent_item):
    for elem in ds:
        tag_str = f"({elem.tag.group:04X},{elem.tag.element:04X})"
        name = elem.name
        vr = elem.VR

        if vr == "SQ":
            seq_item = QTreeWidgetItem(parent_item, [tag_str, vr, name, f"[Sequence of {len(elem.value)}]"])
            seq_item.data_element = elem
            for idx, item in enumerate(elem.value):
                item_root = QTreeWidgetItem(seq_item, [f"Item {idx}", "", "", ""])
                populate_tree(item, item_root)
        else:
            val = elem.value
            if isinstance(val, bytes) and len(val) > 64:
                val_str = "<bytes...>"
            else:
                val_str = str(val)
            child = QTreeWidgetItem(parent_item, [tag_str, vr, name, val_str])
            child.data_element = elem

def save_data_element(elem, new_str):
    vr = elem.VR
    if vr in ("DS", "IS"):
        # Agora escapamos corretamente a barra invertida
        if "\\" in new_str:
            parts = new_str.split("\\")
            converted = []
            for p in parts:
                converted.append(float(p) if vr == "DS" else int(p))
            elem.value = converted
        else:
            elem.value = float(new_str) if vr == "DS" else int(new_str)
    elif vr in ("DA", "TM", "DT", "UI", "SH", "LO", "CS", "PN", "ST", "LT", "UT", "AE", "AS", "AT"):
        elem.value = new_str
    elif vr in ("US", "SS", "UL", "SL"):
        elem.value = int(new_str)
    elif vr in ("FL", "FD"):
        elem.value = float(new_str)
    else:
        elem.value = new_str

def save_dicom_file(ds, path_out):
    ds.save_as(path_out)

def get_beams(ds):
    return getattr(ds, "RTBeamSequence", None) or getattr(ds, "BeamSequence", None)

def get_control_points(beam):
    return beam.ControlPointSequence

def get_bl_seq(cp):
    return getattr(cp, "BeamLimitingDevicePositionSequence", None)

def find_mlc_item(bl_seq):
    for item in bl_seq:
        if "MLC" in getattr(item, "RTBeamLimitingDeviceType", "").upper():
            return item
    return None

def get_mlc_positions(mlc_item):
    return [float(x) for x in mlc_item.LeafJawPositions]

def find_jaw_positions(bl_seq, axis='X'):
    """
    Retorna [min, max] apenas para X JAW ou Y JAW,
    descartando itens 'MLCX' ou 'MLCY'.
    """
    for item in bl_seq:
        dtype = getattr(item, "RTBeamLimitingDeviceType", "").upper()
        # Só aceita exatamente "X JAW" (ou começa com "X JAW") no caso de X,
        # ou "Y JAW" no caso de Y. Evita capturar "MLCX", "MLCY".
        if axis.upper() == 'X' and dtype.startswith("X JAW") and hasattr(item, "LeafJawPositions"):
            vals = item.LeafJawPositions
            if isinstance(vals, (list, tuple)) and len(vals) == 2:
                return [float(vals[0]), float(vals[1])]
        if axis.upper() == 'Y' and dtype.startswith("Y JAW") and hasattr(item, "LeafJawPositions"):
            vals = item.LeafJawPositions
            if isinstance(vals, (list, tuple)) and len(vals) == 2:
                return [float(vals[0]), float(vals[1])]
    return None
