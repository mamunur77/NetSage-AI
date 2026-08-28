# 🚀 Streamlit Deployment Guide — NetSage AI

This guide explains how to set up, run, and deploy the **NetSage AI** dashboard using Streamlit (both locally and on Streamlit Cloud).

---

## Part 1: Local Setup

If you want to run the Streamlit dashboard on your own machine:

### 1. Install Dependencies
Make sure you have installed the required Python packages:
```bash
pip install -r requirements.txt
```
*(This installs `streamlit`, `plotly`, `pandas`, `groq`, and `openpyxl`)*

### 2. Configure Your API Key
To use the **Live Diagnose** page, the app needs your Groq API key. You have three options:

1. **Option A (Recommended):** Add it to your local `.env` file:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
2. **Option B (Streamlit Config):** Create a file at `.streamlit/secrets.toml` and add:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
3. **Option C (Interactive):** Paste your key directly into the password box on the **Live Diagnose** tab in your browser.

### 3. Run the App
Launch the server from the root of your project directory:
```bash
python -m streamlit run app.py
```
This will automatically open your web browser to `http://localhost:8501`.

---

## Part 2: Deploying to Streamlit Cloud (Free Hosting)

Streamlit offers free hosting directly connected to your GitHub repository. Follow these steps to host your NetSage AI project online:

### 1. Push Code to GitHub
Your repository is already initialized and pushed to GitHub:
👉 [https://github.com/mamunur77/packet_tracer_ai_diagnoser](https://github.com/mamunur77/packet_tracer_ai_diagnoser)

*(Ensure your latest modifications to `app.py` and `requirements.txt` are pushed to the remote repository. They are already pushed as of the last commit).*

### 2. Sign In to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click **Connect with GitHub** and log in with your GitHub account.

### 3. Deploy the App
1. Once logged in, click the **New app** button.
2. Fill out the application details:
   - **Repository:** `mamunur77/packet_tracer_ai_diagnoser`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Click the **Advanced settings...** button *before* clicking deploy.

### 4. Configure Advanced Settings (Secrets)
Under the **Secrets** section, paste your Groq API key so the cloud app can access it securely without putting it in your public repository:
```toml
GROQ_API_KEY = "your_actual_groq_api_key_here"
```
4. Click **Save**.
5. Click **Deploy!** 🚀

Streamlit will now spin up a virtual container, install all packages from your `requirements.txt`, and launch your app. It will give you a public URL (e.g., `https://netsage-ai.streamlit.app`) that you can share with your Cisco team or include in your project demo!
