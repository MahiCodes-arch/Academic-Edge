"""Small SQLite data layer shared by all four modules."""
from pathlib import Path
import sqlite3
import pandas as pd
from datetime import date

DB_PATH = Path(__file__).resolve().parent / "sem_survivor.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

def connect():
    con=sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with connect() as con: con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

def query(sql, params=()):
    with connect() as con: return pd.read_sql_query(sql,con,params=params)

def execute(sql, params=()):
    with connect() as con:
        cur=con.execute(sql,params); con.commit(); return cur.lastrowid

def subjects(): return query("SELECT * FROM subjects ORDER BY name")
def chapters(subject_id=None):
    sql="SELECT c.*,s.name subject FROM chapters c JOIN subjects s ON s.id=c.subject_id"
    return query(sql+ (" WHERE c.subject_id=?" if subject_id is not None else "")+" ORDER BY s.name,c.id", (() if subject_id is None else (subject_id,)))
def attendance_update(subject_id, present):
    execute("UPDATE subjects SET attendance_total=attendance_total+1, attendance_present=attendance_present+? WHERE id=?",(int(present),subject_id))
def add_subject(name, exam_date=None):
    execute("INSERT INTO subjects(name,exam_date) VALUES(?,?)",(name.strip(),exam_date))
def add_chapters(subject_id, titles):
    with connect() as con:
        con.executemany("INSERT OR IGNORE INTO chapters(subject_id,title) VALUES(?,?)",[(subject_id,t.strip()) for t in titles if t.strip()])
def set_chapter(chapter_id, complete): execute("UPDATE chapters SET is_complete=? WHERE id=?",(int(complete),chapter_id))
def delete_chapter(chapter_id): execute("DELETE FROM chapters WHERE id=?",(chapter_id,))
def delete_subject(subject_id):
    """Remove a subject and its chapters; preserve study time as general study."""
    execute("DELETE FROM subjects WHERE id=?",(subject_id,))
def save_exam(subject_id, exam_date): execute("UPDATE subjects SET exam_date=? WHERE id=?",(exam_date,subject_id))
def add_log(day, subject_id, hours, notes): execute("INSERT INTO study_logs(study_date,subject_id,hours,notes) VALUES(?,?,?,?)",(day,subject_id,hours,notes.strip()))
def logs(since=None):
    sql="SELECT l.*,COALESCE(s.name,'General study') subject FROM study_logs l LEFT JOIN subjects s ON s.id=l.subject_id"
    return query(sql+(" WHERE study_date>=?" if since else "")+" ORDER BY study_date DESC,id DESC",(() if since is None else (since,)))
def get_today_logs(): return query("SELECT COALESCE(s.name,'General study') subject,l.hours,l.notes FROM study_logs l LEFT JOIN subjects s ON s.id=l.subject_id WHERE l.study_date=? ORDER BY l.id DESC",(date.today().isoformat(),))
def get_dashboard_summary():
    ss=subjects(); cc=chapters()
    total=int(ss.attendance_total.sum()) if not ss.empty else 0
    present=int(ss.attendance_present.sum()) if not ss.empty else 0
    today=get_today_logs()
    progress=(cc.groupby("subject",as_index=False).is_complete.mean().assign(progress=lambda d:d.is_complete*100).drop(columns="is_complete") if not cc.empty else pd.DataFrame(columns=["subject","progress"]))
    return {"attendance":100*present/total if total else 0,"syllabus":100*cc.is_complete.mean() if not cc.empty else 0,"today_hours":float(today.hours.sum()) if not today.empty else 0,"subjects":len(ss),"subject_progress":progress}
