import PyPDF2

pdf = PyPDF2.PdfReader('Ex2/HW2-2026.pdf')
text = ''
for page in pdf.pages:
    text += page.extract_text()
print(text)