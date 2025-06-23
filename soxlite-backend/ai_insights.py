import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_sox_insights(journal_entries):
    """
    Calls OpenAI to analyze journal entries and return compliance insights.
    
    Args:
        journal_entries (list of dict): Journal entry records.
    
    Returns:
        str: AI-generated insights as plain text.
    """
    # Format journal entries into a string summary for the prompt
    entries_text = ""
    for entry in journal_entries:
        txn_date = entry.get("TxnDate", "N/A")
        note = entry.get("PrivateNote", "")
        lines = entry.get("Line", [])
        line_summaries = []
        for line in lines:
            desc = line.get("Description", "")
            amt = line.get("Amount", 0)
            post_type = line.get("JournalEntryLineDetail", {}).get("PostingType", "")
            account = line.get("JournalEntryLineDetail", {}).get("AccountRef", {}).get("name", "")
            line_summaries.append(f"{desc} | Amount: {amt} | {post_type} to {account}")
        line_text = "; ".join(line_summaries)
        entries_text += f"- Date: {txn_date}; Note: {note}; Lines: {line_text}\n"

    prompt = f"""
You are an expert SOX 404 compliance auditor. Here are some journal entries:

{entries_text}

Analyze the data and list any potential compliance risks, anomalies, or control weaknesses in plain English.

Return the insights as a numbered list. If no issues are found, say 'No compliance issues detected.'
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SOX 404 compliance auditor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3,
        )
        insights = response.choices[0].message.content.strip()
        return insights
    except Exception as e:
        return f"Error generating AI insights: {str(e)}"
