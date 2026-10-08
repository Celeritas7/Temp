# Sample project: BRK-100 assembly tooling

A made-up project for trying DocSearch. **BRK-100** is a motor bracket. It is assembled with five tools:

| Tool ID | Tool | Kind | CAD model |
| --- | --- | --- | --- |
| FX-201 | Locating Fixture | made in-house | `CAD/FX-201_Locating_Fixture.step` |
| PT-301 | Bushing Press Punch | made in-house | `CAD/PT-301_Bushing_Press_Punch.step` |
| GA-401 | Go/No-Go Pin Gauge | made in-house | `CAD/GA-401_Go_No-Go_Pin_Gauge.step` |
| TW-101 | Torque Wrench 2-25 Nm | purchased | — |
| AP-501 | Arbor Press 1 t | purchased | — |

```
BRK-100_Tooling/
├── CAD/                 3 STEP models + tool_models.py (parametric source)
├── Drawings/            BRK-100_Tool_Drawings.pdf (one page per tool)
├── Work_Instructions/   WI-BRK-100-A_Assembly_RevC.docx
├── Tooling/             Tooling_Register.xlsx (register + calibration log)
├── Training/            BRK-100_Operator_Training.pptx
├── Quality/             NCR-0042_Loose_Bushing.txt, Inspection_Log_2026-09.csv
└── Meetings/            2026-09-20_Tooling_Review.md
```

All files use the same tool numbers, so one search finds a tool everywhere it is mentioned.

## Practice searches

Start the website (`python docsearch_web.py`) and set **Folder** to the `samples/BRK-100_Tooling` folder.

| # | Search for | Settings | What you should see |
| --- | --- | --- | --- |
| 1 | `PT-301` | defaults | 8 files: STEP model, drawing, work instruction, register, slides, NCR, meeting notes, CAD script |
| 2 | `PT-301` | only **CAD (STEP)** ticked | the part names inside the STEP model |
| 3 | `9.5 Nm` | defaults | the torque setting in the work instruction, slides, register and inspection log |
| 4 | `NCR-0042` | defaults | the whole story of the loose-bushing problem across 6 files |
| 5 | `FX-20\d` | **Regular expression** | FX-201 *and* the planned FX-202 fixture in the meeting notes |
| 6 | `pin` | **Whole word**, only **PowerPoint** | finds "pin" and "Pin", but not "pins" |
| 7 | `NO-GO` | **Match case**, only **PDF** | the gauge drawing, page 3 |
| 8 | `TW-101` | only **Excel** | the register row, the calibration log, and the inspection log (CSV files count as Excel) |

Click **Open** on a result to open the file in its normal program, or **Show folder** to open the folder it's in.

## Change the tool models

The STEP files are generated from `CAD/tool_models.py`. Every dimension is a named parameter at the top of
that file, for example `FX201["pocket_length"]` or `GA401["nogo_diameter"]`.

```bash
pip install cadquery
python samples/BRK-100_Tooling/CAD/tool_models.py     # rewrites the 3 .step files
```

Open the `.step` files in any CAD program (SolidWorks, Fusion 360, FreeCAD, Onshape, CATIA, NX, Creo).

To rebuild the whole sample project, including the documents:

```bash
pip install cadquery python-docx openpyxl python-pptx reportlab
python samples/make_samples.py
```

The parts, tools, people and records here are fictional. They exist only to demonstrate the search.
