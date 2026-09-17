import pdfplumber

# Get PDF file path from user
pdf_file = input("Enter PDF file path: ").strip().strip('"').strip("'")

# Open the PDF
with pdfplumber.open(pdf_file) as pdf:

    print("\nTotal Pages:", len(pdf.pages))
    print("\n----- Extracted Text -----\n")

    # Read every page
    for page in pdf.pages:
        text = page.extract_text()

        if text:
            print(text)
        else:
            print("No text found on this page.")