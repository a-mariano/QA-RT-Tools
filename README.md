# QA-RTplan-Editor

O **QA-RTplan-Editor** é um conjunto de ferramentas em Python voltado para controle de qualidade (QA) em radioterapia. Por meio de uma interface gráfica simples, é possível:

- Abrir, visualizar e editar planos de tratamento no formato DICOM RTPLAN.
- Navegar entre beams e control points, com visualização gráfica de MLC (Multi‑Leaf Collimator) e posições de jaws.
- Exportar e importar parâmetros de control points via planilhas Excel.
- Converter RTPLAN para o formato EFS (para uso em sistemas que exigem esse padrão).
- Gerar um phantom de TC com um cubo de água em fundo de ar, usando uma interface em Tkinter.
- Atualizar, em memória, atributos de RTPLAN para referenciar um novo estudo de CT (por exemplo, quando se insere um CT sintético).
- Salvar as modificações no RTPLAN em disco.

---

## Índice

1. [Visão Geral](#visão-geral)  
2. [Pré-requisitos](#pré-requisitos)  
3. [Instalação](#instalação)  
4. [Estrutura do Projeto](#estrutura-do-projeto)  
5. [Uso](#uso)  
   1. [Launcher](#launcher)  
   2. [Editor de RTPLAN DICOM](#editor-de-rtplan-dicom)  
   3. [Gerador de CT Phantom](#gerador-de-ct-phantom)  
6. [Componentes Internos](#componentes-internos)  
   1. [dicom_utils](#dicom_utils)  
   2. [efs_converter](#efs_converter)  
7. [Licença](#licença)  

---

## Visão Geral

O objetivo do **QA-RTplan-Editor** é oferecer uma solução unificada para tarefas comuns de QA em radioterapia, como inspeção e edição de arquivos RTPLAN, geração de exames sintéticos de TC e conversão entre formatos específicos (EFS). A interface principal permite alternar facilmente entre:

- **Editor de RTPLAN DICOM**: visualização hierárquica do DICOM, edição de tags, navegação entre beams/CPs, exportação/importação de control points, conversão para EFS e atualização dinâmica de referências de CT.
- **Gerador de CT Phantom (cubo de água)**: criação de um volume 3D de um cubo de água em fundo de ar, exportável como série de DICOMs.

---

## Pré-requisitos

Antes de usar, instale as bibliotecas Python necessárias. As principais dependências são:

- **Python 3.10+**  
- **PyQt5** (interface gráfica do editor DICOM)  
- **pydicom** (leitura e escrita de arquivos DICOM)  
- **numpy** (manipulação de matrizes para TC e MLC)  
- **matplotlib** (gráficos de MLC)  
- **tkinter** (interface do gerador de CT Phantom)  
- **openpyxl** (manipulação de planilhas Excel)  

Em geral, pode-se instalar tudo via `pip`:

```bash
pip install pydicom numpy matplotlib pyqt5 openpyxl
```

O **tkinter** geralmente acompanha a instalação padrão do Python; se não estiver presente, instale-o via gerenciador da sua distribuição (por exemplo, `sudo apt install python3-tk` em Linux).

---

## Instalação

1. Clone ou faça o download deste repositório:  
   ```bash
   git clone https://github.com/a-mariano/QA-RTplan-Editor.git
   cd QA-RTplan-Editor
   ```
2. Crie e ative um ambiente virtual (opcional, mas recomendado):  
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate.bat     # Windows
   ```
3. Instale as dependências do `requirements.txt`:  
   ```bash
   pip install -r requirements.txt
   ```
   - Se preferir, instale apenas as bibliotecas principais conforme descrito em [Pré-requisitos](#pré-requisitos).

---

## Estrutura do Projeto

```
QA-RTplan-Editor/
├── launcher.py
├── requirements.txt
├── README.md
├── LICENSE
├── dicomrt_editor/
│   ├── main_window.py
│   ├── __init__.py
│   ├── dicom_utils/
│   │   ├── reader.py
│   │   ├── export_excel.py
│   │   └── __init__.py
│   └── efs_converter/
│       ├── DCM2EFS.py
│       └── __init__.py
├── pycubo_generator/
│   ├── PyCuboQA.py
│   └── __init__.py
└── icons/
    ├── dicomrt_icon.png
    └── pycubo_icon.png
```

- **launcher.py**  
  Script principal que exibe uma janela de “Launcher” com botões para iniciar o editor DICOM ou o gerador de CT Phantom.
- **dicomrt_editor/**  
  Contém o código‑fonte do editor de RTPLAN DICOM, organizado em:
  - `main_window.py` – interface principal do editor (PyQt5).
  - `dicom_utils/` – sub‑pacote com funções auxiliares para leitura de DICOM, extração de beams/CPs, manipulação de MLC/jaws e exportação/importação de Excel.
  - `efs_converter/` – módulo para converter RTPLAN para arquivos `.efs`.
- **pycubo_generator/**  
  Interface em Tkinter para gerar um phantom de TC contendo um cubo (ou paralelepípedo) de água em fundo de ar.
- **icons/**  
  Ícones utilizados no launcher (para distinguir visualmente cada ferramenta).

---

## Uso

### Launcher

O ponto de partida é o `launcher.py`. Ele abre uma janela simples com dois botões:

- **Editor de DICOM** – abre o script `dicomrt_editor/main_window.py` em um processo separado usando o interpretador Python.
- **Gerador de CT Phantom** – abre o script `pycubo_generator/PyCuboQA.py` em outro processo.

Execute:
```bash
python launcher.py
```
Depois, clique no botão desejado.

---

### Editor de RTPLAN DICOM

1. No launcher, clique em **Editor de DICOM** (ou diretamente execute `dicomrt_editor/main_window.py`):
   ```bash
   python dicomrt_editor/main_window.py
   ```
2. Na janela do editor:
   - Clique em **“Abrir RTPLAN DICOM”** para selecionar um arquivo `.dcm` que contenha um RTPLAN válido.
   - Abaixo, à esquerda, a **Árvore de Tags DICOM** exibirá cada Data Element no formato `(gggg,eeee) VR Nome Valor`.  
     - Clicar em um item (não‑SQ) preenche os campos de edição (Tag, VR, Name, Value) à direita, permitindo alterar o valor manualmente.
   - À direita, há vários grupos:
     1. **Editor de Tag Selecionada**  
        - Exibe Tag, VR, Name e permite editar o campo “Valor atual” para qualquer Data Element de VR editável.  
        - Clique em **“Salvar Valor”** para atualizar em memória. Para gravar no disco, use “Salvar Como...” no menu “Arquivo”.
     2. **Controles de MLC e Parâmetros**  
        - Seletor de **Modelo MLC** (Agility 5 mm ou MLCi2 10 mm), que ajusta a visualização (espessura).
        - Rótulos que exibem o **ângulo do gantry**, **ângulo do colimador**, **ângulo da mesa**, **MU total** (conforme definido em `BeamMeterset`) e **Cumulative Meterset Weight** (Fraction).
        - Controles de navegação de CP:
          - Combobox **Feixe:** lista todos os beams presentes no RTPLAN, usando `BeamSequence`.
          - Botões **“Anterior CP”** e **“Próximo CP”** para percorrer cada Control Point do beam selecionado.
          - Rótulo **CP: i/j** indica posição atual.
     3. **Control Points (Excel)**  
        - **Exportar CPs para Excel** – exporta todas as informações de cada control point (incluindo posições de MLC/jaws) para um arquivo `.xlsx`, usando `dicom_utils/export_excel.py`.
        - **Importar CPs do Excel** – permite ler uma planilha no mesmo formato e atualizar control points no RTPLAN.
     4. **Visualizador de MLC e Jaws**  
        - Mostra, em um gráfico matplotlib:
          - As lâminas de MLC (retângulos cinza) de acordo com `BeamLimitingDevicePositionSequence` de cada CP.
          - Linhas tracejadas em vermelho para Jaws X (se presente).
          - Linhas tracejadas em azul para Jaws Y (se presente).
        - Ajusta automaticamente as escalas X (–200 a 200 mm) e Y (espessura total / 2 ± posições de jaws).
        - Exibe mensagens de “OBS:” indicando se faltam jaws ou MLC em determinado CP.
   - **Menu “Arquivo”**  
     - **“Salvar Como…”** – grava em disco o RTPLAN modificado.
     - **“Exportar EFS”** – chama `dicom_utils/efs_converter/DCM2EFS.py` para gerar um conjunto de arquivos `.efs` em uma pasta à sua escolha.
   - **Menu “CT”**  
     - **“Atualizar RTPLAN com CT”** – permite apontar para uma pasta contendo DICOMs de TC (por exemplo, um phantom recém‑gerado). O RTPLAN é atualizado em memória para referenciar:
       - `PatientName`, `PatientID`
       - `StudyInstanceUID`, `SeriesInstanceUID`
       - `FrameOfReferenceUID`
       - `SOPInstanceUID` (novo UID gerado)
       - Sequências de referência em `ReferencedStudySequence`, `ReferencedSeriesSequence` e `ReferencedFrameOfReferenceSequence`.
     - Após atualização, a árvore e o visualizador de MLC são recarregados para refletir as mudanças.
   - **Menu “Ajuda”**  
     - **“Repositório no GitHub”** – abre o navegador na página oficial:  
       `https://github.com/a-mariano/QA-RTplan-Editor`.

---

### Gerador de CT Phantom

1. No launcher, clique em **Gerador de CT Phantom** (ou execute diretamente `pycubo_generator/PyCuboQA.py`):
   ```bash
   python pycubo_generator/PyCuboQA.py
   ```
2. A interface em Tkinter permitirá definir:
   - Dimensões (mm) do cubo de água (comprimento, largura, altura).
   - Tamanho de pixel (mm) e espessura de fatia (mm).
   - Gerar um volume onde:
     - O cubo é preenchido com densidade de água (~0 HU).
     - O restante do volume é “ar” (~ –1000 HU).
   - O resultado é exibido em três cortes (axial, coronal, sagital) usando matplotlib embutido.
   - Ao salvar, grava uma série de DICOMs na pasta escolhida, com metadados básicos necessários (PatientName, PatientID, StudyInstanceUID, etc.).
   - Esse CT sintético pode então ser utilizado no Editor de RTPLAN para atualizar referências (menu “CT”).

---

## Componentes Internos

### dicom_utils

Localizado em `dicomrt_editor/dicom_utils/`, contém funções auxiliares para manipulação de RTPLAN:

- **reader.py**  
  - `open_dicom_file(path)` – lê e retorna um objeto `pydicom.Dataset`.
  - `populate_tree(dataset, tree_root)` – percorre `dataset` e adiciona nós à árvore Qt (`QTreeWidgetItem`), armazenando o próprio DataElement em cada item.
  - `get_beams(dataset)` – retorna `dataset.BeamSequence` (lista de beams).
  - `get_control_points(beam)` – retorna `beam.ControlPointSequence` (lista de CPs).
  - `get_bl_seq(cp)` – retorna `cp.BeamLimitingDevicePositionSequence` (lista de posições de lâminas/jaws).
  - `find_mlc_item(bl_seq)` – localiza o item em `bl_seq` cujo `RTBeamLimitingDeviceType` seja “MLCX” ou “MLCY” (primeiro par de lâminas MLC).
  - `get_mlc_positions(mlc_item)` – retorna uma lista com todas as posições das lâminas MLC (vetor de 2 N valores, primeiro metade = folhas esquerdas, segunda metade = folhas direitas).
  - `find_jaw_positions(bl_seq, axis)` – retorna as posições de jaws (X ou Y) obtidas de itens em `bl_seq` cujo `RTBeamLimitingDeviceType` comece com “X” ou “Y”.
  - `save_data_element(elem, new_value)` – atualiza `elem.value`, fazendo conversão de VR quando necessário.
  - `save_dicom_file(dataset, path_out)` – chama `dataset.save_as(path_out)` para gravar.
- **export_excel.py**  
  - `export_cp_to_excel(dataset, path_out)` – percorre todos os beams e CPs, coleta atributos relevantes (controles de lâminas, jaws, MU, Fraction, ângulos) e escreve em planilha `.xlsx` usando `openpyxl`.
  - `import_cp_from_excel(dataset, path_in)` – lê uma planilha `.xlsx` no formato esperado e atualiza `dataset.BeamSequence[i].ControlPointSequence[j]` conforme valores de posições de lâminas/jaws.

### efs_converter

Localizado em `dicomrt_editor/efs_converter/DCM2EFS.py`, contém a lógica para gerar arquivos no formato `.efs` a partir de um RTPLAN DICOM:

- `convert_dcm2efs(input_dcm_path, output_folder)` – usa funções próprias (ou chamadas a utilitários externos) para criar, dentro de `output_folder`, um conjunto de arquivos `.efs` (um por beam ou por control point, conforme desejado).

---

## Licença

Este projeto é distribuído sob a [MIT License](LICENSE).

---

**Agradecimentos**  
Obrigado por usar o **QA-RTplan-Editor**. Caso tenha dúvidas, sugestões ou problemas, por favor abra uma _issue_ no repositório GitHub.