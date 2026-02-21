"""
Documents App - OCR Service
Extracts data from Aadhaar Card and 7/12 Extract using EasyOCR (free, offline).
No API keys required!

EasyOCR supports English, Hindi, and Marathi out of the box.
Models are downloaded automatically on first use (~100-200MB).
"""

import re
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

# Lazy-loaded EasyOCR reader (models are loaded once and reused)
_reader = None


def _get_reader():
    """Get or create the EasyOCR reader (lazy initialization)"""
    global _reader
    if _reader is None:
        try:
            import easyocr
            logger.info("Initializing EasyOCR reader (first load downloads models)...")
            _reader = easyocr.Reader(
                ['en', 'hi', 'mr'],  # English + Hindi + Marathi
                gpu=False,           # CPU mode (works everywhere)
            )
            logger.info("EasyOCR reader initialized successfully")
        except ImportError:
            logger.error(
                "EasyOCR is not installed. Install with: pip install easyocr"
            )
            raise
    return _reader


class OCRResult:
    """Structured result from OCR extraction"""
    
    def __init__(self, success=False, data=None, raw_text='', confidence=0.0, errors=None):
        self.success = success
        self.data = data or {}
        self.raw_text = raw_text
        self.confidence = confidence
        self.errors = errors or []
    
    def to_dict(self):
        return {
            'success': self.success,
            'data': self.data,
            'raw_text': self.raw_text,
            'confidence': self.confidence,
            'errors': self.errors,
        }


class OCRService:
    """
    OCR Service for extracting data from Indian government documents.
    Uses EasyOCR — free, offline, no API keys needed.
    Supports English, Hindi, and Marathi.
    """
    
    def _extract_text(self, image_content: bytes) -> str:
        """
        Extract text from image bytes using EasyOCR.
        
        Args:
            image_content: Raw image bytes
            
        Returns:
            Extracted text as a single string
        """
        reader = _get_reader()
        
        # EasyOCR can read from bytes directly
        results = reader.readtext(image_content, detail=1, paragraph=True)
        
        # results is a list of (bbox, text, confidence) tuples
        # Sort by vertical position (top to bottom) for natural reading order
        lines = []
        for item in results:
            if len(item) >= 2:
                text = item[1] if isinstance(item[1], str) else str(item[1])
                lines.append(text)
        
        return '\n'.join(lines)
    
    def extract_from_aadhaar(self, file) -> OCRResult:
        """
        Extract data from an Aadhaar card image.
        
        Extracts:
        - Full Name (English)
        - Date of Birth
        - Gender
        - Aadhaar Number (masked - last 4 digits only)
        
        Args:
            file: Uploaded file object
            
        Returns:
            OCRResult with extracted data
        """
        try:
            image_content = file.read()
            file.seek(0)  # Reset file pointer for later use
            
            # Extract text using EasyOCR
            raw_text = self._extract_text(image_content)
            
            if not raw_text.strip():
                return OCRResult(
                    success=False,
                    errors=['Could not extract text from the image. Please ensure the image is clear and well-lit.']
                )
            
            logger.info(f"Aadhaar OCR raw text:\n{raw_text}")
            
            # Parse Aadhaar data from raw text
            data = self._parse_aadhaar_text(raw_text)
            confidence = self._calculate_aadhaar_confidence(data)
            
            return OCRResult(
                success=True,
                data=data,
                raw_text=raw_text,
                confidence=confidence,
            )
            
        except ImportError:
            return OCRResult(
                success=False,
                errors=['EasyOCR is not installed. Run: pip install easyocr']
            )
        except Exception as e:
            logger.error(f"Aadhaar OCR extraction failed: {e}")
            return OCRResult(
                success=False,
                errors=[f'OCR extraction failed: {str(e)}']
            )
    
    def _parse_aadhaar_text(self, text: str) -> dict:
        """
        Parse extracted text to find Aadhaar card fields.
        
        Aadhaar cards have these common patterns:
        - Name in English (after DOB or "Name:" label)
        - DOB in DD/MM/YYYY format
        - Gender: Male/Female/Transgender
        - 12-digit Aadhaar number (XXXX XXXX XXXX)
        """
        data = {
            'name': '',
            'date_of_birth': '',
            'gender': '',
            'aadhaar_number_masked': '',
            'age': None,
        }
        
        lines = text.strip().split('\n')
        clean_lines = [line.strip() for line in lines if line.strip()]
        full_text_joined = ' '.join(clean_lines)
        
        # ─── Extract Aadhaar Number (12 digits, possibly with spaces) ───
        aadhaar_pattern = re.compile(r'\b(\d{4}\s?\d{4}\s?\d{4})\b')
        for line in clean_lines:
            match = aadhaar_pattern.search(line)
            if match:
                aadhaar_num = match.group(1).replace(' ', '')
                if len(aadhaar_num) == 12:
                    data['aadhaar_number_masked'] = f"XXXX-XXXX-{aadhaar_num[-4:]}"
                    break
        
        # ─── Extract Date of Birth ───
        dob_patterns = [
            re.compile(r'(?:DOB|D\.?O\.?B\.?|Date of Birth|जन्म तिथि|Birth)\s*[:\-]?\s*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})'),
            re.compile(r'(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})'),  # Generic date
            re.compile(r'(?:Year of Birth|YOB)\s*[:\-]?\s*(\d{4})'),  # Year only
        ]
        
        for pattern in dob_patterns:
            match = pattern.search(full_text_joined)
            if match:
                date_str = match.group(1)
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        data['date_of_birth'] = parsed_date.strftime('%Y-%m-%d')
                        today = date.today()
                        data['age'] = today.year - parsed_date.year - (
                            (today.month, today.day) < (parsed_date.month, parsed_date.day)
                        )
                        break
                    except ValueError:
                        continue
                
                # Year only fallback
                if not data['date_of_birth'] and len(date_str) == 4:
                    year = int(date_str)
                    data['date_of_birth'] = f"{year}-01-01"
                    data['age'] = date.today().year - year
                
                if data['date_of_birth']:
                    break
        
        # ─── Extract Gender ───
        gender_patterns = [
            (re.compile(r'\b(MALE|Male|male|पुरुष)\b'), 'male'),
            (re.compile(r'\b(FEMALE|Female|female|महिला|स्त्री)\b'), 'female'),
            (re.compile(r'\b(TRANSGENDER|Transgender|transgender|तृतीय लिंग)\b'), 'other'),
        ]
        
        for pattern, gender_value in gender_patterns:
            if pattern.search(full_text_joined):
                data['gender'] = gender_value
                break
        
        # ─── Extract Name ───
        name_patterns = [
            re.compile(r'(?:Name|नाम)\s*[:\-]?\s*([A-Za-z\s]+)', re.IGNORECASE),
        ]
        
        for pattern in name_patterns:
            match = pattern.search(full_text_joined)
            if match:
                name = match.group(1).strip()
                noise_words = ['government', 'india', 'unique', 'identification', 
                              'authority', 'aadhaar', 'aadhar', 'male', 'female',
                              'dob', 'address', 'year', 'birth']
                name_words = name.split()
                clean_name = ' '.join(
                    w for w in name_words 
                    if w.lower() not in noise_words and len(w) > 1
                )
                if clean_name and len(clean_name) > 2:
                    data['name'] = clean_name.title()
                    break
        
        # Fallback: find name from lines
        if not data['name']:
            for line in clean_lines:
                if re.search(r'\d', line):
                    continue
                if any(kw in line.lower() for kw in ['government', 'india', 'aadhaar', 'unique', 'authority', 'address', 'dob']):
                    continue
                words = line.split()
                if 1 <= len(words) <= 5 and all(re.match(r'^[A-Za-z]+$', w) for w in words):
                    data['name'] = line.title()
                    break
        
        return data
    
    def _calculate_aadhaar_confidence(self, data: dict) -> float:
        """Calculate confidence score for Aadhaar extraction"""
        score = 0.0
        total_fields = 4  # name, dob, gender, aadhaar_number
        
        if data.get('name'):
            score += 1
        if data.get('date_of_birth'):
            score += 1
        if data.get('gender'):
            score += 1
        if data.get('aadhaar_number_masked'):
            score += 1
        
        return round((score / total_fields) * 100, 1)
    
    def extract_from_seven_twelve(self, file) -> OCRResult:
        """
        Extract data from a 7/12 Extract (सातबारा उतारा).
        Maharashtra-specific land record document.
        
        Extracts:
        - Land size (area in Hectare/Acre/Guntha)
        - Village name
        - Taluka
        - District 
        - State (default: Maharashtra)
        - Survey/Gut number
        - Owner name(s)
        """
        try:
            image_content = file.read()
            file.seek(0)
            
            # Extract text using EasyOCR
            raw_text = self._extract_text(image_content)
            
            if not raw_text.strip():
                return OCRResult(
                    success=False,
                    errors=['Could not extract text from the image. Please ensure the image is clear and well-lit.']
                )
            
            logger.info(f"7/12 OCR raw text:\n{raw_text}")
            
            # Parse 7/12 data from raw text
            data = self._parse_seven_twelve_text(raw_text)
            confidence = self._calculate_seven_twelve_confidence(data)
            
            return OCRResult(
                success=True,
                data=data,
                raw_text=raw_text,
                confidence=confidence,
            )
            
        except ImportError:
            return OCRResult(
                success=False,
                errors=['EasyOCR is not installed. Run: pip install easyocr']
            )
        except Exception as e:
            logger.error(f"7/12 OCR extraction failed: {e}")
            return OCRResult(
                success=False,
                errors=[f'OCR extraction failed: {str(e)}']
            )
    
    def _parse_seven_twelve_text(self, text: str) -> dict:
        """
        Parse extracted text to find 7/12 Extract fields.
        
        7/12 documents typically contain:
        - गावाचे नाव (Village name)
        - तालुका (Taluka)
        - जिल्हा (District)
        - गट क्र / सर्वे नंबर (Survey/Gut number)
        - क्षेत्र (Area) in हेक्टर, एकर, गुंठे
        - खातेदाराचे नाव (Owner name)
        """
        data = {
            'village': '',
            'taluka': '',
            'district': '',
            'state': 'Maharashtra',  # 7/12 is Maharashtra-specific
            'land_size': 0.0,
            'land_size_unit': 'acres',
            'survey_number': '',
            'owner_name': '',
        }
        
        lines = text.strip().split('\n')
        clean_lines = [line.strip() for line in lines if line.strip()]
        full_text_joined = ' '.join(clean_lines)
        
        # ─── Extract Village ───
        village_patterns = [
            re.compile(r'(?:गावाचे नाव|गाव|Village|मौजे)\s*[:\-]?\s*([^\n,]+)', re.IGNORECASE),
            re.compile(r'(?:मौजा|मौजे|Mauza|Mouza)\s*[:\-]?\s*([^\n,]+)', re.IGNORECASE),
        ]
        for pattern in village_patterns:
            match = pattern.search(full_text_joined)
            if match:
                village = match.group(1).strip()
                village = re.sub(r'[^\w\s\u0900-\u097F]', '', village).strip()
                if village and len(village) > 1:
                    data['village'] = village
                    break
        
        # ─── Extract Taluka ───
        taluka_patterns = [
            re.compile(r'(?:तालुका|Taluka|Ta\.?)\s*[:\-]?\s*([^\n,]+)', re.IGNORECASE),
        ]
        for pattern in taluka_patterns:
            match = pattern.search(full_text_joined)
            if match:
                taluka = match.group(1).strip()
                taluka = re.sub(r'[^\w\s\u0900-\u097F]', '', taluka).strip()
                if taluka and len(taluka) > 1:
                    data['taluka'] = taluka
                    break
        
        # ─── Extract District ───
        district_patterns = [
            re.compile(r'(?:जिल्हा|District|Dist\.?|Jilha)\s*[:\-]?\s*([^\n,]+)', re.IGNORECASE),
        ]
        for pattern in district_patterns:
            match = pattern.search(full_text_joined)
            if match:
                district = match.group(1).strip()
                district = re.sub(r'[^\w\s\u0900-\u097F]', '', district).strip()
                if district and len(district) > 1:
                    data['district'] = district
                    break
        
        # ─── Extract Survey/Gut Number ───
        survey_patterns = [
            re.compile(r'(?:गट\s*(?:क्र|नं)\.?|Survey\s*No\.?|Gut\s*No\.?|सर्वे\s*(?:क्र|नं)\.?)\s*[:\-]?\s*(\d+[\/\-]?\d*)', re.IGNORECASE),
        ]
        for pattern in survey_patterns:
            match = pattern.search(full_text_joined)
            if match:
                data['survey_number'] = match.group(1).strip()
                break
        
        # ─── Extract Land Area ───
        area_patterns = [
            # Hectare: "0.25 हे." or "1.50 Hectare"
            re.compile(r'(\d+\.?\d*)\s*(?:हे\.?|हेक्टर|Hectare|Ha\.?|ha\.?)', re.IGNORECASE),
            # Acre: "2.5 एकर" or "2.5 Acre"
            re.compile(r'(\d+\.?\d*)\s*(?:एकर|Acre|Ac\.?)', re.IGNORECASE),
            # Guntha: "10 गुंठे"
            re.compile(r'(\d+\.?\d*)\s*(?:गुंठे|गुंठा|Guntha|Gunthe)', re.IGNORECASE),
            # Generic area
            re.compile(r'(?:क्षेत्र|क्षेत्रफळ|Area)\s*[:\-]?\s*(\d+\.?\d*)', re.IGNORECASE),
        ]
        
        for i, pattern in enumerate(area_patterns):
            match = pattern.search(full_text_joined)
            if match:
                area_value = float(match.group(1))
                if i == 0:  # Hectare → Acres
                    data['land_size'] = round(area_value * 2.47105, 2)
                elif i == 1:  # Already Acres
                    data['land_size'] = round(area_value, 2)
                elif i == 2:  # Guntha → Acres (40 guntha = 1 acre)
                    data['land_size'] = round(area_value / 40, 2)
                else:  # Assume hectare
                    data['land_size'] = round(area_value * 2.47105, 2)
                data['land_size_unit'] = 'acres'
                break
        
        # ─── Extract Owner Name ───
        owner_patterns = [
            re.compile(r'(?:खातेदाराचे नाव|खातेदार|Owner|Holder)\s*[:\-]?\s*([^\n]+)', re.IGNORECASE),
            re.compile(r'(?:नाव|Name)\s*[:\-]?\s*([^\n]+)', re.IGNORECASE),
        ]
        for pattern in owner_patterns:
            match = pattern.search(full_text_joined)
            if match:
                owner = match.group(1).strip()
                owner = re.sub(r'[^\w\s\u0900-\u097F\.]', '', owner).strip()
                if owner and len(owner) > 1:
                    data['owner_name'] = owner
                    break
        
        return data
    
    def _calculate_seven_twelve_confidence(self, data: dict) -> float:
        """Calculate confidence score for 7/12 extraction"""
        score = 0.0
        total_fields = 5  # village, district, land_size, survey_number, owner_name
        
        if data.get('village'):
            score += 1
        if data.get('district'):
            score += 1
        if data.get('land_size', 0) > 0:
            score += 1
        if data.get('survey_number'):
            score += 1
        if data.get('owner_name'):
            score += 1
        
        return round((score / total_fields) * 100, 1)
