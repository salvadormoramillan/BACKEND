from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
import fitz

app = FastAPI(title="PDF Editor Backend")


@app.get("/")
def home():
    return {"status": "Backend PDF funcionando"}


@app.post("/edit-pdf")
async def edit_pdf(
    file: UploadFile = File(...),
    text: str = Form(""),
    page_num: int = Form(0),
    pos_x: float = Form(100),
    pos_y: float = Form(100),
    font_size: int = Form(12)
):
    pdf_bytes = await file.read()

    doc = fitz.open(
        stream=bytes(pdf_bytes),
        filetype="pdf"
    )

    if page_num < 0 or page_num >= len(doc):
        doc.close()
        raise HTTPException(
            status_code=400,
            detail="Página fuera de rango"
        )

    page = doc[page_num]

    if text.strip():
        page.insert_text(
            (pos_x, pos_y),
            text,
            fontsize=font_size,
            color=(0, 0, 0),
            fontname="helv"
        )

    output_bytes = doc.tobytes(
        garbage=4,
        deflate=True,
        clean=True
    )

    doc.close()

    return Response(
        content=output_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=pdf_editado.pdf"
        }
    )