import pdfplumber
from docx import Document
import email

def parse_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def parse_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def parse_email(path):
    with open(path, "rb") as f:  # open as binary, not text
        raw_bytes = f.read()
    msg = email.message_from_bytes(raw_bytes)
    # Now extract text as before
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                # decode using the correct encoding if available
                charset = part.get_content_charset() or 'utf-8'
                try:
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    return part.get_payload(decode=True).decode('utf-8', errors="replace")
    else:
        charset = msg.get_content_charset() or 'utf-8'
        return msg.get_payload(decode=True).decode(charset, errors="replace")
