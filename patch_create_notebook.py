import os

print("Reading create_notebook.py...")
with open('create_notebook.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update Section 2c
old_2c = """# 2c. Hybrid Embedding and FAISS indexing
import faiss

# L2 normalize helper
def l2_normalize(vecs):
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms

# L2-normalize individual embedding modalities
text_norm = l2_normalize(text_embeddings)
visual_norm = l2_normalize(visual_embeddings)

# Concatenate hybrid embeddings: 40% Text, 60% Visual
combined_embeddings = np.hstack([0.4 * text_norm, 0.6 * visual_norm])

# L2-normalize the combined vector so that inner product is cosine similarity
combined_norm = l2_normalize(combined_embeddings)

# Build FAISS IndexFlatIP
dim = combined_norm.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(combined_norm.astype('float32'))

# Save index
faiss.write_index(index, 'fashion.index')
print("Built and saved FAISS IndexFlatIP index with dimension:", dim)"""

new_2c = """# 2c. Hybrid Embedding and FAISS indexing
import faiss
import os

# Check for precomputed similarity matrix cache to avoid re-extracting
USE_SIM_CACHE = os.path.exists('sim_matrix.npy')

# L2 normalize helper
def l2_normalize(vecs):
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms

# L2-normalize individual embedding modalities
text_norm = l2_normalize(text_embeddings)
visual_norm = l2_normalize(visual_embeddings)

# Concatenate hybrid embeddings: 40% Text, 60% Visual
combined_embeddings = np.hstack([0.4 * text_norm, 0.6 * visual_norm])

# L2-normalize the combined vector so that inner product is cosine similarity
combined_norm = l2_normalize(combined_embeddings)

if USE_SIM_CACHE:
    print("Loading precomputed similarity matrix from cache...")
    sim_matrix = np.load('sim_matrix.npy')
else:
    print("Computing similarity matrix...")
    sim_matrix = np.dot(combined_norm, combined_norm.T)
    np.save('sim_matrix.npy', sim_matrix)

# Build FAISS IndexFlatIP
dim = combined_norm.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(combined_norm.astype('float32'))

# Save index
faiss.write_index(index, 'fashion.index')
print("Built and saved FAISS IndexFlatIP index with dimension:", dim)
print("Similarity matrix shape:", sim_matrix.shape)"""

if old_2c in code:
    code = code.replace(old_2c, new_2c)
    print("Successfully patched Section 2c")
else:
    print("WARNING: Section 2c not found!")

# 2. Update Section 3b
old_3b = """# 3b. Color Harmony Rules
COLOR_HARMONY = {
    'neutrals': ["White", "Black", "Grey", "Navy Blue", "Beige", "Off White", "Cream", "Dark Grey"],
    'pairs': {
        frozenset(["Red", "Black"]),
        frozenset(["Red", "White"]),
        frozenset(["Red", "Grey"]),
        frozenset(["Blue", "Beige"]),
        frozenset(["Blue", "White"]),
        frozenset(["Green", "Beige"]),
        frozenset(["Green", "White"]),
        frozenset(["Pink", "Grey"]),
        frozenset(["Pink", "White"]),
        frozenset(["Yellow", "Navy Blue"]),
        frozenset(["Yellow", "White"]),
        frozenset(["Gold", "Black"]),
        frozenset(["Gold", "Red"]),
        frozenset(["Lavender", "Blue"]),
        frozenset(["Lavender", "White"]),
        frozenset(["Lavender", "Grey"]),
        frozenset(["Olive", "Black"]),
        frozenset(["Olive", "Beige"]),
        frozenset(["Maroon", "Black"]),
        frozenset(["Maroon", "White"]),
        frozenset(["Cream", "Gold"]),
        frozenset(["Tan", "Navy Blue"]),
        frozenset(["Tan", "White"])
    }
}

def color_compatible(c1, c2) -> bool:
    \"\"\"
    Checks if two colors are compatible.
    Rules: same color = True, neutral + anything = True, specified harmonious pairs = True
    \"\"\"
    if c1 == 'Unknown' or c2 == 'Unknown':
        return True
    if c1 == c2:
        return True
    if c1 in COLOR_HARMONY['neutrals'] or c2 in COLOR_HARMONY['neutrals']:
        return True
    if frozenset([c1, c2]) in COLOR_HARMONY['pairs']:
        return True
    return False"""

new_3b = """# 3b. Color Harmony Rules
# Standalone list defined first to prevent NameError in Section 7
NEUTRAL_COLORS = ["White", "Black", "Grey", "Navy Blue", "Beige", "Off White", "Cream", "Dark Grey"]

COLOR_HARMONY = {
    'neutrals': NEUTRAL_COLORS,
    'pairs': {
        frozenset(["Red", "Black"]),
        frozenset(["Red", "White"]),
        frozenset(["Red", "Grey"]),
        frozenset(["Blue", "Beige"]),
        frozenset(["Blue", "White"]),
        frozenset(["Green", "Beige"]),
        frozenset(["Green", "White"]),
        frozenset(["Pink", "Grey"]),
        frozenset(["Pink", "White"]),
        frozenset(["Yellow", "Navy Blue"]),
        frozenset(["Yellow", "White"]),
        frozenset(["Gold", "Black"]),
        frozenset(["Gold", "Red"]),
        frozenset(["Lavender", "Blue"]),
        frozenset(["Lavender", "White"]),
        frozenset(["Lavender", "Grey"]),
        frozenset(["Olive", "Black"]),
        frozenset(["Olive", "Beige"]),
        frozenset(["Maroon", "Black"]),
        frozenset(["Maroon", "White"]),
        frozenset(["Cream", "Gold"]),
        frozenset(["Tan", "Navy Blue"]),
        frozenset(["Tan", "White"])
    }
}

def color_compatible(c1, c2) -> bool:
    \"\"\"
    Checks if two colors are compatible.
    Rules: same color = True, neutral + anything = True, specified harmonious pairs = True
    \"\"\"
    if c1 == 'Unknown' or c2 == 'Unknown':
        return True
    if c1 == c2:
        return True
    if c1 in COLOR_HARMONY['neutrals'] or c2 in COLOR_HARMONY['neutrals']:
        return True
    if frozenset([c1, c2]) in COLOR_HARMONY['pairs']:
        return True
    return False"""

if old_3b in code:
    code = code.replace(old_3b, new_3b)
    print("Successfully patched Section 3b")
else:
    print("WARNING: Section 3b not found!")

# 3. Update Section 3c (compatibility_score)
old_3c = """# 3c. Pairwise Compatibility Scorer
def compatibility_score(id1, id2, df, combined_norm) -> tuple:
    \"\"\"
    Computes compatibility score in [0.0, 1.0] and returns an explanation.
    Formula: Score = 0.4*category_match + 0.3*color_harmony + 0.3*embedding_similarity
    \"\"\"
    idx1 = df[df['id'] == id1].index[0]
    idx2 = df[df['id'] == id2].index[0]
    
    row1 = df.iloc[idx1]
    row2 = df.iloc[idx2]
    
    # 1. Category matching
    cat1, cat2 = row1['category'], row2['category']
    cat_match = 0.0
    if cat2 in COMPATIBLE_CATEGORIES.get(cat1, []) or cat1 in COMPATIBLE_CATEGORIES.get(cat2, []):
        cat_match = 1.0
        
    # 2. Color harmony matching
    col1, col2 = row1['color'], row2['color']
    col_match = 1.0 if color_compatible(col1, col2) else 0.0
    
    # 3. Embedding similarity
    sim = np.dot(combined_norm[idx1], combined_norm[idx2])
    sim_score = float(np.clip((sim + 1) / 2, 0.0, 1.0)) # Scale to [0, 1]
    
    total_score = 0.4 * cat_match + 0.3 * col_match + 0.3 * sim_score
    
    # Explanation builder
    reasons = []
    if cat_match > 0:
        reasons.append(f"the style profile of {cat1} pairs well with {cat2}")
    else:
        reasons.append(f"{cat1} and {cat2} are an unconventional clothing combination")
        
    if col_match > 0:
        if col1 == col2:
            reasons.append(f"the monochromatic look in {col1} is clean and structured")
        elif col1 in COLOR_HARMONY['neutrals'] or col2 in COLOR_HARMONY['neutrals']:
            reasons.append(f"the classic contrast of {col1} and {col2} is versatile")
        else:
            reasons.append(f"the color pairing of {col1} and {col2} looks naturally balanced")
    else:
        reasons.append(f"the color clash between {col1} and {col2} creates a highly bold aesthetic")
        
    reasons.append(f"the visual-textual similarity match is {sim_score*100:.0f}%")
    explanation = f"Recommended because " + ", and ".join(reasons) + "."
    
    return total_score, explanation"""

new_3c = """# 3c. Pairwise Compatibility Scorer
def compatibility_score(id1_or_idx, id2_or_idx, df, sim_matrix) -> tuple:
    \"\"\"
    Computes compatibility score in [0.0, 1.0] and returns an explanation.
    Supports both string product IDs and integer indices.
    Formula: Score = 0.4*category_match + 0.3*color_harmony + 0.3*embedding_similarity
    \"\"\"
    # Robust index lookup with error handling
    if isinstance(id1_or_idx, (int, np.integer)):
        idx1 = int(id1_or_idx)
    else:
        matches = df[df['id'] == id1_or_idx]
        if matches.empty:
            raise ValueError(f"Item ID '{id1_or_idx}' not found in dataframe")
        idx1 = matches.index[0]
        
    if isinstance(id2_or_idx, (int, np.integer)):
        idx2 = int(id2_or_idx)
    else:
        matches = df[df['id'] == id2_or_idx]
        if matches.empty:
            raise ValueError(f"Item ID '{id2_or_idx}' not found in dataframe")
        idx2 = matches.index[0]
        
    row1 = df.iloc[idx1]
    row2 = df.iloc[idx2]
    
    # 1. Category matching
    cat1, cat2 = row1['category'], row2['category']
    cat_match = 0.0
    if cat2 in COMPATIBLE_CATEGORIES.get(cat1, []) or cat1 in COMPATIBLE_CATEGORIES.get(cat2, []):
        cat_match = 1.0
        
    # 2. Color harmony matching
    col1, col2 = row1['color'], row2['color']
    col_match = 1.0 if color_compatible(col1, col2) else 0.0
    
    # 3. Embedding similarity from precomputed sim_matrix
    sim = sim_matrix[idx1, idx2]
    sim_score = float(np.clip((sim + 1) / 2, 0.0, 1.0)) # Scale to [0, 1]
    
    total_score = 0.4 * cat_match + 0.3 * col_match + 0.3 * sim_score
    
    # Explanation builder
    reasons = []
    if cat_match > 0:
        reasons.append(f"the style profile of {cat1} pairs well with {cat2}")
    else:
        reasons.append(f"{cat1} and {cat2} are an unconventional clothing combination")
        
    if col_match > 0:
        if col1 == col2:
            reasons.append(f"the monochromatic look in {col1} is clean and structured")
        elif col1 in COLOR_HARMONY['neutrals'] or col2 in COLOR_HARMONY['neutrals']:
            reasons.append(f"the classic contrast of {col1} and {col2} is versatile")
        else:
            reasons.append(f"the color pairing of {col1} and {col2} looks naturally balanced")
    else:
        reasons.append(f"the color clash between {col1} and {col2} creates a highly bold aesthetic")
        
    reasons.append(f"the visual-textual similarity match is {sim_score*100:.0f}%")
    explanation = f"Recommended because " + ", and ".join(reasons) + "."
    
    return total_score, explanation"""

if old_3c in code:
    code = code.replace(old_3c, new_3c)
    print("Successfully patched Section 3c")
else:
    print("WARNING: Section 3c not found!")

# 4. Update Section 3d (OUTFIT_SLOTS and dynamic SLOT_MAPPING)
old_3d = """# 3d. Outfit Generator
SLOT_MAPPING = {
    'formal-shirts': 'top', 'casual-shirts': 'top', 'linen-shirts': 'top', 'party-shirts': 'top',
    'tshirts': 'top', 'polo-tshirts': 'top', 'sweatshirts': 'top', 'sweaters': 'top', 'tops': 'top',
    'trousers': 'bottom', 'jeans': 'bottom', 'chinos': 'bottom', 'shorts': 'bottom', 'track-pants': 'bottom', 'skirts': 'bottom', 'leggings': 'bottom',
    'running-shoes': 'footwear', 'sneakers': 'footwear', 'formal-shoes': 'footwear', 'loafers': 'footwear', 'boots': 'footwear', 'sandals': 'footwear', 'flats': 'footwear', 'heels': 'footwear', 'ethnic-footwear': 'footwear',
    'blazers': 'layer', 'suits': 'layer', 'nehru-jackets': 'layer', 'denim-jackets': 'layer', 'long-coats': 'layer',
    'party-dresses': 'dress', 'casual-dresses': 'dress', 'maxi-dresses': 'dress', 'co-ord-sets': 'dress', 'kurta-sets': 'dress', 'sherwanis': 'dress', 'sharara-sets': 'dress', 'salwar-suits': 'dress', 'wedding-sarees': 'dress',
    'necklaces': 'accessory', 'earrings': 'accessory', 'clutches': 'accessory', 'handbags': 'accessory', 'sunglasses': 'accessory', 'watches': 'accessory', 'caps': 'accessory'
}

def generate_complete_outfit(seed_id, df, combined_norm, top_k=10):
    \"\"\"
    Generates a complete outfit around a seed product ID.
    Recommends items for required slots: bottom, footwear, accessory.
    \"\"\"
    seed_idx = df[df['id'] == seed_id].index[0]
    seed_item = df.iloc[seed_idx]
    seed_slot = SLOT_MAPPING.get(seed_item['category'], 'accessory')
    seed_gender = seed_item['gender']
    seed_occasion = seed_item['occasion']
    
    if seed_slot == 'dress':
        target_slots = ['footwear', 'accessory']
    elif seed_slot == 'top':
        target_slots = ['bottom', 'footwear', 'accessory']
    elif seed_slot == 'bottom':
        target_slots = ['top', 'footwear', 'accessory']
    elif seed_slot == 'footwear':
        target_slots = ['top', 'bottom', 'accessory']
    else:
        target_slots = ['top', 'bottom', 'footwear']
        
    complementary_items = []
    
    for slot in target_slots:
        best_cand = None
        best_score = -1
        best_explanation = ""
        
        # Gather matching items from the dataset
        for idx, row in df.iterrows():
            if row['id'] == seed_id:
                continue
            item_slot = SLOT_MAPPING.get(row['category'], 'accessory')
            
            # Special category override: dress can act as a top for outfit slot matching
            if slot == 'top' and item_slot == 'dress':
                pass
            elif item_slot != slot:
                continue
                
            # Filter gender
            if seed_gender != 'unisex' and row['gender'] != 'unisex' and row['gender'] != seed_gender:
                continue
                
            score, explanation = compatibility_score(seed_id, row['id'], df, combined_norm)
            
            # Boost score slightly if occasion matches
            if row['occasion'] == seed_occasion:
                score += 0.05
                explanation += f" This item matches the '{seed_occasion}' occasion requirements."
            score = float(np.clip(score, 0.0, 1.0))
            
            if score > best_score:
                best_score = score
                best_cand = row
                best_explanation = explanation
                
        if best_cand is not None:
            complementary_items.append({
                'slot': slot,
                'item': best_cand.to_dict(),
                'score': round(best_score, 2),
                'reason': best_explanation
            })
            
    return {
        'seed': seed_item.to_dict(),
        'complementary_items': complementary_items
    }"""

new_3d = """# 3d. Outfit Generator
# Define OUTFIT_SLOTS explicitly first
OUTFIT_SLOTS = {
    'top': ['formal-shirts', 'casual-shirts', 'linen-shirts', 'party-shirts', 'tshirts', 'polo-tshirts', 'sweatshirts', 'sweaters', 'tops'],
    'bottom': ['trousers', 'jeans', 'chinos', 'shorts', 'track-pants', 'skirts', 'leggings'],
    'footwear': ['running-shoes', 'sneakers', 'ethnic-footwear', 'heels', 'boots', 'flats', 'formal-shoes', 'loafers', 'sandals'],
    'layer': ['blazers', 'suits', 'nehru-jackets', 'denim-jackets', 'long-coats'],
    'dress': ['party-dresses', 'casual-dresses', 'maxi-dresses', 'co-ord-sets', 'kurta-sets', 'sherwanis', 'sharara-sets', 'salwar-suits', 'wedding-sarees'],
    'accessory': ['necklaces', 'earrings', 'clutches', 'handbags', 'sunglasses', 'watches', 'caps']
}

# Dynamically invert mapping: {article_type: slot_name}
SLOT_MAPPING = {article_type: slot_name for slot_name, types in OUTFIT_SLOTS.items() for article_type in types}

def generate_complete_outfit(seed_id, df, sim_matrix, top_k=10):
    \"\"\"
    Generates a complete outfit around a seed product ID.
    Recommends items for required slots: bottom, footwear, accessory.
    \"\"\"
    # Robust index lookup with error handling
    matches = df[df['id'] == seed_id]
    if matches.empty:
        raise ValueError(f"Seed ID '{seed_id}' not found in dataframe")
    seed_idx = matches.index[0]
    
    seed_item = df.iloc[seed_idx]
    seed_slot = SLOT_MAPPING.get(seed_item['category'], 'accessory')
    seed_gender = seed_item['gender']
    seed_occasion = seed_item['occasion']
    
    if seed_slot == 'dress':
        target_slots = ['footwear', 'accessory']
    elif seed_slot == 'top':
        target_slots = ['bottom', 'footwear', 'accessory']
    elif seed_slot == 'bottom':
        target_slots = ['top', 'footwear', 'accessory']
    elif seed_slot == 'footwear':
        target_slots = ['top', 'bottom', 'accessory']
    else:
        target_slots = ['top', 'bottom', 'footwear']
        
    complementary_items = []
    
    for slot in target_slots:
        best_cand = None
        best_score = -1
        best_explanation = ""
        
        # Gather matching items from the dataset
        for idx, row in df.iterrows():
            # Gap 2: Exclude seed item explicitly
            if idx == seed_idx:
                continue
            item_slot = SLOT_MAPPING.get(row['category'], 'accessory')
            
            # Special category override: dress can act as a top for outfit slot matching
            if slot == 'top' and item_slot == 'dress':
                pass
            elif item_slot != slot:
                continue
                
            # Filter gender
            if seed_gender != 'unisex' and row['gender'] != 'unisex' and row['gender'] != seed_gender:
                continue
                
            score, explanation = compatibility_score(seed_id, row['id'], df, sim_matrix)
            
            # Boost score slightly if occasion matches
            if row['occasion'] == seed_occasion:
                score += 0.05
                explanation += f" This item matches the '{seed_occasion}' occasion requirements."
            score = float(np.clip(score, 0.0, 1.0))
            
            if score > best_score:
                best_score = score
                best_cand = row
                best_explanation = explanation
                
        if best_cand is not None:
            complementary_items.append({
                'slot': slot,
                'item': best_cand.to_dict(),
                'score': round(best_score, 2),
                'reason': best_explanation
            })
            
    return {
        'seed': seed_item.to_dict(),
        'complementary_items': complementary_items
    }"""

if old_3d in code:
    code = code.replace(old_3d, new_3d)
    print("Successfully patched Section 3d")
else:
    print("WARNING: Section 3d not found!")

# 5. Replace references to combined_norm with sim_matrix in Section 4, 5, 6
replacements = {
    "def build_response(intent, parsed, df, combined_norm) -> tuple:": "def build_response(intent, parsed, df, sim_matrix) -> tuple:",
    "outfit = generate_complete_outfit(seed['id'], df, combined_norm)": "outfit = generate_complete_outfit(seed['id'], df, sim_matrix)",
    "score, reason = compatibility_score(seed['id'], item2['id'], df, combined_norm)": "score, reason = compatibility_score(seed['id'], item2['id'], df, sim_matrix)",
    "outfit = generate_complete_outfit(p1['id'], df, combined_norm)": "outfit = generate_complete_outfit(p1['id'], df, sim_matrix)",
    "score, reason = compatibility_score(p1['id'], p2['id'], df, combined_norm)": "score, reason = compatibility_score(p1['id'], p2['id'], df, sim_matrix)",
    "response_text, items = build_response(parsed['intent'], parsed, df, combined_norm)": "response_text, items = build_response(parsed['intent'], parsed, df, sim_matrix)",
    "response, items = build_response(parsed['intent'], parsed, df, combined_norm)": "response, items = build_response(parsed['intent'], parsed, df, sim_matrix)",
    "s, _ = compatibility_score(hero_id, second_id, df, combined_norm)": "s, _ = compatibility_score(hero_id, second_id, df, sim_matrix)",
    "s, _ = compatibility_score(hero_id, footwear_id, df, combined_norm)": "s, _ = compatibility_score(hero_id, footwear_id, df, sim_matrix)",
    "s, _ = compatibility_score(p1, p2, df, combined_norm)": "s, _ = compatibility_score(p1, p2, df, sim_matrix)",
    "outfit = generate_complete_outfit(seed_id, df, combined_norm)": "outfit = generate_complete_outfit(seed_id, df, sim_matrix)",
    "outfit = generate_complete_outfit(random_seed_id, df, combined_norm)": "outfit = generate_complete_outfit(random_seed_id, df, sim_matrix)",
}

for old_str, new_str in replacements.items():
    if old_str in code:
        code = code.replace(old_str, new_str)
        print(f"Patched: {old_str[:40]}...")
    else:
        print(f"WARNING: Could not find downstream ref: {old_str[:40]}")

# 6. Add Section 5a Backward Compatibility check
# Let's verify compatibility_score both ways
old_eval_top = """# 5a. Quantitative Evaluation using outfits.csv as ground-truth benchmark
outfit_scores = []"""

new_eval_top = """# 5a. Quantitative Evaluation using outfits.csv as ground-truth benchmark
# Gap 4 Verification: Call compatibility_score both ways and assert same result
score_by_int = compatibility_score(0, 1, df, sim_matrix)
score_by_str = compatibility_score(df.iloc[0]['id'], df.iloc[1]['id'], df, sim_matrix)
assert score_by_int[0] == score_by_str[0], "Backward compatibility test failed!"
print("✅ Verification Check: compatibility_score backward compatibility confirmed.")

outfit_scores = []"""

if old_eval_top in code:
    code = code.replace(old_eval_top, new_eval_top)
    print("Successfully added Gap 4 Verification assert")
else:
    print("WARNING: Could not add Gap 4 Verification assert!")

# Write the patched create_notebook.py back
with open('create_notebook.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patching of create_notebook.py complete!")
