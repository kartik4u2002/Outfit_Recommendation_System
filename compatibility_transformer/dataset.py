import os
import random
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from typing import Dict, List, Tuple, Any

from .utils import extract_all_metadata, MetadataVocabulary

SLOT_TO_ID = {
    'top': 0,
    'bottom': 1,
    'footwear': 2,
    'layer': 3,
    'dress': 4,
    'accessory': 5
}

OUTFIT_SLOTS = {
    'top': ['formal-shirts', 'casual-shirts', 'linen-shirts', 'party-shirts', 'tshirts', 'polo-tshirts', 'sweatshirts', 'sweaters', 'tops'],
    'bottom': ['trousers', 'jeans', 'chinos', 'shorts', 'track-pants', 'skirts', 'leggings'],
    'footwear': ['running-shoes', 'sneakers', 'ethnic-footwear', 'heels', 'boots', 'flats', 'formal-shoes', 'loafers', 'sandals'],
    'layer': ['blazers', 'suits', 'nehru-jackets', 'denim-jackets', 'long-coats'],
    'dress': ['party-dresses', 'casual-dresses', 'maxi-dresses', 'co-ord-sets', 'kurta-sets', 'sherwanis', 'sharara-sets', 'salwar-suits', 'wedding-sarees'],
    'accessory': ['necklaces', 'earrings', 'clutches', 'handbags', 'sunglasses', 'watches', 'caps']
}

SLOT_MAPPING = {article_type: slot_name for slot_name, types in OUTFIT_SLOTS.items() for article_type in types}

def get_slot_id(category: str) -> int:
    slot_name = SLOT_MAPPING.get(str(category).lower(), 'accessory')
    return SLOT_TO_ID.get(slot_name, 5)

class OutfitDataset(Dataset):
    """
    Outfit Dataset that loads pre-extracted Fashion-CLIP features and metadata.
    Implements 1:5 negative sampling.
    """
    def __init__(self, 
                 products_df: pd.DataFrame, 
                 outfits_df: pd.DataFrame,
                 visual_embs: np.ndarray,
                 text_embs: np.ndarray,
                 vocab: MetadataVocabulary,
                 num_negatives: int = 5,
                 is_train: bool = True):
        self.products_df = products_df.copy()
        self.outfits_df = outfits_df.copy()
        self.visual_embs = visual_embs
        self.text_embs = text_embs
        self.vocab = vocab
        self.num_negatives = num_negatives
        self.is_train = is_train
        
        # Build mapping from product ID to row index
        self.id_to_idx = {row['id']: idx for idx, row in self.products_df.iterrows()}
        
        # Category to product IDs mapping for slot-aware negative sampling
        self.slot_to_ids = {slot: [] for slot in SLOT_TO_ID}
        for _, row in self.products_df.iterrows():
            cat = str(row['category']).lower()
            slot = SLOT_MAPPING.get(cat, 'accessory')
            if slot in self.slot_to_ids:
                self.slot_to_ids[slot].append(row['id'])
                
        # Parse outfits into list of product IDs
        self.outfit_columns = [
            'hero_id', 'second_id', 'layer_id', 'footwear_id', 'accessory_1_id', 'accessory_2_id'
        ]
        
        self.samples: List[Tuple[List[str], int]] = []
        self._prepare_samples()
        
    def _prepare_samples(self):
        """Prepares positive and negative outfit sequences."""
        # Reset random seed for reproducible splits if needed, but standard is fine
        for _, row in self.outfits_df.iterrows():
            # Get valid item IDs in the outfit
            outfit_items = []
            for col in self.outfit_columns:
                item_id = row.get(col)
                if pd.notna(item_id) and str(item_id).strip() != "" and str(item_id).strip() in self.id_to_idx:
                    outfit_items.append(str(item_id).strip())
                    
            if len(outfit_items) < 2:
                continue  # Need at least two items to constitute a pairwise/outfit compatibility check
                
            # Add positive sample
            self.samples.append((outfit_items, 1))
            
            # Generate negative samples
            if self.is_train:
                negatives_generated = 0
                attempts = 0
                while negatives_generated < self.num_negatives and attempts < 50:
                    attempts += 1
                    # Copy positive outfit
                    neg_items = list(outfit_items)
                    # Pick a random item in the outfit to swap
                    swap_idx = random.randint(0, len(neg_items) - 1)
                    swap_item_id = neg_items[swap_idx]
                    
                    # Find slot of the item being swapped
                    swap_item_row = self.products_df.loc[self.products_df['id'] == swap_item_id].iloc[0]
                    cat = str(swap_item_row['category']).lower()
                    slot = SLOT_MAPPING.get(cat, 'accessory')
                    
                    # Pick a random replacement from the same slot
                    candidates = self.slot_to_ids.get(slot, list(self.id_to_idx.keys()))
                    # Filter out items already in the outfit
                    candidates = [c for c in candidates if c not in outfit_items]
                    
                    if not candidates:
                        # Fallback: pick any random item not in the outfit
                        candidates = [c for c in self.id_to_idx.keys() if c not in outfit_items]
                        
                    replacement_id = random.choice(candidates)
                    neg_items[swap_idx] = replacement_id
                    
                    # Ensure it's not a duplicate negative or matches positive
                    if neg_items != outfit_items:
                        self.samples.append((neg_items, 0))
                        negatives_generated += 1
            else:
                # For validation/testing, generate exactly num_negatives negatives for evaluation consistency
                for _ in range(self.num_negatives):
                    neg_items = list(outfit_items)
                    swap_idx = random.randint(0, len(neg_items) - 1)
                    swap_item_id = neg_items[swap_idx]
                    swap_item_row = self.products_df.loc[self.products_df['id'] == swap_item_id].iloc[0]
                    cat = str(swap_item_row['category']).lower()
                    slot = SLOT_MAPPING.get(cat, 'accessory')
                    
                    candidates = self.slot_to_ids.get(slot, list(self.id_to_idx.keys()))
                    candidates = [c for c in candidates if c not in outfit_items]
                    if not candidates:
                        candidates = [c for c in self.id_to_idx.keys() if c not in outfit_items]
                    
                    replacement_id = random.choice(candidates)
                    neg_items[swap_idx] = replacement_id
                    self.samples.append((neg_items, 0))

    def __len__(self) -> int:
        return len(self.samples)
        
    def __getitem__(self, idx: int) -> Tuple[List[str], int]:
        return self.samples[idx]

def collate_outfits(batch: List[Tuple[List[str], int]], 
                    products_df: pd.DataFrame, 
                    id_to_idx: Dict[str, int],
                    visual_embs: np.ndarray, 
                    text_embs: np.ndarray, 
                    vocab: MetadataVocabulary, 
                    max_seq_len: int = 6) -> Dict[str, torch.Tensor]:
    """Collates a list of outfit items into padded tensors."""
    batch_size = len(batch)
    
    # Pre-allocate tensors
    v_tensor = torch.zeros(batch_size, max_seq_len, 512, dtype=torch.float32)
    t_tensor = torch.zeros(batch_size, max_seq_len, 512, dtype=torch.float32)
    meta_tensor = torch.zeros(batch_size, max_seq_len, 10, dtype=torch.long)
    slot_tensor = torch.zeros(batch_size, max_seq_len, dtype=torch.long)
    padding_mask = torch.zeros(batch_size, max_seq_len, dtype=torch.bool)
    labels = torch.zeros(batch_size, 1, dtype=torch.float32)
    
    fields = ['category', 'color', 'occasion', 'season', 'gender', 'style', 'material', 'pattern', 'brand', 'fit']
    
    for b_idx, (item_ids, label) in enumerate(batch):
        labels[b_idx, 0] = label
        
        # Populate each item in the outfit
        for seq_idx, item_id in enumerate(item_ids[:max_seq_len]):
            if item_id not in id_to_idx:
                continue
                
            row_idx = id_to_idx[item_id]
            row = products_df.iloc[row_idx]
            
            # Extract embeddings
            v_tensor[b_idx, seq_idx] = torch.tensor(visual_embs[row_idx], dtype=torch.float32)
            t_tensor[b_idx, seq_idx] = torch.tensor(text_embs[row_idx], dtype=torch.float32)
            
            # Encode metadata
            meta = extract_all_metadata(row)
            for f_idx, field in enumerate(fields):
                meta_tensor[b_idx, seq_idx, f_idx] = vocab.encode(field, meta[field])
                
            # Slot ID
            slot_tensor[b_idx, seq_idx] = get_slot_id(row['category'])
            # Set padding mask to False (this position is NOT ignored)
            padding_mask[b_idx, seq_idx] = False
            
        # Pad remaining positions
        for seq_idx in range(len(item_ids), max_seq_len):
            slot_tensor[b_idx, seq_idx] = 5  # Pad slot ID
            padding_mask[b_idx, seq_idx] = True  # Ignore in attention
            
    return {
        "visual_embs": v_tensor,
        "text_embs": t_tensor,
        "metadata": meta_tensor,
        "slot_ids": slot_tensor,
        "padding_mask": padding_mask,
        "label": labels
    }
