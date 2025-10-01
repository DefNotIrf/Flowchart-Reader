from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import pytesseract
import json
import re
from spellchecker import SpellChecker
from PIL import Image
from inference_sdk import InferenceHTTPClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# prefer env var inside container, fallback to system binary
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", "tesseract")
spell = SpellChecker()

def clean_and_correct(text):
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\n•\-•\*\.\,]', '', text)
    corrected = []
    for line in text.split('\n'):
        words = line.split()
        corrected_line = []
        for word in words:
            if word.isalpha():
                corr = spell.correction(word)
                corrected_line.append(corr if corr is not None else word)
            else:
                corrected_line.append(word)
        corrected.append(' '.join(corrected_line))
    return '\n'.join(corrected)

@app.post("/ocr")
async def ocr_endpoint(
    image: UploadFile = File(...),
    boxes: str = Form(...),
    arrows: str = Form(None)
):
    img = np.array(Image.open(image.file))
    boxes = json.loads(boxes)
    arrows = json.loads(arrows) if arrows else []
    results = []
    for box in boxes:
        margin = 10
        x1 = max(0, int(box['x1']) - margin)
        y1 = max(0, int(box['y1']) - margin)
        x2 = min(img.shape[1], int(box['x2']) + margin)
        y2 = min(img.shape[0], int(box['y2']) + margin)
        crop = img[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        sharpen = cv2.GaussianBlur(gray, (0, 0), 3)
        sharpen = cv2.addWeighted(gray, 1.5, sharpen, -0.5, 0)
        _, thresh = cv2.threshold(sharpen, 150, 255, cv2.THRESH_BINARY)
        text = pytesseract.image_to_string(thresh, config='--oem 1 --psm 6', lang='eng').strip()
        text = clean_and_correct(text)
        results.append({'box': box, 'ocr_text': text})
    return JSONResponse(content={"results": results, "arrows": arrows})

@app.post("/cvmodel")
async def cvmodel_endpoint(image: UploadFile = File(...)):
    # Save uploaded image temporarily
    temp_img_path = "temp_uploaded.png"
    with open(temp_img_path, "wb") as f:
        f.write(await image.read())

    # Set up Roboflow inference client
    CLIENT = InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key=os.getenv("ROBOFLOW_API_KEY")
    )

    # Run inference on the uploaded image
    result = CLIENT.infer(
        temp_img_path,
        model_id="aiboardscannerdatasetcomplete-vvbe4/11"
    )

    # Convert Roboflow predictions to box format for frontend
    boxes = []
    for pred in result.get("predictions", []):
        x1 = int(pred['x'] - pred['width'] / 2)
        y1 = int(pred['y'] - pred['height'] / 2)
        x2 = int(pred['x'] + pred['width'] / 2)
        y2 = int(pred['y'] + pred['height'] / 2)
        boxes.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "label": "box"})

    return JSONResponse(content={"boxes": boxes})

@app.get("/health")
async def health():
    return {"status": "ok"}