# Zomato Interview KB — V0

First working version of the offline question-KB pipeline.

## Flow

raw_sources.json
-> SQLite source table
-> LLM extraction
-> normalization + classification
-> duplicate protection
-> CSV export

## Run

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python -m src.seed
python -m src.extract
python -m src.export

## Important

The seed file contains development examples from public interview reports.
It is not a complete or guaranteed-current list of Zomato interview questions.

Every question keeps its source URL and reported date.

Next:
1. add more source records
2. add semantic duplicate detection
3. aggregate frequency across independent reports
4. score recency
5. match questions against a JD
6. feed selected questions into the live interviewer
