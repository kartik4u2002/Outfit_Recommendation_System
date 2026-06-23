with open('create_notebook.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Normalize newlines
code = code.replace('\r\n', '\n')

section_7_code = """
# Section 7: User & Context-Aware Recommendations
cells.append(nbf.v4.new_markdown_cell(\"\"\"## SECTION 7: User & Context-Aware Recommendations
> This section extends the base outfit generator with 4 profile dimensions: Gender, Age Group, Occasion, and Style Preference.
> Recommendations are re-ranked using a 5-signal weighted scorer that combines base compatibility (30%), occasion relevance (25%), color context (20%), style alignment (15%), and age-formality fit (10%).\"\"\"))

# 7a: User Profile Schema
cells.append(nbf.v4.new_markdown_cell(\"\"\"## 7a: User Profile Schema
Define the UserProfile dataclass to represent demographic and situational context.\"\"\"))

cells.append(nbf.v4.new_code_cell(\"\"\"from dataclasses import dataclass, field
from typing import Optional

@dataclass
class UserProfile:
    \\\"\\\"\\\"
    Central user profile object for context-aware recommendations.
    All fields are optional — missing fields = no filtering on that dimension.
    \\\"\\\"\\\"
    gender:      Optional[str] = None   # 'Men', 'Women', 'Boys', 'Girls', 'Unisex'
    age_group:   Optional[str] = None   # '20s', '30s', '40s', '50s+'
    occasion:    Optional[str] = None   # 'Office', 'Party', 'Wedding', 'Beach', 
                                        #  'Casual', 'Formal', 'Date Night', 'Sport'
    style_pref:  Optional[str] = None   # 'Formal', 'Smart Casual', 'Casual', 
                                        #  'Streetwear', 'Bohemian', 'Minimalist'
    
    def summary(self) -> str:
        parts = []
        if self.gender:    parts.append(f"Gender: {self.gender}")
        if self.age_group: parts.append(f"Age: {self.age_group}")
        if self.occasion:  parts.append(f"Occasion: {self.occasion}")
        if self.style_pref:parts.append(f"Style: {self.style_pref}")
        return " | ".join(parts) if parts else "No profile set"

# Demo: create test profiles used throughout this section
profile_office_man    = UserProfile(gender='Men',   age_group='30s', 
                                    occasion='Office',  style_pref='Formal')
profile_party_woman   = UserProfile(gender='Women', age_group='20s', 
                                    occasion='Party',   style_pref='Smart Casual')
profile_casual_teen   = UserProfile(gender='Boys',  age_group='20s', 
                                    occasion='Casual',  style_pref='Streetwear')
profile_wedding_woman = UserProfile(gender='Women', age_group='40s', 
                                    occasion='Wedding', style_pref='Formal')

print("Sample profiles created:")
for p in [profile_office_man, profile_party_woman, 
          profile_casual_teen, profile_wedding_woman]:
    print(f"  → {p.summary()}")\"\"\"))


# 7b: Context Mapping Tables
cells.append(nbf.v4.new_markdown_cell(\"\"\"## 7b: Context Mapping Tables
Static lookup tables to match profile dimensions with styling preferences.\"\"\"))

cells.append(nbf.v4.new_code_cell(\"\"\"# OCCASION → article type preferences + color palette
OCCASION_PROFILE = {
    'Office': {
        'preferred_types':  ['formal-shirts', 'linen-shirts', 'trousers', 'chinos', 'blazers', 'suits', 'formal-shoes', 'loafers', 'watches'],
        'preferred_colors': ['White', 'Black', 'Grey', 'Navy Blue', 'Beige', 'Off White'],
        'avoid_types':      ['shorts', 'track-pants', 'activewear', 'caps'],
        'formality_score':  0.9,
    },
    'Party': {
        'preferred_types':  ['party-dresses', 'casual-dresses', 'tops', 'jeans', 'heels', 'clutches', 'earrings', 'necklaces'],
        'preferred_colors': ['Black', 'Red', 'Maroon', 'Gold', 'Silver', 'Navy Blue', 'Pink'],
        'avoid_types':      ['track-pants', 'running-shoes', 'trousers'],
        'formality_score':  0.6,
    },
    'Wedding': {
        'preferred_types':  ['kurta-sets', 'sherwanis', 'sharara-sets', 'salwar-suits', 'wedding-sarees', 'blazers', 'heels', 'flats', 'ethnic-footwear', 'clutches', 'earrings', 'necklaces'],
        'preferred_colors': ['Red', 'Gold', 'Maroon', 'Pink', 'Cream', 'Beige', 'Navy Blue', 'Off White'],
        'avoid_types':      ['jeans', 'tshirts', 'sneakers', 'shorts'],
        'formality_score':  0.95,
    },
    'Beach': {
        'preferred_types':  ['shorts', 'tshirts', 'casual-dresses', 'maxi-dresses', 'sandals', 'flats', 'sunglasses', 'caps'],
        'preferred_colors': ['White', 'Blue', 'Yellow', 'Tan', 'Light Blue', 'Green'],
        'avoid_types':      ['formal-shoes', 'blazers', 'trousers', 'sweaters', 'boots'],
        'formality_score':  0.1,
    },
    'Casual': {
        'preferred_types':  ['tshirts', 'casual-shirts', 'polo-tshirts', 'jeans', 'shorts', 'sneakers', 'loafers', 'caps', 'handbags'],
        'preferred_colors': ['Blue', 'White', 'Grey', 'Black', 'Olive', 'Khaki', 'Red'],
        'avoid_types':      ['formal-shoes', 'blazers', 'trousers'],
        'formality_score':  0.2,
    },
    'Formal': {
        'preferred_types':  ['formal-shirts', 'trousers', 'chinos', 'blazers', 'suits', 'formal-shoes', 'loafers', 'watches'],
        'preferred_colors': ['White', 'Black', 'Navy Blue', 'Dark Grey', 'Grey', 'Maroon'],
        'avoid_types':      ['jeans', 'tshirts', 'sneakers', 'shorts', 'caps'],
        'formality_score':  1.0,
    },
    'Date Night': {
        'preferred_types':  ['casual-shirts', 'party-dresses', 'casual-dresses', 'maxi-dresses', 'jeans', 'heels', 'loafers', 'watches', 'earrings', 'necklaces'],
        'preferred_colors': ['Black', 'Red', 'Maroon', 'Navy Blue', 'White'],
        'avoid_types':      ['track-pants', 'running-shoes', 'caps'],
        'formality_score':  0.65,
    },
    'Sport': {
        'preferred_types':  ['track-pants', 'activewear', 'tshirts', 'shorts', 'running-shoes', 'caps'],
        'preferred_colors': ['Black', 'White', 'Grey', 'Blue', 'Red'],
        'avoid_types':      ['formal-shoes', 'heels', 'formal-shirts', 'party-dresses', 'blazers'],
        'formality_score':  0.05,
    },
}

# AGE GROUP → style modifier weights
AGE_STYLE_WEIGHTS = {
    '20s': {
        'style_boost':  ['Streetwear', 'Casual', 'Smart Casual'],
        'color_boost':  ['Bold', 'Bright'],
        'formality_adj': -0.1,
        'trend_weight':  0.8,
    },
    '30s': {
        'style_boost':  ['Smart Casual', 'Formal', 'Casual'],
        'color_boost':  ['Neutral', 'Classic'],
        'formality_adj':  0.0,
        'trend_weight':   0.5,
    },
    '40s': {
        'style_boost':  ['Formal', 'Smart Casual', 'Classic'],
        'color_boost':  ['Neutral', 'Muted'],
        'formality_adj':  0.1,
        'trend_weight':   0.3,
    },
    '50s+': {
        'style_boost':  ['Formal', 'Minimalist'],
        'color_boost':  ['Neutral', 'Muted'],
        'formality_adj':  0.15,
        'trend_weight':   0.2,
    },
}

# STYLE PREFERENCE → articleType boosted categories
STYLE_TYPE_MAP = {
    'Formal':       ['formal-shirts', 'trousers', 'chinos', 'blazers', 'suits', 'formal-shoes', 'loafers'],
    'Smart Casual': ['casual-shirts', 'linen-shirts', 'polo-tshirts', 'chinos', 'jeans', 'loafers', 'watches'],
    'Casual':       ['tshirts', 'jeans', 'sneakers', 'shorts', 'caps', 'handbags'],
    'Streetwear':   ['tshirts', 'sweatshirts', 'track-pants', 'sneakers', 'caps'],
    'Bohemian':     ['casual-dresses', 'maxi-dresses', 'skirts', 'sandals', 'flats', 'earrings', 'necklaces'],
    'Minimalist':   ['formal-shirts', 'trousers', 'chinos', 'sneakers', 'formal-shoes', 'watches'],
}

# GENDER → dataset filter values (using exact categories in products.csv: 'men', 'women', 'unisex')
GENDER_FILTER_MAP = {
    'Men':    ['men', 'unisex'],
    'Women':  ['women', 'unisex'],
    'Boys':   ['men', 'unisex'],
    'Girls':  ['women', 'unisex'],
    'Unisex': ['men', 'women', 'unisex'],
}

print("✅ Context mapping tables loaded successfully!")\"\"\"))


# 7c: Profile-Based Candidate Filtering
cells.append(nbf.v4.new_markdown_cell(\"\"\"## 7c: Profile-Based Candidate Filtering
Step to filter out completely incompatible products based on gender and avoid tags.\"\"\"))

cells.append(nbf.v4.new_code_cell(\"\"\"def filter_by_profile(df: pd.DataFrame, profile: UserProfile) -> pd.Index:
    \\\"\\\"\\\"
    Applies gender filter and occasion avoid_types filter.
    Never returns an empty index (falls back to full df.index if over-filtered).
    \\\"\\\"\\\"
    mask = pd.Series([True] * len(df), index=df.index)
    
    # 1. Gender check
    if profile.gender:
        allowed_genders = GENDER_FILTER_MAP.get(profile.gender, [profile.gender.lower()])
        gender_col = [c for c in df.columns if 'gender' in c.lower()][0]
        # Match case-insensitively
        mask &= df[gender_col].str.lower().isin([g.lower() for g in allowed_genders])
        
    # 2. Occasion check: exclude avoid_types
    if profile.occasion and profile.occasion in OCCASION_PROFILE:
        avoid = OCCASION_PROFILE[profile.occasion]['avoid_types']
        type_col = [c for c in df.columns if 'category' in c.lower() or 'article' in c.lower() or 'type' in c.lower()][0]
        mask &= ~df[type_col].str.lower().isin([a.lower() for a in avoid])
        
    filtered = df[mask].index
    if len(filtered) == 0:
        print(f"⚠️ Over-filtered for profile {profile.summary()}, reverting to full dataset.")
        return df.index
        
    return filtered

# Quick checks
test_filtered = filter_by_profile(df, profile_office_man)
print(f"Office Man Profile: filtered {len(df)} items down to {len(test_filtered)}")
test_filtered_party = filter_by_profile(df, profile_party_woman)
print(f"Party Woman Profile: filtered {len(df)} items down to {len(test_filtered_party)}")\"\"\"))


# 7d: Context-Aware Scoring Function
cells.append(nbf.v4.new_markdown_cell(\"\"\"## 7d: Context-Aware Scoring Function
Upgraded scorer incorporating: compatibility (30%), occasion (25%), color (20%), style preference (15%), and age formality (10%).\"\"\"))

cells.append(nbf.v4.new_code_cell(\"\"\"def context_aware_score(
    seed_idx: int,
    candidate_idx: int,
    df: pd.DataFrame,
    sim_matrix: np.ndarray,
    profile: UserProfile
) -> tuple:
    \\\"\\\"\\\"
    Calculates a multi-signal context-aware similarity score in [0.0, 1.0].
    \\\"\\\"\\\"
    # Signal 1: Base compatibility (30%)
    base_score, base_reason = compatibility_score(seed_idx, candidate_idx, df, sim_matrix)
    
    candidate = df.iloc[candidate_idx]
    type_col = [c for c in df.columns if 'category' in c.lower() or 'article' in c.lower() or 'type' in c.lower()][0]
    color_col = [c for c in df.columns if 'color' in c.lower() or 'colour' in c.lower()][0]
    
    item_type = str(candidate.get(type_col, '')).lower()
    item_color = str(candidate.get(color_col, ''))
    
    # Signal 2: Occasion relevance (25%)
    occasion_score = 0.5
    if profile.occasion and profile.occasion in OCCASION_PROFILE:
        occ = OCCASION_PROFILE[profile.occasion]
        preferred = [t.lower() for t in occ['preferred_types']]
        avoided = [t.lower() for t in occ['avoid_types']]
        if item_type in preferred:
            occasion_score = 1.0
        elif item_type in avoided:
            occasion_score = 0.0
        else:
            occasion_score = 0.5
            
    # Signal 3: Color context match (20%)
    color_score = 0.5
    if profile.occasion and profile.occasion in OCCASION_PROFILE:
        pref_colors = [c.lower() for c in OCCASION_PROFILE[profile.occasion]['preferred_colors']]
        neutral_colors = [c.lower() for c in NEUTRAL_COLORS]
        if item_color.lower() in pref_colors:
            color_score = 1.0
        elif item_color.lower() in neutral_colors:
            color_score = 0.7
        else:
            color_score = 0.3
            
    # Signal 4: Style alignment (15%)
    style_score = 0.5
    if profile.style_pref and profile.style_pref in STYLE_TYPE_MAP:
        pref_types = [t.lower() for t in STYLE_TYPE_MAP[profile.style_pref]]
        if item_type in pref_types:
            style_score = 1.0
        else:
            style_score = 0.3
            
    # Signal 5: Age formality fit (10%)
    age_score = 0.5
    if profile.age_group and profile.age_group in AGE_STYLE_WEIGHTS:
        age_cfg = AGE_STYLE_WEIGHTS[profile.age_group]
        target_formality = 0.5 + age_cfg['formality_adj']
        
        # Simple heuristic formality mapping
        formal_types = [t.lower() for t in STYLE_TYPE_MAP.get('Formal', [])]
        casual_types = [t.lower() for t in STYLE_TYPE_MAP.get('Casual', [])]
        
        if item_type in formal_types:
            item_formality = 0.9
        elif item_type in casual_types:
            item_formality = 0.2
        else:
            item_formality = 0.5
            
        age_score = max(0.0, 1.0 - abs(item_formality - target_formality))
        
    final_score = (
        0.30 * base_score +
        0.25 * occasion_score +
        0.20 * color_score +
        0.15 * style_score +
        0.10 * age_score
    )
    
    breakdown = {
        'base': round(base_score, 3),
        'occasion': round(occasion_score, 3),
        'color': round(color_score, 3),
        'style': round(style_score, 3),
        'age_formality': round(age_score, 3),
        'final': round(final_score, 3)
    }
    
    reasons = [base_reason] if base_reason else []
    if occasion_score >= 0.8 and profile.occasion:
        reasons.append(f"suited for {profile.occasion}")
    if color_score >= 0.8 and profile.occasion:
        reasons.append(f"color {item_color} is highly suited for {profile.occasion}")
    if style_score >= 0.8 and profile.style_pref:
        reasons.append(f"matches {profile.style_pref} style preference")
        
    explanation = "; ".join(reasons) if reasons else "Profile-matched style."
    return round(final_score, 3), breakdown, explanation

# Quick test print
t_score, t_bd, t_ex = context_aware_score(0, 1, df, sim_matrix, profile_office_man)
print("Test Score:", t_score)
print("Breakdown:", t_bd)
print("Reason:", t_ex)\"\"\"))


# 7e: Profile-Aware Outfit Generator
cells.append(nbf.v4.new_markdown_cell(\"\"\"## 7e: Profile-Aware Outfit Generator
Generates outfit coordinates utilizing context-aware scoring and hard profile candidate filtering.\"\"\"))

cells.append(nbf.v4.new_code_cell(\"\"\"def generate_profile_outfit(
    seed_idx: int,
    df: pd.DataFrame,
    sim_matrix: np.ndarray,
    profile: UserProfile,
    top_k: int = 5
) -> dict:
    \\\"\\\"\\\"
    Generates a full context-aware outfit.
    \\\"\\\"\\\"
    seed = df.iloc[seed_idx]
    valid_indices = filter_by_profile(df, profile)
    filtered_df = df.loc[valid_indices]
    
    outfit = {
        'seed': seed.to_dict(),
        'profile': profile.summary(),
        'items': []
    }
    
    type_col = [c for c in df.columns if 'category' in c.lower() or 'article' in c.lower() or 'type' in c.lower()][0]
    
    for slot, categories in OUTFIT_SLOTS.items():
        # Match candidate types
        slot_candidates = filtered_df[filtered_df[type_col].str.lower().isin([c.lower() for c in categories])]
        # Gap 2: Exclude seed item
        slot_candidates = slot_candidates[slot_candidates.index != seed_idx]
        
        # Fallback if over-filtered
        if slot_candidates.empty:
            slot_candidates = df[df[type_col].str.lower().isin([c.lower() for c in categories])]
            slot_candidates = slot_candidates[slot_candidates.index != seed_idx]
            
        if slot_candidates.empty:
            continue
            
        scored = []
        for idx in slot_candidates.index:
            score, breakdown, reason = context_aware_score(seed_idx, idx, df, sim_matrix, profile)
            scored.append((idx, score, breakdown, reason))
            
        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0]
        
        outfit['items'].append({
            'slot': slot,
            'item': df.iloc[best[0]].to_dict(),
            'final_score': best[1],
            'breakdown': best[2],
            'reason': best[3],
            'idx': best[0]
        })
        
    return outfit

# Demo print the 4 profiles
print("Demo execution across all 4 sample profiles:")
for p in [profile_office_man, profile_party_woman, profile_casual_teen, profile_wedding_woman]:
    # Select a valid seed item
    valid_seeds = filter_by_profile(df, p)
    s_idx = valid_seeds[0] if len(valid_seeds) > 0 else df.index[0]
    out = generate_profile_outfit(s_idx, df, sim_matrix, p)
    print(f"\\nProfile: {p.summary()}")
    print(f"  Hero Seed: {out['seed']['brand']} {out['seed']['name']} (Category: {out['seed']['category']})")
    for item in out['items']:
        print(f"  → Slot [{item['slot'].upper()}]: {item['item']['brand']} {item['item']['name']} (Score: {item['final_score']:.2f})")
        print(f"    Reason: {item['reason']}")\"\"\"))


# 7f: Profile-Aware Chat Integration
cells.append(nbf.v4.new_markdown_cell(\"\"\"## 7f: Profile-Aware Chat Integration
Helpers to extract demographic details from messages and execute response building.\"\"\"))

cells.append(nbf.v4.new_code_cell(\"\"\"# 7f-i: Profile Extractor from Natural Language
def extract_profile_from_text(text: str) -> UserProfile:
    \\\"\\\"\\\"
    Parses natural language queries to extract profiling parameters.
    \\\"\\\"\\\"
    text_lower = text.lower()
    
    # 1. Gender
    gender = None
    gender_map = {
        'Men': ['men', 'male', 'man', 'guy', 'him'],
        'Women': ['women', 'female', 'woman', 'girl', 'her'],
        'Boys': ['boy', 'boys', 'teen boy'],
        'Girls': ['girl', 'girls', 'teen girl'],
    }
    for g, kws in gender_map.items():
        if any(kw in text_lower for kw in kws):
            gender = g
            break
            
    # 2. Age group
    age_group = None
    age_map = {
        '20s': ['20s', 'twenties', '20 year', '25 year', 'college', 'young adult'],
        '30s': ['30s', 'thirties', '30 year', '35 year'],
        '40s': ['40s', 'forties', '40 year', '45 year'],
        '50s+': ['50s', 'fifties', '50 year', '60s', 'senior', 'mature'],
    }
    for ag, kws in age_map.items():
        if any(kw in text_lower for kw in kws):
            age_group = ag
            break
            
    # 3. Occasion
    occasion = None
    occasion_map = {
        'Office': ['office', 'work', 'meeting', 'corporate', 'professional', 'interview', 'business'],
        'Party': ['party', 'club', 'night out', 'cocktail', 'celebration'],
        'Wedding': ['wedding', 'marriage', 'reception', 'sangeet', 'mehendi'],
        'Beach': ['beach', 'vacation', 'holiday', 'summer', 'resort'],
        'Casual': ['casual', 'everyday', 'weekend', 'errands', 'hangout'],
        'Formal': ['formal', 'gala', 'ceremony', 'black tie'],
        'Date Night': ['date', 'dinner', 'romantic', 'evening out'],
        'Sport': ['gym', 'workout', 'sports', 'running', 'exercise', 'training'],
    }
    for occ, kws in occasion_map.items():
        if any(kw in text_lower for kw in kws):
            occasion = occ
            break
            
    # 4. Style Preference
    style_pref = None
    style_map = {
        'Formal': ['formal', 'classic', 'traditional', 'professional'],
        'Smart Casual': ['smart casual', 'smart-casual', 'business casual'],
        'Casual': ['casual', 'relaxed', 'laid back'],
        'Streetwear': ['streetwear', 'street style', 'urban', 'hypebeast'],
        'Bohemian': ['boho', 'bohemian', 'flowy'],
        'Minimalist': ['minimal', 'minimalist', 'clean look'],
    }
    for sp, kws in style_map.items():
        if any(kw in text_lower for kw in kws):
            style_pref = sp
            break
            
    return UserProfile(gender=gender, age_group=age_group, occasion=occasion, style_pref=style_pref)

# 7f-ii: Updated build_response_with_profile()
def build_response_with_profile(
    user_text: str,
    df: pd.DataFrame,
    sim_matrix: np.ndarray,
    base_profile: Optional[UserProfile] = None
) -> tuple:
    \\\"\\\"\\\"
    Complete response pipeline with UserProfile extraction and overriding.
    \\\"\\\"\\\"
    text_profile = extract_profile_from_text(user_text)
    
    # Merge dropdown profile with text-extracted profile (text overrides dropdown)
    merged = UserProfile(
        gender=text_profile.gender or (base_profile.gender if base_profile else None),
        age_group=text_profile.age_group or (base_profile.age_group if base_profile else None),
        occasion=text_profile.occasion or (base_profile.occasion if base_profile else None),
        style_pref=text_profile.style_pref or (base_profile.style_pref if base_profile else None)
    )
    
    intent = parse_intent(user_text, df)
    valid_indices = filter_by_profile(df, merged)
    seed_idx = valid_indices[0] if len(valid_indices) > 0 else df.index[0]
    
    # Find matching seed category
    type_col = [c for c in df.columns if 'category' in c.lower() or 'article' in c.lower() or 'type' in c.lower()][0]
    for cat in df[type_col].unique():
        if cat.lower() in user_text.lower():
            matches = df.loc[valid_indices][df.loc[valid_indices, type_col] == cat]
            if not matches.empty:
                seed_idx = matches.index[0]
                break
                
    if intent['intent'] == 'complete_outfit':
        outfit = generate_profile_outfit(seed_idx, df, sim_matrix, merged)
        text = f"👤 **Active Profile**: {merged.summary()}\\n"
        text += f"🌟 **Multimodal Outfit for**: {outfit['seed']['brand']} {outfit['seed']['name']}\\n\\n"
        imgs = [outfit['seed']['image']]
        
        for item in outfit['items']:
            score_pct = f"{item['final_score']*100:.0f}%"
            text += f"👉 **Slot [{item['slot'].upper()}]**: {item['item']['brand']} {item['item']['name']} (Compatibility: {score_pct})\\n"
            bd = item['breakdown']
            text += f"   📊 Breakdown — Base:{bd['base']:.2f} | Occasion:{bd['occasion']:.2f} | Color:{bd['color']:.2f} | Style:{bd['style']:.2f} | Age:{bd['age_formality']:.2f}\\n"
            text += f"   💬 Verdict: {item['reason']}\\n\\n"
            imgs.append(item['item']['image'])
            
        text += f"🎨 **Stylist Tip**: This curated outfit was optimized using personal style metrics for a polished visual weight."
        return text, imgs, merged
        
    else:
        # Search queries
        candidates = df.loc[valid_indices]
        if intent['filters']['color']:
            color_col = [c for c in df.columns if 'color' in c.lower()][0]
            candidates = candidates[candidates[color_col] == intent['filters']['color']]
            
        if candidates.empty:
            resp = f"👤 **Active Profile**: {merged.summary()}\\n" \\
                   f"Sorry, no matching items found for your search filters and active profile. Try broadening your keywords! 🔍"
            return resp, [], merged
            
        resp = f"👤 **Active Profile**: {merged.summary()}\\n" \\
               f"🛍️ Found {len(candidates)} products matching your query:\\n"
        for _, row in candidates.head(5).iterrows():
            resp += f"  • **{row['brand']} {row['name']}** (Color: {row['color']}, Category: {row['category']})\\n"
            
        image_col = [c for c in df.columns if 'image' in c.lower()][0]
        imgs = candidates.head(5)[image_col].tolist()
        return resp, imgs, merged\"\"\"))


# 7g: Profile-Aware Chat Widget
cells.append(nbf.v4.new_markdown_cell(\"\"\"## 7g: Profile-Aware Chat Widget
Widget dashboard combining profile selections and simulated demo outputs.\"\"\"))

cells.append(nbf.v4.new_code_cell(\"\"\"# Dropdowns setup
gender_dd  = widgets.Dropdown(
    options=['(not set)', 'Men', 'Women', 'Boys', 'Girls', 'Unisex'],
    description='Gender:', layout=widgets.Layout(width='200px'))

age_dd     = widgets.Dropdown(
    options=['(not set)', '20s', '30s', '40s', '50s+'],
    description='Age Group:', layout=widgets.Layout(width='200px'))

occasion_dd= widgets.Dropdown(
    options=['(not set)', 'Office', 'Party', 'Wedding', 'Beach', 
             'Casual', 'Formal', 'Date Night', 'Sport'],
    description='Occasion:', layout=widgets.Layout(width='200px'))

style_dd   = widgets.Dropdown(
    options=['(not set)', 'Formal', 'Smart Casual', 'Casual', 
             'Streetwear', 'Bohemian', 'Minimalist'],
    description='Style:', layout=widgets.Layout(width='200px'))

profile_panel = widgets.VBox([
    widgets.HTML("<b>👤 Set Your Profile (optional — also typeable in chat)</b>"),
    widgets.HBox([gender_dd, age_dd]),
    widgets.HBox([occasion_dd, style_dd]),
])

profile_chat_history = []

def get_base_profile():
    return UserProfile(
        gender     = None if gender_dd.value   == '(not set)' else gender_dd.value,
        age_group  = None if age_dd.value      == '(not set)' else age_dd.value,
        occasion   = None if occasion_dd.value == '(not set)' else occasion_dd.value,
        style_pref = None if style_dd.value    == '(not set)' else style_dd.value,
    )

input_box2   = widgets.Text(
    placeholder='e.g. "Outfit for a beach vacation for women"',
    layout=widgets.Layout(width='65%'))
send_btn2    = widgets.Button(description='Send 💬', button_style='primary')
chat_out2    = widgets.Output()

def on_send_profile(b):
    user_text = input_box2.value.strip()
    if not user_text: return
    input_box2.value = ''
    
    base = get_base_profile()
    response_text, img_paths, used_profile = build_response_with_profile(
        user_text, df, sim_matrix, base
    )
    
    profile_chat_history.append({
        'user': user_text, 
        'response': response_text,
        'images': img_paths,
        'profile': used_profile.summary()
    })
    
    with chat_out2:
        clear_output()
        for turn in profile_chat_history:
            print(f"🧑 You: {turn['user']}")
            print(f"📌 Profile used: {turn['profile']}")
            print(f"🤖 Assistant:\\n{turn['response']}")
            
            # Matplotlib show recommendations
            imgs = turn.get('images', [])
            import os
            # Ensure file exists using try/except
            valid_imgs = []
            for img_p in imgs:
                if img_p and os.path.exists(img_p):
                    valid_imgs.append(img_p)
            if valid_imgs:
                fig, axes = plt.subplots(1, min(4, len(valid_imgs)), figsize=(12, 3))
                if len(valid_imgs) == 1:
                    axes = [axes]
                for ax, p in zip(axes, valid_imgs[:4]):
                    try:
                        img = Image.open(p).convert('RGB')
                        ax.imshow(img)
                    except Exception:
                        ax.text(0.5, 0.5, 'N/A', ha='center', va='center')
                    ax.axis('off')
                plt.tight_layout()
                plt.show()
            print("─" * 60)

send_btn2.on_click(on_send_profile)
chat_widget = widgets.VBox([
    widgets.HTML("<h3>👗 Context-Aware Fashion Assistant</h3>"),
    profile_panel,
    widgets.HTML("<hr>"),
    chat_out2,
    widgets.HBox([input_box2, send_btn2])
])
# display(chat_widget)
\"\"\"))

cells.append(nbf.v4.new_code_cell(\"\"\"# ============================================================
# SECTION 7g STATIC DEMO — visible in saved notebook/GitHub
# ============================================================
PROFILE_DEMO_QUERIES = [
    ("I need a formal outfit for a job interview for men in their 30s",
     UserProfile('Men', '30s', 'Office', 'Formal')),
    ("Beach vacation outfit for a young woman",
     UserProfile('Women', '20s', 'Beach', 'Casual')),
    ("Wedding outfit ideas for women in their 40s",
     UserProfile('Women', '40s', 'Wedding', 'Formal')),
    ("Streetwear look for teenage boys",
     UserProfile('Boys', '20s', 'Casual', 'Streetwear')),
    ("Smart casual dinner date outfit for men",
     UserProfile('Men', '30s', 'Date Night', 'Smart Casual')),
]

print("=" * 70)
print("SECTION 7 — CONTEXT-AWARE ASSISTANT STATIC DEMO")
print("=" * 70)

for query, profile in PROFILE_DEMO_QUERIES:
    print(f"\\n🧑 User: {query}")
    extracted = extract_profile_from_text(query)
    print(f"📌 Extracted Profile: {extracted.summary()}")
    response, imgs, used = build_response_with_profile(
        query, df, sim_matrix, profile
    )
    print(f"🤖 Assistant:\\n{response}")
    print("─" * 70)\"\"\"))
"""

# Let's insert section_7_code before the notebook saving block
saving_block_start = "# Assign cells to notebook and save"
if saving_block_start in code:
    code = code.replace(saving_block_start, section_7_code + "\n" + saving_block_start)
    print("Successfully appended Section 7 cells to create_notebook.py!")
else:
    print("WARNING: Notebook save block not found in create_notebook.py!")

with open('create_notebook.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patching complete!")
