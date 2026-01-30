import PyPDF2
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Extract HW3_2025.pdf
print("=== HW3_2025.pdf ===\n")
pdf = PyPDF2.PdfReader('Ex3/HW3_2025.pdf')
text_2025 = ''
for page in pdf.pages:
    text_2025 += page.extract_text()
print(text_2025)

print("\n\n" + "="*80 + "\n\n")

# Extract HW3_2026.pdf
print("=== HW3_2026.pdf ===\n")
pdf = PyPDF2.PdfReader('Ex3/HW3_2026.pdf')
text_2026 = ''
for page in pdf.pages:
    text_2026 += page.extract_text()
print(text_2026)

# Save to files for easier comparison
with open('hw3_2025_text.txt', 'w', encoding='utf-8') as f:
    f.write(text_2025)
with open('hw3_2026_text.txt', 'w', encoding='utf-8') as f:
    f.write(text_2026)

print("\n\nTexts saved to hw3_2025_text.txt and hw3_2026_text.txt")
