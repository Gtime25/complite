from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime, timedelta
import pandas as pd
import os
import shutil
import requests
import json
import hashlib
import jwt
from typing import Optional
from collections import Counter

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

import matplotlib.pyplot as plt
import matplotlib

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
CHROMA_DIR = "chroma_db"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# User storage (in production, use a proper database)
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_jwt_token(username: str) -> str:
    payload = {
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=7)  # 7 days expiry
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("username")
    except:
        return None

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    username = verify_jwt_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username

@app.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...)):
    users = load_users()
    
    if username in users:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    hashed_password = hash_password(password)
    users[username] = {
        "password": hashed_password,
        "created_at": datetime.now().isoformat()
    }
    save_users(users)
    
    token = create_jwt_token(username)
    return {"token": token, "username": username, "message": "User created successfully"}

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    users = load_users()
    
    if username not in users:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    hashed_password = hash_password(password)
    if users[username]["password"] != hashed_password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_jwt_token(username)
    return {"token": token, "username": username, "message": "Login successful"}

@app.get("/verify-token")
async def verify_token(current_user: str = Depends(get_current_user)):
    return {"username": current_user, "valid": True}

# --- Utility ---
def save_versioned_file(file: UploadFile) -> str:
    name, ext = os.path.splitext(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    versioned_path = os.path.join(UPLOAD_DIR, f"{name}_{timestamp}{ext}")
    with open(versioned_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return versioned_path

def send_slack_alerts(alerts, mode="sox"):
    if SLACK_WEBHOOK_URL:
        mode_text = "SOX" if mode == "sox" else "ESG"
        payload = {
            "text": f"*Real-Time {mode_text} Compliance Alerts:*\n" + "\n".join(f"• {a}" for a in alerts)
        }
        try:
            requests.post(SLACK_WEBHOOK_URL, json=payload)
        except:
            pass

def detect_anomalies_df(df: pd.DataFrame, mode="sox"):
    anomalies = []
    
    if mode == "sox":
        # SOX anomaly detection
        if "Risk Rating" in df.columns and "Result" in df.columns:
            failed_low = df[
                (df["Risk Rating"].str.lower() == "low") &
                (df["Result"].str.lower().str.contains("fail"))
            ]
            if not failed_low.empty:
                anomalies.append("Low-risk controls have failed results.")

        if "Risk Rating" in df.columns and "Frequency" in df.columns:
            high_rare = df[
                (df["Risk Rating"].str.lower() == "high") &
                (df["Frequency"].str.lower().str.contains("annual|rare"))
            ]
            if not high_rare.empty:
                anomalies.append("High-risk controls have rare testing frequencies.")

        if "Owner" in df.columns:
            missing_owner = df[df["Owner"].isnull() | df["Owner"].astype(str).str.strip().eq("")]
            if not missing_owner.empty:
                anomalies.append(f"{len(missing_owner)} control(s) have no assigned owner.")

        if "Result" in df.columns:
            missing_result = df[df["Result"].isnull() | df["Result"].astype(str).str.strip().eq("")]
            if not missing_result.empty:
                anomalies.append(f"{len(missing_result)} control(s) have no result recorded.")

        if "Due Date" in df.columns:
            due_dates = pd.to_datetime(df["Due Date"], errors="coerce")
            overdue = due_dates < pd.Timestamp.now()
            if overdue.any():
                anomalies.append(f"{overdue.sum()} control(s) are overdue.")
            if due_dates.isna().sum() > 0:
                anomalies.append(f"{due_dates.isna().sum()} control(s) have invalid or missing due dates.")

        if "Risk Rating" in df.columns and "Frequency" in df.columns:
            high_no_freq = df[
                (df["Risk Rating"].str.lower() == "high") &
                (df["Frequency"].isnull() | df["Frequency"].astype(str).str.strip().eq(""))
            ]
            if not high_no_freq.empty:
                anomalies.append(f"{len(high_no_freq)} high-risk control(s) have no testing frequency set.")

        if "GL Code" in df.columns:
            dupes = df["GL Code"][df["GL Code"].duplicated()]
            if not dupes.empty:
                anomalies.append(f"{len(dupes)} control(s) have duplicate GL Codes.")
    
    elif mode == "esg":
        # ESG anomaly detection
        if "ESG Factor" in df.columns and "Status" in df.columns:
            failed_status = df[
                (df["Status"].str.lower().str.contains("fail"))
            ]
            if not failed_status.empty:
                anomalies.append(f"{len(failed_status)} ESG metric(s) have failed status.")

        if "Value" in df.columns and "Threshold" in df.columns:
            # Convert to numeric, handling any non-numeric values
            df_numeric = df.copy()
            df_numeric["Value"] = pd.to_numeric(df_numeric["Value"], errors="coerce")
            df_numeric["Threshold"] = pd.to_numeric(df_numeric["Threshold"], errors="coerce")
            
            below_threshold = df_numeric[
                (df_numeric["Value"] < df_numeric["Threshold"]) & 
                (df_numeric["Value"].notna()) & 
                (df_numeric["Threshold"].notna())
            ]
            if not below_threshold.empty:
                anomalies.append(f"{len(below_threshold)} ESG metric(s) are below threshold.")

        if "Owner" in df.columns:
            missing_owner = df[df["Owner"].isnull() | df["Owner"].astype(str).str.strip().eq("")]
            if not missing_owner.empty:
                anomalies.append(f"{len(missing_owner)} ESG metric(s) have no assigned owner.")

        if "Status" in df.columns:
            missing_status = df[df["Status"].isnull() | df["Status"].astype(str).str.strip().eq("")]
            if not missing_status.empty:
                anomalies.append(f"{len(missing_status)} ESG metric(s) have no status recorded.")

        if "Due Date" in df.columns:
            due_dates = pd.to_datetime(df["Due Date"], errors="coerce")
            overdue = due_dates < pd.Timestamp.now()
            if overdue.any():
                anomalies.append(f"{overdue.sum()} ESG metric(s) are overdue.")
            if due_dates.isna().sum() > 0:
                anomalies.append(f"{due_dates.isna().sum()} ESG metric(s) have invalid or missing due dates.")

        if "ESG Factor" in df.columns:
            dupes = df["ESG Factor"][df["ESG Factor"].duplicated()]
            if not dupes.empty:
                anomalies.append(f"{len(dupes)} ESG metric(s) have duplicate factors.")

    elif mode == "soc2":
        # SOC 2 anomaly detection
        if "Trust Service Criteria" in df.columns and "Status" in df.columns:
            failed_status = df[
                (df["Status"].str.lower().str.contains("fail"))
            ]
            if not failed_status.empty:
                anomalies.append(f"{len(failed_status)} SOC 2 control(s) have failed status.")

        if "Control Type" in df.columns:
            missing_controls = df[df["Control Type"].isnull() | df["Control Type"].astype(str).str.strip().eq("")]
            if not missing_controls.empty:
                anomalies.append(f"{len(missing_controls)} control(s) have no control type specified.")

        if "Owner" in df.columns:
            missing_owner = df[df["Owner"].isnull() | df["Owner"].astype(str).str.strip().eq("")]
            if not missing_owner.empty:
                anomalies.append(f"{len(missing_owner)} control(s) have no assigned owner.")

        if "Status" in df.columns:
            missing_status = df[df["Status"].isnull() | df["Status"].astype(str).str.strip().eq("")]
            if not missing_status.empty:
                anomalies.append(f"{len(missing_status)} control(s) have no status recorded.")

        if "Last Test Date" in df.columns:
            test_dates = pd.to_datetime(df["Last Test Date"], errors="coerce")
            old_tests = test_dates < (pd.Timestamp.now() - pd.Timedelta(days=90))
            if old_tests.any():
                anomalies.append(f"{old_tests.sum()} control(s) haven't been tested in over 90 days.")
            if test_dates.isna().sum() > 0:
                anomalies.append(f"{test_dates.isna().sum()} control(s) have no test date recorded.")

        if "Trust Service Criteria" in df.columns:
            # Check for controls covering all TSC categories
            tsc_categories = ["CC", "DC", "AI", "PR", "SL"]
            missing_tsc = []
            for tsc in tsc_categories:
                if not df[df["Trust Service Criteria"].str.contains(tsc, na=False, case=False)].empty:
                    continue
                missing_tsc.append(tsc)
            if missing_tsc:
                anomalies.append(f"Missing controls for Trust Service Criteria: {', '.join(missing_tsc)}")

        if "Control ID" in df.columns:
            dupes = df["Control ID"][df["Control ID"].duplicated()]
            if not dupes.empty:
                anomalies.append(f"{len(dupes)} control(s) have duplicate Control IDs.")

    elif mode == "iso27001":
        # ISO 27001 anomaly detection
        if "Status" in df.columns:
            failed = df[df["Status"].str.lower().str.contains("fail|not implemented", na=False)]
            if not failed.empty:
                anomalies.append(f"{len(failed)} controls are failed or not implemented.")
        if "Last Review Date" in df.columns:
            review_dates = pd.to_datetime(df["Last Review Date"], errors="coerce")
            overdue = review_dates < (pd.Timestamp.now() - pd.Timedelta(days=365))
            if overdue.any():
                anomalies.append(f"{overdue.sum()} controls have not been reviewed in over 12 months.")
            if review_dates.isna().sum() > 0:
                anomalies.append(f"{review_dates.isna().sum()} controls have no review date recorded.")
        if "Evidence" in df.columns:
            missing_evidence = df[df["Evidence"].isnull() | df["Evidence"].astype(str).str.strip().eq("")]
            if not missing_evidence.empty:
                anomalies.append(f"{len(missing_evidence)} controls are missing evidence.")
        if "Control Owner" in df.columns:
            missing_owner = df[df["Control Owner"].isnull() | df["Control Owner"].astype(str).str.strip().eq("")]
            if not missing_owner.empty:
                anomalies.append(f"{len(missing_owner)} controls are missing assigned owners.")
        if "Annex A Reference" in df.columns:
            missing_annex = df[df["Annex A Reference"].isnull() | df["Annex A Reference"].astype(str).str.strip().eq("")]
            if not missing_annex.empty:
                anomalies.append(f"{len(missing_annex)} controls are missing Annex A references.")
        if "Control ID" in df.columns:
            dupes = df["Control ID"][df["Control ID"].duplicated()]
            if not dupes.empty:
                anomalies.append(f"{len(dupes)} controls have duplicate Control IDs.")

    return anomalies or ["No anomalies detected."]

# --- Embedding ---
def embed_file(path: str, mode="sox"):
    ext = path.split('.')[-1].lower()
    df = pd.read_csv(path) if ext == "csv" else pd.read_excel(path, engine="openpyxl")
    text = df.to_csv(index=False)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(text)
    documents = [Document(page_content=chunk) for chunk in chunks]
    Chroma.from_documents(
        documents,
        OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY),
        persist_directory=CHROMA_DIR
    )

@app.post("/auto-embed/")
async def auto_embed(file: UploadFile = File(...), mode: str = Form("sox")):
    try:
        file.file.seek(0)
        path = save_versioned_file(file)
        embed_file(path, mode)
        return {"status": "success"}
    except Exception as e:
        print(f"Error in auto-embed for {mode}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Failed to embed {mode.upper()} data: {str(e)}"})

@app.post("/detect-anomalies/")
async def detect_anomalies(file: UploadFile = File(...), mode: str = Form("sox")):
    try:
        ext = file.filename.split('.')[-1].lower()
        df = pd.read_csv(BytesIO(await file.read())) if ext == "csv" else pd.read_excel(BytesIO(await file.read()))
        anomalies = detect_anomalies_df(df, mode)
        return {"anomalies": anomalies}
    except Exception as e:
        print(f"Error in detect-anomalies for {mode}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Failed to detect anomalies for {mode.upper()} data: {str(e)}"})

@app.post("/detect-alerts/")
async def detect_alerts(file: UploadFile = File(...), mode: str = Form("sox")):
    try:
        ext = file.filename.split('.')[-1].lower()
        df = pd.read_csv(BytesIO(await file.read())) if ext == "csv" else pd.read_excel(BytesIO(await file.read()))
        df.columns = [c.strip().lower() for c in df.columns]

        alerts = []

        if mode == "sox":
            # SOX alerts
            if "risk rating" in df.columns and "result" in df.columns:
                failed_critical = df[
                    (df["risk rating"].str.lower().isin(["high", "critical"])) &
                    (df["result"].str.lower().str.contains("fail"))
                ]
                if not failed_critical.empty:
                    alerts.append("High or critical risk controls have failed results.")

            if "risk rating" in df.columns and "due date" in df.columns:
                df["due date"] = pd.to_datetime(df["due date"], errors="coerce")
                overdue = df[
                    (df["risk rating"].str.lower().isin(["high", "critical"])) &
                    (df["due date"] < pd.Timestamp.now())
                ]
                if not overdue.empty:
                    alerts.append("High or critical risk controls are overdue.")

            if "owner" in df.columns:
                missing_owner = df[df["owner"].isnull() | df["owner"].astype(str).str.strip().eq("")]
                if not missing_owner.empty:
                    alerts.append("Some controls are missing assigned owners.")

            if "frequency" in df.columns:
                missing_freq = df[df["frequency"].isnull() | df["frequency"].astype(str).str.strip().eq("")]
                if not missing_freq.empty:
                    alerts.append("Some controls do not have a defined test frequency.")

            if "due date" in df.columns:
                overdue_30 = df[
                    pd.to_datetime(df["due date"], errors="coerce") <
                    pd.Timestamp.now() - pd.Timedelta(days=30)
                ]
                if not overdue_30.empty:
                    alerts.append("Some controls are overdue by more than 30 days.")

        elif mode == "esg":
            # ESG alerts
            if "esg factor" in df.columns and "status" in df.columns:
                failed_status = df[
                    (df["status"].str.lower().str.contains("fail"))
                ]
                if not failed_status.empty:
                    alerts.append(f"{len(failed_status)} ESG metrics have failed status.")

            if "value" in df.columns and "threshold" in df.columns:
                # Convert to numeric, handling any non-numeric values
                df_numeric = df.copy()
                df_numeric["value"] = pd.to_numeric(df_numeric["value"], errors="coerce")
                df_numeric["threshold"] = pd.to_numeric(df_numeric["threshold"], errors="coerce")
                
                below_threshold = df_numeric[
                    (df_numeric["value"] < df_numeric["threshold"]) & 
                    (df_numeric["value"].notna()) & 
                    (df_numeric["threshold"].notna())
                ]
                if not below_threshold.empty:
                    alerts.append(f"{len(below_threshold)} ESG metrics are below threshold.")

            if "owner" in df.columns:
                missing_owner = df[df["owner"].isnull() | df["owner"].astype(str).str.strip().eq("")]
                if not missing_owner.empty:
                    alerts.append("Some ESG metrics are missing assigned owners.")

            if "due date" in df.columns:
                df["due date"] = pd.to_datetime(df["due date"], errors="coerce")
                overdue = df[
                    (df["due date"] < pd.Timestamp.now())
                ]
                if not overdue.empty:
                    alerts.append("Some ESG metrics are overdue.")

            if "due date" in df.columns:
                overdue_30 = df[
                    pd.to_datetime(df["due date"], errors="coerce") <
                    pd.Timestamp.now() - pd.Timedelta(days=30)
                ]
                if not overdue_30.empty:
                    alerts.append("Some ESG metrics are overdue by more than 30 days.")

        elif mode == "soc2":
            # SOC 2 alerts
            if "trust service criteria" in df.columns and "status" in df.columns:
                failed_status = df[
                    (df["status"].str.lower().str.contains("fail"))
                ]
                if not failed_status.empty:
                    alerts.append(f"{len(failed_status)} SOC 2 controls have failed status.")

            if "last test date" in df.columns:
                test_dates = pd.to_datetime(df["last test date"], errors="coerce")
                old_tests = test_dates < (pd.Timestamp.now() - pd.Timedelta(days=90))
                if old_tests.any():
                    alerts.append(f"{old_tests.sum()} controls haven't been tested in over 90 days.")

            if "owner" in df.columns:
                missing_owner = df[df["owner"].isnull() | df["owner"].astype(str).str.strip().eq("")]
                if not missing_owner.empty:
                    alerts.append("Some SOC 2 controls are missing assigned owners.")

            if "trust service criteria" in df.columns:
                # Check for controls covering all TSC categories
                tsc_categories = ["CC", "DC", "AI", "PR", "SL"]
                missing_tsc = []
                for tsc in tsc_categories:
                    if not df[df["trust service criteria"].str.contains(tsc, na=False, case=False)].empty:
                        continue
                    missing_tsc.append(tsc)
                if missing_tsc:
                    alerts.append(f"Missing controls for Trust Service Criteria: {', '.join(missing_tsc)}")

            if "control type" in df.columns:
                missing_controls = df[df["control type"].isnull() | df["control type"].astype(str).str.strip().eq("")]
                if not missing_controls.empty:
                    alerts.append(f"{len(missing_controls)} controls have no control type specified.")

        elif mode == "iso27001":
            # ISO 27001 alerts
            if "Status" in df.columns:
                failed = df[df["Status"].str.lower().str.contains("fail|not implemented", na=False)]
                if not failed.empty:
                    alerts.append(f"{len(failed)} controls are failed or not implemented.")
            if "Last Review Date" in df.columns:
                review_dates = pd.to_datetime(df["Last Review Date"], errors="coerce")
                overdue = review_dates < (pd.Timestamp.now() - pd.Timedelta(days=365))
                if overdue.any():
                    alerts.append(f"{overdue.sum()} controls have not been reviewed in over 12 months.")
                if review_dates.isna().sum() > 0:
                    alerts.append(f"{review_dates.isna().sum()} controls have no review date recorded.")
            if "Evidence" in df.columns:
                missing_evidence = df[df["Evidence"].isnull() | df["Evidence"].astype(str).str.strip().eq("")]
                if not missing_evidence.empty:
                    alerts.append(f"{len(missing_evidence)} controls are missing evidence.")
            if "Control Owner" in df.columns:
                missing_owner = df[df["Control Owner"].isnull() | df["Control Owner"].astype(str).str.strip().eq("")]
                if not missing_owner.empty:
                    alerts.append(f"{len(missing_owner)} controls are missing assigned owners.")
            if "Annex A Reference" in df.columns:
                missing_annex = df[df["Annex A Reference"].isnull() | df["Annex A Reference"].astype(str).str.strip().eq("")]
                if not missing_annex.empty:
                    alerts.append(f"{len(missing_annex)} controls are missing Annex A references.")
            if "Control ID" in df.columns:
                dupes = df["Control ID"][df["Control ID"].duplicated()]
                if not dupes.empty:
                    alerts.append(f"{len(dupes)} controls have duplicate Control IDs.")

        if alerts:
            send_slack_alerts(alerts, mode)

        return {"alerts": alerts or ["No urgent alerts detected."]}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/query/")
async def query_with_memory(file: UploadFile = File(...), prompt: str = Form(...), mode: str = Form("sox")):
    try:
        vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY))
        retriever = vectordb.as_retriever()

        mode_context = "SOX compliance and internal controls" if mode == "sox" else "ESG (Environmental, Social, and Governance) compliance" if mode == "esg" else "SOC 2 (System and Organization Controls) compliance"
        
        template = f"""
        You are a helpful {mode_context} assistant. Use the following extracted content to answer the question.

        {{context}}

        Question: {{question}}
        Answer:"""
        prompt_template = PromptTemplate.from_template(template)
        model = OpenAI(openai_api_key=OPENAI_API_KEY)
        chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt_template
            | model
            | StrOutputParser()
        )
        result = chain.invoke(prompt)
        return {"response": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ask-ai/")
async def ask_ai(file: UploadFile = File(...), prompt: str = Form(...), generate_pdf: bool = Form(...), mode: str = Form("sox")):
    try:
        print(f"Starting ask_ai function for mode: {mode}")
        file.file.seek(0)
        path = save_versioned_file(file)
        ext = path.split('.')[-1].lower()
        df = pd.read_csv(path) if ext == "csv" else pd.read_excel(path)
        preview = df.head(30).to_string(index=False)

        mode_context = (
            "SOX compliance" if mode == "sox" else
            "ESG compliance" if mode == "esg" else
            "SOC 2 compliance" if mode == "soc2" else
            "ISO 27001 Information Security Management"
        )
        
        # Generate default prompt if none provided
        if not prompt.strip():
            default_prompt = f"""
            Provide a comprehensive analysis of this {mode_context} dataset including:
            1. Overall compliance health and key metrics
            2. Critical risks and areas of concern
            3. Patterns and trends in the data
            4. Recommendations for improvement
            5. Executive summary for stakeholders
            
            Focus on actionable insights and prioritize the most important findings.
            """
            prompt = default_prompt
            print("Using default comprehensive analysis prompt")

        print("Generating AI response...")
        ai = OpenAI(openai_api_key=OPENAI_API_KEY)
        response = ai.invoke(f"{prompt}\n\nHere is the preview:\n{preview}")
        
        # Generate additional insights for comprehensive reports
        recommendations = ai.invoke(f"Based on this {mode_context} data, provide specific, actionable improvement recommendations:\n\n" + preview)
        conclusion = ai.invoke(f"Summarize the key executive takeaways and what leadership should focus on from this {mode_context} data:\n\n" + preview)

        if not generate_pdf:
            print("PDF generation disabled, returning response only")
            return {"response": response}

        print("Starting PDF generation...")
        anomalies = detect_anomalies_df(df, mode)

        # Simple PDF Generation without complex charts
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title Page
        elements.append(Paragraph(f"CompLite {mode.upper()} Compliance Report", styles["Title"]))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        elements.append(Paragraph(f"Dataset: {file.filename}", styles["Normal"]))
        elements.append(PageBreak())

        # Executive Summary
        elements.append(Paragraph("Executive Summary", styles["Heading1"]))
        
        # Calculate key metrics
        total_items = len(df)
        if mode == "sox":
            failed_count = len(df[df["Result"].str.lower().str.contains("fail", na=False)]) if "Result" in df.columns else 0
            overdue_count = len(df[pd.to_datetime(df["Due Date"], errors="coerce") < pd.Timestamp.now()]) if "Due Date" in df.columns else 0
            missing_owner = len(df[df["Owner"].isnull() | df["Owner"].astype(str).str.strip().eq("")]) if "Owner" in df.columns else 0
        elif mode == "esg":
            failed_count = len(df[df["Status"].str.lower().str.contains("fail", na=False)]) if "Status" in df.columns else 0
            overdue_count = len(df[pd.to_datetime(df["Due Date"], errors="coerce") < pd.Timestamp.now()]) if "Due Date" in df.columns else 0
            missing_owner = len(df[df["Owner"].isnull() | df["Owner"].astype(str).str.strip().eq("")]) if "Owner" in df.columns else 0
        elif mode == "soc2":
            failed_count = len(df[df["Status"].str.lower().str.contains("fail", na=False)]) if "Status" in df.columns else 0
            overdue_count = len(df[pd.to_datetime(df["Last Test Date"], errors="coerce") < (pd.Timestamp.now() - pd.Timedelta(days=90))]) if "Last Test Date" in df.columns else 0
            missing_owner = len(df[df["Owner"].isnull() | df["Owner"].astype(str).str.strip().eq("")]) if "Owner" in df.columns else 0
        else:  # iso27001
            failed_count = len(df[df["Status"].str.lower().str.contains("fail|not implemented", na=False)]) if "Status" in df.columns else 0
            overdue_count = len(df[pd.to_datetime(df["Last Review Date"], errors="coerce") < (pd.Timestamp.now() - pd.Timedelta(days=365))]) if "Last Review Date" in df.columns else 0
            missing_owner = len(df[df["Control Owner"].isnull() | df["Control Owner"].astype(str).str.strip().eq("")]) if "Control Owner" in df.columns else 0
            missing_evidence = len(df[df["Evidence"].isnull() | df["Evidence"].astype(str).str.strip().eq("")]) if "Evidence" in df.columns else 0
            missing_annex = len(df[df["Annex A Reference"].isnull() | df["Annex A Reference"].astype(str).str.strip().eq("")]) if "Annex A Reference" in df.columns else 0

        failed_pct = (failed_count / total_items * 100) if total_items > 0 else 0
        overdue_pct = (overdue_count / total_items * 100) if total_items > 0 else 0
        missing_owner_pct = (missing_owner / total_items * 100) if total_items > 0 else 0

        # Calculate compliance score
        if mode == "iso27001":
            compliance_score = max(0, 100 - failed_pct - overdue_pct - missing_owner_pct - (missing_evidence / total_items * 100 if total_items > 0 else 0) - (missing_annex / total_items * 100 if total_items > 0 else 0))
        else:
            compliance_score = max(0, 100 - failed_pct - overdue_pct - missing_owner_pct)

        # Key Metrics Table
        elements.append(Paragraph("Key Compliance Metrics", styles["Heading2"]))
        
        metrics_data = [
            ["Metric", "Count", "Percentage"],
            ["Total Items", str(total_items), "100%"],
            ["Failed/Not Implemented", str(failed_count), f"{failed_pct:.1f}%"],
            ["Overdue Items", str(overdue_count), f"{overdue_pct:.1f}%"],
            ["Missing Owners", str(missing_owner), f"{missing_owner_pct:.1f}%"],
            ["Overall Compliance Score", f"{compliance_score:.1f}%", ""]
        ]
        
        if mode == "iso27001":
            metrics_data.insert(4, ["Missing Evidence", str(missing_evidence), f"{(missing_evidence / total_items * 100) if total_items > 0 else 0:.1f}%"])
            metrics_data.insert(5, ["Missing Annex A References", str(missing_annex), f"{(missing_annex / total_items * 100) if total_items > 0 else 0:.1f}%"])
        
        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 20))

        # AI Analysis
        elements.append(Paragraph("AI Analysis", styles["Heading2"]))
        elements.append(Paragraph(response, styles["Normal"]))
        elements.append(PageBreak())

        # Generate and add charts
        print("Generating charts...")
        charts = create_compliance_charts(df, mode, compliance_score, failed_pct, overdue_pct, missing_owner_pct)
        
        if charts:
            elements.append(Paragraph("Visual Analytics", styles["Heading1"]))
            
            for chart_name, chart_buffer in charts:
                if chart_name == 'compliance_score':
                    elements.append(Paragraph("Compliance Score Breakdown", styles["Heading2"]))
                elif chart_name == 'risk_distribution':
                    elements.append(Paragraph("Risk Rating Distribution", styles["Heading2"]))
                elif chart_name == 'owner_performance':
                    elements.append(Paragraph("Control Distribution by Owner", styles["Heading2"]))
                elif chart_name == 'trend_analysis':
                    elements.append(Paragraph("Overdue Items Trend Analysis", styles["Heading2"]))
                
                elements.append(Spacer(1, 12))
                
                # Convert chart to ReportLab image
                from reportlab.platypus import Image
                chart_img = Image(chart_buffer)
                chart_img.drawHeight = 250
                chart_img.drawWidth = 450
                elements.append(chart_img)
                elements.append(Spacer(1, 12))
            
            elements.append(PageBreak())

        # Top Issues Section
        elements.append(Paragraph("Critical Issues Requiring Attention", styles["Heading1"]))
        
        # Identify problematic controls
        problematic_controls = []
        
        if mode == "sox":
            desc_col = "Control Description" if "Control Description" in df.columns else "Description"
            risk_col = "Risk Rating"
            status_col = "Result"
            
            # High risk controls
            high_risk = df[df[risk_col].str.lower().str.contains("high", na=False)]
            for _, control in high_risk.iterrows():
                problematic_controls.append({
                    'name': control.get(desc_col, 'Unnamed Control'),
                    'risk': control.get(risk_col, 'Unknown'),
                    'owner': control.get('Owner', 'Unknown'),
                    'status': control.get(status_col, 'Unknown'),
                    'type': 'High Risk'
                })
            
            # Failed controls
            failed = df[df[status_col].str.lower().str.contains("fail", na=False)]
            for _, control in failed.iterrows():
                problematic_controls.append({
                    'name': control.get(desc_col, 'Unnamed Control'),
                    'risk': control.get(risk_col, 'Unknown'),
                    'owner': control.get('Owner', 'Unknown'),
                    'status': control.get(status_col, 'Unknown'),
                    'type': 'Failed'
                })
                
        elif mode == "esg":
            desc_col = "Metric" if "Metric" in df.columns else "Description"
            risk_col = "ESG Factor"
            status_col = "Status"
            
            # Failed ESG metrics
            failed = df[df[status_col].str.lower().str.contains("fail", na=False)]
            for _, control in failed.iterrows():
                problematic_controls.append({
                    'name': control.get(desc_col, 'Unnamed Metric'),
                    'risk': control.get(risk_col, 'Unknown'),
                    'owner': control.get('Owner', 'Unknown'),
                    'status': control.get(status_col, 'Unknown'),
                    'type': 'Failed'
                })
                
        elif mode == "soc2":
            desc_col = "Control Description" if "Control Description" in df.columns else "Description"
            risk_col = "Trust Service Criteria"
            status_col = "Status"
            
            # Failed SOC 2 controls
            failed = df[df[status_col].str.lower().str.contains("fail", na=False)]
            for _, control in failed.iterrows():
                problematic_controls.append({
                    'name': control.get(desc_col, 'Unnamed Control'),
                    'risk': control.get(risk_col, 'Unknown'),
                    'owner': control.get('Owner', 'Unknown'),
                    'status': control.get(status_col, 'Unknown'),
                    'type': 'Failed'
                })
                
        else:  # iso27001
            desc_col = "Control Description" if "Control Description" in df.columns else "Description"
            risk_col = "Status"
            status_col = "Status"
            
            # Failed ISO 27001 controls
            failed = df[df[status_col].str.lower().str.contains("fail|not implemented", na=False)]
            for _, control in failed.iterrows():
                problematic_controls.append({
                    'name': control.get(desc_col, 'Unnamed Control'),
                    'risk': control.get(risk_col, 'Unknown'),
                    'owner': control.get('Control Owner', 'Unknown'),
                    'status': control.get(status_col, 'Unknown'),
                    'type': 'Failed'
                })

        # Add overdue controls
        if "Due Date" in df.columns:
            overdue = df[pd.to_datetime(df["Due Date"], errors="coerce") < pd.Timestamp.now()]
            for _, control in overdue.iterrows():
                problematic_controls.append({
                    'name': control.get(desc_col, 'Unnamed Control'),
                    'risk': control.get(risk_col, 'Unknown'),
                    'owner': control.get('Owner', 'Unknown'),
                    'status': control.get(status_col, 'Unknown'),
                    'type': 'Overdue'
                })

        # Remove duplicates and limit to top 10
        unique_controls = []
        seen_names = set()
        for control in problematic_controls:
            if control['name'] not in seen_names and len(unique_controls) < 10:
                unique_controls.append(control)
                seen_names.add(control['name'])

        # Create issues table
        if unique_controls:
            issues_data = [["Issue", "Type", "Risk Level", "Owner", "Status"]]
            for control in unique_controls:
                issues_data.append([
                    control['name'][:50] + "..." if len(control['name']) > 50 else control['name'],
                    control['type'],
                    control['risk'],
                    control['owner'],
                    control['status']
                ])
            
            issues_table = Table(issues_data)
            issues_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            elements.append(issues_table)
        else:
            elements.append(Paragraph("No critical issues identified.", styles["Normal"]))
        
        elements.append(PageBreak())

        # AI Recommendations
        elements.append(Paragraph("AI Recommendations", styles["Heading1"]))
        elements.append(Paragraph(recommendations, styles["Normal"]))
        elements.append(PageBreak())

        # Anomaly Detection
        if anomalies:
            elements.append(Paragraph("Anomaly Detection", styles["Heading1"]))
            for a in anomalies:
                elements.append(Paragraph(f"• {a}", styles["Normal"]))
            elements.append(PageBreak())

        # Conclusion
        elements.append(Paragraph("Executive Conclusion", styles["Heading1"]))
        elements.append(Paragraph(conclusion, styles["Normal"]))

        print("Building PDF document...")
        doc.build(elements)
        buffer.seek(0)
        print("PDF generation completed successfully")
        print(f"PDF buffer size: {len(buffer.getvalue())} bytes")
        print(f"Returning StreamingResponse for PDF download")
        return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={mode}_compliance_report.pdf"})

    except Exception as e:
        print(f"Error in ask_ai: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/generate-evidence/")
async def generate_evidence(mode: str = Form("sox")):
    try:
        vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY))
        retriever = vectordb.as_retriever()
        
        if mode == "sox":
            query = "Show me all high-risk controls with failed results and overdue dates."
        elif mode == "esg":
            query = "Show me all critical ESG metrics with failed status and overdue dates."
        elif mode == "soc2":
            query = "Show me all SOC 2 controls with failed status and missing Trust Service Criteria coverage."
        else:  # iso27001
            query = "Show me all ISO 27001 controls with failed status and missing Annex A references."
            
        docs = retriever.get_relevant_documents(query)
        text = "\n---\n".join([doc.page_content for doc in docs])

        mode_context = "SOX control" if mode == "sox" else "ESG compliance" if mode == "esg" else "SOC 2 control" if mode == "soc2" else "ISO 27001 control"
        ai = OpenAI(openai_api_key=OPENAI_API_KEY)
        summary = ai.invoke(f"Summarize the following {mode_context} data into an audit evidence package:\n{text}")

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [Paragraph(f"{mode.upper()} Audit Evidence Package", styles["Title"]),
                    Spacer(1, 12),
                    Paragraph(summary, styles["Normal"])]
        doc.build(elements)
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={mode}_evidence.pdf"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/send-slack-alert/")
async def send_slack_alert(payload: dict):
    import requests
    import os

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    alerts = payload.get("alerts", [])
    mode = payload.get("mode", "sox")

    if not webhook_url:
        return JSONResponse(status_code=500, content={"error": "Missing Slack webhook URL"})

    if not alerts:
        return {"status": "no alerts to send"}

    mode_text = "SOX" if mode == "sox" else "ESG"
    message = f"*Real-Time {mode_text} Compliance Alerts:*\n" + "\n".join([f"• {alert}" for alert in alerts])
    data = {"text": message}

    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code != 200:
            raise Exception(f"Slack returned status {response.status_code}")
        return {"status": "sent"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/analytics/trends/")
async def analytics_trends(file: UploadFile = File(...), mode: str = Form("sox")):
    """
    Returns time-series trends for pass/fail, overdue, missing evidence, etc. for the selected module.
    """
    ext = file.filename.split('.')[-1].lower()
    df = pd.read_csv(BytesIO(await file.read())) if ext == "csv" else pd.read_excel(BytesIO(await file.read()))
    trends = {}
    if mode == "sox":
        if "Due Date" in df.columns:
            df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
            df["Due Month"] = df["Due Date"].dt.to_period('M')
            overdue_by_month = df[df["Due Date"] < pd.Timestamp.now()].groupby("Due Month").size().to_dict()
            trends["overdue_by_month"] = {str(k): v for k, v in overdue_by_month.items()}
        if "Result" in df.columns and "Due Date" in df.columns:
            df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
            df["Due Month"] = df["Due Date"].dt.to_period('M')
            fail_by_month = df[df["Result"].str.lower().str.contains("fail", na=False)].groupby("Due Month").size().to_dict()
            trends["fail_by_month"] = {str(k): v for k, v in fail_by_month.items()}
    elif mode == "esg":
        if "Due Date" in df.columns:
            df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
            df["Due Month"] = df["Due Date"].dt.to_period('M')
            overdue_by_month = df[df["Due Date"] < pd.Timestamp.now()].groupby("Due Month").size().to_dict()
            trends["overdue_by_month"] = {str(k): v for k, v in overdue_by_month.items()}
        if "Status" in df.columns and "Due Date" in df.columns:
            df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
            df["Due Month"] = df["Due Date"].dt.to_period('M')
            fail_by_month = df[df["Status"].str.lower().str.contains("fail", na=False)].groupby("Due Month").size().to_dict()
            trends["fail_by_month"] = {str(k): v for k, v in fail_by_month.items()}
    elif mode == "soc2":
        if "Last Test Date" in df.columns:
            df["Last Test Date"] = pd.to_datetime(df["Last Test Date"], errors="coerce")
            df["Test Month"] = df["Last Test Date"].dt.to_period('M')
            overdue_by_month = df[df["Last Test Date"] < (pd.Timestamp.now() - pd.Timedelta(days=90))].groupby("Test Month").size().to_dict()
            trends["overdue_by_month"] = {str(k): v for k, v in overdue_by_month.items()}
        if "Status" in df.columns and "Last Test Date" in df.columns:
            df["Last Test Date"] = pd.to_datetime(df["Last Test Date"], errors="coerce")
            df["Test Month"] = df["Last Test Date"].dt.to_period('M')
            fail_by_month = df[df["Status"].str.lower().str.contains("fail", na=False)].groupby("Test Month").size().to_dict()
            trends["fail_by_month"] = {str(k): v for k, v in fail_by_month.items()}
    elif mode == "iso27001":
        if "Last Review Date" in df.columns:
            df["Last Review Date"] = pd.to_datetime(df["Last Review Date"], errors="coerce")
            df["Review Month"] = df["Last Review Date"].dt.to_period('M')
            overdue_by_month = df[df["Last Review Date"] < (pd.Timestamp.now() - pd.Timedelta(days=365))].groupby("Review Month").size().to_dict()
            trends["overdue_by_month"] = {str(k): v for k, v in overdue_by_month.items()}
        if "Status" in df.columns and "Last Review Date" in df.columns:
            df["Last Review Date"] = pd.to_datetime(df["Last Review Date"], errors="coerce")
            df["Review Month"] = df["Last Review Date"].dt.to_period('M')
            fail_by_month = df[df["Status"].str.lower().str.contains("fail|not implemented", na=False)].groupby("Review Month").size().to_dict()
            trends["fail_by_month"] = {str(k): v for k, v in fail_by_month.items()}
    return {"trends": trends}

@app.post("/analytics/owner-performance/")
async def analytics_owner_performance(file: UploadFile = File(...), mode: str = Form("sox")):
    """
    Returns aggregated stats per owner for the selected module.
    """
    ext = file.filename.split('.')[-1].lower()
    df = pd.read_csv(BytesIO(await file.read())) if ext == "csv" else pd.read_excel(BytesIO(await file.read()))
    owner_stats = {}
    if mode == "sox":
        if "Owner" in df.columns and "Result" in df.columns:
            for owner, group in df.groupby("Owner"):
                total = len(group)
                failed = group["Result"].str.lower().str.contains("fail", na=False).sum()
                overdue = 0
                if "Due Date" in group.columns:
                    due_dates = pd.to_datetime(group["Due Date"], errors="coerce")
                    overdue = (due_dates < pd.Timestamp.now()).sum()
                owner_stats[owner] = {"total": total, "failed": int(failed), "overdue": int(overdue)}
    elif mode == "esg":
        if "Owner" in df.columns and "Status" in df.columns:
            for owner, group in df.groupby("Owner"):
                total = len(group)
                failed = group["Status"].str.lower().str.contains("fail", na=False).sum()
                overdue = 0
                if "Due Date" in group.columns:
                    due_dates = pd.to_datetime(group["Due Date"], errors="coerce")
                    overdue = (due_dates < pd.Timestamp.now()).sum()
                owner_stats[owner] = {"total": total, "failed": int(failed), "overdue": int(overdue)}
    elif mode == "soc2":
        if "Owner" in df.columns and "Status" in df.columns:
            for owner, group in df.groupby("Owner"):
                total = len(group)
                failed = group["Status"].str.lower().str.contains("fail", na=False).sum()
                overdue = 0
                if "Last Test Date" in group.columns:
                    test_dates = pd.to_datetime(group["Last Test Date"], errors="coerce")
                    overdue = (test_dates < (pd.Timestamp.now() - pd.Timedelta(days=90))).sum()
                owner_stats[owner] = {"total": total, "failed": int(failed), "overdue": int(overdue)}
    elif mode == "iso27001":
        if "Control Owner" in df.columns and "Status" in df.columns:
            for owner, group in df.groupby("Control Owner"):
                total = len(group)
                failed = group["Status"].str.lower().str.contains("fail|not implemented", na=False).sum()
                overdue = 0
                if "Last Review Date" in group.columns:
                    review_dates = pd.to_datetime(group["Last Review Date"], errors="coerce")
                    overdue = (review_dates < (pd.Timestamp.now() - pd.Timedelta(days=365))).sum()
                owner_stats[owner] = {"total": total, "failed": int(failed), "overdue": int(overdue)}
    return {"owner_performance": owner_stats}

@app.post("/analytics/benchmarks/")
async def analytics_benchmarks(file: UploadFile = File(...), mode: str = Form("sox")):
    """
    Returns static/dynamic industry benchmark data (placeholder for now).
    """
    return {"benchmarks": {"industry_avg_overdue": 5, "industry_avg_failed": 3}}

@app.post("/analytics/root-cause/")
async def analytics_root_cause(file: UploadFile = File(...), mode: str = Form("sox")):
    """
    Returns AI clustering/explanation of failures (placeholder for now).
    """
    return {"root_cause": "Most failures are due to missing evidence in IT controls."}

@app.post("/analytics/heatmap/")
async def analytics_heatmap(file: UploadFile = File(...), mode: str = Form("sox")):
    """
    Returns risk vs. frequency or coverage heatmap data based on the uploaded dataset.
    """
    try:
        ext = file.filename.split('.')[-1].lower()
        df = pd.read_csv(BytesIO(await file.read())) if ext == "csv" else pd.read_excel(BytesIO(await file.read()))
        
        heatmap_data = {}
        
        if mode == "sox":
            if "Risk Rating" in df.columns and "Frequency" in df.columns:
                # Create risk vs frequency heatmap
                risk_freq_data = df.groupby(['Risk Rating', 'Frequency']).size().unstack(fill_value=0)
                heatmap_data = risk_freq_data.to_dict()
            elif "Risk Rating" in df.columns and "Result" in df.columns:
                # Create risk vs result heatmap
                risk_result_data = df.groupby(['Risk Rating', 'Result']).size().unstack(fill_value=0)
                heatmap_data = risk_result_data.to_dict()
            else:
                # Fallback to basic risk distribution
                if "Risk Rating" in df.columns:
                    risk_dist = df['Risk Rating'].value_counts().to_dict()
                    heatmap_data = {"Risk Distribution": risk_dist}
                
        elif mode == "esg":
            if "ESG Factor" in df.columns and "Status" in df.columns:
                # Create ESG factor vs status heatmap
                esg_status_data = df.groupby(['ESG Factor', 'Status']).size().unstack(fill_value=0)
                heatmap_data = esg_status_data.to_dict()
            elif "ESG Factor" in df.columns and "Metric" in df.columns:
                # Create ESG factor vs metric count heatmap
                esg_metric_data = df.groupby(['ESG Factor', 'Metric']).size().unstack(fill_value=0)
                heatmap_data = esg_metric_data.to_dict()
            else:
                # Fallback to ESG factor distribution
                if "ESG Factor" in df.columns:
                    esg_dist = df['ESG Factor'].value_counts().to_dict()
                    heatmap_data = {"ESG Factor Distribution": esg_dist}
                    
        elif mode == "soc2":
            if "Trust Service Criteria" in df.columns and "Status" in df.columns:
                # Create TSC vs status heatmap
                tsc_status_data = df.groupby(['Trust Service Criteria', 'Status']).size().unstack(fill_value=0)
                heatmap_data = tsc_status_data.to_dict()
            elif "Trust Service Criteria" in df.columns and "Control Type" in df.columns:
                # Create TSC vs control type heatmap
                tsc_type_data = df.groupby(['Trust Service Criteria', 'Control Type']).size().unstack(fill_value=0)
                heatmap_data = tsc_type_data.to_dict()
            else:
                # Fallback to TSC distribution
                if "Trust Service Criteria" in df.columns:
                    tsc_dist = df['Trust Service Criteria'].value_counts().to_dict()
                    heatmap_data = {"Trust Service Criteria Distribution": tsc_dist}
                    
        elif mode == "iso27001":
            if "Status" in df.columns and "Control ID" in df.columns:
                # Create status vs control ID pattern heatmap
                # Extract first part of control ID for grouping
                df['Control Category'] = df['Control ID'].str.extract(r'([A-Z]+)', expand=False)
                if 'Control Category' in df.columns:
                    status_category_data = df.groupby(['Status', 'Control Category']).size().unstack(fill_value=0)
                    heatmap_data = status_category_data.to_dict()
            elif "Status" in df.columns and "Annex A Reference" in df.columns:
                # Create status vs annex reference heatmap
                status_annex_data = df.groupby(['Status', 'Annex A Reference']).size().unstack(fill_value=0)
                heatmap_data = status_annex_data.to_dict()
            else:
                # Fallback to status distribution
                if "Status" in df.columns:
                    status_dist = df['Status'].value_counts().to_dict()
                    heatmap_data = {"Status Distribution": status_dist}
        
        # If no meaningful heatmap data could be generated, provide a basic distribution
        if not heatmap_data:
            # Try to find any categorical columns for basic distribution
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) >= 2:
                col1, col2 = categorical_cols[:2]
                basic_data = df.groupby([col1, col2]).size().unstack(fill_value=0)
                heatmap_data = basic_data.to_dict()
            else:
                # Last resort - return empty heatmap
                heatmap_data = {"No Data": {"No Categories": 0}}
        
        return {"heatmap": heatmap_data}
        
    except Exception as e:
        print(f"Error generating heatmap: {e}")
        return {"heatmap": {"Error": {"Could not generate": 0}}}

@app.post("/analytics/cross-framework/")
async def analytics_cross_framework(file: UploadFile = File(...), mode: str = Form("sox")):
    """
    Returns cross-framework mapping/overlap/gap analysis (placeholder for now).
    """
    return {"cross_framework": {"sox_iso_overlap": 12, "soc2_iso_overlap": 8}}

def create_compliance_charts(df, mode, compliance_score, failed_pct, overdue_pct, missing_owner_pct):
    """
    Create matplotlib charts for the PDF report with proper error handling
    """
    charts = []
    
    try:
        matplotlib.use('Agg')
        
        # Set a consistent style
        plt.style.use('default')
        
        # Create compliance score breakdown chart
        fig, ax = plt.subplots(figsize=(10, 6))
        categories = ['Passed', 'Failed', 'Overdue', 'Missing Owner']
        values = [100-failed_pct-overdue_pct-missing_owner_pct, failed_pct, overdue_pct, missing_owner_pct]
        
        # Use hex colors to avoid matplotlib color issues
        colors = ['#2E8B57', '#DC143C', '#FF8C00', '#696969']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.8)
        ax.set_ylabel('Percentage (%)', fontsize=12)
        ax.set_title(f'{mode.upper()} Compliance Score: {compliance_score:.1f}%', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Save chart to buffer
        chart_buffer = BytesIO()
        plt.savefig(chart_buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        chart_buffer.seek(0)
        plt.close()
        
        charts.append(('compliance_score', chart_buffer))
        print("Compliance score chart created successfully")
        
    except Exception as e:
        print(f"Error creating compliance score chart: {e}")
    
    try:
        # Create risk distribution chart if applicable
        if mode == "sox" and "Risk Rating" in df.columns:
            risk_counts = df['Risk Rating'].value_counts()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = ['#FF6B6B', '#FFE66D', '#4ECDC4']
            
            wedges, texts, autotexts = ax.pie(risk_counts.values, labels=risk_counts.index, 
                                             autopct='%1.1f%%', colors=colors[:len(risk_counts)],
                                             startangle=90)
            ax.set_title('Risk Rating Distribution', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            
            risk_buffer = BytesIO()
            plt.savefig(risk_buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            risk_buffer.seek(0)
            plt.close()
            
            charts.append(('risk_distribution', risk_buffer))
            print("Risk distribution chart created successfully")
            
    except Exception as e:
        print(f"Error creating risk distribution chart: {e}")
    
    try:
        # Create owner performance chart if applicable
        owner_col = "Owner" if mode in ["sox", "esg", "soc2"] else "Control Owner"
        if owner_col in df.columns:
            owner_stats = df.groupby(owner_col).size().sort_values(ascending=False).head(8)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22', '#34495E']
            
            bars = ax.bar(range(len(owner_stats)), owner_stats.values, 
                         color=colors[:len(owner_stats)], alpha=0.8)
            ax.set_xlabel('Control Owners', fontsize=12)
            ax.set_ylabel('Number of Controls', fontsize=12)
            ax.set_title('Control Distribution by Owner', fontsize=14, fontweight='bold')
            ax.set_xticks(range(len(owner_stats)))
            ax.set_xticklabels(owner_stats.index, rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, value in zip(bars, owner_stats.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       str(value), ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            
            owner_buffer = BytesIO()
            plt.savefig(owner_buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
            owner_buffer.seek(0)
            plt.close()
            
            charts.append(('owner_performance', owner_buffer))
            print("Owner performance chart created successfully")
            
    except Exception as e:
        print(f"Error creating owner performance chart: {e}")
    
    try:
        # Create time series chart for overdue items if applicable
        if "Due Date" in df.columns:
            df_temp = df.copy()
            df_temp['Due Date'] = pd.to_datetime(df_temp['Due Date'], errors='coerce')
            overdue_by_month = df_temp[df_temp['Due Date'] < pd.Timestamp.now()].groupby(
                df_temp['Due Date'].dt.to_period('M')
            ).size()
            
            if not overdue_by_month.empty and len(overdue_by_month) > 1:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                overdue_by_month.plot(kind='line', marker='o', ax=ax, color='#E74C3C', linewidth=2, markersize=6)
                ax.set_xlabel('Month', fontsize=12)
                ax.set_ylabel('Number of Overdue Items', fontsize=12)
                ax.set_title('Overdue Items Trend', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                
                trend_buffer = BytesIO()
                plt.savefig(trend_buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
                trend_buffer.seek(0)
                plt.close()
                
                charts.append(('trend_analysis', trend_buffer))
                print("Trend analysis chart created successfully")
                
    except Exception as e:
        print(f"Error creating trend analysis chart: {e}")
    
    return charts
