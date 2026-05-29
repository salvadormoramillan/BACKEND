from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
import fitz  # PyMuPDF

app = FastAPI()

@app.get("/")
def home():
    return {"status": "PDF backend V2 funcionando perfectamente"}

@app.post("/edit-pdf")
async def edit_pdf(
    file: UploadFile = File(...),
    text: str = Form(""),
    page_num: int = Form(0),
    pos_x: float = Form(0.0),
    pos_y: float = Form(0.0),
    fontsize: int = Form(12)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo enviado debe ser un PDF")
    try:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        if page_num < 0 or page_num >= len(doc):
            raise HTTPException(status_code=400, detail="Página fuera de rango")

        page = doc[page_num]

        # Cubrir el área con rectángulo blanco para limpiar el texto original debajo
        rect = fitz.Rect(pos_x, pos_y - fontsize, pos_x + 300, pos_y + 4)
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

        # Insertar el texto nuevo sobre el área limpia
        page.insert_text(
            (pos_x, pos_y),
            text,
            fontsize=fontsize,
            color=(0, 0, 0),
            fontname="helv"
        )

        output_bytes = doc.tobytes()
        doc.close()

        return Response(
            content=output_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=editado.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")