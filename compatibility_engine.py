import os
import pandas as pd
import numpy as np
import torch
from typing import Tuple, List, Dict, Any

from compatibility_transformer.inference import FashionCompatibilityInferenceEngine

# Lazy-loaded global inference engine
_engine = None

def get_engine(df=None) -> FashionCompatibilityInferenceEngine:
    global _engine
    if _engine is None:
        DATA_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # Load files if not provided
        if df is None:
            products_path = os.path.join(DATA_DIR, 'products.csv')
            df = pd.read_csv(products_path)
            
        visual_path = os.path.join(DATA_DIR, 'visual_embeddings.npy')
        text_path = os.path.join(DATA_DIR, 'text_embeddings.npy')
        
        visual_embs = np.load(visual_path)
        text_embs = np.load(text_path)
        
        model_path = os.path.join(DATA_DIR, 'compatibility_transformer', 'compatibility_model.pt')
        vocab_path = os.path.join(DATA_DIR, 'compatibility_transformer', 'vocab_mapping.pkl')
        
        _engine = FashionCompatibilityInferenceEngine(
            model_path=model_path,
            vocab_path=vocab_path,
            products_df=df,
            visual_embs=visual_embs,
            text_embs=text_embs
        )
    return _engine

def compatibility_score(id1_or_idx, id2_or_idx, df=None, sim_matrix=None) -> Tuple[float, str]:
    """
    Exposes a backward-compatible wrapper for the legacy compatibility_score function.
    Returns (score, explanation).
    """
    # Load default DataFrame if not provided
    if df is None:
        DATA_DIR = os.path.dirname(os.path.abspath(__file__))
        products_path = os.path.join(DATA_DIR, 'products.csv')
        df = pd.read_csv(products_path)
        
    # Resolve IDs
    if isinstance(id1_or_idx, (int, np.integer)):
        id1 = df.iloc[int(id1_or_idx)]['id']
    else:
        id1 = str(id1_or_idx)
        
    if isinstance(id2_or_idx, (int, np.integer)):
        id2 = df.iloc[int(id2_or_idx)]['id']
    else:
        id2 = str(id2_or_idx)
        
    engine = get_engine(df)
    res = engine.predict_compatibility([id1, id2])
    
    return res["compatibility_score"], res["explanation"]

def predict_compatibility(item_ids: List[str]) -> Dict[str, Any]:
    """Predicts detailed compatibility for a list of item IDs."""
    engine = get_engine()
    return engine.predict_compatibility(item_ids)

def rank_candidates(seed_id: str, candidate_ids: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    """Ranks candidate items based on compatibility with a seed item."""
    engine = get_engine()
    return engine.rank_candidates(seed_id, candidate_ids, top_k)
