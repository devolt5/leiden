#%%
#
# Transform DIO data from the T3 database
#
# Step 1: Preprocess text.
#         Replaces broken markup, see dio/preprocess.csv
# Step 2: Transform the data using the dio.ebnf grammar.
#         The script shows a summary statistic of how many files were well-formed.
#
# For developing the grammar, this script generates the test file
# 03_test_dio_sco_passau.ini which contains the content as ist comes from the T3 database.
# It includes structural markup (sco, sec, par tags...).
#   This file can be used to develop the dio.ebnf.
#
# The data is XML, that means angle brackets in the inscriptions
# are represented with named entities (&lt; &gt;).
#
#
import csv
from pathlib import Path

PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
    if "__file__" in globals()
    else Path.cwd()
)
DIO_ROOT = PROJECT_ROOT / "parsers" / "dio"

import pandas as pd
import parsers.dio.dioParser as dioParser
from tqdm import tqdm
import re

import importlib
importlib.reload(dioParser)

#%% Load transcriptions

filename = "dio_public_raw.csv"
inputfile = PROJECT_ROOT / "data" / "input" / filename
with inputfile.open(encoding="utf-8-sig", newline="") as file:
    delimiter = csv.Sniffer().sniff(file.readline(), delimiters=",;").delimiter
df = pd.read_csv(inputfile, delimiter=delimiter, encoding="utf-8-sig")
df['case'] = range(1, len(df) + 1)

#%% Preprocess
regs = pd.read_csv(DIO_ROOT / "preprocess.csv", delimiter = ';', keep_default_na=False)
for idx, row in regs.iterrows():
    #df['content'] =  df['content'].str.replace(row['search'], row['replace'], regex=True) # , flags = re.MULTILINE
    pattern = re.compile(row['search'])
    df['content'] = df['content'].apply(lambda x: pattern.sub(row['replace'], x) if isinstance(x, str) else x)

#%% Save test cases for dio sco

tests = "".join(
    f'\nC{row["case"]}: """{str(row["content"]).strip()}"""' for _, row in df.iterrows()
)

outputname = Path(filename).stem
with open(DIO_ROOT / "tests" / f"{outputname}.ini", "w", encoding="utf-8") as file:
    #file.write("[match:sco]\n" + tests)
    file.write("[match:document]\n" + tests)

#%% Build parser

grammarpath = DIO_ROOT / "dio.ebnf"
dioParser.recompile_grammar(str(grammarpath), force=True)
import importlib

importlib.reload(dioParser)

#%% Parse all dio sco

df['error'] = ""
df['parsed'] = ""

for idx, row in tqdm(df.iterrows()):
    try:
        source = row['content'].strip()
        result, errors = dioParser.compile_snippet(source)
        strings = ["letters", "terminator", "space", "binder"]
        # TODO: do we need to list all those tags?
        inline =  ["lno","lin","snt","snr","wtr", "z", "abr","del","cpl","add","insec","lig","b","strong","em","chr","sup","sub","nl","appalpha","appnum","tab","translation"], # some tags added to the EBNF still missing here ...
        df.loc[idx,'parsed'] = result.as_xml(string_tags= strings, inline_tags = inline, indentation=2)
    except Exception as e:
        df.loc[idx, 'error'] = str(e)

# How many are well-formed?
#df['ok'] = df['parsed'].str.startswith("<sco>")
df['ok'] = df['parsed'].str.startswith("<document>")
print(df['ok'].value_counts())

#%% Save result
outputdir = PROJECT_ROOT / "data" / "output"
outputdir.mkdir(parents=True, exist_ok=True)
df.to_csv(outputdir / f"{outputname}.csv", index=False, sep=";")
