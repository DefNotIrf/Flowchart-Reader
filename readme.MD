# Flowchart Reader POC

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) **OR** Python 3.12 with all requirements installed
- Modern web browser (Chrome, Edge, Firefox, etc.)

---

## 1. Backend (FastAPI) - Docker Method (Recommended - but not yet setup)

1. **Build the Docker image:**
   ```sh
   docker build -t flowchart-reader .
   ```

2. **Run the Docker container:**
   ```sh
   docker run -d -p 8000:8000 flowchart-reader
   ```

The backend API will be available at [http://localhost:8000](http://localhost:8000).

---

## 2. Backend (FastAPI) - Python Method

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Start the FastAPI server:**
   ```sh
   uvicorn app:app --reload
   ```

---

## 3. Frontend (index.html)

1. **Open `index.html` directly in your web browser**  
   (Double-click the file or right-click → Open with → your browser)

2. **Usage:**
   - Upload your flowchart image.
   - Use the toolbar to auto-detect, draw, resize, or remove boxes/arrows.
   - Click "Run OCR & Export JSON" to process and export results.
   - Copy or download the resulting JSON as needed.

---

## Notes

- Make sure the backend (FastAPI) is running before using the frontend.
- The frontend expects the backend API to be at `http://localhost:8000`.
- If you want to serve `index.html` from the backend, use a simple HTTP server or integrate with FastAPI static files.

---

## Troubleshooting

- If you see CORS errors, ensure CORS middleware is enabled in `app.py`.
- If Docker is not recognized, install Docker Desktop and restart your terminal.
- For any issues, check your terminal for error messages and ensure all dependencies are installed.