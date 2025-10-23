
import os, json, time, requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="NCP-ADS Mock Exam + GPU Link", layout="wide")
st.title("🎯 NCP-ADS Mock Exam — Dashboard (GPU Link Ready)")

# Load questions (use bundled 60 first, fallback to sample, or user upload)
default_json = os.path.join(os.path.dirname(__file__), "questions_60.json")
fallback_json = os.path.join(os.path.dirname(__file__), "questions_sample.json")

st.sidebar.header("Load & Options")
uploaded = st.sidebar.file_uploader("Upload questions JSON (optional)", type=["json"])
candidate_name = st.sidebar.text_input("Candidate Name", value="Your Name")
show_exp_default = st.sidebar.checkbox("Show explanations by default", value=True)

# Colab GPU API endpoint
st.sidebar.header("Colab GPU Link")
gpu_api = st.sidebar.text_input("Colab GPU API endpoint", placeholder="https://xxxx.ngrok-free.app/gpu_task")
if st.sidebar.button("🔁 Test GPU Connection"):
    try:
        payload = {"values": [1, 2, 3, 4, 5]}
        r = requests.post(gpu_api, json=payload, timeout=12)
        if r.status_code == 200:
            st.success(f"GPU Response OK → mean={r.json().get('gpu_mean')}")
        else:
            st.error(f"API Error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        st.error(f"Connection failed: {e}")

def load_questions():
    if uploaded:
        return json.load(uploaded)
    if os.path.exists(default_json):
        with open(default_json) as f:
            return json.load(f)
    with open(fallback_json) as f:
        return json.load(f)

qs = load_questions()
df = pd.DataFrame(qs)

# Filters
domains = ["All"] + sorted(df["domain"].unique().tolist())
difficulties = ["All"] + (sorted(df["difficulty"].dropna().unique().tolist()) if "difficulty" in df.columns else [])
sel_domain = st.sidebar.selectbox("Filter by Domain", domains)
sel_diff = st.sidebar.selectbox("Filter by Difficulty", difficulties if difficulties else ["All"])

mask = (df["domain"].isin([sel_domain]) if sel_domain!="All" else df["domain"].notna())
if sel_diff!="All" and "difficulty" in df.columns:
    mask = mask & (df["difficulty"]==sel_diff)
filtered = df[mask]

st.write(f"Loaded **{len(df)}** questions | Showing **{len(filtered)}**")

with st.form("exam_form"):
    answers = {}
    for _, row in filtered.iterrows():
        st.markdown(f"**Q{int(row['id'])}. {row['q']}**  \n"
                    f"A. {row['options'][0]}  \n"
                    f"B. {row['options'][1]}  \n"
                    f"C. {row['options'][2]}  \n"
                    f"D. {row['options'][3]}")
        answers[int(row["id"])] = st.radio(
            f"Your answer for Q{int(row['id'])}", ["A","B","C","D"], index=0, horizontal=True, key=f"q{int(row['id'])}"
        )
        if "difficulty" in row and not pd.isna(row["difficulty"]):
            st.caption(f"Difficulty: {row['difficulty']} • Domain: {row['domain']}")
        st.divider()

    show_exp = st.checkbox("Show explanations after submit", value=show_exp_default)
    submitted = st.form_submit_button("Submit & Score")

rows = []
domain_scores = {}
diff_scores = {}
total_correct = 0

if submitted:
    df_all = df.set_index("id")
    for qid, user_a in answers.items():
        row = df_all.loc[qid]
        is_correct = (user_a == row["answer"])
        total_correct += int(is_correct)
        d = row["domain"]
        domain_scores.setdefault(d, [0,0])
        domain_scores[d][1]+=1
        domain_scores[d][0]+=int(is_correct)
        diff = row.get("difficulty","NA") if "difficulty" in row else "NA"
        diff_scores.setdefault(diff, [0,0])
        diff_scores[diff][1]+=1
        diff_scores[diff][0]+=int(is_correct)
        rows.append({
            "QID": qid, "Domain": d, "Difficulty": diff, "Your": user_a, "Correct": row["answer"],
            "Result": "✅" if is_correct else "❌",
            "Explanation": row["explanation"] if show_exp else ""
        })

    st.success(f"Total Score: {total_correct}/{len(filtered)}  ({(total_correct/len(filtered))*100:.1f}%)")
    st.dataframe(pd.DataFrame(rows).sort_values("QID"), use_container_width=True)

    # Charts
    if domain_scores:
        st.subheader("Domain-wise Accuracy")
        doms = list(domain_scores.keys())
        acc = [v[0]/v[1]*100 for v in domain_scores.values()]
        fig = plt.figure()
        plt.bar(doms, acc)
        plt.ylabel("Accuracy (%)")
        plt.xticks(rotation=30, ha="right")
        st.pyplot(fig)

    if diff_scores:
        st.subheader("Difficulty-wise Accuracy")
        diffs = list(diff_scores.keys())
        acc2 = [v[0]/v[1]*100 for v in diff_scores.values()]
        fig2 = plt.figure()
        plt.bar(diffs, acc2)
        plt.ylabel("Accuracy (%)")
        plt.xticks(rotation=0)
        st.pyplot(fig2)

    # PDF (professional style)
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    from datetime import date

    wrongs = [r for r in rows if r["Result"] == "❌"]
    safe_name = candidate_name.strip().replace(' ', '_') or 'Candidate'
    pdf_name = f"NCP_ADS_WrongAnswer_Review_{safe_name}.pdf"
    pdf_path = pdf_name

    if st.button("📄 Generate Professional Review PDF"):
        c = canvas.Canvas(pdf_path, pagesize=LETTER)
        width, height = LETTER

        c.setFillColor(colors.HexColor('#76B900'))
        c.rect(0, height-60, width, 60, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height-35, "NVIDIA CERTIFIED PROGRAM")
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width-72, height-35, "NCP-ADS MOCK EXAM REVIEW REPORT")

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(72, height-80, f"Candidate: {candidate_name}")
        c.drawRightString(width-72, height-80, f"Date: {date.today().isoformat()}")

        y = height-110
        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, y, "DOMAIN PERFORMANCE SUMMARY")
        y -= 16
        c.setFont("Helvetica", 10)
        total_q = len(filtered)
        overall_acc = (total_correct/total_q)*100 if total_q else 0.0
        for d,(s,t) in domain_scores.items():
            c.drawString(72, y, f"{d}")
            c.drawRightString(width-180, y, f"{s} / {t}")
            c.drawRightString(width-72, y, f"({(s/t)*100:.1f}%)")
            y -= 12
            if y < 96:
                c.showPage(); y = height-72; c.setFont("Helvetica", 10)

        y -= 6
        c.setFont("Helvetica-Bold", 10)
        c.drawString(72, y, f"Overall Accuracy: {overall_acc:.1f}%")
        y -= 18

        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, y, "WRONG ANSWER DETAILS")
        y -= 16
        c.setFont("Helvetica", 10)

        if not wrongs:
            c.drawString(72, y, "Great job! No wrong answers in this session.")
            y -= 12
        else:
            import textwrap as _tw
            for r in wrongs:
                lines = [
                    f"Q{r['QID']} | Domain: {r['Domain']} | Difficulty: {r['Difficulty']}",
                    f"❌ Your Answer: {r['Your']}   |   ✅ Correct: {r['Correct']}",
                    f"Explanation: {r['Explanation']}",
                    "----------------------------------------------------------------"
                ]
                for line in lines:
                    for w in _tw.wrap(line, width=95):
                        c.drawString(72, y, w)
                        y -= 12
                        if y < 72:
                            c.showPage(); y = height-72; c.setFont("Helvetica", 10)
                if y < 84:
                    c.showPage(); y = height-72; c.setFont("Helvetica", 10)

        c.setFont("Helvetica", 8)
        c.drawCentredString(width/2, 40, "Generated by NCP-ADS Mock Exam Dashboard")
        c.save()

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download Professional Review PDF", f, file_name=pdf_name, mime="application/pdf")
