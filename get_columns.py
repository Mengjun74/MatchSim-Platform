import pandas as pd
import os

files = ['data/raw/1503_discipline.xlsx', 'data/raw/1503_program_master.xlsx']

with open('columns.txt', 'w') as out:
    for f in files:
        try:
            out.write(f"\n--- {f} ---\n")
            df = pd.read_excel(f, nrows=1)
            out.write(str(df.columns.tolist()) + "\n")
        except Exception as e:
            out.write(f"Error: {e}\n")
