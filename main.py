from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import re
from datetime import datetime
from typing import Dict
import io

app = FastAPI(title="FinTrack Expense Analyzer")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_date(date_str: str) -> str:
    """Convert various date formats to ISO format (YYYY-MM-DD)"""
    if pd.isna(date_str) or not date_str:
        return None
    
    date_str = str(date_str).strip()
    
    # Try different date formats
    formats = [
        "%Y-%m-%d",      # 2023-04-20
        "%d/%m/%Y",      # 20/04/2023
        "%m/%d/%Y",      # 04/20/2023
        "%d-%m-%Y",      # 20-04-2023
        "%m-%d-%Y",      # 04-20-2023
        "%Y/%m/%d",      # 2023/04/20
    ]
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return date_str  # Return original if no format matches

def clean_amount(amount_str: str) -> float:
    """Clean and convert amount strings to float"""
    if pd.isna(amount_str):
        return 0.0
    
    amount_str = str(amount_str).strip()
    
    # Remove extra spaces
    amount_str = re.sub(r'\s+', '', amount_str)
    
    # Handle European format (comma as decimal separator)
    if ',' in amount_str and '.' not in amount_str:
        amount_str = amount_str.replace(',', '.')
    elif ',' in amount_str and '.' in amount_str:
        # Handle cases like 1,234.56 (thousands separator)
        amount_str = amount_str.replace(',', '')
    
    try:
        return float(amount_str)
    except ValueError:
        return 0.0

def clean_category(category_str: str) -> str:
    """Normalize category names"""
    if pd.isna(category_str) or not category_str:
        return "Other"
    
    category_str = str(category_str).strip().lower()
    
    # Map variations to standard categories
    category_mapping = {
        'food': 'Food',
        'travel': 'Travel',
        'health': 'Health',
        'office': 'Office',
        'other': 'Other'
    }
    
    return category_mapping.get(category_str, 'Other')

def clean_name(name_str: str) -> str:
    """Clean and normalize names"""
    if pd.isna(name_str) or not name_str:
        return ""
    
    name_str = str(name_str).strip()
    
    # Convert to title case for consistency
    name_str = ' '.join([word.capitalize() for word in name_str.split()])
    
    return name_str

@app.post("/analyze")
async def analyze_expenses(file: UploadFile = File(...)):
    """
    Analyze expenses from uploaded CSV file and return total spending on Food category
    """
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read CSV file
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';')
        
        # Clean the data
        df['Name'] = df['Name'].apply(clean_name)
        df['Date'] = df['Date'].apply(clean_date)
        df['Amount'] = df['Amount'].apply(clean_amount)
        df['Category'] = df['Category'].apply(clean_category)
        
        # Filter for Food category
        food_expenses = df[df['Category'] == 'Food']
        
        # Calculate total amount spent on Food
        total_food_spending = food_expenses['Amount'].sum()
        
        # Format response
        response = {
            "answer": f"${total_food_spending:.2f}",
            "email": "22f3003091@ds.study.iitm.ac.in",
            "exam": "tds-2025-05-roe"
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
