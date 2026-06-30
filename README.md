# TruthLens — AI-Powered Fake News Detection System

An AI-powered fact-verification platform that checks the truthfulness of claims, news headlines, and article URLs in real time — combining a search-grounded Large Language Model with a self-trained Machine Learning classifier that improves from user feedback.

## 🔍 What It Does

Paste any news claim or article link, and TruthLens will:
- Search the live web for current evidence (not just static training data)
- Apply structured, rule-based reasoning to avoid common AI mistakes (like confusing "this was debunked" with "this is true")
- Return a truthfulness score (0–100), verdict, supporting evidence, and an official source
- Compare its verdict against an independently-trained ML model
- Learn from your feedback over time

## 🛠️ Tech Stack

**Backend:** Python, FastAPI  
**AI:** Google Gemini 2.5 Flash with Google Search grounding  
**Machine Learning:** scikit-learn (TF-IDF + Logistic Regression)  
**Data:** Pandas, SQLite  
**Web Scraping:** BeautifulSoup4, requests  
**Frontend:** Python (Streamlit/HTML)

## ⚙️ How It Works

1. **Input** — User submits a claim or URL
2. **Scraping** — If a URL is given, article text is extracted automatically
3. **AI Verification** — Gemini 2.5 Flash runs a 5-step chain-of-thought reasoning process with live Google Search grounding:
   - Claim deconstruction
   - Search query optimization (3 targeted searches)
   - Evidence analysis with negation-trap detection
   - Visual/technical anomaly check
   - Score calibration (0–100)
4. **ML Cross-Check** — A locally-trained scikit-learn classifier gives an independent prediction
5. **Storage & Learning** — Every result is saved; user feedback (correct/incorrect) becomes training data for the ML model

## 🧠 Key Engineering Detail — Negation-Trap Detection

A common failure in AI fact-checkers: treating a fact-checker's article *debunking* a claim as evidence that the claim is *true* (since a credible source "discussed" it). TruthLens explicitly handles this with a rule-based override:

> If a credible source (Reuters, AP, AFP, PolitiFact, etc.) explicitly states a claim is false → verdict is forced to "Likely Fake," regardless of the source's general credibility.

## 📊 Features

- Real-time fact-checking with live web search
- Custom ML classifier trained on accumulated human feedback
- Analytics dashboard — verdict trends, score distribution, topic breakdown
- CSV/Excel data export for further analysis
- Feedback loop for continuous model improvement

## 🚀 Running Locally

```bash
# Clone the repo
git clone https://github.com/abhishek458934-coder/truthlens-fake-news-detector.git
cd truthlens-fake-news-detector

# Install dependencies
pip install -r requirements.txt

# Add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Run the backend
bash start_api.sh

# Run the frontend (in a separate terminal)
bash start_frontend.sh
```

Get a free Gemini API key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## 📁 Project Structure
verifyit-ds/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── routes/               # API endpoints
│   ├── services/
│   │   ├── gemini.py         # AI fact-checking logic
│   │   ├── scraper.py        # URL content extraction
│   │   └── nlp.py            # Text processing
│   ├── db/                   # Database models & operations
│   └── schemas.py            # Data validation
├── frontend/
│   └── app.py                # User interface
└── requirements.txt

## 🎓 About

This project was built as a self-driven academic project for MSc Data Science, exploring the intersection of generative AI reasoning and classical supervised machine learning for real-world misinformation detection.

## 📄 License

This project is for academic and educational purposes.
