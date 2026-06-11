import fitz
import pytesseract
from PIL import Image
import io


#====================================================================================
#============ TODO: Pb du cas ou le PDF contient des images + du texte ===========
# Notes: Split la logique en 2 fonctions : une pour les images, une pour les PDF scannés
# (potentiellement dans deux fichiers différents)
#====================================================================================

def run_tesseract(filepath: str) -> dict:
    pages_data = []
    total_conf = 0.0
    valid_pages_count = 0
    
    # Si c'est une image
    if filepath.lower().endswith((".jpg", ".jpeg", ".png")):
        dict_result = extract_text_from_image(filepath)
        return dict_result
        
    # Si c'est un PDF scanné
    else:
        dict_result = extract_text_from_pdf(filepath)
        return dict_result



def extract_text_from_image(filepath: str) -> dict: 
    pages_data = []
    total_conf = 0.0
    valid_pages_count = 0

    img = Image.open(filepath)
    data = pytesseract.image_to_data(img, lang="fra", output_type=pytesseract.Output.DICT)
        
    confs = [int(c) for c in data['conf'] if int(c) != -1]
    textes = [t for t, c in zip(data['text'], data['conf']) if int(c) != -1 and t.strip()]
        
    page_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
    pages_data.append({"page_number": 1, "text": " ".join(textes), "confidence": round(page_conf, 3)})
    valid_pages_count, total_conf = 1, page_conf

    avg_confidence = round(total_conf / valid_pages_count, 3) if valid_pages_count > 0 else 0.0

    return {"pages": pages_data, "avg_confidence": avg_confidence, "engine": "tesseract"}

def extract_text_from_pdf(filepath: str) -> dict:
        pages_data = []
        total_conf = 0.0
        valid_pages_count = 0

        doc = fitz.open(filepath)
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            data = pytesseract.image_to_data(img, lang="fra", output_type=pytesseract.Output.DICT)
            confs = [int(c) for c in data['conf'] if int(c) != -1]
            textes = [t for t, c in zip(data['text'], data['conf']) if int(c) != -1 and t.strip()]
            
            page_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
            pages_data.append({"page_number": page_num + 1, "text": " ".join(textes), "confidence": round(page_conf, 3)})
            total_conf += page_conf
            valid_pages_count += 1

        avg_confidence = round(total_conf / valid_pages_count, 3) if valid_pages_count > 0 else 0.0

        return {"pages": pages_data, "avg_confidence": avg_confidence, "engine": "tesseract"}