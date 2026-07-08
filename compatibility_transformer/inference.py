import os
import numpy as np
import pandas as pd
import torch
from typing import List, Dict, Tuple, Any

from .utils import extract_all_metadata, MetadataVocabulary, extract_color
from .model import FashionTransformerCompatibilityModel
from .dataset import get_slot_id

# Color harmony configuration (legacy and stylistic support)
NEUTRAL_COLORS = ["white", "black", "grey", "navy blue", "beige", "off white", "cream", "dark grey"]
COLOR_HARMONY_PAIRS = {
    frozenset(["red", "black"]), frozenset(["red", "white"]), frozenset(["red", "grey"]),
    frozenset(["blue", "beige"]), frozenset(["blue", "white"]), frozenset(["green", "beige"]),
    frozenset(["green", "white"]), frozenset(["pink", "grey"]), frozenset(["pink", "white"]),
    frozenset(["yellow", "navy blue"]), frozenset(["yellow", "white"]), frozenset(["gold", "black"]),
    frozenset(["gold", "red"]), frozenset(["lavender", "blue"]), frozenset(["lavender", "white"]),
    frozenset(["lavender", "grey"]), frozenset(["olive", "black"]), frozenset(["olive", "beige"]),
    frozenset(["maroon", "black"]), frozenset(["maroon", "white"]), frozenset(["cream", "gold"]),
    frozenset(["tan", "navy blue"]), frozenset(["tan", "white"])
}

class ExplanationModule:
    """Generates stylist explanations using metadata comparison, model attention weights, and style cues."""
    def __init__(self):
        pass
        
    def generate_explanation(self, 
                             items_metadata: List[Dict[str, str]], 
                             attention_weights: List[float], 
                             compatibility_score: float) -> str:
        if len(items_metadata) < 2:
            return "A minimum of two items is required to evaluate compatibility."
            
        # 1. Identify the focal/anchor item using attention weights
        anchor_idx = int(np.argmax(attention_weights))
        anchor = items_metadata[anchor_idx]
        anchor_weight_pct = attention_weights[anchor_idx] * 100
        
        reasons = []
        
        # focal point statement
        reasons.append(f"this combination is styled around the {anchor['brand']} {anchor['category']} which serves as the visual anchor (holding {anchor_weight_pct:.0f}% of the outfit weight)")
        
        # 2. Analyze Pairwise Category Compatibility
        cat1, cat2 = items_metadata[0]['category'], items_metadata[1]['category']
        reasons.append(f"the style silhouettes of {cat1} and {cat2} pair together naturally")
        
        # 3. Analyze Color Harmony
        col1 = items_metadata[0]['color']
        col2 = items_metadata[1]['color']
        
        if col1 == col2:
            reasons.append(f"the monochromatic coordination in {col1.title()} looks highly unified and polished")
        elif col1 in NEUTRAL_COLORS or col2 in NEUTRAL_COLORS:
            reasons.append(f"the neutral contrast of {col1.title()} and {col2.title()} is classic and highly versatile")
        elif frozenset([col1, col2]) in COLOR_HARMONY_PAIRS:
            reasons.append(f"the complementary color palette of {col1.title()} and {col2.title()} feels visually balanced and pleasing")
        else:
            reasons.append(f"the combination of {col1.title()} and {col2.title()} creates an expressive, fashion-forward color pairing")
            
        # 4. Fit & Occasion alignment
        fit1, fit2 = items_metadata[0]['fit'], items_metadata[1]['fit']
        style1, style2 = items_metadata[0]['style'], items_metadata[1]['style']
        occ = items_metadata[0]['occasion']
        
        if fit1 == 'oversized' or fit2 == 'oversized':
            reasons.append(f"the relaxed proportions of the fit offer a modern, comfortable silhouette")
        else:
            reasons.append(f"the coordinated {fit1} and {fit2} fits keep the outline neat and structured")
            
        if style1 == style2:
            reasons.append(f"both items align perfectly with a {style1} aesthetic suitable for a {occ} setting")
        else:
            reasons.append(f"the mix of {style1} and {style2} styles creates a curated smart-casual aesthetic")
            
        # Compile into human stylist explanation
        explanation = "Recommended because " + ", ".join(reasons[:-1]) + ", and " + reasons[-1] + "."
        return explanation


class FashionCompatibilityInferenceEngine:
    """Inference engine to predict compatibility scores, confidence, and perform candidate ranking."""
    def __init__(self, 
                 model_path: str, 
                 vocab_path: str,
                 products_df: pd.DataFrame,
                 visual_embs: np.ndarray,
                 text_embs: np.ndarray,
                 device: torch.device = None):
        self.products_df = products_df.copy()
        self.visual_embs = visual_embs
        self.text_embs = text_embs
        
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
            
        # Map product ID to row index
        self.id_to_idx = {row['id']: idx for idx, row in self.products_df.iterrows()}
        
        # Load vocab
        self.vocab = MetadataVocabulary()
        if not self.vocab.load(vocab_path):
            raise FileNotFoundError(f"Vocabulary map not found at {vocab_path}")
            
        # Determine vocabulary sizes for model construction
        vocab_sizes = {field: self.vocab.get_vocab_size(field) for field in self.vocab.fields}
        
        # Load model architecture
        self.model = FashionTransformerCompatibilityModel(vocab_sizes=vocab_sizes, dim=512)
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            print(f"Loaded compatibility model weights from {model_path}")
        else:
            print(f"Warning: model weights path {model_path} not found. Running with unitialized weights.")
            
        self.model.to(self.device)
        self.model.eval()
        
        self.explanation_module = ExplanationModule()
        
    def predict_compatibility(self, item_ids: List[str], threshold: float = 0.5) -> Dict[str, Any]:
        """
        Calculates compatibility score and generates full stylist explanation.
        Args:
            item_ids: List of unique item ID strings.
            threshold: Compatibility boundary.
        Returns:
            Dict containing compatibility_score, confidence, compatible, outfit_embedding, explanation.
        """
        # Filter item IDs to only valid ones in database
        valid_ids = [str(i).strip() for i in item_ids if str(i).strip() in self.id_to_idx]
        if len(valid_ids) < 2:
            return {
                "compatibility_score": 0.0,
                "confidence": 0.0,
                "compatible": False,
                "outfit_embedding": None,
                "explanation": "Insufficient valid items to check compatibility."
            }
            
        max_seq_len = max(6, len(valid_ids))
        
        # Prepare tensors for single forward pass
        v_tensor = torch.zeros(1, max_seq_len, 512, dtype=torch.float32, device=self.device)
        t_tensor = torch.zeros(1, max_seq_len, 512, dtype=torch.float32, device=self.device)
        meta_tensor = torch.zeros(1, max_seq_len, 10, dtype=torch.long, device=self.device)
        slot_tensor = torch.zeros(1, max_seq_len, dtype=torch.long, device=self.device)
        padding_mask = torch.zeros(1, max_seq_len, dtype=torch.bool, device=self.device)
        
        fields = ['category', 'color', 'occasion', 'season', 'gender', 'style', 'material', 'pattern', 'brand', 'fit']
        items_metadata = []
        
        for seq_idx, item_id in enumerate(valid_ids):
            row_idx = self.id_to_idx[item_id]
            row = self.products_df.iloc[row_idx]
            
            # Embeddings
            v_tensor[0, seq_idx] = torch.tensor(self.visual_embs[row_idx], dtype=torch.float32, device=self.device)
            t_tensor[0, seq_idx] = torch.tensor(self.text_embs[row_idx], dtype=torch.float32, device=self.device)
            
            # Metadata
            meta = extract_all_metadata(row)
            items_metadata.append(meta)
            for f_idx, field in enumerate(fields):
                meta_tensor[0, seq_idx, f_idx] = self.vocab.encode(field, meta[field])
                
            # Slot
            slot_tensor[0, seq_idx] = get_slot_id(row['category'])
            padding_mask[0, seq_idx] = False
            
        # Pad remaining positions
        for seq_idx in range(len(valid_ids), max_seq_len):
            slot_tensor[0, seq_idx] = 5
            padding_mask[0, seq_idx] = True
            
        with torch.no_grad():
            outputs = self.model(v_tensor, t_tensor, meta_tensor, slot_tensor, padding_mask)
            
        compat_score = float(outputs["compatibility_score"][0, 0].item())
        confidence = float(outputs["confidence"][0, 0].item())
        outfit_emb = outputs["outfit_embedding"][0].cpu()
        
        # Get attention weights for valid items
        attn_weights = outputs["attention_weights"][0, :len(valid_ids)].cpu().numpy()
        # Re-normalize attention weights over the valid items
        if np.sum(attn_weights) > 0:
            attn_weights = attn_weights / np.sum(attn_weights)
        else:
            attn_weights = np.ones_like(attn_weights) / len(valid_ids)
            
        # Generate Stylist Explanation
        explanation = self.explanation_module.generate_explanation(
            items_metadata, attn_weights.tolist(), compat_score
        )
        
        return {
            "compatibility_score": compat_score,
            "confidence": confidence,
            "compatible": compat_score >= threshold,
            "outfit_embedding": outfit_emb,
            "explanation": explanation
        }
        
    def rank_candidates(self, seed_id: str, candidate_ids: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Ranks candidate items based on their compatibility with a seed item.
        Args:
            seed_id: Anchor item ID.
            candidate_ids: List of candidate item ID strings to evaluate.
            top_k: Number of recommendations to return.
        Returns:
            List of scored candidate dicts sorted by compatibility_score.
        """
        if seed_id not in self.id_to_idx:
            return []
            
        scored = []
        for cand_id in candidate_ids:
            if cand_id == seed_id or cand_id not in self.id_to_idx:
                continue
                
            res = self.predict_compatibility([seed_id, cand_id])
            scored.append({
                "id": cand_id,
                "compatibility_score": res["compatibility_score"],
                "confidence": res["confidence"],
                "outfit_embedding": res["outfit_embedding"],
                "explanation": res["explanation"]
            })
            
        # Sort in descending order of compatibility score
        scored.sort(key=lambda x: x["compatibility_score"], reverse=True)
        return scored[:top_k]
