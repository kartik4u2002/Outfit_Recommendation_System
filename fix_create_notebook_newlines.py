with open('create_notebook.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace literal newlines in Section 7 code cells with escaped \\n
replacements = {
    'print(f"\\nProfile: {p.summary()}")': 'print(f"\\\\nProfile: {p.summary()}")',
    'text  = f"👤 Profile: {merged.summary()}\\n"': 'text  = f"👤 Profile: {merged.summary()}\\\\n"',
    'text += f"🌟 Outfit for **{outfit[\'seed\'].get(\'productDisplayName\',\'item\')}**:\\n\\n"': 'text += f"🌟 Outfit for **{outfit[\'seed\'].get(\'productDisplayName\',\'item\')}**:\\\\n\\\\n"',
    'text += f"  {item[\'slot\']:20s} → {item[\'item\'].get(\'productDisplayName\',\'?\')} "': 'text += f"  {item[\'slot\']:20s} → {item[\'item\'].get(\'productDisplayName\',\'?\')} "',
    'text += f"({score_pct})\\n"': 'text += f"({score_pct})\\\\n"',
    'text += (f"    📊 Scores — Base:{bd[\'base\']:.2f} | "': 'text += (f"    📊 Scores — Base:{bd[\'base\']:.2f} | "',
    'f"Occasion:{bd[\'occasion\']:.2f} | "': 'f"Occasion:{bd[\'occasion\']:.2f} | "',
    'f"Color:{bd[\'color\']:.2f} | "': 'f"Color:{bd[\'color\']:.2f} | "',
    'f"Style:{bd[\'style\']:.2f} | "': 'f"Style:{bd[\'style\']:.2f} | "',
    'f"Age:{bd[\'age_formality\']:.2f}\\n")': 'f"Age:{bd[\'age_formality\']:.2f}\\\\n")',
    'text += f"    ✨ {item[\'reason\']}\\n\\n"': 'text += f"    ✨ {item[\'reason\']}\\\\n\\\\n"',
    'resp = (f"👤 Profile: {merged.summary()}\\n"': 'resp = (f"👤 Profile: {merged.summary()}\\\\n"',
    'f"Sorry, no items match your profile and filters. "': 'f"Sorry, no items match your profile and filters. "',
    'f"Try broadening your search! 🔍")': 'f"Try broadening your search! 🔍")',
    'resp  = f"👤 Profile: {merged.summary()}\\n"': 'resp  = f"👤 Profile: {merged.summary()}\\\\n"',
    'resp += f"🛍️ Found {len(candidates)} items matching your profile:\\n"': 'resp += f"🛍️ Found {len(candidates)} items matching your profile:\\\\n"',
    'resp += f"  • {row.get(\'productDisplayName\',\'item\')}\\n"': 'resp += f"  • {row.get(\'productDisplayName\',\'item\')}\\\\n"',
    'text = f"👤 **Active Profile**: {merged.summary()}\\n"': 'text = f"👤 **Active Profile**: {merged.summary()}\\\\n"',
    'text += f"🌟 **Multimodal Outfit for**: {outfit[\'seed\'][\'brand\']} {outfit[\'seed\'][\'name\']}\\n\\n"': 'text += f"🌟 **Multimodal Outfit for**: {outfit[\'seed\'][\'brand\']} {outfit[\'seed\'][\'name\']}\\\\n\\\\n"',
    'text += f"👉 **Slot [{item[\'slot\'].upper()}]**: {item[\'item\'][\'brand\']} {item[\'item\'][\'name\']} (Compatibility: {score_pct})\\n"': 'text += f"👉 **Slot [{item[\'slot\'].upper()}]**: {item[\'item\'][\'brand\']} {item[\'item\'][\'name\']} (Compatibility: {score_pct})\\\\n"',
    'text += f"   📊 Breakdown — Base:{bd[\'base\']:.2f} | Occasion:{bd[\'occasion\']:.2f} | Color:{bd[\'color\']:.2f} | Style:{bd[\'style\']:.2f} | Age:{bd[\'age_formality\']:.2f}\\n"': 'text += f"   📊 Breakdown — Base:{bd[\'base\']:.2f} | Occasion:{bd[\'occasion\']:.2f} | Color:{bd[\'color\']:.2f} | Style:{bd[\'style\']:.2f} | Age:{bd[\'age_formality\']:.2f}\\\\n"',
    'text += f"   💬 Verdict: {item[\'reason\']}\\n\\n"': 'text += f"   💬 Verdict: {item[\'reason\']}\\\\n\\\\n"',
    'resp = f"👤 **Active Profile**: {merged.summary()}\\n" \\\\': 'resp = f"👤 **Active Profile**: {merged.summary()}\\\\n" \\\\',
    'f"Sorry, no matching items found for your search filters and active profile. Try broadening your keywords! 🔍"': 'f"Sorry, no matching items found for your search filters and active profile. Try broadening your keywords! 🔍"',
    'resp = f"👤 **Active Profile**: {merged.summary()}\\n" \\\\': 'resp = f"👤 **Active Profile**: {merged.summary()}\\\\n" \\\\',
    'f"🛍️ Found {len(candidates)} products matching your query:\\n"': 'f"🛍️ Found {len(candidates)} products matching your query:\\\\n"',
    'resp += f"  • **{row[\'brand\']} {row[\'name\']}** (Color: {row[\'color\']}, Category: {row[\'category\']})\\n"': 'resp += f"  • **{row[\'brand\']} {row[\'name\']}** (Color: {row[\'color\']}, Category: {row[\'category\']})\\\\n"',
    'print(f"🤖 Assistant:\\n{turn[\'response\']}")': 'print(f"🤖 Assistant:\\\\n{turn[\'response\']}")',
    'print(f"\\nUser: {q}")': 'print(f"\\\\nUser: {q}")',
    'print(f"\\nTurn {idx+1} [User]: {q}")': 'print(f"\\\\nTurn {idx+1} [User]: {q}")',
    'print(f"\\n🧑 User: {query}")': 'print(f"\\\\n🧑 User: {query}")',
    'print(f"🤖 Assistant:\\n{response}")': 'print(f"🤖 Assistant:\\\\n{response}")'
}

for old, new in replacements.items():
    if old in code:
        code = code.replace(old, new)
        print("Fixed replacement")
    else:
        # Check if the normalized version is present
        norm_code = code.replace('\r\n', '\n')
        norm_old = old.replace('\r\n', '\n')
        if norm_old in norm_code:
            norm_code = norm_code.replace(norm_old, new)
            code = norm_code
            print("Fixed replacement (normalized)")
        else:
            # Safely print without unicode characters
            safe_text = old[:15].encode('ascii', errors='replace').decode('ascii')
            print("WARNING: Replacement not found for item starting with:", safe_text)

with open('create_notebook.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Notebook newlines fixing complete!")
