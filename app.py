
import os, json, requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="NCP-ADS Mock Exam – Advanced Edition", layout="wide")
st.title("🎯 NCP-ADS Mock Exam — Advanced Edition (GPU Link + Resources)")

def load_questions():
    default72 = os.path.join(os.path.dirname(__file__), "questions_72.json")
    fallback = os.path.join(os.path.dirname(__file__), "questions_sample.json")
    uploaded = st.sidebar.file_uploader("Upload custom questions JSON (optional)", type=["json"])
    if uploaded:
        return json.load(uploaded), "uploaded"
    if os.path.exists(default72):
        with open(default72) as f: return json.load(f), "questions_72.json"
    with open(fallback) as f: return json.load(f), "questions_sample.json"

st.sidebar.header("Options")
candidate_name = st.sidebar.text_input("Candidate Name", value="Your Name")
show_exp_default = st.sidebar.checkbox("Show explanations by default", value=True)

st.sidebar.header("Colab GPU Link")
gpu_api = st.sidebar.text_input("Colab GPU API endpoint", placeholder="https://xxxx.ngrok-free.app/gpu_task")
if st.sidebar.button("🔁 Test GPU Connection"):
    try:
        r = requests.post(gpu_api, json={"values":[1,2,3,4,5]}, timeout=12)
        if r.status_code == 200:
            st.sidebar.success(f"GPU OK → mean={r.json().get('gpu_mean')}")
        else:
            st.sidebar.error(f"API Error {r.status_code}: {r.text[:160]}")
    except Exception as e:
        st.sidebar.error(f"Connection failed: {e}")

tab_exam, tab_resources = st.tabs(["🧮 Exam Dashboard", "📚 Domain Resources"])

with tab_exam:
    qs, source_name = load_questions()
    st.caption(f"Loaded from: **{source_name}** — Total questions: {len(qs)}")
    df = pd.DataFrame(qs)
    domains = ["All"] + sorted(df["domain"].unique().tolist())
    diffs = ["All"] + sorted(df["difficulty"].dropna().unique().tolist())
    sel_domain = st.selectbox("Filter by Domain", domains, index=0)
    sel_diff = st.selectbox("Filter by Difficulty", diffs, index=0)
    mask = (df["domain"].isin([sel_domain]) if sel_domain!="All" else df["domain"].notna())
    if sel_diff!="All":
        mask = mask & (df["difficulty"]==sel_diff)
    filtered = df[mask]
    st.write(f"Showing **{len(filtered)}** questions")

    with st.form("exam_form"):
        answers = {}
        for _, row in filtered.iterrows():
            st.markdown(f"**Q{int(row['id'])}. {row['q']}**  \nA. {row['options'][0]}  \nB. {row['options'][1]}  \nC. {row['options'][2]}  \nD. {row['options'][3]}")
            answers[int(row["id"])] = st.radio(f"Your answer for Q{int(row['id'])}", ["A","B","C","D"], index=0, horizontal=True, key=f"q{int(row['id'])}")
            st.caption(f"Difficulty: {row['difficulty']} • Domain: {row['domain']}")
            st.divider()
        show_exp = st.checkbox("Show explanations after submit", value=show_exp_default)
        submitted = st.form_submit_button("Submit & Score")

    if submitted:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
        from datetime import date
        rows, domain_scores, total_correct = [], {}, 0
        for _, row in df.iterrows():
            user_a = answers.get(row["id"], "A")
            is_correct = (user_a == row["answer"])
            total_correct += int(is_correct)
            d = row["domain"]
            domain_scores.setdefault(d, [0,0]); domain_scores[d][1]+=1; domain_scores[d][0]+=int(is_correct)
            rows.append({"QID": row["id"], "Domain": d, "Your": user_a, "Correct": row["answer"], "Result": "✅" if is_correct else "❌", "Explanation": row["explanation"] if show_exp else ""})
        st.success(f"Total Score: {total_correct}/{len(filtered)}  ({(total_correct/len(filtered))*100:.1f}%)")
        st.dataframe(pd.DataFrame(rows).sort_values("QID"), use_container_width=True)

        if st.button("📄 Generate Professional Review PDF"):
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=LETTER)
            width, height = LETTER
            c.setFillColor(colors.HexColor('#76B900')); c.rect(0, height-60, width, 60, fill=1, stroke=0)
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 16)
            c.drawString(72, height-35, "NVIDIA CERTIFIED PROGRAM")
            c.setFont("Helvetica-Bold", 12); c.drawRightString(width-72, height-35, "NCP-ADS MOCK EXAM REVIEW REPORT")
            c.setFillColor(colors.black); c.setFont("Helvetica", 10)
            c.drawString(72, height-80, f"Candidate: {candidate_name}")
            c.drawRightString(width-72, height-80, f"Date: {date.today().isoformat()}")
            y = height-110
            c.setFont("Helvetica-Bold", 12); c.drawString(72, y, "WRONG ANSWER DETAILS"); y -= 16; c.setFont("Helvetica", 10)
            for r in rows:
                if r["Result"]=="❌":
                    c.drawString(72, y, f"Q{r['QID']} ({r['Domain']}) — Your: {r['Your']} / Correct: {r['Correct']}")
                    y -= 12
                    for line in r["Explanation"].split('. '):
                        c.drawString(72, y, line.strip()); y -= 12
                    y -= 8
                    if y<72: c.showPage(); y=height-72
            c.save(); buffer.seek(0)
            st.download_button("📥 Download Professional Review PDF", data=buffer, file_name=f"NCP_ADS_Review_{candidate_name}.pdf", mime="application/pdf")

with tab_resources:
    st.header("Recommended Learning Resources by Domain")
    links = {
        "Data Preparation and Loading": ["https://docs.rapids.ai/api/cudf/stable","https://docs.nvidia.com/deeplearning/dali","https://developer.nvidia.com/nvtabular"],
        "Advanced GPU Systems": ["https://openucx.readthedocs.io/en/master/","https://github.com/NVIDIA/DALI","https://distributed.dask.org/en/stable/"]
    }
    for d, l in links.items():
        st.subheader(d)
        for u in l: st.markdown(f"- [{u}]({u})")
        st.divider()
