from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from backend.ocr_processor import process_file  
import os
import shutil


app = FastAPI()

# Get the current directory path
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set up Jinja2 for template rendering
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# Directory to store uploaded files
UPLOAD_DIR = os.path.join(current_dir, "temp_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...), prompt: str = Form(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = process_file(file_path, prompt)


        os.remove(file_path)

        if result.status == "success":
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "content": result.content, "success": True, "extracted": result.extracted_text}
            )
        else:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "error": result.message, "success": False}
            )

       
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(e), "success": False}
        )

