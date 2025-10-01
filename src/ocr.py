import cv2
import json
import pytesseract
import re
from spellchecker import SpellChecker

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\irfan.rosdin\tesseract.exe'  # Update path if needed

image_path = r'data/images/v1/flowchart_page_3.png'
json_path = r'data/jsonf/flowchart_page_3_roboflow_edited.json'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

img = cv2.imread(image_path)

# Resize image for display (e.g., max width 900, max height 600 for smaller window)
max_w, max_h = 900, 600
h, w = img.shape[:2]
scale = min(max_w / w, max_h / h, 1.0)
img_disp = cv2.resize(img, (int(w * scale), int(h * scale)))

spell = SpellChecker()

def clean_and_correct(text):
    # Remove non-printable characters and extra spaces
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    text = re.sub(r'\s+', ' ', text)
    # Allow only letters, numbers, spaces, newlines, and common bullet points
    text = re.sub(r'[^\w\s\n•\-•\*\.\,]', '', text)
    # Spellcheck each word
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

for i, pred in enumerate(data['predictions']):
    if pred.get('deleted'):
        continue
    # Calculate box coordinates for display
    x1 = int((pred['x'] - pred['width'] / 2) * scale)
    y1 = int((pred['y'] - pred['height'] / 2) * scale)
    x2 = int((pred['x'] + pred['width'] / 2) * scale)
    y2 = int((pred['y'] + pred['height'] / 2) * scale)

    # Crop from the original image for OCR (not the resized one)
    orig_x1 = int(pred['x'] - pred['width'] / 2)
    orig_y1 = int(pred['y'] - pred['height'] / 2)
    orig_x2 = int(pred['x'] + pred['width'] / 2)
    orig_y2 = int(pred['y'] + pred['height'] / 2)
    margin = 8
    crop_x1 = max(orig_x1 - margin, 0)
    crop_y1 = max(orig_y1 - margin, 0)
    crop_x2 = min(orig_x2 + margin, img.shape[1])
    crop_y2 = min(orig_y2 + margin, img.shape[0])
    crop = img[crop_y1:crop_y2, crop_x1:crop_x2]

    # Preprocess for OCR: grayscale, sharpen, threshold
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    sharpen = cv2.GaussianBlur(gray, (0, 0), 3)
    sharpen = cv2.addWeighted(gray, 1.5, sharpen, -0.5, 0)
    _, thresh = cv2.threshold(sharpen, 150, 255, cv2.THRESH_BINARY)

    # Use Tesseract LSTM engine and block mode
    custom_config = r'--oem 1 --psm 6'
    text = pytesseract.image_to_string(thresh, config=custom_config, lang='eng').strip()
    text = clean_and_correct(text)
    data['predictions'][i]['ocr_text'] = text
    print(f"Shape {i}: {text}")

    # Draw rectangle on display image
    cv2.rectangle(img_disp, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Put OCR text inside the box on display image, using smaller font
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.25  # Smaller font
    thickness = 1

    max_text_width = x2 - x1 - 8
    wrapped_lines = []
    for line in text.split('\n'):
        words = line.split(' ')
        current_line = ''
        for word in words:
            test_line = current_line + (' ' if current_line else '') + word
            (test_w, _), _ = cv2.getTextSize(test_line, font, font_scale, thickness)
            if test_w > max_text_width and current_line:
                wrapped_lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            wrapped_lines.append(current_line)

    # Draw each line inside the box, but allow unlimited vertical space
    text_y = y1 + 16
    line_height = 14  # Smaller line height for smaller font
    for line in wrapped_lines:
        cv2.putText(img_disp, line, (x1 + 4, text_y), font, font_scale, (0,0,255), thickness, cv2.LINE_AA)
        text_y += line_height

# Optionally, save the updated JSON
with open(json_path.replace('.json', '_ocr.json'), 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

cv2.imshow("Boxes with OCR Text", img_disp)
cv2.waitKey(0)
cv2.destroyAllWindows()

print("OCR extraction complete.")