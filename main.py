from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
import fitz

app = FastAPI()

@app.get("/")
def home():
    return {"status": "PDF backend funcionando"}

@app.post("/edit-pdf")
async def edit_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    page = doc[0]
    page.insert_text((100, 100), "PDF EDITADO", fontsize=20)

    output_bytes = doc.write()
    doc.close()

    return Response(
        content=output_bytes,
        media_type="application/pdf"
    )