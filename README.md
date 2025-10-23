
# 🌐 NCP-ADS Mock Exam — Streamlit Cloud + Colab GPU Link

This package contains:
- `app.py` — Streamlit dashboard (deployed on Streamlit Cloud)
- `colab_gpu_server.ipynb` — Colab notebook that starts a **GPU-backed REST API** via Flask + ngrok
- `questions_60.json` — 60 blueprint-aligned questions
- `requirements.txt`, `README.md`

## Deploy on Streamlit Cloud
1. Create a new GitHub repo and push these files.
2. Go to https://share.streamlit.io → **Deploy an app**
3. Set **Main file path** to `app.py`.

## Start the Colab GPU backend
1. Open `colab_gpu_server.ipynb` in Google Colab.
2. Run all cells → copy the printed **Public API endpoint** (e.g., `https://xxxx.ngrok-free.app`).
3. In Streamlit app (sidebar), paste the endpoint into **Colab GPU API endpoint**.
4. Click **Test GPU Connection** — you should see a numeric response.

## Notes
- The demo endpoint `/gpu_task` computes a mean on the GPU using CuPy.
- You can extend the Flask API to expose RAPIDS/cuML operations for advanced labs.
