from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, JSONResponse
import fitz  # PyMuPDF

app = FastAPI(title="PDF Editor Backend")


@app.get("/")
def home():
    return {"status": "Backend PDF funcionando"}


# --------------------------------------------------
# 1. ANALIZAR PDF
# --------------------------------------------------

@app.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    total_text = ""
    has_forms = False

    for page in doc:
        total_text += page.get_text().strip()

    for page in doc:
        widgets = page.widgets()
        if widgets:
            has_forms = True
            break

    has_text = len(total_text.strip()) > 20
    is_scanned = not has_text

    if has_forms:
        recommended = "fill_form"
    elif has_text:
        recommended = "edit_content"
    else:
        recommended = "annotate_or_ocr"

    result = {
        "pages": len(doc),
        "has_text": has_text,
        "has_forms": has_forms,
        "is_scanned": is_scanned,
        "recommended_mode": recommended
    }

    doc.close()
    return JSONResponse(result)


# --------------------------------------------------
# 2. ANOTAR PDF
# --------------------------------------------------

@app.post("/annotate-pdf")
async def annotate_pdf(
    file: UploadFile = File(...),
    page_num: int = Form(0),
    text: str = Form(""),
    pos_x: float = Form(0),
    pos_y: float = Form(0),
    fontsize: int = Form(12),
    color_r: float = Form(0),
    color_g: float = Form(0),
    color_b: float = Form(0)
):
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    if page_num < 0 or page_num >= len(doc):
        raise HTTPException(status_code=400, detail="Página fuera de rango")

    page = doc[page_num]

    page.insert_text(
        (pos_x, pos_y),
        text,
        fontsize=fontsize,
        color=(color_r, color_g, color_b),
        fontname="helv"
    )

    output = doc.tobytes()
    doc.close()

    return Response(
        content=output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=anotado.pdf"}
    )


@app.post("/highlight-pdf")
async def highlight_pdf(
    file: UploadFile = File(...),
    page_num: int = Form(0),
    x0: float = Form(...),
    y0: float = Form(...),
    x1: float = Form(...),
    y1: float = Form(...)
):
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    if page_num < 0 or page_num >= len(doc):
        raise HTTPException(status_code=400, detail="Página fuera de rango")

    page = doc[page_num]
    rect = fitz.Rect(x0, y0, x1, y1)

    annot = page.add_highlight_annot(rect)
    annot.update()

    output = doc.tobytes()
    doc.close()

    return Response(
        content=output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resaltado.pdf"}
    )


@app.post("/draw-pdf")
async def draw_pdf(
    file: UploadFile = File(...),
    page_num: int = Form(0),
    x0: float = Form(...),
    y0: float = Form(...),
    x1: float = Form(...),
    y1: float = Form(...),
    width: float = Form(2)
):
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    if page_num < 0 or page_num >= len(doc):
        raise HTTPException(status_code=400, detail="Página fuera de rango")

    page = doc[page_num]
    page.draw_line(
        p1=(x0, y0),
        p2=(x1, y1),
        color=(0, 0, 0),
        width=width
    )

    output = doc.tobytes()
    doc.close()

    return Response(
        content=output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=dibujado.pdf"}
    )


# --------------------------------------------------
# 3. RELLENAR FORMULARIOS PDF
# --------------------------------------------------

@app.post("/get-form-fields")
async def get_form_fields(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    fields = []

    for page_index, page in enumerate(doc):
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                fields.append({
                    "page": page_index,
                    "name": widget.field_name,
                    "type": widget.field_type_string,
                    "value": widget.field_value,
                    "rect": [
                        widget.rect.x0,
                        widget.rect.y0,
                        widget.rect.x1,
                        widget.rect.y1
                    ]
                })

    doc.close()
    return {"fields": fields}


@app.post("/fill-form")
async def fill_form(
    file: UploadFile = File(...),
    field_name: str = Form(...),
    value: str = Form(...)
):
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    found = False

    for page in doc:
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                if widget.field_name == field_name:
                    widget.field_value = value
                    widget.update()
                    found = True

    if not found:
        doc.close()
        raise HTTPException(status_code=404, detail="Campo no encontrado")

    output = doc.tobytes()
    doc.close()

    return Response(
        content=output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=formulario_rellenado.pdf"}
    )


# --------------------------------------------------
# 4. PDF A HTML EDITABLE
# --------------------------------------------------

@app.post("/pdf-to-html")
async def pdf_to_html(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pages_html = []

    for index, page in enumerate(doc):
        page_html = page.get_text("html")

        pages_html.append(f"""
        <section class="pdf-page" contenteditable="true" data-page="{index}">
            {page_html}
        </section>
        """)

    doc.close()

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 20px;
                background: #d0d0d0;
                font-family: Arial, sans-serif;
            }}

            .pdf-page {{
                background: white;
                width: 794px;
                min-height: 1123px;
                margin: 0 auto 30px auto;
                padding: 30px;
                box-shadow: 0 0 8px rgba(0,0,0,0.4);
                outline: none;
            }}

            .pdf-page * {{
                max-width: 100%;
            }}
        </style>
    </head>
    <body>
        {''.join(pages_html)}
    </body>
    </html>
    """

    return Response(content=full_html, media_type="text/html")
