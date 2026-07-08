import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Dict, List, Tuple, Any

def compute_outfit_item_similarity(item_embs: torch.Tensor, padding_mask: torch.Tensor) -> torch.Tensor:
    """
    Computes the average pairwise cosine similarity of items in each outfit in the batch.
    Args:
        item_embs: [B, S, Dim] (contextual item embeddings from Transformer)
        padding_mask: [B, S] (Boolean mask, True for pad positions)
    Returns:
        outfit_sims: [B] (average pairwise similarity for each outfit)
    """
    B, S, D = item_embs.shape
    # Normalize embeddings to unit sphere
    norms = torch.norm(item_embs, p=2, dim=-1, keepdim=True)
    norms = torch.where(norms == 0, torch.ones_like(norms), norms)
    item_embs_norm = item_embs / norms  # [B, S, Dim]
    
    # Compute dot product similarity matrix for each outfit in batch
    sim_matrices = torch.bmm(item_embs_norm, item_embs_norm.transpose(1, 2))  # [B, S, S]
    
    outfit_sims = torch.zeros(B, device=item_embs.device)
    
    for b in range(B):
        # Find non-padded items
        non_pad_mask = ~padding_mask[b]  # [S]
        valid_indices = torch.nonzero(non_pad_mask).squeeze(-1)
        K = len(valid_indices)
        
        if K < 2:
            outfit_sims[b] = 0.0
            continue
            
        # Select submatrix of valid item similarities
        valid_sims = sim_matrices[b][valid_indices][:, valid_indices]  # [K, K]
        
        # Sum upper triangular part (excluding diagonal)
        triu_indices = torch.triu_indices(row=K, col=K, offset=1, device=item_embs.device)
        triu_sims = valid_sims[triu_indices[0], triu_indices[1]]
        
        # Average
        outfit_sims[b] = torch.mean(triu_sims)
        
    return outfit_sims

def compute_triplet_margin_loss(outfit_sims: torch.Tensor, labels: torch.Tensor, margin: float = 0.2) -> torch.Tensor:
    """
    Computes Triplet Margin Loss comparing positive outfits against negative outfits.
    Enforces outfit_sims(pos) > outfit_sims(neg) + margin.
    """
    pos_mask = (labels == 1.0).squeeze(-1)
    neg_mask = (labels == 0.0).squeeze(-1)
    
    pos_sims = outfit_sims[pos_mask]
    neg_sims = outfit_sims[neg_mask]
    
    if len(pos_sims) == 0 or len(neg_sims) == 0:
        return torch.tensor(0.0, device=outfit_sims.device)
        
    # Broadcast to compare every positive with every negative
    # pos_sims: [P, 1], neg_sims: [1, N]
    diffs = neg_sims.unsqueeze(0) - pos_sims.unsqueeze(1) + margin  # [P, N]
    losses = torch.clamp(diffs, min=0.0)
    
    return torch.mean(losses)

def compute_ranking_loss(scores: torch.Tensor, labels: torch.Tensor, margin: float = 0.1) -> torch.Tensor:
    """
    Computes Ranking Loss comparing compatibility scores of positive vs negative outfits.
    Enforces scores(pos) > scores(neg) + margin.
    """
    pos_mask = (labels == 1.0).squeeze(-1)
    neg_mask = (labels == 0.0).squeeze(-1)
    
    pos_scores = scores[pos_mask]
    neg_scores = scores[neg_mask]
    
    if len(pos_scores) == 0 or len(neg_scores) == 0:
        return torch.tensor(0.0, device=scores.device)
        
    diffs = neg_scores.unsqueeze(0) - pos_scores.unsqueeze(1) + margin
    losses = torch.clamp(diffs, min=0.0)
    return torch.mean(losses)

def train_epoch(model: nn.Module, 
                dataloader: DataLoader, 
                optimizer: optim.Optimizer, 
                device: torch.device, 
                lambda_triplet: float = 1.0, 
                lambda_ranking: float = 0.5) -> Tuple[float, float, float, float]:
    model.train()
    
    total_loss = 0.0
    total_bce = 0.0
    total_triplet = 0.0
    total_ranking = 0.0
    
    bce_loss_fn = nn.BCELoss()
    
    for batch in dataloader:
        v_embs = batch['visual_embs'].to(device)
        t_embs = batch['text_embs'].to(device)
        meta = batch['metadata'].to(device)
        slot_ids = batch['slot_ids'].to(device)
        padding_mask = batch['padding_mask'].to(device)
        labels = batch['label'].to(device)
        
        optimizer.zero_grad()
        
        outputs = model(v_embs, t_embs, meta, slot_ids, padding_mask)
        scores = outputs['compatibility_score']
        item_embs = outputs['item_embeddings']
        
        # 1. Binary Compatibility Loss
        loss_bce = bce_loss_fn(scores, labels)
        
        # 2. Triplet Margin Loss on Item Cosine Similarities
        outfit_sims = compute_outfit_item_similarity(item_embs, padding_mask)
        loss_triplet = compute_triplet_margin_loss(outfit_sims, labels, margin=0.2)
        
        # 3. Ranking Loss on Outputs
        loss_ranking = compute_ranking_loss(scores, labels, margin=0.1)
        
        loss = loss_bce + lambda_triplet * loss_triplet + lambda_ranking * loss_ranking
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * len(labels)
        total_bce += loss_bce.item() * len(labels)
        total_triplet += loss_triplet.item() * len(labels)
        total_ranking += loss_ranking.item() * len(labels)
        
    num_samples = len(dataloader.dataset)
    return (
        total_loss / num_samples,
        total_bce / num_samples,
        total_triplet / num_samples,
        total_ranking / num_samples
    )

def evaluate_model(model: nn.Module, 
                   dataloader: DataLoader, 
                   device: torch.device) -> Tuple[float, float]:
    model.eval()
    
    correct = 0
    total = 0
    total_bce = 0.0
    bce_loss_fn = nn.BCELoss()
    
    with torch.no_grad():
        for batch in dataloader:
            v_embs = batch['visual_embs'].to(device)
            t_embs = batch['text_embs'].to(device)
            meta = batch['metadata'].to(device)
            slot_ids = batch['slot_ids'].to(device)
            padding_mask = batch['padding_mask'].to(device)
            labels = batch['label'].to(device)
            
            outputs = model(v_embs, t_embs, meta, slot_ids, padding_mask)
            scores = outputs['compatibility_score']
            
            loss_bce = bce_loss_fn(scores, labels)
            total_bce += loss_bce.item() * len(labels)
            
            preds = (scores >= 0.5).float()
            correct += (preds == labels).sum().item()
            total += len(labels)
            
    return total_bce / total, correct / total

def train_model(model: nn.Module, 
                train_loader: DataLoader, 
                val_loader: DataLoader, 
                epochs: int, 
                lr: float, 
                device: torch.device, 
                save_path: str = "compatibility_model.pt") -> Dict[str, List[float]]:
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    history = {
        "train_loss": [],
        "train_bce": [],
        "train_triplet": [],
        "train_ranking": [],
        "val_loss": [],
        "val_acc": []
    }
    
    best_acc = -1.0
    
    print(f"Starting training on device: {device} for {epochs} epochs...")
    for epoch in range(epochs):
        loss, bce, triplet, rank = train_epoch(
            model, train_loader, optimizer, device, lambda_triplet=1.0, lambda_ranking=0.5
        )
        scheduler.step()
        
        val_bce, val_acc = evaluate_model(model, val_loader, device)
        
        history["train_loss"].append(loss)
        history["train_bce"].append(bce)
        history["train_triplet"].append(triplet)
        history["train_ranking"].append(rank)
        history["val_loss"].append(val_bce)
        history["val_acc"].append(val_acc)
        
        print(f"Epoch {epoch+1:02d}/{epochs:02d} | Train Loss: {loss:.4f} (BCE: {bce:.4f}, Trip: {triplet:.4f}, Rank: {rank:.4f}) | Val BCE: {val_bce:.4f} | Val Acc: {val_acc*100:.2f}%")
        
        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), save_path)
            print(f" => Saved new best model checkpoint to {save_path} (Val Acc: {val_acc*100:.2f}%)")
            
    return history
