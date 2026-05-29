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
    pos_x: float = Form(0.0), # Cambiado a 0.0 para mayor precisión inicial
    pos_y: float = Form(0.0),
    fontsize: int = Form(12)   # Reducido a 12 para formularios estándar
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo enviado debe ser un PDF")

    try:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        if page_num < 0 or page_num >= len(doc):
            raise HTTPException(status_code=400, detail="Página fuera de rango")

        page = doc[page_num]
        
        # MEJORA: Definir color negro exacto y fuente estándar (Helvética)
        # Esto asegura que el texto se vea integrado con la fuente del documento
        page.insert_text(
            (pos_x, pos_y), 
            text, 
            fontsize=fontsize, 
            color=(0, 0, 0),    # Negro puro
            fontname="helv"     # Fuente estándar del sistema PDF
        )

        # Extraer bytes correctamente
        output_bytes = doc.tobytes()
        doc.close()

        return Response(
            content=output_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=editado.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")