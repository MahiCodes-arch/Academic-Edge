"""Exam-aware seven-day study timetable with ML-assisted subject ordering."""
from datetime import date,datetime,time,timedelta
import pandas as pd
import streamlit as st
from database.db import subjects,chapters,save_exam
from ml.priority_model import predict_priority

def _exam_label(exam):
    if exam is None:
        return "Not set"
    return f"Past · {exam:%d %b}" if exam < date.today() else exam.strftime("%d %b")

def _planning_inputs(ss,cc,available,start_time):
    """Create a signature so a saved plan can be refreshed when inputs change."""
    subject_state=tuple((int(r.id),str(r.exam_date or ""),int(r.attendance_present),int(r.attendance_total)) for _,r in ss.iterrows())
    chapter_state=tuple((int(r.id),int(r.is_complete)) for _,r in cc.iterrows())
    return (date.today().isoformat(),float(available),start_time.isoformat(),subject_state,chapter_state)

def _make_timetable(ss,cc,available,start_time,signature):
    """Schedule two short, distinct focus blocks for each unfinished chapter."""
    subject_rows=[]
    pending_by_subject={}
    for _,subject in ss.iterrows():
        rows=cc[cc.subject_id==subject.id] if not cc.empty else pd.DataFrame()
        pending=rows.loc[rows.is_complete==0,"title"].tolist() if not rows.empty else []
        if not pending:
            continue
        exam=pd.to_datetime(subject.exam_date).date() if pd.notna(subject.exam_date) and subject.exam_date else None
        days=(exam-date.today()).days if exam else 45
        total=int(subject.attendance_total)
        attendance=100*int(subject.attendance_present)/total if total else 75
        subject_rows.append({
            "subject":subject["name"],"pending_chapters":len(pending),
            "days_to_exam":max(1,days) if exam else 45,
            "attendance_pct":attendance,"has_exam_date":int(exam is not None),
            "exam_label":_exam_label(exam),"days_until_exam":days if exam else None,
        })
        pending_by_subject[subject["name"]]=pending
    if not subject_rows:
        return {"signature":signature,"no_pending":True,"rows":[],"leftover":0,"pending_chapters":0,"capacity":7*int(available)}

    ranked=predict_priority(pd.DataFrame(subject_rows))
    queues=[]
    for _,row in ranked.iterrows():
        tasks=[]
        for chapter in pending_by_subject[row["subject"]]:
            tasks.append({"focus":f"Learn · {chapter}","chapter":chapter})
            tasks.append({"focus":f"Practice & recall · {chapter}","chapter":chapter})
        queues.append({
            "subject":row["subject"],"priority":row["priority"],
            "exam_label":row["exam_label"],"tasks":tasks,
        })

    plan=[]; start_day=date.today(); slots_per_day=int(available)
    for day_offset in range(7):
        plan_day=start_day+timedelta(days=day_offset)
        for slot in range(slots_per_day):
            selected=None
            for queue in queues:
                if queue["tasks"]:
                    selected=queue
                    task=queue["tasks"].pop(0)
                    break
            if selected is None:
                break
            block_start=datetime.combine(plan_day,start_time)+timedelta(hours=slot)
            focus_end=block_start+timedelta(minutes=50)
            reset_end=block_start+timedelta(hours=1)
            plan.append({
                "Day":plan_day.strftime("%a, %d %b"),
                "Time block":f"{block_start:%I:%M %p}–{focus_end:%I:%M %p} · reset to {reset_end:%I:%M %p}",
                "Subject":selected["subject"],"Focus":task["focus"],
                "Exam":selected["exam_label"],"Priority":selected["priority"],
            })
        if not any(queue["tasks"] for queue in queues):
            break
    leftover=sum(len(queue["tasks"]) for queue in queues)
    pending_chapters=sum(len(titles) for titles in pending_by_subject.values())
    return {"signature":signature,"no_pending":False,"rows":plan,"leftover":leftover,
            "pending_chapters":pending_chapters,"capacity":7*slots_per_day}

def _render_exam_dates(ss):
    """Make missing exam dates explicit and let users clear saved dates."""
    missing=ss.exam_date.isna().any()
    with st.expander("🗓️ Exam dates",expanded=missing):
        st.caption("A saved date helps the planner bring that subject forward as the exam gets closer.")
        for _,row in ss.iterrows():
            name=row["name"]; subject_id=int(row.id)
            col_name,col_date,col_action=st.columns([1.1,2,1])
            col_name.markdown(f"**{name}**")
            if pd.notna(row.exam_date) and row.exam_date:
                current=pd.to_datetime(row.exam_date).date()
                picked=col_date.date_input("Exam date",value=current,key=f"exam_{subject_id}")
                if col_action.button("Save date",key=f"save_exam_{subject_id}",use_container_width=True):
                    save_exam(subject_id,picked.isoformat()); st.rerun()
                if col_action.button("Clear date",key=f"clear_exam_{subject_id}",use_container_width=True):
                    save_exam(subject_id,None); st.rerun()
            else:
                has_exam=col_date.checkbox("Exam date is known",key=f"has_exam_{subject_id}")
                if has_exam:
                    picked=col_date.date_input("Choose exam date",value=date.today(),key=f"new_exam_{subject_id}")
                    col_action.caption("Save to include it")
                    if col_action.button("Save date",key=f"save_new_exam_{subject_id}",type="primary",use_container_width=True):
                        save_exam(subject_id,picked.isoformat()); st.rerun()
                else:
                    col_date.caption("No exam date set · steady review")

def render():
    st.markdown('<div class="page-hero planner-hero"><div class="page-icon">✨</div><div><div class="page-kicker">A LITTLE PLAN, A LOT MORE CLARITY</div><div class="page-heading">Make room for what matters.</div><div class="page-deck">Build a real seven-day timetable from unfinished chapters, exam dates, attendance, and your daily study window.</div></div></div>',unsafe_allow_html=True)
    ss=subjects()
    if ss.empty:
        st.info("First, add your subjects in Attendance or Syllabus. Then your study timetable can take shape here.")
        return
    _render_exam_dates(ss)
    col_hours,col_start=st.columns(2)
    available=col_hours.number_input("Daily study window (hours)",min_value=1,max_value=12,value=3,step=1,help="Each hour is one 50-minute focus block plus a 10-minute reset.")
    start_time=col_start.time_input("Start the first focus block at",value=time(9,0),key="plan_start_time")
    signature=_planning_inputs(ss,chapters(),available,start_time)
    if st.button("✨ Build my 7-day timetable",type="primary",use_container_width=True):
        st.session_state["study_plan_result"]=_make_timetable(ss,chapters(),available,start_time,signature)

    result=st.session_state.get("study_plan_result")
    if result is None:
        st.info("Set any exam dates, choose your daily study window, then build your timetable.")
        return
    if result["signature"]!=signature:
        st.info("Your subjects or planning inputs have changed. Build the timetable again to refresh it.")
        return
    if result["no_pending"]:
        st.success("All tracked chapters are complete — lovely work. Add upcoming chapters in Syllabus when you’re ready.")
        return

    st.subheader("Your next seven days")
    st.caption("Each block has 50 minutes of focused study followed by a 10-minute reset. Chapters get one learn block and one practice-and-recall block.")
    planned=len(result["rows"])
    c1,c2,c3=st.columns(3)
    c1.metric("Chapters to work on",result["pending_chapters"])
    c2.metric("Focus blocks scheduled",planned)
    c3.metric("Open blocks this week",max(0,result["capacity"]-planned))
    st.dataframe(pd.DataFrame(result["rows"]),hide_index=True,use_container_width=True)
    if result["leftover"]:
        st.warning(f"{result['leftover']} focus blocks did not fit into this seven-day view. Build the next timetable after this week to continue.")
    else:
        st.info("Any time left in your daily window stays open for revision, rest, or life outside study. Nothing is padded just to fill the hours.")
    st.caption("Subjects with no exam date are shown as “Not set” and receive steady review. The model helps order subjects; the schedule stays a flexible guide.")
