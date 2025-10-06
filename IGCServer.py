from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import os
import zipfile
import tempfile
import shutil
from typing import List
from datetime import datetime
import IGCParser

app = FastAPI(title="IGCServer", description="REST API for storing and managing IGC files")

# Directory to store IGC files
IGC_DIR = "igc_storage"
os.makedirs(IGC_DIR, exist_ok=True)

# Templates
templates = Jinja2Templates(directory="templates")

class IGCInfo(BaseModel):
    filename: str
    pilot: str = Field(default="")
    date: str = Field(default="")
    start_time: str = Field(default="")
    datetime: str = Field(default="")
    duration: str = Field(default="")
    location: str = Field(default="")
    glider_model: str = Field(default="")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    files = []
    for filename in os.listdir(IGC_DIR):
        if filename.lower().endswith('.igc'):
            filepath = os.path.join(IGC_DIR, filename)
            info = extract_igc_info(filepath)
            files.append(info)
    files.sort(key=lambda x: x.date, reverse=True)
    return templates.TemplateResponse("index.html", {"request": request, "files": files})

@app.get("/igc/", response_model=List[IGCInfo])
async def list_igc_files():
    files = []
    for filename in os.listdir(IGC_DIR):
        if filename.lower().endswith('.igc'):
            filepath = os.path.join(IGC_DIR, filename)
            info = extract_igc_info(filepath)
            files.append(info)
    return files

@app.post("/igc/upload", response_class=RedirectResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    if file.filename.lower().endswith('.igc'):
        filepath = os.path.join(IGC_DIR, file.filename)
        with open(filepath, "wb") as f:
            f.write(await file.read())
        extract_igc_info(filepath)
    elif file.filename.lower().endswith('.zip'):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, file.filename)
            with open(zip_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            for root, dirs, files in os.walk(temp_dir):
                for filename in files:
                    if filename.lower().endswith('.igc'):
                        src = os.path.join(root, filename)
                        dest = os.path.join(IGC_DIR, filename)
                        shutil.move(src, dest)
                        extract_igc_info(dest)
    else:
        raise HTTPException(status_code=400, detail="Only .igc or .zip files are allowed")
        
    return RedirectResponse("/", status_code=303)

@app.get("/igc/{filename}")
async def download_igc_file(filename: str):
    filepath = os.path.join(IGC_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type='application/octet-stream', filename=filename)

@app.delete("/igc/{filename}", response_class=RedirectResponse)
async def delete_igc_file(filename: str):
    filepath = os.path.join(IGC_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(filepath)
    return RedirectResponse("/", status_code=303)

@app.post("/igc/delete-selected")
async def delete_selected_files(selected_files: List[str] = Form(...)):
    for filename in selected_files:
        filepath = os.path.join(IGC_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    return RedirectResponse("/", status_code=303)

@app.post("/igc/download-selected")
async def download_selected_files(selected_files: List[str] = Form(...)):
    if not selected_files:
        return RedirectResponse("/", status_code=303)

    if len(selected_files) == 1:
        filename = selected_files[0]
        filepath = os.path.join(IGC_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(filepath, media_type='application/octet-stream', filename=filename)

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "igc_files.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for filename in selected_files:
            filepath = os.path.join(IGC_DIR, filename)
            if os.path.exists(filepath):
                zipf.write(filepath, filename)
    
    def cleanup():
        shutil.rmtree(temp_dir)

    return FileResponse(zip_path, media_type='application/zip', filename='igc_files.zip', background=cleanup)

def extract_igc_info(filepath: str) -> IGCInfo:
    try:
        headers = IGCParser.parse(filepath)
        
        date_str = headers.get('date', '')
        time_str = headers.get('start_time', '')
        datetime_str = ""

        if date_str and time_str:
            try:
                # Assuming date is in YYYY-MM-DD and time is in HH:MM:SS
                dt_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                datetime_str = dt_obj.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                # Handle cases where date/time format might be different or invalid
                datetime_str = f"{date_str} {time_str}"

        info = IGCInfo(
            filename=os.path.basename(filepath),
            pilot=headers.get('pilot', ''),
            date=date_str,
            start_time=time_str,
            datetime=datetime_str,
            duration=headers.get('duration', ''),
            location=headers.get('location', ''),
            glider_model=headers.get('glider_model', '')
        )
        print(f"Extracted info for {info.filename}: {info}")
        return info
    except Exception as e:
        print(f"Error extracting info for {os.path.basename(filepath)}: {e}")
        return IGCInfo(filename=os.path.basename(filepath))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)