from http.client import EXPECTATION_FAILED
import pydicom
import os
import tkinter as tk
from tkinter import filedialog


def create_efs(efs_file_path):
    # Cria (ou zera) o arquivo .efs no caminho especificado
    with open(efs_file_path, 'w') as file:
        file.write('')


def MLCX1_Lookup(leave):
    MLC_code = {
        '1': '101',
        '2': '102',
        '3': '103',
        '4': '104',
        '5': '105',
        '6': '106',
        '7': '107',
        '8': '108',
        '9': '109',
        '10': '10a',
        '11': '10b',
        '12': '10c',
        '13': '10d',
        '14': '10e',
        '15': '10f',
        '16': '110',
        '17': '111',
        '18': '112',
        '19': '113',
        '20': '114',
        '21': '115',
        '22': '116',
        '23': '117',
        '24': '118',
        '25': '119',
        '26': '11a',
        '27': '11b',
        '28': '11c',
        '29': '11d',
        '30': '11e',
        '31': '11f',
        '32': '120',
        '33': '121',
        '34': '122',
        '35': '123',
        '36': '124',
        '37': '125',
        '38': '126',
        '39': '127',
        '40': '128',
        '41': '129',
        '42': '12a',
        '43': '12b',
        '44': '12c',
        '45': '12d',
        '46': '12e',
        '47': '12f',
        '48': '130',
        '49': '131',
        '50': '132',
        '51': '133',
        '52': '134',
        '53': '135',
        '54': '136',
        '55': '137',
        '56': '138',
        '57': '139',
        '58': '13a',
        '59': '13b',
        '60': '13c',
        '61': '13d',
        '62': '13e',
        '63': '13f',
        '64': '140',
        '65': '141',
        '66': '142',
        '67': '143',
        '68': '144',
        '69': '145',
        '70': '146',
        '71': '147',
        '72': '148',
        '73': '149',
        '74': '14a',
        '75': '14b',
        '76': '14c',
        '77': '14d',
        '78': '14e',
        '79': '14f',
        '80': '150',
    }
    return MLC_code[leave]


def MLCX2_Lookup(leave):
    MLC_code = {
        '1': '201',
        '2': '202',
        '3': '203',
        '4': '204',
        '5': '205',
        '6': '206',
        '7': '207',
        '8': '208',
        '9': '209',
        '10': '20a',
        '11': '20b',
        '12': '20c',
        '13': '20d',
        '14': '20e',
        '15': '20f',
        '16': '210',
        '17': '211',
        '18': '212',
        '19': '213',
        '20': '214',
        '21': '215',
        '22': '216',
        '23': '217',
        '24': '218',
        '25': '219',
        '26': '21a',
        '27': '21b',
        '28': '21c',
        '29': '21d',
        '30': '21e',
        '31': '21f',
        '32': '220',
        '33': '221',
        '34': '222',
        '35': '223',
        '36': '224',
        '37': '225',
        '38': '226',
        '39': '227',
        '40': '228',
        '41': '229',
        '42': '22a',
        '43': '22b',
        '44': '22c',
        '45': '22d',
        '46': '22e',
        '47': '22f',
        '48': '230',
        '49': '231',
        '50': '232',
        '51': '233',
        '52': '234',
        '53': '235',
        '54': '236',
        '55': '237',
        '56': '238',
        '57': '239',
        '58': '23a',
        '59': '23b',
        '60': '23c',
        '61': '23d',
        '62': '23e',
        '63': '23f',
        '64': '240',
        '65': '241',
        '66': '242',
        '67': '243',
        '68': '244',
        '69': '245',
        '70': '246',
        '71': '247',
        '72': '248',
        '73': '249',
        '74': '24a',
        '75': '24b',
        '76': '24c',
        '77': '24d',
        '78': '24e',
        '79': '24f',
        '80': '250',
    }
    return MLC_code[leave]


def write_efs(file_name, cp, code, data):  # f-string formatting changed to .format for 3.4 compatibility.
    codes_Dict = {
        'MUs': "5001,1-0 {}\n".format(data),
        'LINAC': "7001,1-0 {}\n".format(data),
        'PID': "7001,2-0 {}\n".format(data),
        'PName': "7001,3-0 {}\n".format(data),
        'PlanName': "7001,4-0 {}\n".format(data),
        'TxName': "7001,5-0 {}\n".format(data),
        'BeamName': "7001,7-0 {}\n".format(data),
        'BeamID': "7001,6-0 {}\n".format(data),
        'FieldComplexity': "7002,5-0 {}\n".format(data),
        'LeafWidth': "7002,6-0 {}\n".format(data),
        'RadType': "5001,2-{0} {1}\n".format(cp, data),
        'Energy': "5001,3-{0} {1} MV\n".format(cp, data),
        'Wedge': "5001,4-{0} {1}\n".format(cp, data),  # OUT
        'Gantry': "5001,7-{0} {1}\n".format(cp, data),
        'Acc': "5001,f-{0} {1}\n".format(cp, data),
        'GantryDirection': "5001,19-{0} {1}\n".format(cp, data),
        'Collimator': "5001,8-{0} {1}\n".format(cp, data),
        'CollimatorDir': "5001,bb-{0} {1}\n".format(cp, data),
        'X1': "5001,9-{0} {1}\n".format(cp, data),
        'X2': "5001,a-{0} {1}\n".format(cp, data),
        'Y1': "5001,b-{0} {1}\n".format(cp, data),
        'Y2': "5001,c-{0} {1}\n".format(cp, data),
        'MeterSet': "7002,4-{0} {1}\n".format(cp, data),  # is zero
        # Add more cases as needed
    }
    with open(file_name, 'a') as file:
        if "MLC" not in code:
            line_to_write = codes_Dict[code]
            file.write(line_to_write)
        else:
            mlc = 1
            for leave in data:
                if mlc < 81:
                    mlc_code = MLCX2_Lookup(str(81 - mlc))
                    line_to_write = "5001,{0}-{1} {2}\n".format(mlc_code, cp, round(-leave / 10, 2))
                else:
                    mlc_code = MLCX1_Lookup(str(161 - mlc))
                    line_to_write = "5001,{0}-{1} {2}\n".format(mlc_code, cp, round(leave / 10, 2))
                mlc += 1
                file.write(line_to_write)


def getGantry(cp):
    gantry = cp.GantryAngle
    gantry_rot = cp.GantryRotationDirection
    if gantry > 180:
        gantry_angle = gantry - 360
    else:
        gantry_angle = gantry
    return gantry_angle, gantry_rot


def getCollimator(beam):
    coll = beam.ControlPointSequence[0].BeamLimitingDeviceAngle
    if coll > 180:
        collimator = coll - 360
    else:
        collimator = coll
    return collimator


def get_total_MUs(rtplan, beam_number):
    # Get the total MUs for the beam from Fraction Group
    total_mus = 0.0
    fraction_group = rtplan.FractionGroupSequence[0]
    for referenced_beam in fraction_group.ReferencedBeamSequence:
        if referenced_beam.ReferencedBeamNumber == beam_number:
            total_mus = referenced_beam.BeamMeterset
            break
    return total_mus


def getFirstGantry(beam):
    first_gantry_rot = beam.ControlPointSequence[0].GantryRotationDirection
    first_gantry = beam.ControlPointSequence[0].GantryAngle
    if first_gantry > 180:
        first_gantry_angle = first_gantry - 360
    else:
        first_gantry_angle = first_gantry
    return first_gantry_angle, first_gantry_rot


def getBeamDelimiters(Beam_Lim_Dev_Pos_Seq, First_Yjaw_position):
    """
    Refatorado para não depender de índices fixos.
    Varre todos os itens em BeamLimitingDevicePositionSequence, filtra por RTBeamLimitingDeviceType:
     - Se começa com 'X', atribui a Xjaw_position
     - Se começa com 'Y', atribui a Yjaw_position
     - Se contém 'MLC', atribui a mlc_positions
    Se algum não for encontrado, aplica valores padrão ou usa First_Yjaw_position.
    """
    Xjaw_position = None
    Yjaw_position = None
    mlc_positions = []

    for item in Beam_Lim_Dev_Pos_Seq:
        dtype = getattr(item, "RTBeamLimitingDeviceType", "").upper()
        if dtype.startswith("X") and hasattr(item, "LeafJawPositions"):
            Xjaw_position = [float(x) for x in item.LeafJawPositions]
        elif dtype.startswith("Y") and hasattr(item, "LeafJawPositions"):
            Yjaw_position = [float(x) for x in item.LeafJawPositions]
        elif "MLC" in dtype and hasattr(item, "LeafJawPositions"):
            mlc_positions = [float(x) for x in item.LeafJawPositions]

    if Xjaw_position is None:
        Xjaw_position = [-200.0, 200.0]
    if Yjaw_position is None:
        Yjaw_position = First_Yjaw_position if First_Yjaw_position is not None else [-200.0, 200.0]

    return Xjaw_position, Yjaw_position, mlc_positions


def efs_standard_header_struct(crtplan, cbeam, efs_file):
    PatientID = crtplan.PatientID
    patient_name = crtplan.PatientName
    treatment_name = crtplan.BeamSequence[0].TreatmentMachineName

    try:
        beam_id = int(cbeam.BeamNumber)
    except:
        beam_id = 1
    beam_name = cbeam.BeamDescription
    leaf_width = 0.5

    total_monitor_units = round(get_total_MUs(crtplan, cbeam.BeamNumber), 2)

    create_efs(efs_file)
    write_efs(efs_file, 0, 'MUs', total_monitor_units)
    write_efs(efs_file, 0, 'LINAC', '6480')
    write_efs(efs_file, 0, 'PID', PatientID)
    write_efs(efs_file, 0, 'PName', patient_name)
    write_efs(efs_file, 0, 'PlanName', 'DCM2EFS')
    write_efs(efs_file, 0, 'TxName', treatment_name)
    write_efs(efs_file, 0, 'BeamID', beam_id)
    write_efs(efs_file, 0, 'BeamName', beam_name)
    write_efs(efs_file, 0, 'LeafWidth', leaf_width)


def efs_control_point_struct(FieldTech, energy, gantry_angle, gantry_rot, collimator,
                             Xjaw_position, Yjaw_position, mlc_positions,
                             monitor_units, cp_count, efs_file):
    write_efs(efs_file, cp_count, 'RadType', 'XRAY')
    write_efs(efs_file, cp_count, 'Energy', energy)
    write_efs(efs_file, cp_count, 'Wedge', 'OUT')
    write_efs(efs_file, cp_count, 'Gantry', gantry_angle)
    write_efs(efs_file, cp_count, 'Collimator', collimator)
    write_efs(efs_file, cp_count, 'X1', Yjaw_position[1] / 10)   # invertido conforme original
    write_efs(efs_file, cp_count, 'X2', -Yjaw_position[0] / 10)
    write_efs(efs_file, cp_count, 'Y1', -Xjaw_position[0] / 10)
    write_efs(efs_file, cp_count, 'Y2', Xjaw_position[1] / 10)
    write_efs(efs_file, cp_count, 'Acc', 0)
    write_efs(efs_file, cp_count, 'GantryDirection', gantry_rot)
    write_efs(efs_file, cp_count, 'CollimatorDir', 'NONE')

    # Exporta MLC em todos os CPs, assegurando que mlc_positions seja usado
    write_efs(efs_file, cp_count, 'MLC', mlc_positions)
    write_efs(efs_file, cp_count, 'MeterSet', 100 * monitor_units)


def convert_dcm2efs(file_path, efs_name_path=None):
    try:
        rtplan = pydicom.dcmread(file_path,force=True)
        if efs_name_path is None:
            efs_name_path = os.path.dirname(file_path)
        efs_names = []

        for beam in rtplan.BeamSequence:
            safe_name = beam.BeamName.replace(" ", "_")
            efs_file = os.path.join(efs_name_path, 'Beam_' + safe_name + '.efs')

            # Cabeçalhos gerais
            efs_standard_header_struct(rtplan, beam, efs_file)

            control_points = beam.ControlPointSequence
            collimator = int(getCollimator(beam))
            energy = control_points[0].NominalBeamEnergy

            cp_count = 1
            cp_len = len(control_points)
            First_gantry, First_gantry_rot = getFirstGantry(beam)

            # Obtém First_Yjaw_position do primeiro CP, caso exista
            first_bl_seq = control_points[0].BeamLimitingDevicePositionSequence
            First_Yjaw_position = None
            if first_bl_seq:
                for item in first_bl_seq:
                    dtype = getattr(item, "RTBeamLimitingDeviceType", "").upper()
                    if dtype.startswith("Y") and hasattr(item, "LeafJawPositions"):
                        First_Yjaw_position = [float(x) for x in item.LeafJawPositions]
                        break

            total_mus = get_total_MUs(rtplan, beam.BeamNumber)

            # Determina técnica do feixe
            if 'NONE' in First_gantry_rot and cp_len > 2:
                FieldTech = 'IMRT'
                write_efs(efs_file, 0, 'FieldComplexity', 'Dynamic')
            elif 'NONE' in First_gantry_rot and cp_len == 2:
                FieldTech = 'Static'
            else:
                FieldTech = 'VMAT'
                write_efs(efs_file, 0, 'FieldComplexity', 'IMAT')

            # Loop por todos os Control Points
            for cp in control_points:
                if 'VMAT' in FieldTech:
                    gantry_angle, gantry_rot = getGantry(cp)
                else:
                    gantry_angleFl, gantry_rot = getFirstGantry(beam)
                    gantry_angle = int(gantry_angleFl)

                monitor_units = cp.CumulativeMetersetWeight

                # Só pula o último CP em static, escrevendo somente MeterSet; nos demais, escreve tudo
#                if not ('Static' in FieldTech and cp_count == cp_len):
                if not ('Static' in FieldTech and cp_count > cp_len):
                    bl_seq = cp.BeamLimitingDevicePositionSequence
                    Xjaw_position, Yjaw_position, mlc_positions = getBeamDelimiters(bl_seq, First_Yjaw_position)
                    efs_control_point_struct(
                        FieldTech,
                        energy,
                        gantry_angle,
                        gantry_rot,
                        collimator,
                        Xjaw_position,
                        Yjaw_position,
                        mlc_positions,
                        monitor_units,
                        cp_count,
                        efs_file
                    )
                else:
                    write_efs(efs_file, cp_count, 'MeterSet', 100 * monitor_units)

                cp_count += 1

            efs_names.append(efs_file)

        return efs_names

    except Exception as e:
        print(e)
        return None


def open_file_dialog():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    file_path = filedialog.askopenfilename(title="Select a file")

    if file_path:
        print("Selected file: %s" % file_path)
    else:
        print("No file selected")
    return file_path
