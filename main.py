from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
import fitz

app = FastAPI()

@app.get("/")
def home():
    # Cambiamos el mensaje para que sepas con total seguridad en el navegador que se ha actualizado
    return {"status": "PDF backend V2 funcionando perfectamente"}

@app.post("/edit-pdf")
async def edit_pdf(
    file: UploadFile = File(...),
    text: str = Form(""),
    page_num: int = Form(0),       # Opcional: por defecto la primera página
    pos_x: float = Form(100.0),    # Opcional: posición X por defecto
    pos_y: float = Form(100.0),    # Opcional: posición Y por defecto
    fontsize: int = Form(20)       # Opcional: tamaño de letra por defecto
):
    # Validación para asegurarse de que es un PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo enviado debe ser un PDF")

    try:
        # 1. Leer los bytes del archivo enviado desde Android
        pdf_bytes = await file.read()
        
        # 2. Abrir el PDF en la memoria RAM
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # 3. Validar que la página solicitada exista en el PDF
        if page_num < 0 or page_num >= len(doc):
            raise HTTPException(status_code=400, detail="El número de página solicitado no existe")

        # 4. Seleccionar la página e insertar el texto
        page = doc[page_num]
        page.insert_text((pos_x, pos_y), text, fontsize=fontsize)

        # 5. --- ¡AQUÍ ESTÁ EL ARREGLO! ---
        # Cambiamos 'doc.write()' por 'doc.tobytes()' para extraer correctamente el PDF modificado
        output_bytes = doc.tobytes()
        
        # 6. Cerrar el documento para liberar memoria
        doc.close()

        # 7. Enviar el PDF modificado de vuelta a Android
        return Response(
            content=output_bytes,
            media_type="application/pdf"
        )
        
    except Exception as e:
        # Si algo falla internamente, te avisará detalladamente en los logs de Railway
        raise HTTPException(status_code=500, detail=f"Error interno procesando el PDF: {str(e)}")