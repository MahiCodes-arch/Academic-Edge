"""Small, explainable model for ranking study urgency."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier

FEATURES=["pending_chapters","days_to_exam","attendance_pct","has_exam_date"]

def _training_data():
    """Build a reproducible teaching set from simple urgency heuristics."""
    rng=np.random.default_rng(17); rows=[]; labels=[]
    for _ in range(900):
        pending=int(rng.integers(0,16))
        has_exam=int(rng.integers(0,2))
        days=int(rng.integers(1,61)) if has_exam else 45
        attendance=int(rng.integers(35,101))
        deadline_pressure=(1.2/(days/7+1)) if has_exam else 0.04
        urgency=pending*(0.18+deadline_pressure)+max(0,75-attendance)*0.045
        urgent=bool(pending and (urgency>=2.1 or (has_exam and days<=5) or attendance<55))
        rows.append([pending,days,attendance,has_exam]); labels.append(int(urgent))
    return np.asarray(rows),np.asarray(labels)

def predict_priority(frame):
    """Add a model score and readable urgency label to subject features."""
    if frame.empty:
        return frame.assign(priority=[],priority_score=[])
    X,y=_training_data()
    model=RandomForestClassifier(n_estimators=120,max_depth=6,random_state=17,class_weight="balanced")
    model.fit(X,y)
    data=frame.copy()
    features=data[FEATURES].fillna(0).to_numpy(dtype=float)
    data["priority_score"]=model.predict_proba(features)[:,1]
    actual_days=data["days_until_exam"] if "days_until_exam" in data else data["days_to_exam"]
    overdue=data["has_exam_date"].astype(bool)&(actual_days<=0)
    near_exam=data["has_exam_date"].astype(bool)&(actual_days<=5)
    data["priority"]=np.where(overdue|near_exam|(data["attendance_pct"]<55),"Urgent",
                       np.where(data["priority_score"]>=0.45,"High","Steady"))
    return data.sort_values(["priority_score","days_to_exam","attendance_pct"],ascending=[False,True,True])
