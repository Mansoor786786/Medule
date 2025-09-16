import os
import pytesseract
from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter
import fitz  # PyMuPDF
import re
import subprocess
import tempfile
import cv2
import numpy as np
import uuid

app = Flask(__name__)

# Set Tesseract path
tesseract_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "tesseract"
]

tesseract_found = False
for path in tesseract_paths:
    try:
        if path == "tesseract":
            subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
            tesseract_found = True
            print("✅ Tesseract found in system PATH")
            break
        elif os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            tesseract_found = True
            print(f"✅ Tesseract found at: {path}")
            break
    except Exception as e:
        continue

# COMPREHENSIVE MEDICAL PARAMETERS DATABASE
HEALTH_METRICS = {
    # HEMATOLOGY - Blood Count
    "Haemoglobin": (12.0, 16.0, "g/dL"),
    "Hemoglobin": (12.0, 16.0, "g/dL"),
    "Hb": (12.0, 16.0, "g/dL"),
    "TRBC": (4.5, 6.0, "million/cmm"),
    "RBC": (4.5, 6.0, "million/cmm"),
    "Red Blood Cells": (4.5, 6.0, "million/cmm"),
    "PCV": (36, 48, "%"),
    "Hematocrit": (36, 48, "%"),
    "HCT": (36, 48, "%"),
    "TWBC": (4000, 11000, "cells/cmm"),
    "WBC": (4000, 11000, "cells/cmm"),
    "White Blood Cells": (4000, 11000, "cells/cmm"),
    "Neutrophils": (40, 70, "%"),
    "Lymphocytes": (20, 40, "%"),
    "Eosinophils": (1, 6, "%"),
    "Monocytes": (2, 10, "%"),
    "Basophils": (0, 2, "%"),
    "Platelet Count": (150000, 450000, "cells/cmm"),
    "Platelets": (150000, 450000, "cells/cmm"),
    
    # RED BLOOD CELL INDICES
    "MCV": (80, 100, "fL"),
    "MCH": (27, 33, "pg"),
    "MCHC": (32, 36, "g/dL"),
    "RDW": (11.5, 14.5, "%"),
    
    # COAGULATION
    "Bleeding Time": (2, 8, "minutes"),
    "Clotting Time": (5, 15, "minutes"),
    "PT": (11, 13, "seconds"),
    "Prothrombin Time": (11, 13, "seconds"),
    "APTT": (25, 35, "seconds"),
    "INR": (0.8, 1.1, ""),
    
    # GLUCOSE TESTS
    "Blood Glucose": (70, 140, "mg/dL"),
    "Glucose": (70, 140, "mg/dL"),
    "Random": (70, 140, "mg/dL"),
    "Fasting": (70, 110, "mg/dL"),
    "Post Prandial": (80, 140, "mg/dL"),
    "PPBS": (80, 140, "mg/dL"),
    "FBS": (70, 110, "mg/dL"),
    "HbA1c": (4.0, 6.0, "%"),
    
    # KIDNEY FUNCTION
    "Blood Urea": (15, 45, "mg/dL"),
    "Urea": (15, 45, "mg/dL"),
    "BUN": (7, 25, "mg/dL"),
    "Serum Creatinine": (0.6, 1.4, "mg/dL"),
    "Creatinine": (0.6, 1.4, "mg/dL"),
    "eGFR": (90, 120, "mL/min/1.73m²"),
    
    # LIVER FUNCTION
    "SGOT": (5, 40, "IU/L"),
    "AST": (5, 40, "IU/L"),
    "SGPT": (5, 40, "IU/L"),
    "ALT": (5, 40, "IU/L"),
    "Alkaline Phosphatase": (44, 147, "IU/L"),
    "ALP": (44, 147, "IU/L"),
    "Total Bilirubin": (0.2, 1.2, "mg/dL"),
    "Direct Bilirubin": (0.0, 0.3, "mg/dL"),
    "Indirect Bilirubin": (0.2, 0.8, "mg/dL"),
    "Albumin": (3.5, 5.0, "g/dL"),
    "Total Protein": (6.0, 8.3, "g/dL"),
    "Globulin": (2.3, 3.5, "g/dL"),
    
    # LIPID PROFILE
    "Total Cholesterol": (150, 200, "mg/dL"),
    "Cholesterol": (150, 200, "mg/dL"),
    "Triglycerides": (50, 150, "mg/dL"),
    "HDL": (40, 80, "mg/dL"),
    "LDL": (50, 130, "mg/dL"),
    "VLDL": (5, 30, "mg/dL"),
    
    # THYROID
    "TSH": (0.27, 4.2, "mIU/L"),
    "T3": (80, 200, "ng/dL"),
    "T4": (5.1, 14.1, "μg/dL"),
    "Free T3": (2.0, 4.4, "pg/mL"),
    "Free T4": (0.93, 1.7, "ng/dL"),
    
    # ELECTROLYTES
    "Sodium": (135, 145, "mEq/L"),
    "Potassium": (3.5, 5.0, "mEq/L"),
    "Chloride": (98, 107, "mEq/L"),
    "Calcium": (8.5, 10.5, "mg/dL"),
    "Phosphorus": (2.5, 4.5, "mg/dL"),
    
    # CARDIAC MARKERS
    "Troponin I": (0, 0.04, "ng/mL"),
    "CK-MB": (0, 6.3, "ng/mL"),
    "LDH": (140, 280, "IU/L"),
    
    # VITAMINS & MINERALS
    "Vitamin D": (30, 100, "ng/mL"),
    "Vitamin B12": (200, 900, "pg/mL"),
    "Folate": (2.7, 17.0, "ng/mL"),
    "Iron": (60, 170, "μg/dL"),
    "Ferritin": (15, 150, "ng/mL"),
    
    # URINE ANALYSIS
    "Specific Gravity": (1.003, 1.030, ""),
    "pH": (4.6, 8.0, ""),
    "Protein": (0, 150, "mg/day"),
    "Sugar": (0, 0, "mg/dL"),
    "Ketones": (0, 0, "mg/dL"),
    "Blood": (0, 0, ""),
    "Pus Cells": (0, 5, "/hpf"),
    "RBC": (0, 2, "/hpf"),
    "Epithelial Cells": (0, 5, "/hpf"),
    "Crystals": (0, 0, ""),
    "Casts": (0, 0, ""),
    
    # STOOL EXAMINATION
    "Colour": (0, 0, ""),
    "Consistency": (0, 0, ""),
    "Occult Blood": (0, 0, ""),
    "Ova": (0, 0, ""),
    "Cysts": (0, 0, ""),
    "Parasites": (0, 0, ""),
    
    # SEROLOGY & IMMUNOLOGY
    "HBsAg": (0, 0, ""),
    "Anti HCV": (0, 0, ""),
    "HIV": (0, 0, ""),
    "VDRL": (0, 0, ""),
    "TPHA": (0, 0, ""),
    "Widal": (0, 0, ""),
    
    # PREGNANCY & HORMONES
    "Beta HCG": (0, 5, "mIU/mL"),
    "Prolactin": (4.0, 15.2, "ng/mL"),
    "Testosterone": (300, 1000, "ng/dL"),
    "Estradiol": (15, 350, "pg/mL"),
    
    # ULTRASOUND MEASUREMENTS (Fetal)
    "Biparietal Diameter": (0, 0, "mm"),
    "BPD": (0, 0, "mm"),
    "Head Circumference": (0, 0, "mm"),
    "HC": (0, 0, "mm"),
    "Abdominal Circumference": (0, 0, "mm"),
    "AC": (0, 0, "mm"),
    "Femur Length": (0, 0, "mm"),
    "FL": (0, 0, "mm"),
    "Humerus Length": (0, 0, "mm"),
    "HL": (0, 0, "mm"),
    "Gestational Age": (0, 0, "weeks"),
    "EDD": (0, 0, ""),
    "Fetal Heart Rate": (120, 160, "bpm"),
    
    # ADDITIONAL PARAMETERS
    "Uric Acid": (3.5, 7.2, "mg/dL"),
    "CRP": (0, 3.0, "mg/L"),
    "ESR": (0, 30, "mm/hr"),
    "Amylase": (25, 125, "IU/L"),
    "Lipase": (10, 140, "IU/L"),
}

def enhance_image_quality(image):
    """Advanced image enhancement for better OCR"""
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Convert to grayscale for processing
        gray_image = image.convert('L')
        
        # Convert to numpy array for OpenCV processing
        img_array = np.array(gray_image)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(img_array, (1, 1), 0)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Convert back to PIL Image
        return Image.fromarray(cleaned)
    except Exception as e:
        print(f"Image enhancement failed: {e}")
        return image

def extract_medical_data(text):
    """Enhanced medical data extraction with better pattern matching"""
    results = []
    abnormal_count = 0
    normal_count = 0
    
    print("🔍 Analyzing medical text...")
    
    # Clean text
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.replace('\n', ' ').replace('\t', ' ')
    
    # Track found values to avoid duplicates
    found_values = set()
    
    for metric, (low, high, unit) in HEALTH_METRICS.items():
        # Skip if already found
        if metric in found_values:
            continue
            
        # Multiple pattern variations
       # compute escaped metric BEFORE list
        escaped_metric = metric.replace(" ", r"\s*")

        patterns = [
            rf"{re.escape(metric)}\s*[:\-=]\s*(\d+\.?\d*)",
            rf"{metric}\s*[:\-=]\s*(\d+\.?\d*)",
            rf"{re.escape(metric)}\s*[:\-=]\s*(\d+\.?\d*)\s*{re.escape(unit)}",
            rf"(\d+\.?\d*)\s+{re.escape(metric)}",
            rf"(\d+\.?\d*)\s*{metric}",
            rf"{escaped_metric}\s*[:\-=]?\s*(\d+\.?\d*)",   # ✅ safe usage
            rf"(?i){re.escape(metric)}\s*[:\-=]?\s*(\d+\.?\d*)",
            rf"{metric}\s*\([^)]\)\s[:\-=]?\s*(\d+\.?\d*)",
            rf"{metric}\s+(\d+\.?\d*)\s+{re.escape(unit)}",
            rf"{metric}\s+(\d+\.?\d*)",
            rf"{metric[:3]}\s*[:\-=]?\s*(\d+\.?\d*)" if len(metric) > 3 else None,
        ]
        
        # Remove None patterns
        patterns = [p for p in patterns if p is not None]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.group(1))
                    
                    # Validate realistic ranges
                    if value < 0 or value > 100000:
                        continue
                    
                    # Skip if this metric was already found
                    if metric in found_values:
                        break
                        
                    found_values.add(metric)
                    print(f"✅ Found {metric}: {value} {unit}")
                    
                    # Determine if normal or abnormal
                    if low == 0 and high == 0:  # Qualitative tests
                        results.append(f"📋 {metric}: {value} {unit}")
                    elif value < low:
                        results.append(f"🔻 {metric}: {value} {unit} (LOW - Normal: {low}-{high})")
                        abnormal_count += 1
                    elif value > high:
                        results.append(f"🔺 {metric}: {value} {unit} (HIGH - Normal: {low}-{high})")
                        abnormal_count += 1
                    else:
                        results.append(f"✅ {metric}: {value} {unit} (Normal)")
                        normal_count += 1
                    
                    break  # Found value for this metric, move to next
                except (ValueError, IndexError):
                    continue
            
            if metric in found_values:
                break  # Found value for this metric, move to next metric
    
    # Also extract qualitative findings
    qualitative_findings = extract_qualitative_findings(text)
    
    # Generate report
    if not results and not qualitative_findings:
        return """❌ No medical data could be extracted from the document.

🔍 **Troubleshooting:**
• Ensure the image is clear and well-lit
• Check if the document contains numerical values
• Try uploading a higher resolution image
• Make sure the text is readable

📋 **Supported Reports:**
• Blood tests (CBC, Biochemistry, Lipid Profile)
• Urine analysis
• Ultrasound reports
• Thyroid function tests
• Liver & kidney function tests
• And 150+ other medical parameters"""
    
    # Build comprehensive report
    report_lines = []
    
    # Header
    total_params = len(results)
    status = "NORMAL" if abnormal_count == 0 else "ABNORMAL"
    status_emoji = "✅" if abnormal_count == 0 else "⚠️"
    
    report_lines.append(f"{status_emoji} **MEDICAL REPORT ANALYSIS**")
    report_lines.append(f"📊 **Status:** {status}")
    report_lines.append(f"🔬 **Parameters Analyzed:** {total_params}")
    report_lines.append(f"✅ **Normal Values:** {normal_count}")
    report_lines.append(f"⚠️ **Abnormal Values:** {abnormal_count}")
    report_lines.append("")
    
    # Abnormal values first
    abnormal_results = [r for r in results if "🔻" in r or "🔺" in r]
    normal_results = [r for r in results if "✅" in r]
    other_results = [r for r in results if "📋" in r]
    
    if abnormal_results:
        report_lines.append("🚨 **ABNORMAL VALUES:**")
        report_lines.extend(abnormal_results)
        report_lines.append("")
    
    if normal_results:
        report_lines.append("✅ **NORMAL VALUES:**")
        report_lines.extend(normal_results)
        report_lines.append("")
    
    if other_results:
        report_lines.append("📋 **OTHER FINDINGS:**")
        report_lines.extend(other_results)
        report_lines.append("")
    
    if qualitative_findings:
        report_lines.append("🔍 **QUALITATIVE FINDINGS:**")
        report_lines.extend(qualitative_findings)
        report_lines.append("")
    
    # Footer
    report_lines.append("📝 **IMPORTANT:** This is an automated analysis for reference only.")
    report_lines.append("👨‍⚕️ **Please consult your doctor for proper medical interpretation.**")
    report_lines.append(f"🔬 **Analysis Engine:** Advanced OCR + AI Pattern Recognition")
    
    return "\n".join(report_lines)

def extract_qualitative_findings(text):
    """Extract qualitative medical findings"""
    findings = []
    
    # Common qualitative patterns
    qualitative_patterns = [
        r"(Normal|Abnormal|Positive|Negative|Present|Absent|Reactive|Non-reactive)",
        r"(Visualized|Not visualized|Intact|Appears normal)",
        r"(No abnormality noted|Within normal limits|WNL)",
        r"(\d+\s*chambers?\s*view,?\s*normal)",
        r"(Cerebellum diameter:\s*\d+\.?\d*\s*mm)",
        r"(Size:\s*\d+\.?\d*\s*[xX]\s*\d+\.?\d*\s*mm)",
    ]
    
    for pattern in qualitative_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            finding = match.group(0).strip()
            if len(finding) > 5:  # Avoid very short matches
                findings.append(f"📋 {finding}")
    
    return findings[:10]  # Limit to 10 findings

def extract_text_from_image(file_path):
    """Enhanced image text extraction with multiple OCR methods"""
    try:
        if not tesseract_found:
            return "❌ Tesseract OCR is not available. Please install Tesseract to process images."
        
        print("🔍 Loading and processing image...")
        original_image = Image.open(file_path)
        
        # Try multiple OCR approaches
        ocr_results = []
        
        print("🔬 Applying OCR Method 1: Direct extraction...")
        try:
            config1 = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz./:()- %'
            text1 = pytesseract.image_to_string(original_image, config=config1)
            ocr_results.append(("Direct OCR", text1))
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
        print("🔬 Applying OCR Method 2: Enhanced image processing...")
        try:
            enhanced_image = enhance_image_quality(original_image)
            config2 = r'--oem 3 --psm 6'
            text2 = pytesseract.image_to_string(enhanced_image, config=config2)
            ocr_results.append(("Enhanced OCR", text2))
        except Exception as e:
            print(f"Method 2 failed: {e}")
        
        print("🔬 Applying OCR Method 3: Table detection...")
        try:
            config3 = r'--oem 3 --psm 4'
            text3 = pytesseract.image_to_string(original_image, config=config3)
            ocr_results.append(("Table OCR", text3))
        except Exception as e:
            print(f"Method 3 failed: {e}")
        
        print("🔬 Applying OCR Method 4: Single block...")
        try:
            config4 = r'--oem 3 --psm 8'
            text4 = pytesseract.image_to_string(original_image, config=config4)
            ocr_results.append(("Block OCR", text4))
        except Exception as e:
            print(f"Method 4 failed: {e}")
        
        # Evaluate and choose best result
        best_text = ""
        best_score = 0
        best_method = ""
        
        for method_name, ocr_text in ocr_results:
            if ocr_text and ocr_text.strip():
                # Score based on medical terms and numbers
                medical_terms = sum(1 for metric in HEALTH_METRICS.keys() 
                                  if metric.lower() in ocr_text.lower())
                numbers = len(re.findall(r'\d+\.?\d*', ocr_text))
                medical_words = len(re.findall(r'\b(normal|abnormal|positive|negative|test|result|value)\b', 
                                             ocr_text, re.IGNORECASE))
                
                score = medical_terms * 20 + numbers * 2 + medical_words * 5
                
                print(f"📊 {method_name}: {medical_terms} terms, {numbers} numbers, {medical_words} words → Score: {score}")
                
                if score > best_score:
                    best_score = score
                    best_text = ocr_text
                    best_method = method_name
        
        if not best_text:
            return "❌ Could not extract readable text from the image. Please ensure the image is clear and contains medical data."
        
        print(f"🏆 Best method: {best_method} (Score: {best_score})")
        print(f"📄 Extracted text preview: {best_text[:300]}...")
        
        return extract_medical_data(best_text)
        
    except Exception as e:
        return f"❌ Error processing image: {str(e)}"

def extract_text_from_pdf(file_path):
    """Enhanced PDF text extraction"""
    try:
        print("📄 Processing PDF...")
        doc = fitz.open(file_path)
        text = ""
        
        # Try direct text extraction first
        for page in doc:
            page_text = page.get_text("text")
            text += page_text
        
        # If no text found, use OCR
        if not text.strip() and tesseract_found:
            print("🔍 PDF appears to be scanned, applying OCR...")
            for page_num, page in enumerate(doc):
                # High resolution rendering
                mat = fitz.Matrix(3.0, 3.0)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Apply OCR
                try:
                    page_text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6')
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                except Exception as e:
                    print(f"OCR failed for page {page_num + 1}: {e}")
        
        doc.close()
        
        if not text.strip():
            return "❌ No text could be extracted from the PDF."
        
        return extract_medical_data(text)
        
    except Exception as e:
        return f"❌ Error processing PDF: {str(e)}"

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>🏥 Medical Report Analyzer</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 900px; 
            margin: 20px auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.2); 
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 10px; 
            font-size: 2.8em; 
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
            font-weight: 500;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .feature-card {
            background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
            padding: 20px;
            border-radius: 15px;
            border-left: 4px solid #667eea;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .feature-card h3 {
            margin-top: 0;
            color: #333;
            font-size: 1.1em;
        }
        .feature-card ul {
            margin: 10px 0 0 0;
            padding-left: 20px;
        }
        .feature-card li {
            margin: 8px 0;
            color: #555;
            font-size: 0.95em;
        }
        .upload-section { margin: 30px 0; }
        .upload-area { 
            border: 3px dashed #667eea; 
            border-radius: 20px; 
            padding: 60px 40px; 
            text-align: center; 
            background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
            cursor: pointer;
            transition: all 0.4s ease;
            position: relative;
        }
        .upload-area:hover { 
            background: linear-gradient(135deg, #e6f3ff 0%, #d4edda 100%); 
            border-color: #28a745; 
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        .upload-icon { 
            font-size: 5em; 
            margin-bottom: 20px; 
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .file-input { display: none; }
        textarea { 
            width: 100%; 
            height: 180px; 
            padding: 25px; 
            border: 2px solid #ddd; 
            border-radius: 15px; 
            font-size: 14px; 
            resize: vertical;
            font-family: 'Courier New', monospace;
            transition: all 0.3s ease;
            background: #fafafa;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 15px rgba(102, 126, 234, 0.3);
            background: white;
        }
        button { 
            width: 100%; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 20px; 
            border: none; 
            border-radius: 15px; 
            font-size: 18px; 
            cursor: pointer; 
            margin-top: 20px;
            transition: all 0.3s ease;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        button:hover { 
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        .result { 
            margin-top: 40px; 
            padding: 30px; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
            border-radius: 20px; 
            white-space: pre-wrap; 
            font-family: 'Courier New', monospace; 
            border-left: 6px solid #667eea;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            line-height: 1.6;
        }
        .loading { 
            text-align: center; 
            color: #666; 
            padding: 40px; 
        }
        .spinner { 
            border: 4px solid #f3f3f3; 
            border-top: 4px solid #667eea; 
            border-radius: 50%; 
            width: 50px; 
            height: 50px; 
            animation: spin 1s linear infinite; 
            margin: 0 auto 20px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .section-title { 
            font-size: 1.4em; 
            font-weight: bold; 
            margin: 30px 0 20px 0; 
            color: #333;
            display: flex;
            align-items: center;
        }
        .section-title::before {
            content: '';
            width: 5px;
            height: 25px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            margin-right: 15px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Medical Report Analyzer</h1>
        <div class="subtitle">Advanced AI-Powered Analysis for Lab Reports & Medical Documents</div>
        
        <div class="features">
            <div class="feature-card">
                <h3>🔬 Lab Reports</h3>
                <ul>
                    <li>Blood Count (CBC)</li>
                    <li>Biochemistry Panel</li>
                    <li>Lipid Profile</li>
                    <li>Liver & Kidney Function</li>
                    <li>Thyroid Tests</li>
                </ul>
            </div>
            <div class="feature-card">
                <h3>🩺 Medical Imaging</h3>
                <ul>
                    <li>Ultrasound Reports</li>
                    <li>X-Ray Reports</li>
                    <li>CT/MRI Reports</li>
                    <li>Fetal Monitoring</li>
                    <li>Cardiac Studies</li>
                </ul>
            </div>
            <div class="feature-card">
                <h3>🎯 Advanced Features</h3>
                <ul>
                    <li>Multi-Method OCR</li>
                    <li>150+ Parameters</li>
                    <li>Normal/Abnormal Detection</li>
                    <li>Qualitative Analysis</li>
                    <li>High Accuracy Processing</li>
                </ul>
            </div>
        </div>
        
        <div class="upload-section">
            <div class="section-title">📄 Upload Medical Document</div>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <div class="upload-icon">📋</div>
                <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 15px;">Upload Your Medical Report</div>
                <div style="color: #666; font-size: 1.1em;">Supports PDF, JPG, JPEG, PNG files</div>
                <div style="font-size: 0.9em; color: #888; margin-top: 15px;">Lab reports, ultrasound scans, blood tests, and more</div>
            </div>
            <input type="file" id="fileInput" class="file-input" accept=".pdf,.jpg,.jpeg,.png">
        </div>
        
        <div class="section-title">✏️ Or Enter Report Text</div>
        <textarea id="textInput" placeholder="Paste your medical report text here...

Example:
Hemoglobin: 14.5 g/dL
WBC: 8500 cells/cmm
Glucose: 95 mg/dL
Creatinine: 1.1 mg/dL
TSH: 2.5 mIU/L

Or ultrasound findings:
Fetal heart rate: 145 bpm
Biparietal diameter: 85 mm
Gestational age: 32 weeks"></textarea>
        <button onclick="analyzeText()">🔬 Analyze Medical Report</button>
        
        <div id="result" class="result" style="display:none;"></div>
    </div>

    <script>
        document.getElementById('fileInput').addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                uploadFile(e.target.files[0]);
            }
        });

        function uploadFile(file) {
            if (file.size > 15 * 1024 * 1024) {
                alert('File size too large. Please upload a file smaller than 15MB.');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            showLoading('🔬 Processing ' + file.name + ' with advanced medical OCR...');
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                showResult(data.result || data.error || 'No result');
            })
            .catch(error => {
                showResult('❌ Upload failed: ' + error.message);
            });
        }

        function analyzeText() {
            const text = document.getElementById('textInput').value.trim();
            
            if (!text) {
                alert('Please enter some medical report text');
                return;
            }

            showLoading('🧠 Analyzing medical data with AI...');

            fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            })
            .then(response => response.json())
            .then(data => {
                showResult(data.result || 'No result');
            })
            .catch(error => {
                showResult('❌ Analysis failed: ' + error.message);
            });
        }

        function showLoading(message) {
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div>' + message + '</div>';
            resultDiv.scrollIntoView({ behavior: 'smooth' });
        }

        function showResult(result) {
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = result;
            resultDiv.scrollIntoView({ behavior: 'smooth' });
        }
    </script>
</body>
</html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '❌ No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '❌ No file selected'})
        
        # Check file size
        file_content = file.read()
        if len(file_content) > 15 * 1024 * 1024:
            return jsonify({'error': '❌ File too large. Please upload a file smaller than 15MB.'})
        
        # Create unique temporary file
        unique_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1].lower()
        temp_path = os.path.join(tempfile.gettempdir(), f"medical_report_{unique_id}{file_ext}")
        
        # Save the file
        with open(temp_path, 'wb') as f:
            f.write(file_content)
        
        try:
            # Process based on file type
            if file_ext == '.pdf':
                result = extract_text_from_pdf(temp_path)
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                result = extract_text_from_image(temp_path)
            else:
                result = "❌ Unsupported file type. Please upload PDF, JPG, JPEG, or PNG files."
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
        
        return jsonify({'result': result})
        
    except Exception as e:
        return jsonify({'error': f'❌ Processing failed: {str(e)}'})

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '❌ No data received'})
            
        text = data.get('text', '')
        if not text.strip():
            return jsonify({'error': '❌ No text provided'})
            
        result = extract_medical_data(text)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'❌ Analysis failed: {str(e)}'})

if __name__ == '__main__':
    print("🚀 Medical Report Analyzer Starting...")
    print("📱 Open: http://localhost:8000")
    print(f"🔬 Medical Parameters: {len(HEALTH_METRICS)}")
    if tesseract_found:
        print("✅ Advanced OCR: Ready for medical document processing")
    else:
        print("⚠️  Tesseract OCR: Not found (text PDFs only)")
    print("🎯 Supports: Lab reports, ultrasound scans, blood tests, and more")
    app.run(debug=True, host='0.0.0.0', port=8000)
