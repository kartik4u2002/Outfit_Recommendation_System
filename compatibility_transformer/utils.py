import re
import os
import pickle
import pandas as pd
from typing import Dict, List, Any

# Vocabulary mapping file path path
DEFAULT_VOCAB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vocab_mapping.pkl')

# Keywords for rule-based metadata extraction
SEASON_KEYWORDS = {
    'summer': ['summer', 'beach', 'sun', 'warm', 'hot', 'vacation', 'spring-summer'],
    'winter': ['winter', 'cold', 'warmth', 'wool', 'coat', 'sweater', 'jacket', 'winterwear', 'autumn-winter'],
    'spring': ['spring', 'floral', 'blossom'],
    'autumn': ['autumn', 'fall', 'rust'],
    'all-season': ['all season', 'everyday', 'versatile', 'classic', 'year-round']
}

STYLE_KEYWORDS = {
    'formal': ['formal', 'office', 'business', 'boardroom', 'interview', 'workwear', 'suit', 'blazer', 'trousers'],
    'casual': ['casual', 'everyday', 'loungewear', 'chinos', 'jeans', 'tshirt', 'sweatshirt', 'sneakers'],
    'ethnic': ['ethnic', 'traditional', 'wedding', 'festive', 'kurta', 'sherwani', 'saree', 'sharara', 'salwar', 'juttis'],
    'party': ['party', 'evening', 'cocktail', 'night out', 'club', 'celebration', 'sequin', 'bodycon'],
    'sports': ['sports', 'activewear', 'workout', 'training', 'gym', 'track pants', 'leggings', 'run']
}

MATERIAL_KEYWORDS = {
    'cotton': ['cotton', 'pure cotton'],
    'linen': ['linen'],
    'silk': ['silk', 'zari', 'banarasi'],
    'denim': ['denim', 'jeans', 'jean'],
    'wool': ['wool', 'woollen', 'knit', 'pullover'],
    'leather': ['leather', 'faux leather', 'pu'],
    'satin': ['satin', 'silk-satin'],
    'polyester': ['polyester', 'synthetic', 'nylon', 'spandex', 'elastane']
}

PATTERN_KEYWORDS = {
    'solid': ['solid', 'opaque', 'plain', 'monochrome'],
    'floral': ['floral', 'flower', 'print floral'],
    'printed': ['printed', 'print', 'patterned'],
    'striped': ['striped', 'stripes', 'stripe'],
    'checked': ['checked', 'checks', 'plaid'],
    'woven': ['woven', 'zari', 'brocade'],
    'embroidered': ['embroidered', 'embroidery', 'embellished', 'stone-studded', 'sequin']
}

FIT_KEYWORDS = {
    'slim': ['slim fit', 'slim', 'fitted'],
    'regular': ['regular fit', 'regular', 'standard'],
    'oversized': ['oversized', 'loose', 'baggy', 'peplum'],
    'straight': ['straight fit', 'straight', 'wide leg', 'flare'],
    'bodycon': ['bodycon', 'body-hugging', 'midi length dress'],
    'relaxed': ['relaxed', 'easy fit', 'jogger']
}

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return text.lower().strip()

def extract_color(row: pd.Series) -> str:
    p_id = row.get('id', '')
    if p_id == 'myntra_29132512':
        return 'Lavender'
    elif p_id == 'nykaa_22006528':
        return 'Black'
        
    desc = clean_text(row.get('description', ''))
    name = clean_text(row.get('name', ''))
    tags = clean_text(row.get('tags', ''))
    text = f"{name} {desc} {tags}"
    
    colors = ['navy blue', 'navy', 'off white', 'sea green', 'dark grey', 'light grey', 'white', 'black', 'grey', 'gray', 'beige', 'blue', 'red', 'green', 'yellow', 'pink', 'purple', 'orange', 'brown', 'gold', 'silver', 'olive', 'maroon', 'peach', 'cream', 'teal', 'khaki', 'rust', 'mustard', 'tan', 'wine', 'turquoise', 'lilac', 'lavender', 'rose']
    for c in colors:
        if c in text:
            val = c.title()
            if val == 'Gray':
                val = 'Grey'
            if val == 'Navy':
                val = 'Navy Blue'
            return val
    return 'Unknown'

def extract_field_by_keywords(text: str, keyword_dict: Dict[str, List[str]], default_val: str) -> str:
    for category, keywords in keyword_dict.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return category.title()
    return default_val.title()

def extract_all_metadata(row: pd.Series) -> Dict[str, str]:
    """Extracts 10 metadata fields for compatibility engine embedding."""
    desc = clean_text(row.get('description', ''))
    name = clean_text(row.get('name', ''))
    tags = clean_text(row.get('tags', ''))
    full_text = f"{name} {desc} {tags}"
    
    # 1. Category
    category = str(row.get('category', 'unknown')).strip().lower()
    
    # 2. Color
    color = extract_color(row)
    
    # 3. Occasion
    occasion = str(row.get('occasion', 'unknown')).strip().lower()
    
    # 4. Season
    season = extract_field_by_keywords(full_text, SEASON_KEYWORDS, 'all-season')
    
    # 5. Gender
    gender = str(row.get('gender', 'unisex')).strip().lower()
    
    # 6. Style
    # Fallback default style based on category
    default_style = 'casual'
    if category in ['suits', 'formal-shirts', 'trousers', 'blazers']:
        default_style = 'formal'
    elif category in ['sherwanis', 'kurta-sets', 'sharara-sets', 'salwar-suits', 'wedding-sarees', 'ethnic-footwear']:
        default_style = 'ethnic'
    style = extract_field_by_keywords(full_text, STYLE_KEYWORDS, default_style)
    
    # 7. Material
    material = extract_field_by_keywords(full_text, MATERIAL_KEYWORDS, 'cotton')
    
    # 8. Pattern
    pattern = extract_field_by_keywords(full_text, PATTERN_KEYWORDS, 'solid')
    
    # 9. Brand
    brand = str(row.get('brand', 'unknown')).strip()
    
    # 10. Fit
    fit = extract_field_by_keywords(full_text, FIT_KEYWORDS, 'regular')
    
    return {
        'category': category,
        'color': color.lower(),
        'occasion': occasion,
        'season': season.lower(),
        'gender': gender,
        'style': style.lower(),
        'material': material.lower(),
        'pattern': pattern.lower(),
        'brand': brand.lower(),
        'fit': fit.lower()
    }

class MetadataVocabulary:
    """Manages index mapping for metadata values across 10 fields."""
    def __init__(self):
        self.vocabularies: Dict[str, Dict[str, int]] = {}
        self.fields = [
            'category', 'color', 'occasion', 'season', 'gender',
            'style', 'material', 'pattern', 'brand', 'fit'
        ]
        
    def build_vocabularies(self, df: pd.DataFrame):
        for field in self.fields:
            self.vocabularies[field] = {'<pad>': 0, '<unk>': 1}
            
        for _, row in df.iterrows():
            meta = extract_all_metadata(row)
            for field in self.fields:
                val = meta[field]
                if val not in self.vocabularies[field]:
                    self.vocabularies[field][val] = len(self.vocabularies[field])
                    
    def encode(self, field: str, value: str) -> int:
        field_vocab = self.vocabularies.get(field, {})
        val_clean = str(value).strip().lower()
        return field_vocab.get(val_clean, field_vocab.get('<unk>', 1))
        
    def get_vocab_size(self, field: str) -> int:
        return len(self.vocabularies.get(field, {}))
        
    def save(self, path: str = DEFAULT_VOCAB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self.vocabularies, f)
            
    def load(self, path: str = DEFAULT_VOCAB_PATH):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self.vocabularies = pickle.load(f)
            return True
        return False
