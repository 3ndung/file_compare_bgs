import os
import glob
import shutil
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Setup directories
os.makedirs("CROSS_CHECK", exist_ok=True)
os.makedirs("REF", exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def run_comparison():
    # Process CROSS_CHECK files
    open('CROSS_ALL.txt', 'w').close()  # Clear existing content
    for x in glob.glob('CROSS_CHECK/*.txt'):
        with open(x) as dat, open('CROSS_ALL.txt', 'a') as tulis:
            data = dat.read()
            for line in data.split('\n'):
                if 'STP' in line and 'ADD RULECONDITIONGROUP:RULENAME="R_XXX_' in line:
                    tulis.write(line + '\n')

    # Process REF files
    open('CROSS_REF.txt', 'w').close()  # Clear existing content
    for x in glob.glob('REF/*.txt'):
        with open(x) as dat, open('CROSS_REF.txt', 'a') as tulis:
            data = dat.read()
            for line in data.split('\n'):
                if 'STP' in line and 'ADD RULECONDITIONGROUP:RULENAME="R_XXX_' in line:
                    tulis.write(line + '\n')

    # Read both files for comparison
    with open('CROSS_ALL.txt') as f:
        cross_all = set(f.read().splitlines())
    
    with open('CROSS_REF.txt') as f:
        cross_ref = set(f.read().splitlines())

    # Find differences
    only_in_all = cross_all - cross_ref
    only_in_ref = cross_ref - cross_all
    common = cross_all & cross_ref

    # Generate report
    report = [
        "COMPARISON REPORT",
        "=" * 40,
        f"Lines only in CROSS_ALL.txt: {len(only_in_all)}",
        f"Lines only in CROSS_REF.txt: {len(only_in_ref)}",
        f"Common lines: {len(common)}",
        "",
        "DETAILED DIFFERENCES",
        "=" * 40
    ]

    if only_in_all:
        report.extend(["", "LINES ONLY IN CROSS_ALL.TXT:", "-" * 40] + list(only_in_all))

    if only_in_ref:
        report.extend(["", "LINES ONLY IN CROSS_REF.TXT:", "-" * 40] + list(only_in_ref))

    return "\n".join(report)

@app.get("/")
async def home(request: Request):
    cross_check_files = os.listdir("CROSS_CHECK")
    ref_files = os.listdir("REF")
    
    report = None
    if os.path.exists("comparison_report.txt"):
        with open("comparison_report.txt", "r") as f:
            report = f.read()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "cross_check_files": cross_check_files,
        "ref_files": ref_files,
        "report": report
    })

@app.post("/upload")
async def upload_file(
    request: Request,
    folder: str = Form(...),
    file: UploadFile = File(...)
):
    target_dir = "CROSS_CHECK" if folder == "cross_check" else "REF"
    file_path = os.path.join(target_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete")
async def delete_file(
    request: Request,
    folder: str = Form(...),
    filename: str = Form(...)
):
    target_dir = "CROSS_CHECK" if folder == "cross_check" else "REF"
    file_path = os.path.join(target_dir, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/compare")
async def compare_files(request: Request):
    report = run_comparison()
    with open("comparison_report.txt", "w") as f:
        f.write(report)
    
    return RedirectResponse(url="/", status_code=303)
