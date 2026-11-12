"""Manual attendance entry and bunk calculations."""
import math
import streamlit as st
from database.db import subjects, add_subject, attendance_update

def attendance_status(pct):
    return ("On track", "🌿") if pct>=75 else (("Near the 75% mark", "🌼") if pct>=65 else ("Needs attention", "💗"))

def _open_subject_manager():
    """Use the shared sidebar navigation to open the subject manager."""
    st.session_state.page = "📖  Syllabus"

def render():
    st.markdown('<div class="page-hero attendance-hero"><div class="page-icon">🌷</div><div><div class="page-kicker">SHOW UP, STAY IN CONTROL</div><div class="page-heading">Your attendance, at a glance.</div><div class="page-deck">Every class moves the number. Keep an eye on your cushion before planning a day away.</div></div></div>',unsafe_allow_html=True)
    ss=subjects()
    with st.container(border=True):
        st.markdown('<div class="attendance-add-anchor"></div>',unsafe_allow_html=True)
        heading="Start here · add your first subject" if ss.empty else "＋ Add another subject"
        st.markdown(f"### {heading}")
        st.caption("Type a subject name to begin tracking it.")
        with st.form("add_attendance_subject"):
            input_col,button_col=st.columns([3,1])
            name=input_col.text_input("Subject name",max_chars=80,placeholder="Type a subject, e.g. Biology",label_visibility="collapsed")
            ok=button_col.form_submit_button("＋ Add subject",type="primary",use_container_width=True)
            if ok:
                if not name.strip(): st.error("Type a subject name first.")
                else:
                    try:
                        add_subject(name)
                        st.session_state["attendance_subject_flash"]=f"{name.strip()} is ready to track."
                        st.rerun()
                    except Exception: st.error("That subject is already on your list.")
    flash=st.session_state.pop("attendance_subject_flash",None)
    if flash: st.success(flash)
    if ss.empty: st.info("Your attendance page is ready. Add a subject above, then use one quick check-in to record each class."); return
    note,action=st.columns([3,1])
    with note:
        st.markdown('<div class="attendance-manage-callout"><span class="callout-icon">🧹</span><div><strong>Need to remove a subject or chapter?</strong><br>Open <b>Syllabus → Manage your list</b> to tidy up your subjects.</div></div>',unsafe_allow_html=True)
    with action:
        st.button("Manage my list  →",key="attendance_manage_subjects",on_click=_open_subject_manager,use_container_width=True)
    st.subheader("A quick class check-in")
    st.caption("One small check-in after class keeps every subject up to date.")
    with st.container(border=True):
        with st.form("attendance_checkin"):
            subject_names=ss.name.tolist()
            subject_name=st.selectbox("Which subject was this?",subject_names)
            class_status=st.radio("How did it go?",["🌷 I was present","☁️ I was absent"],horizontal=True)
            submitted=st.form_submit_button("Save class check-in  ✨",type="primary",use_container_width=True)
        if submitted:
            selected_id=int(ss.loc[ss.name==subject_name,"id"].iloc[0])
            attendance_update(selected_id,class_status.startswith("🌷"))
            st.session_state["attendance_flash"]=f"{subject_name}: check-in saved."
            st.rerun()
    flash=st.session_state.pop("attendance_flash",None)
    if flash: st.success(flash)
    st.subheader("Your subject snapshot")
    for _,row in ss.iterrows():
        total=int(row.attendance_total); present=int(row.attendance_present); pct=100*present/total if total else 0
        status,icon=attendance_status(pct)
        with st.container(border=True):
            a,b,c=st.columns([2,1,2]); a.markdown(f"### {row['name']}"); a.caption(f"{present} present · {total-present} absent · {icon} {status}")
            b.metric("Attendance",f"{pct:.1f}%")
            c.metric("Safe absences left",max(0,math.floor(present/0.75-total)) if total else 0,help="Maximum additional absences while keeping attendance at 75% or above")
            st.progress(min(pct/100,1.0),text=f"{pct:.0f}% of your classes attended")
            needed=max(0,math.ceil((0.75*total-present)/0.25)) if total else 0
            if pct<75: st.warning(f"A small reset is possible: attend the next {needed} classes in a row to reach 75%, assuming no more absences.")
            elif total: st.success("You’re above the 75% mark. Keep checking in after each class.")
