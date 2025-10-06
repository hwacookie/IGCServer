from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import zipfile
import tempfile
import shutil
from aerofiles import igc
from typing import List

app = FastAPI(title="IGCServer", description="REST API for storing and managing IGC files")

# Directory to store IGC files
IGC_DIR = "igc_storage"
os.makedirs(IGC_DIR, exist_ok=True)

# Templates
templates = Jinja2Templates(directory="templates")

class IGCInfo(BaseModel):
    filename: str
    pilot: str = ""
    date: str = ""
    location: str = ""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    files = []
    for filename in os.listdir(IGC_DIR):
        if filename.endswith('.igc'):
            filepath = os.path.join(IGC_DIR, filename)
            info = extract_igc_info(filepath)
            files.append(info)
    return templates.TemplateResponse("index.html", {"request": {}, "files": files})

@app.get("/igc/", response_model=List[IGCInfo])
async def list_igc_files():
    files = []
    for filename in os.listdir(IGC_DIR):
        if filename.endswith('.igc'):
            filepath = os.path.join(IGC_DIR, filename)
            info = extract_igc_info(filepath)
            files.append(info)
    return files

@app.post("/igc/", response_model=IGCInfo)
async def upload_igc_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith('.igc'):
        raise HTTPException(status_code=400, detail="Only .igc files are allowed")
    filepath = os.path.join(IGC_DIR, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    info = extract_igc_info(filepath)
    return info

@app.post("/igc/upload-zip", response_model=List[IGCInfo])
async def upload_zip_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed")
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, file.filename)
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        added_files = []
        for root, dirs, files in os.walk(temp_dir):
            for filename in files:
                if filename.endswith('.igc'):
                    src = os.path.join(root, filename)
                    dest = os.path.join(IGC_DIR, filename)
                    shutil.move(src, dest)
                    info = extract_igc_info(dest)
                    added_files.append(info)
        return added_files

@app.get("/igc/{filename}")
async def download_igc_file(filename: str):
    filepath = os.path.join(IGC_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type='application/octet-stream', filename=filename)

@app.post("/igc/{filename}/delete")
async def delete_igc_file(filename: str):
    filepath = os.path.join(IGC_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(filepath)
    return {"message": "File deleted"}

def extract_igc_info(filepath: str) -> IGCInfo:
    try:
        reader = igc.Reader()
        with open(filepath, 'r') as f:
            flight = reader.read(f)
        pilot = flight['headers'].get('pilot', '')
        date = flight['headers'].get('date', '')
        location = ""
        if flight['fixes']:
            first_fix = flight['fixes'][0]
            location = f"{first_fix['lat']}, {first_fix['lon']}"
        return IGCInfo(filename=os.path.basename(filepath), pilot=pilot, date=date, location=location)
    except Exception as e:
        return IGCInfo(filename=os.path.basename(filepath), pilot="", date="", location="")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)