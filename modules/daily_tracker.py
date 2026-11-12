"""Daily study session entry and weekly/monthly analytics."""
from datetime import date,timedelta
import plotly.express as px
import streamlit as st
from database.db import subjects,add_log,logs

def pd_dates(series):
    """Convert ISO date text to comparable Python dates."""
    import pandas as pd
    return pd.to_datetime(series).dt.date

def render():
    st.markdown('<div class="page-hero tracker-hero"><div class="page-icon">💗</div><div><div class="page-kicker">A DIARY OF YOUR EFFORT</div><div class="page-heading">Count the time you show up.</div><div class="page-deck">Save a study session, add a note for future-you, and watch your steady days add up.</div></div></div>',unsafe_allow_html=True)
    ss=subjects(); choices={"General study":None}
    choices.update({r["name"]:int(r.id) for _,r in ss.iterrows()})
    with st.form("study_log"):
        col1,col2=st.columns(2); day=col1.date_input("When did you study?",value=date.today(),max_value=date.today())
        subject=col2.selectbox("Which subject was it?",list(choices)); hours=st.number_input("Time well spent (hours)",min_value=0.1,max_value=24.0,value=1.0,step=0.25)
        notes=st.text_input("A note to remember (optional)",max_chars=180,placeholder="Reviewed lecture notes, solved practice questions…")
        if st.form_submit_button("Add to my study diary  ♡",type="primary",use_container_width=True):
            add_log(day.isoformat(),choices[subject],hours,notes); st.success("Saved. Another little step, counted.")
    data=logs()
    if data.empty: st.info("Your diary is waiting for its first entry. Add a session above and your weekly view will bloom here."); return
    today=date.today(); week=data[pd_dates(data.study_date)>=today-timedelta(days=6)]; month=data[pd_dates(data.study_date)>=today-timedelta(days=29)]
    c1,c2,c3=st.columns(3); c1.metric("Hours · last 7 days",f"{week.hours.sum():.1f} h"); c2.metric("Hours · last 30 days",f"{month.hours.sum():.1f} h"); c3.metric("Daily average · 30 days",f"{month.hours.sum()/30:.1f} h")
    st.subheader("Your rhythm, at a glance")
    parsed=data.assign(study_date=pd_dates(data.study_date))
    week_chart=parsed[parsed.study_date>=today-timedelta(days=6)].groupby("study_date",as_index=False).hours.sum().sort_values("study_date")
    month_chart=parsed[parsed.study_date>=today-timedelta(days=29)].groupby("study_date",as_index=False).hours.sum().sort_values("study_date")
    weekly,monthly=st.columns(2)
    with weekly:
        st.caption("A closer look · last 7 days")
        fig=px.bar(week_chart,x="study_date",y="hours",labels={"study_date":"Date","hours":"Hours"},color_discrete_sequence=["#9b82d1"]); fig.update_layout(height=280,margin=dict(l=5,r=5,t=10,b=5)); st.plotly_chart(fig,use_container_width=True)
    with monthly:
        st.caption("The bigger picture · last 30 days")
        fig=px.bar(month_chart,x="study_date",y="hours",labels={"study_date":"Date","hours":"Hours"},color_discrete_sequence=["#d99abb"]); fig.update_layout(height=280,margin=dict(l=5,r=5,t=10,b=5)); st.plotly_chart(fig,use_container_width=True)
    st.subheader("Pages from your study diary"); st.dataframe(data[["study_date","subject","hours","notes"]].head(30),hide_index=True,use_container_width=True)
