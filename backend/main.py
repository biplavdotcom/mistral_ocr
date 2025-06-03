from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from backend.ocr_processor import process_file  
from backend.classification import parse_invoice_json, classify_invoice, get_gemini_model, raw_json_string, process_classification, match_vendor_name
import os
import shutil
from .database import collection
from datetime import datetime
import json
from typing import Union

recent_filename = None

app = FastAPI()

current_dir = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

UPLOAD_DIR = os.path.join(current_dir, "temp_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def format_datetime(dt):
    """Format datetime to a readable string"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/extract")
async def upload_file(request: Request, file: UploadFile = File(...), prompt: str = Form(None) ):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = process_file(file_path, prompt or "")
        total_uploads = collection.count_documents({"file_name": {"$exists":True}})

        if prompt:
            structure = {
                "file_name": file.filename,
                "uid": total_uploads+1,
                "prompt_type": "user_given_prompt",
                "prompt": prompt,
                "raw_text": result.extracted_text,
                "extracted_details": result.content,
                "uploaded_at": format_datetime(datetime.now())
            }
        else:
            structure = {
                "file_name": file.filename,
                "uid": total_uploads+1,
                "prompt_type": "default_prompt",
                "raw_text": result.extracted_text,
                "extracted_details": result.content,
                "uploaded_at": format_datetime(datetime.now())
            }
        collection.insert_one(structure)
        
        os.remove(file_path)

        if result.status == "success":
            document = collection.find_one({"file_name": file.filename}, sort = [("uid", -1)])
            document_id = document["uid"]

            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Text extracted and structured successfully",
                    "content": result.content,
                    "extracted_text": result.extracted_text,
                    "document_id": document_id
                }
            )   
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": result.message
                }
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    


@app.get("/text-extraction/pdf")
async def get_all_extractions(file:str = None):
    try:
        if file:
            if not file.endswith('.pdf'):
                filename = f"{file}.pdf"
                document_find = list(collection.find(({"file_name": filename}), {'_id': 0}))
                return {'documents': document_find}
            else:
                document_find = list(collection.find(({"file_name": file}), {'_id': 0}))
                return {'documents': document_find}
        else:
            all_extractions = list(collection.find(({"file_name":{"$exists": True}}),{'_id':0,'default_prompt':0}))
            # for item in all_extractions:
            #     item['_id'] = str(item['_id'])
            return {'documents': all_extractions}
    except Exception as e:
        return{
            "message": "No file found"
        }

@app.delete("/delete/{file}")
async def delete_extraction(file: str):
    try:
        if not file.endswith('.pdf'):
            filename = f"{file}.pdf"
        result = collection.delete_one({"file_name": filename})
        total_uploads = collection.count_documents({"file_name": {"$exists":True}})
        if result.deleted_count == 0:
            return JSONResponse(
                status_code=404,
                content={"message": f"No file found with name: {file}"}
            )
        return JSONResponse(
            status_code=200,
            content={"message": f"File {file}.pdf deleted successfully"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error deleting file: {str(e)}"}
        )
    
@app.put("/update-prompt")
async def update_prompt(doc_id: int, prompt: str):
    try:
        document = collection.find_one({
            "uid": doc_id,
            "prompt_type": "user_given_prompt"
        })
        
        if not document:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "Document not found or is not a user-given prompt document"
                }
            )

        
        result = collection.update_one(
            {"uid": doc_id},
            {"$set": {"prompt": prompt}}
        )
        
        if result.modified_count > 0:
            return JSONResponse(
                status_code=200,
                content={"message": f"Prompt updated successfully for document {doc_id}"}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"message": "No changes were made to the document"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error updating prompt: {str(e)}"}
        )    
    
@app.get("/default-prompts")
async def get_default_prompts():
    try:
        default_prompt = list(collection.find({"default_type": {"$exists": True}},{"_id": 0}))
        if not default_prompt:
            return {"message": "No default prompts found"}
        else:
            return default_prompt
    except Exception as e:
        return{
            "error": str(e)
        } 

@app.get("/classification/{document_id}")
async def classify_document(document_id: int):
    try:

        document_name = collection.find_one({"uid": document_id},{"file_name":1, "extracted_details": 1, "_id": 0 })

        classification_result = process_classification(document_id)
        print("\n📄 Document Type:", classification_result)
        match_vendor_name(document_id)
        collection.update_one({"uid": document_id}, {"$set":  {"classification": classification_result }})
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "classification": classification_result,
                "document_id": document_id,
                "file_name": document_name["file_name"],
                "extracted_details": document_name["extracted_details"]
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )    
