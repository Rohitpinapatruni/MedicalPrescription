from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

# Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash")

# PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql+asyncpg://interaction_cu9z_user:CJZYm0RLbVzn5VrbfcD4P1TiLOii4EIO@dpg-d26oc4ggjchc73e8ufa0-a.singapore-postgres.render.com/interaction_cu9z"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input schema
class PrescriptionInput(BaseModel):
    text: str
    age: int
    temperature: float

# Drug extraction using Gemini
def extract_drugs_from_text(text: str) -> List[str]:
    prompt = f"Extract drug names mentioned in this prescription as individual strings separated by commas without any symbols just as individual: {text}"
    response = model.generate_content(prompt)
    return [drug.strip() for drug in response.text.split(',') if drug.strip()]

# Interaction checker using PostgreSQL
async def check_interactions(drugs: List[str]) -> List[str]:
    if not drugs:
        return []
    async with AsyncSessionLocal() as session:
        drug_list = [drug.lower() for drug in drugs]
        query = text("""
            SELECT "Drug 1", "Drug 2", "Interaction Description"
            FROM interaction
            WHERE LOWER("Drug 1") = ANY(:drugs) AND LOWER("Drug 2") = ANY(:drugs);
        """)
        result = await session.execute(query, {"drugs": drug_list})
        rows = result.fetchall()
        return [row[2] for row in rows]

@app.post("/analyze")
async def analyze(data: PrescriptionInput):
    drugs = extract_drugs_from_text(data.text)
    interactions = await check_interactions(drugs)

    prompt = f"""
    You are a medical assistant AI. Based on the following:
    Prescription: {data.text}
    Age: {data.age}
    Temperature: {data.temperature}
    Drugs: {', '.join(drugs)}
    Interactions found: {', '.join(interactions) if interactions else 'None'}

    1. Recommend proper dosage per drug.
    2. If any interaction is risky, suggest safer alternatives.
    """
    gemini_response = model.generate_content(prompt)

    return {
        "extracted_drugs": drugs,
        "interactions": interactions,
        "gemini_analysis": gemini_response.text.strip()
    }
