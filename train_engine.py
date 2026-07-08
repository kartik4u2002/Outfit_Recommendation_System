import os
import argparse
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader

from compatibility_transformer import (
    MetadataVocabulary, OutfitDataset, collate_outfits, 
    FashionTransformerCompatibilityModel, train_model
)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    parser = argparse.ArgumentParser(description="Train the Fashion Multimodal Transformer Compatibility Model.")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    args = parser.parse_args()

    print("=== Fashion Compatibility Transformer Training Pipeline ===")
    
    # 1. Load Data
    products_path = os.path.join(DATA_DIR, 'products.csv')
    outfits_path = os.path.join(DATA_DIR, 'outfits.csv')
    visual_embeddings_path = os.path.join(DATA_DIR, 'visual_embeddings.npy')
    text_embeddings_path = os.path.join(DATA_DIR, 'text_embeddings.npy')
    
    if not os.path.exists(products_path) or not os.path.exists(outfits_path):
        raise FileNotFoundError("Missing products.csv or outfits.csv in current directory.")
        
    print("Loading datasets...")
    products_df = pd.read_csv(products_path)
    outfits_df = pd.read_csv(outfits_path)
    
    if os.path.exists(visual_embeddings_path) and os.path.exists(text_embeddings_path):
        print("Loading pre-extracted Fashion-CLIP embeddings...")
        visual_embs = np.load(visual_embeddings_path)
        text_embs = np.load(text_embeddings_path)
    else:
        raise FileNotFoundError("Pre-extracted Fashion-CLIP embeddings ('visual_embeddings.npy' / 'text_embeddings.npy') are missing.")
        
    # 2. Build and save vocabulary
    vocab = MetadataVocabulary()
    vocab.build_vocabularies(products_df)
    vocab_path = os.path.join(DATA_DIR, 'compatibility_transformer', 'vocab_mapping.pkl')
    vocab.save(vocab_path)
    print(f"Saved metadata vocabulary mapping to {vocab_path}")
    
    # 3. Train / Val Split
    # Since we have only 25 outfits, we do a simple split (20 train, 5 validation)
    # We shuffle the outfits randomly to get a good spread of styles
    outfits_shuffled = outfits_df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    train_outfits = outfits_shuffled.iloc[:20]
    val_outfits = outfits_shuffled.iloc[20:]
    
    print(f"Dataset split: {len(train_outfits)} train outfits, {len(val_outfits)} validation outfits.")
    
    # 4. Create Datasets & Dataloaders
    train_dataset = OutfitDataset(
        products_df, train_outfits, visual_embs, text_embs, vocab, num_negatives=5, is_train=True
    )
    val_dataset = OutfitDataset(
        products_df, val_outfits, visual_embs, text_embs, vocab, num_negatives=5, is_train=False
    )
    
    # Custom collate helper
    id_to_idx = {row['id']: idx for idx, row in products_df.iterrows()}
    
    def custom_collate(batch):
        return collate_outfits(
            batch, products_df, id_to_idx, visual_embs, text_embs, vocab, max_seq_len=6
        )
        
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=custom_collate)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=custom_collate)
    
    print(f"Dataloaders initialized. Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    
    # 5. Initialize Model
    vocab_sizes = {field: vocab.get_vocab_size(field) for field in vocab.fields}
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = FashionTransformerCompatibilityModel(vocab_sizes=vocab_sizes, dim=512)
    model = model.to(device)
    
    # Save path for the checkpoint
    model_save_path = os.path.join(DATA_DIR, 'compatibility_transformer', 'compatibility_model.pt')
    
    # 6. Train the model
    train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=args.epochs,
        lr=args.lr,
        device=device,
        save_path=model_save_path
    )
    
    print("\nTraining completed successfully!")
    print(f"Saved best model checkpoint to: {model_save_path}")
    print("\n[Recommendation for Generalization]")
    print("Due to the small dataset size (25 curated outfits), this model is prone to overfitting.")
    print("For production use, we strongly recommend pre-training this architecture on larger public fashion datasets:")
    print("- Polyvore Outfits (contain over 68,000 outfits)")
    print("- DeepFashion (contains over 800,000 images with rich attribute annotations)")
    print("- FashionGen (contains over 293,000 high-resolution items paired with professional descriptions)")
    print("Then fine-tune the model on your curated stylized outfits to specialize its style preferences.")

if __name__ == "__main__":
    main()
