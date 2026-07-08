import torch
import torch.nn as nn
import torch.nn.functional as F

class AttentionPooling(nn.Module):
    """Aggregates item embeddings into a single outfit embedding using query-based attention."""
    def __init__(self, dim: int = 512):
        super().__init__()
        self.query = nn.Parameter(torch.randn(1, 1, dim))
        self.key_proj = nn.Linear(dim, dim)
        self.value_proj = nn.Linear(dim, dim)
        self.scale = dim ** -0.5

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None):
        """
        Args:
            x: Item embeddings [BatchSize, SeqLen, Dim]
            mask: Attention mask [BatchSize, SeqLen] (True for padded positions)
        Returns:
            outfit_emb: [BatchSize, Dim]
            attn_probs: [BatchSize, SeqLen]
        """
        B, S, D = x.shape
        # Expand query to batch size
        q = self.query.expand(B, 1, D)  # [B, 1, D]
        k = self.key_proj(x)            # [B, S, D]
        v = self.value_proj(x)          # [B, S, D]

        # Compute query-key dot-product attention
        scores = torch.bmm(q, k.transpose(1, 2)) * self.scale  # [B, 1, S]

        if mask is not None:
            # Mask out padded tokens (masked positions filled with negative infinity)
            scores = scores.masked_fill(mask.unsqueeze(1), float('-inf'))

        attn_probs = torch.softmax(scores, dim=-1)  # [B, 1, S]
        pooled = torch.bmm(attn_probs, v)           # [B, 1, D]
        
        return pooled.squeeze(1), attn_probs.squeeze(1)


class FashionTransformerCompatibilityModel(nn.Module):
    """
    Multimodal Transformer Compatibility Model
    - 4 Transformer Encoder Layers
    - 8 Attention Heads
    - 512 Hidden Size
    - Modality Fusion for Visual, Text, and Metadata Embeddings
    - Attention Pooling for Outfit Embedding
    - Compatibility and Confidence classification heads
    """
    def __init__(self, vocab_sizes: dict, embed_dims: dict = None, dim: int = 512):
        super().__init__()
        self.dim = dim
        
        # 1. Modality Projectors
        self.visual_projector = nn.Sequential(
            nn.Linear(512, dim),
            nn.LayerNorm(dim),
            nn.ReLU(),
            nn.Linear(dim, dim)
        )
        
        self.text_projector = nn.Sequential(
            nn.Linear(512, dim),
            nn.LayerNorm(dim),
            nn.ReLU(),
            nn.Linear(dim, dim)
        )
        
        # 2. Metadata Embeddings
        # Default embedding sizes for metadata attributes
        if embed_dims is None:
            embed_dims = {
                'category': 64,
                'color': 32,
                'occasion': 32,
                'season': 16,
                'gender': 16,
                'style': 32,
                'material': 32,
                'pattern': 32,
                'brand': 64,
                'fit': 32
            }
        
        self.metadata_embeddings = nn.ModuleDict({
            field: nn.Embedding(vocab_sizes[field], embed_dims[field])
            for field in vocab_sizes
        })
        
        total_meta_dim = sum(embed_dims.values())
        self.metadata_projector = nn.Sequential(
            nn.Linear(total_meta_dim, dim),
            nn.LayerNorm(dim),
            nn.ReLU(),
            nn.Linear(dim, dim)
        )
        
        # 3. Fusion Norm & Slot Embeddings
        self.fusion_norm = nn.LayerNorm(dim)
        self.fusion_dropout = nn.Dropout(0.1)
        
        # Slot/Type Embeddings (0: topwear, 1: bottomwear, 2: footwear, 3: layer, 4: accessory, 5: pad)
        self.slot_embeddings = nn.Embedding(6, dim)
        self.pos_embeddings = nn.Embedding(10, dim)
        
        # 4. Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=dim,
            nhead=8,
            dim_feedforward=2048,
            dropout=0.1,
            activation='relu',
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=4)
        
        # 5. Attention Pooling
        self.attention_pooling = AttentionPooling(dim=dim)
        
        # 6. Compatibility & Confidence Prediction Heads
        self.compat_head = nn.Sequential(
            nn.Linear(dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 1)
        )
        
        self.conf_head = nn.Sequential(
            nn.Linear(dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 1)
        )
        
    def forward(self, visual_embs: torch.Tensor, text_embs: torch.Tensor, 
                metadata: torch.Tensor, slot_ids: torch.Tensor, 
                padding_mask: torch.Tensor = None) -> dict:
        """
        Args:
            visual_embs: [BatchSize, SeqLen, 512]
            text_embs: [BatchSize, SeqLen, 512]
            metadata: [BatchSize, SeqLen, 10] (indices of category, color, occasion, etc.)
            slot_ids: [BatchSize, SeqLen] (indices of slot mapping)
            padding_mask: [BatchSize, SeqLen] (Boolean tensor, True for pad elements)
        Returns:
            Dict containing:
                compatibility_score: [BatchSize, 1]
                confidence: [BatchSize, 1]
                outfit_embedding: [BatchSize, 512]
                attention_weights: [BatchSize, SeqLen]
                item_embeddings: [BatchSize, SeqLen, 512]
        """
        B, S, _ = visual_embs.shape
        
        # Project inputs
        v_proj = self.visual_projector(visual_embs)  # [B, S, Dim]
        t_proj = self.text_projector(text_embs)      # [B, S, Dim]
        
        # Process metadata
        meta_embs_list = []
        # Fields are ordered: category, color, occasion, season, gender, style, material, pattern, brand, fit
        fields = ['category', 'color', 'occasion', 'season', 'gender', 'style', 'material', 'pattern', 'brand', 'fit']
        for i, field in enumerate(fields):
            field_indices = metadata[:, :, i]  # [B, S]
            emb = self.metadata_embeddings[field](field_indices)  # [B, S, FieldDim]
            meta_embs_list.append(emb)
            
        meta_concat = torch.cat(meta_embs_list, dim=-1)  # [B, S, TotalMetaDim]
        meta_proj = self.metadata_projector(meta_concat)  # [B, S, Dim]
        
        # Fuse projected features (Add)
        fused = v_proj + t_proj + meta_proj  # [B, S, Dim]
        fused = self.fusion_norm(fused)
        fused = self.fusion_dropout(fused)
        
        # Add slot and positional embeddings
        slot_emb = self.slot_embeddings(slot_ids)  # [B, S, Dim]
        pos_indices = torch.arange(S, device=visual_embs.device).unsqueeze(0).expand(B, S)
        pos_emb = self.pos_embeddings(pos_indices)  # [B, S, Dim]
        
        x = fused + slot_emb + pos_emb  # [B, S, Dim]
        
        # Pass through Transformer Encoder
        # PyTorch src_key_padding_mask takes True for elements to ignore
        item_ctx = self.transformer_encoder(x, src_key_padding_mask=padding_mask)  # [B, S, Dim]
        
        # Outfit aggregation via Attention Pooling
        outfit_emb, attn_weights = self.attention_pooling(item_ctx, mask=padding_mask)  # [B, Dim], [B, S]
        
        # Predict scores
        compatibility_score = torch.sigmoid(self.compat_head(outfit_emb))  # [B, 1]
        confidence = torch.sigmoid(self.conf_head(outfit_emb))            # [B, 1]
        
        return {
            "compatibility_score": compatibility_score,
            "confidence": confidence,
            "outfit_embedding": outfit_emb,
            "attention_weights": attn_weights,
            "item_embeddings": item_ctx
        }
