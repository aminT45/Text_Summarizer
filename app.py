import re
import torch
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Initialize FastAPI app
app = FastAPI(title="Text Summarizer App", description="Text Summarization using T5", version="1.0")

# Determine optimal device once
if torch.backends.mps.is_available():
    device = torch.device("mps")
elif torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

# Load model & tokenizer to memory
MODEL_PATH = "D:/Models/text summarize app/saved_summary_model"
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH)
tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)

# Push model to processing device permanently
model.to(device)
model.eval()  # Set model to evaluation mode to save memory/prevent gradient calculations

# UI Templating
templates = Jinja2Templates(directory=".")

# Input schema
class DialogueInput(BaseModel):
    dialogue: str

def clean_data(text: str) -> str:
    text = re.sub(r"\r\n", " ", text)    # Remove line breaks
    text = re.sub(r"\s+", " ", text)     # Remove double spaces
    text = re.sub(r"<.*?>", " ", text)   # Strip HTML tags
    return text.strip().lower()

def summarize_dialogue(dialogue: str) -> str:
    dialogue = clean_data(dialogue)

    # Tokenize input text
    inputs = tokenizer(
        dialogue,
        padding="max_length",
        max_length=512,
        truncation=True,
        return_tensors="pt"
    ).to(device)

    # Generate summary tokens safely without computing gradients
    with torch.no_grad():
        targets = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=150,
            num_beams=4,
            early_stopping=True
        )

    # Decode and return final text string
    summary = tokenizer.decode(targets[0], skip_special_tokens=True)
    return summary

# API Endpoints
@app.post("/summarize/")
async def summarize(dialogue_input: DialogueInput):
    summary = summarize_dialogue(dialogue_input.dialogue)
    return {"summary": summary}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )
    

