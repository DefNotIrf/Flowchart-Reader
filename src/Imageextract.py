from pdf2image import convert_from_path
import os

pdf_path = r'C:\Users\irfan.rosdin\OneDrive - Daythree Digital Berhad\Desktop\Side task\ImageText\data\kb_samples\Servicing Process L1 & L2 [CD] - Home Fibre.pdf'  # Update with your PDF filename
output_folder = r'C:\Users\irfan.rosdin\OneDrive - Daythree Digital Berhad\Desktop\Side task\ImageText\data\images\v1'
poppler_path = r'C:\Users\irfan.rosdin\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin'  # <-- Use the bin folder, no quotes

os.makedirs(output_folder, exist_ok=True)

# Convert PDF pages to images
pages = convert_from_path(pdf_path, poppler_path=poppler_path)
for i, page in enumerate(pages):
    image_path = os.path.join(output_folder, f'flowchart_page_{i+1}.png')
    page.save(image_path, 'PNG')
    print(f'Saved: {image_path}')