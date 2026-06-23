with open('create_notebook.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Patch Section 3b
old_part_3b = """COLOR_HARMONY = {
    'neutrals': ["White", "Black", "Grey", "Navy Blue", "Beige", "Off White", "Cream", "Dark Grey"],"""

new_part_3b = """NEUTRAL_COLORS = ["White", "Black", "Grey", "Navy Blue", "Beige", "Off White", "Cream", "Dark Grey"]

COLOR_HARMONY = {
    'neutrals': NEUTRAL_COLORS,"""

if old_part_3b in code:
    code = code.replace(old_part_3b, new_part_3b)
    print("Patched 3b neutrals")
else:
    # Try with different newlines or spaces if needed
    normalized_code = code.replace('\r\n', '\n')
    if old_part_3b.replace('\r\n', '\n') in normalized_code:
        normalized_code = normalized_code.replace(old_part_3b.replace('\r\n', '\n'), new_part_3b)
        code = normalized_code
        print("Patched 3b neutrals (normalized)")
    else:
        print("WARNING: 3b neutrals not found!")

# 2. Patch Section 3c (compatibility_score definition & body)
old_part_3c = """def compatibility_score(id1, id2, df, combined_norm) -> tuple:
    \"\"\"
    Computes compatibility score in [0.0, 1.0] and returns an explanation.
    Formula: Score = 0.4*category_match + 0.3*color_harmony + 0.3*embedding_similarity
    \"\"\"
    idx1 = df[df['id'] == id1].index[0]
    idx2 = df[df['id'] == id2].index[0]"""

new_part_3c = """def compatibility_score(id1_or_idx, id2_or_idx, df, sim_matrix) -> tuple:
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
        idx2 = matches.index[0]"""

# Also replace the similarity computation in 3c
old_sim_3c = """    # 3. Embedding similarity
    sim = np.dot(combined_norm[idx1], combined_norm[idx2])"""

new_sim_3c = """    # 3. Embedding similarity from precomputed sim_matrix
    sim = sim_matrix[idx1, idx2]"""

normalized_code = code.replace('\r\n', '\n')
if old_part_3c.replace('\r\n', '\n') in normalized_code:
    normalized_code = normalized_code.replace(old_part_3c.replace('\r\n', '\n'), new_part_3c)
    if old_sim_3c.replace('\r\n', '\n') in normalized_code:
        normalized_code = normalized_code.replace(old_sim_3c.replace('\r\n', '\n'), new_sim_3c)
    code = normalized_code
    print("Patched 3c compatibility_score")
else:
    print("WARNING: 3c compatibility_score not found!")

# 3. Patch Section 3d (OUTFIT_SLOTS, SLOT_MAPPING & generate_complete_outfit)
old_part_3d = """# 3d. Outfit Generator
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
    seed_idx = df[df['id'] == seed_id].index[0]"""

new_part_3d = """# 3d. Outfit Generator
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
    seed_idx = matches.index[0]"""

# Also update the inner loop of generate_complete_outfit to pass sim_matrix and check index
old_loop_3d = """        # Gather matching items from the dataset
        for idx, row in df.iterrows():
            if row['id'] == seed_id:
                continue"""

new_loop_3d = """        # Gather matching items from the dataset
        for idx, row in df.iterrows():
            # Gap 2: Exclude seed item explicitly
            if idx == seed_idx:
                continue"""

old_call_3d = """            score, explanation = compatibility_score(seed_id, row['id'], df, combined_norm)"""
new_call_3d = """            score, explanation = compatibility_score(seed_id, row['id'], df, sim_matrix)"""

normalized_code = code.replace('\r\n', '\n')
if old_part_3d.replace('\r\n', '\n') in normalized_code:
    normalized_code = normalized_code.replace(old_part_3d.replace('\r\n', '\n'), new_part_3d)
    if old_loop_3d.replace('\r\n', '\n') in normalized_code:
        normalized_code = normalized_code.replace(old_loop_3d.replace('\r\n', '\n'), new_loop_3d)
    if old_call_3d.replace('\r\n', '\n') in normalized_code:
        normalized_code = normalized_code.replace(old_call_3d.replace('\r\n', '\n'), new_call_3d)
    code = normalized_code
    print("Patched 3d generate_complete_outfit")
else:
    print("WARNING: 3d generate_complete_outfit not found!")

# Save the final file
with open('create_notebook.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patching round 2 complete!")
