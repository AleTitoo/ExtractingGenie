"""Render exact source regions from archived PDFs for human verification."""
from io import BytesIO

def render_png(pdf_path, page_number, bbox=None, scale=2.0):
    import pypdfium2 as pdfium
    document = pdfium.PdfDocument(str(pdf_path))
    try:
        if not 1 <= int(page_number) <= len(document):
            raise ValueError('PDF page is out of range.')
        page = document[int(page_number) - 1]
        image = page.render(scale=scale).to_pil()
        if bbox:
            x0, top, x1, bottom = map(float, bbox)
            page_width, _ = page.get_size()
            left = max(0, int(24 * scale))
            right = min(image.width, int((page_width - 24) * scale))
            upper = max(0, int((top - 18) * scale))
            lower = min(image.height, int((bottom + 18) * scale))
            image = image.crop((left, upper, right, lower))
        output = BytesIO()
        image.save(output, format='PNG', optimize=True)
        return output.getvalue()
    finally:
        document.close()
