"""ACADEMIC EDGE: a local, beginner-friendly academic dashboard."""
import streamlit as st
import plotly.express as px
from database.db import init_db, get_dashboard_summary, get_today_logs
from modules import bunk_calculator, syllabus_tracker, study_planner, daily_tracker

st.set_page_config(page_title="ACADEMIC EDGE", page_icon="✿", layout="wide", initial_sidebar_state="expanded")
init_db()
for stylesheet in ("assets/style.css","assets/navigation.css"):
    with open(stylesheet, encoding="utf-8") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

PAGES = {"⌂  Overview": None, "🌷  Attendance": bunk_calculator, "📖  Syllabus": syllabus_tracker,
         "✨  Study Planner": study_planner, "💗  Daily Tracker": daily_tracker}
if "page" not in st.session_state:
    st.session_state.page = "⌂  Overview"

def open_page(destination):
    """Let dashboard cards open a module through the sidebar navigation state."""
    st.session_state.page = destination

with st.sidebar:
    st.markdown('<div class="brand-lockup"><div class="brand-flower">✿</div><div><div class="brand-kicker">YOUR LITTLE STUDY SPACE</div><div class="brand-script">ACADEMIC<br>EDGE</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Plan softly. Make progress. ✨</div>',unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">✦ YOUR STUDY MENU</div>',unsafe_allow_html=True)
    st.caption("Choose a space to explore")
    for index,label in enumerate(PAGES):
        st.button(label,key=f"sidebar_nav_{index}",type="primary" if st.session_state.page==label else "secondary",
                  on_click=open_page,args=(label,),use_container_width=True)
    page=st.session_state.page
    current_page=page.split(maxsplit=1)[-1]
    st.markdown(f'<div class="active-location"><span>NOW OPEN</span><strong>{current_page}</strong></div>',unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="sidebar-footer">A little progress every day adds up <span>🌱</span></div>',unsafe_allow_html=True)

if PAGES[page]:
    PAGES[page].render()
else:
    summary = get_dashboard_summary()
    st.markdown('<div class="welcome-title">A fresh page starts today ✨</div><div class="welcome-subtitle">A little planning, a little progress—and your semester begins to feel lighter.</div>',unsafe_allow_html=True)
    buddies={"🐱 Miso":"Tiny steps still count. You’ve got this!", "🐰 Mochi":"Pick one topic and make it yours today!", "🐸 Pebble":"A little focus goes a long way 🌱"}
    st.markdown("#### Pick a study buddy")
    buddy=st.radio("Choose your study buddy",list(buddies),horizontal=True,key="study_buddy",label_visibility="collapsed")
    stat_cards=[
        ("stat-attendance","🌷","ATTENDANCE",f"{summary['attendance']:.0f}%","Across classes you’ve logged"),
        ("stat-syllabus","📖","SYLLABUS",f"{summary['syllabus']:.0f}%","Chapters completed so far"),
        ("stat-study","☀️","STUDY TODAY",f"{summary['today_hours']:.1f} h","Time you’ve invested today"),
        ("stat-subjects","✧","SUBJECTS",str(summary["subjects"]),"On your semester list"),
    ]
    left_metrics,right_metrics=st.columns(2)
    for column,items in ((left_metrics,stat_cards[:2]),(right_metrics,stat_cards[2:])):
        for style,icon,label,value,note in items:
            with column:
                st.markdown(f'<div class="stat-card {style}"><div class="stat-top"><span class="stat-icon">{icon}</span><span class="stat-label">{label}</span></div><div class="stat-value">{value}</div><div class="stat-note">{note}</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="buddy-card"><span class="buddy-character">{buddy.split()[0]}</span><div><strong>{buddy.split(maxsplit=1)[1]} says...</strong><br>{buddies[buddy]}</div><span class="buddy-sparkle">✦</span></div>',unsafe_allow_html=True)

    st.subheader("Where would you like to start? ✿")
    module_cards=[
        ("🌷  Attendance","Keep an eye on class attendance and safe absences.","🌷  Attendance","STAY ON TRACK","#fbe9f0","#a24f72"),
        ("📖  Syllabus","Tick off chapters and watch your progress grow.","📖  Syllabus","LITTLE BY LITTLE","#e8f2e7","#527a5d"),
        ("✨  Study Planner","Turn exam dates and pending chapters into a study plan.","✨  Study Planner","PLAN YOUR FOCUS","#fff3cf","#8b6b24"),
        ("💗  Daily Tracker","Log a study session and see your weekly rhythm.","💗  Daily Tracker","CELEBRATE PROGRESS","#eee5fc","#70569d"),
    ]
    for row_start in (0,2):
        cols=st.columns(2)
        for col,(title,description,destination,chip,chip_bg,chip_color) in zip(cols,module_cards[row_start:row_start+2]):
            with col:
                with st.container(border=True):
                    st.markdown(f'<span class="module-chip" style="background:{chip_bg};color:{chip_color}">{chip}</span>',unsafe_allow_html=True)
                    st.markdown(f"### {title}")
                    st.write(description)
                    st.button("Let's go  →",key=f"open_{row_start}_{destination}",on_click=open_page,args=(destination,),use_container_width=True)

    left,right=st.columns([1.1,1])
    with left:
        st.subheader("Today's activity 🌷")
        logs=get_today_logs()
        if logs.empty:
            st.info("No study sessions logged today yet. Add one in Daily Tracker to see it here.")
        else:
            st.dataframe(logs[["subject","hours","notes"]], hide_index=True, use_container_width=True)
        st.markdown(f"**{summary['today_hours']:.1f} hours** logged today")
    with right:
        st.subheader("Syllabus snapshot")
        subjects=summary["subject_progress"]
        if subjects.empty:
            st.info("Add subjects and chapters in Syllabus to see your progress here.")
        else:
            fig=px.bar(subjects,x="subject",y="progress",range_y=[0,100],labels={"subject":"Subject","progress":"Complete (%)"},color_discrete_sequence=["#9b82d1"])
            fig.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)

with st.popover("🌷 Quick guide",key="quick_guide",use_container_width=False):
    st.markdown("### Your semester, one step at a time")
    st.markdown("**01 · Attendance**  \nAdd your subjects, then record each class as present or absent.")
    st.markdown("**02 · Syllabus**  \nAdd chapter names and tick them off as you complete them.")
    st.markdown("**03 · Study Planner**  \nSave exam dates, choose your daily study window, and build a seven-day timetable.")
    st.markdown("**04 · Daily Tracker**  \nLog a study session and see your weekly and monthly rhythm.")
    st.caption("Your data stays in the local SQLite database on this computer.")
