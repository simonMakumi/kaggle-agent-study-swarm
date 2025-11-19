import fitz  # PyMuPDF

def read_pdf(file_path: str) -> str:
    """
    Reads a PDF file from the given path and extracts all its text.
    
    Args:
        file_path: The exact path to the PDF file (e.g., 'test_files/document.pdf').
        
    Returns:
        A string containing the full text of the PDF.
    """
    try:
        # Open the document
        doc = fitz.open(file_path)
        text = ""
        
        # Iterate over every page and extract text
        for page in doc:
            text += page.get_text() + "\n"
            
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
