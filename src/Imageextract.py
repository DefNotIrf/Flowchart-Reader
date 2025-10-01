from pdf2image import convert_from_path
import os

pdf_path = r'test.pdf'  # Update with your PDF filename
output_folder = r'C:\Users\data\images\v1'
poppler_path = r'C:\Users\bin'  # <-- Use the bin folder, no quotes

os.makedirs(output_folder, exist_ok=True)

# Convert PDF pages to images
pages = convert_from_path(pdf_path, poppler_path=poppler_path)
for i, page in enumerate(pages):
    image_path = os.path.join(output_folder, f'flowchart_page_{i+1}.png')
    page.save(image_path, 'PNG')
    print(f'Saved: {image_path}')
