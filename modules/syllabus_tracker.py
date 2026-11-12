"""Subject and chapter management with progress visualization."""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database.db import subjects,chapters,add_subject,add_chapters,set_chapter,delete_subject,delete_chapter

def _render_list_manager(ss, cc):
    """Offer confirmed removal controls even when a subject has no chapters yet."""
    with st.expander("🧹 Manage your list · remove a subject or chapter"):
        st.caption("A little housekeeping, whenever you need it.")
        remove_kind=st.radio("Choose what to remove",["A whole subject","One chapter"],horizontal=True,key="remove_kind")
        if remove_kind=="A whole subject":
            selected_name=st.selectbox("Subject to remove",ss.name.tolist(),key="remove_subject_choice")
            selected_id=int(ss.loc[ss.name==selected_name,"id"].iloc[0])
            st.warning("This also removes that subject’s attendance total and chapter checklist. Study diary entries are kept and relabeled “General study.”")
            confirmed=st.checkbox(f"Yes, remove {selected_name} and its attendance and chapters",key=f"confirm_subject_{selected_id}")
            if st.button("Remove this subject",key=f"delete_subject_{selected_id}",disabled=not confirmed):
                delete_subject(selected_id); st.success(f"{selected_name} and its attendance and chapters were removed."); st.rerun()
        else:
            selected_name=st.selectbox("Choose a subject",ss.name.tolist(),key="remove_chapter_subject")
            selected_id=int(ss.loc[ss.name==selected_name,"id"].iloc[0])
            options=cc[cc.subject_id==selected_id]
            if options.empty:
                st.info("This subject has no chapters to remove.")
            else:
                chapter_ids=options.id.astype(int).tolist()
                labels={int(r.id):r.title for _,r in options.iterrows()}
                chapter_id=st.selectbox("Chapter to remove",chapter_ids,format_func=lambda value:labels[value],key=f"remove_chapter_choice_{selected_id}")
                confirmed=st.checkbox(f"Yes, remove “{labels[chapter_id]}”",key=f"confirm_chapter_{chapter_id}")
                if st.button("Remove this chapter",key=f"delete_chapter_{chapter_id}",disabled=not confirmed):
                    delete_chapter(int(chapter_id)); st.success("Chapter removed from your checklist."); st.rerun()

def render():
    st.markdown('<div class="page-hero syllabus-hero"><div class="page-icon">📖</div><div><div class="page-kicker">ONE CHAPTER AT A TIME</div><div class="page-heading">Make your progress visible.</div><div class="page-deck">Gather every topic in one place, then give yourself credit as each one is done.</div></div></div>',unsafe_allow_html=True)
    ss=subjects()
    cc=chapters()
    with st.expander("＋ Set up a subject or add chapters",expanded=ss.empty or cc.empty):
        if ss.empty:
            with st.form("new_syllabus_subject"):
                name=st.text_input("Subject name",max_chars=80,placeholder="For example: Psychology"); titles=st.text_area("Chapter names — one per line",placeholder="Foundations\nMemory and learning\nResearch methods")
                if st.form_submit_button("Create my subject",type="primary"):
                    if not name.strip(): st.error("Give your subject a name first.")
                    else:
                        try:
                            add_subject(name); ss=subjects(); sid=int(ss.loc[ss.name==name.strip(),"id"].iloc[0]); add_chapters(sid,titles.splitlines()); st.success("Your subject is ready."); st.rerun()
                        except Exception: st.error("That subject is already on your list.")
        else:
            names=ss.name.tolist(); chosen=st.selectbox("Choose a subject",names); sid=int(ss.loc[ss.name==chosen,"id"].iloc[0])
            text=st.text_area("Chapter names — one per line",key=f"chapters_{sid}",placeholder="Unit 1\nUnit 2\nFinal review")
            if st.button("Add these chapters",key=f"addchap_{sid}",type="primary"):
                add_chapters(sid,text.splitlines()); st.success("Chapters added to your list."); st.rerun()
    ss=subjects(); cc=chapters()
    if ss.empty: st.info("Start with one subject above. You can add chapters now or come back to them later."); return
    _render_list_manager(ss,cc)
    if cc.empty: st.info("Your subjects are ready. Add a few chapter names above and your progress view will appear here."); return
    done=int(cc.is_complete.sum()); total=len(cc)
    progress_side,checklist_side=st.columns([1.05,1])
    with progress_side:
        st.metric("Your overall progress",f"{100*done/total:.0f}%",f"{done} of {total} chapters complete")
        chart=cc.groupby("subject",as_index=False).agg(done=("is_complete","sum"),total=("is_complete","count"))
        chart["progress"]=100*chart.done/chart.total
        chart=chart.sort_values("progress",ascending=True)
        st.subheader("Progress by subject")
        st.caption("Each ring shows completed chapters against those still to do.")
        columns=2; rows=(len(chart)+columns-1)//columns
        specs=[[{"type":"domain"} if row*columns+col<len(chart) else None for col in range(columns)] for row in range(rows)]
        fig=make_subplots(rows=rows,cols=columns,specs=specs,subplot_titles=chart.subject.tolist(),horizontal_spacing=.12,vertical_spacing=.14)
        for index,(_,subject_row) in enumerate(chart.iterrows()):
            row=index//columns+1; col=index%columns+1
            complete=int(subject_row.done); remaining=int(subject_row.total)-complete
            fig.add_trace(go.Pie(labels=["Completed","To do"],values=[complete,remaining],hole=.64,sort=False,direction="clockwise",rotation=270,
                                 marker=dict(colors=["#9b82d1","#e9cad7"],line=dict(color="#ffffff",width=3)),
                                 textinfo="percent",textposition="inside",textfont=dict(color="#443650",size=12),
                                 hovertemplate=f"{subject_row['subject']}<br>%{{label}}: %{{value}} chapters<br>%{{percent}}<extra></extra>",
                                 showlegend=index==0),row=row,col=col)
        fig.update_layout(height=max(290,190*rows),margin=dict(l=8,r=8,t=48,b=32),paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="DM Sans",color="#574c61"),legend=dict(orientation="h",y=-.05,x=.5,xanchor="center"),
                          uniformtext_minsize=10,uniformtext_mode="hide")
        st.plotly_chart(fig,use_container_width=True)
    with checklist_side:
        with st.container(border=True):
            st.markdown('<div class="syllabus-checklist-anchor"></div>',unsafe_allow_html=True)
            st.markdown("### 🐸 The chapter crew")
            st.caption("Tap a character’s chapter when it’s complete. They love a little progress.")
            goofy_characters=["🐸","🐙","🦆","🐼","🦥","🐢","🐣","🦖","🦄","🪿","🦀","🦔"]
            for index,(_,row) in enumerate(cc.iterrows()):
                key=f"chapter_{row.id}"; mascot=goofy_characters[index%len(goofy_characters)]
                val=st.checkbox(f"{mascot}  {row.subject} · {row.title}",value=bool(row.is_complete),key=key)
                if val!=bool(row.is_complete): set_chapter(int(row.id),val); st.rerun()
