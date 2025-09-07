"""
UNet-128 Model Configuration for Stage 1 Fine-tuning
Lightweight UNet architecture for fast iteration on T4 GPU
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
import math

class TimestepEmbedding(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim
        
    def forward(self, timesteps: torch.Tensor) -> torch.Tensor:
        device = timesteps.device
        half_dim = self.dim // 2
        embeddings = math.log(10000) / (half_dim - 1)
        embeddings = torch.exp(torch.arange(half_dim, device=device) * -embeddings)
        embeddings = timesteps[:, None] * embeddings[None, :]
        embeddings = torch.cat([embeddings.sin(), embeddings.cos()], dim=-1)
        return embeddings

class CrossAttention(nn.Module):
    def __init__(self, query_dim: int, context_dim: int, heads: int = 8, head_dim: int = 64):
        super().__init__()
        inner_dim = head_dim * heads
        self.heads = heads
        self.scale = head_dim ** -0.5
        
        self.to_q = nn.Linear(query_dim, inner_dim, bias=False)
        self.to_k = nn.Linear(context_dim, inner_dim, bias=False)
        self.to_v = nn.Linear(context_dim, inner_dim, bias=False)
        self.to_out = nn.Linear(inner_dim, query_dim)
        
    def forward(self, x: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        h = self.heads
        q = self.to_q(x)
        k = self.to_k(context)
        v = self.to_v(context)
        
        q, k, v = map(lambda t: t.view(t.shape[0], t.shape[1], h, -1).transpose(1, 2), (q, k, v))
        
        sim = torch.einsum('b h i d, b h j d -> b h i j', q, k) * self.scale
        attn = sim.softmax(dim=-1)
        
        out = torch.einsum('b h i j, b h j d -> b h i d', attn, v)
        out = out.transpose(1, 2).contiguous().view(out.shape[0], out.shape[2], -1)
        return self.to_out(out)

class ResBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, time_emb_dim: int, dropout: float = 0.0):
        super().__init__()
        self.time_mlp = nn.Sequential(
            nn.SiLU(),
            nn.Linear(time_emb_dim, out_channels)
        )
        
        self.block1 = nn.Sequential(
            nn.GroupNorm(8, in_channels),
            nn.SiLU(),
            nn.Conv2d(in_channels, out_channels, 3, padding=1)
        )
        
        self.block2 = nn.Sequential(
            nn.GroupNorm(8, out_channels),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Conv2d(out_channels, out_channels, 3, padding=1)
        )
        
        self.skip_conv = nn.Conv2d(in_channels, out_channels, 1) if in_channels != out_channels else nn.Identity()
        
    def forward(self, x: torch.Tensor, time_emb: torch.Tensor) -> torch.Tensor:
        h = self.block1(x)
        h = h + self.time_mlp(time_emb)[:, :, None, None]
        h = self.block2(h)
        return h + self.skip_conv(x)

class AttentionBlock(nn.Module):
    def __init__(self, channels: int, context_dim: int):
        super().__init__()
        self.norm = nn.GroupNorm(8, channels)
        self.self_attn = CrossAttention(channels, channels, heads=4, head_dim=32)
        self.cross_attn = CrossAttention(channels, context_dim, heads=4, head_dim=32)
        
    def forward(self, x: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        
        # Reshape for attention
        x_norm = self.norm(x)
        x_flat = x_norm.view(b, c, h * w).transpose(1, 2)  # (b, h*w, c)
        
        # Self attention
        x_flat = x_flat + self.self_attn(x_flat, x_flat)
        
        # Cross attention with CLIP embeddings
        x_flat = x_flat + self.cross_attn(x_flat, context)
        
        # Reshape back
        x_out = x_flat.transpose(1, 2).view(b, c, h, w)
        return x + x_out

class UNet128(nn.Module):
    """
    Lightweight UNet for Stage 1 fine-tuning
    - 128 base channels instead of 320
    - Fewer attention layers
    - Optimized for T4 GPU
    """
    
    def __init__(
        self,
        in_channels: int = 4,
        out_channels: int = 4,
        model_channels: int = 128,
        num_res_blocks: int = 2,
        attention_resolutions: Tuple[int, ...] = (4, 2),
        dropout: float = 0.0,
        channel_mult: Tuple[int, ...] = (1, 2, 4),
        conv_resample: bool = True,
        num_heads: int = 4,
        context_dim: int = 768,  # CLIP embedding dimension
    ):
        super().__init__()
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.model_channels = model_channels
        self.num_res_blocks = num_res_blocks
        self.attention_resolutions = attention_resolutions
        self.dropout = dropout
        self.channel_mult = channel_mult
        self.conv_resample = conv_resample
        self.num_heads = num_heads
        
        # Time embedding
        time_embed_dim = model_channels * 4
        self.time_embed = nn.Sequential(
            TimestepEmbedding(model_channels),
            nn.Linear(model_channels, time_embed_dim),
            nn.SiLU(),
            nn.Linear(time_embed_dim, time_embed_dim),
        )
        
        # Input projection
        self.input_blocks = nn.ModuleList([
            nn.Conv2d(in_channels, model_channels, 3, padding=1)
        ])
        
        # Encoder
        input_block_chans = [model_channels]
        ch = model_channels
        ds = 1
        
        for level, mult in enumerate(channel_mult):
            for _ in range(num_res_blocks):
                layers = [ResBlock(ch, mult * model_channels, time_embed_dim, dropout)]
                ch = mult * model_channels
                
                if ds in attention_resolutions:
                    layers.append(AttentionBlock(ch, context_dim))
                
                self.input_blocks.append(nn.ModuleList(layers))
                input_block_chans.append(ch)
            
            if level != len(channel_mult) - 1:
                self.input_blocks.append(nn.Conv2d(ch, ch, 3, stride=2, padding=1))
                input_block_chans.append(ch)
                ds *= 2
        
        # Middle
        self.middle_block = nn.Sequential(
            ResBlock(ch, ch, time_embed_dim, dropout),
            AttentionBlock(ch, context_dim),
            ResBlock(ch, ch, time_embed_dim, dropout),
        )
        
        # Decoder
        self.output_blocks = nn.ModuleList([])
        for level, mult in list(enumerate(channel_mult))[::-1]:
            for i in range(num_res_blocks + 1):
                ich = input_block_chans.pop()
                layers = [ResBlock(ch + ich, mult * model_channels, time_embed_dim, dropout)]
                ch = mult * model_channels
                
                if ds in attention_resolutions:
                    layers.append(AttentionBlock(ch, context_dim))
                
                if level and i == num_res_blocks:
                    layers.append(nn.ConvTranspose2d(ch, ch, 4, stride=2, padding=1))
                    ds //= 2
                
                self.output_blocks.append(nn.ModuleList(layers))
        
        # Output
        self.out = nn.Sequential(
            nn.GroupNorm(8, model_channels),
            nn.SiLU(),
            nn.Conv2d(model_channels, out_channels, 3, padding=1),
        )
        
    def forward(self, x: torch.Tensor, timesteps: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        """
        x: (B, 4, H, W) latent
        timesteps: (B,) timestep
        context: (B, 768) CLIP embedding
        """
        # Expand context for cross-attention
        context = context.unsqueeze(1)  # (B, 1, 768)
        
        # Time embedding
        emb = self.time_embed(timesteps)
        
        # Encoder
        hs = []
        h = x
        for module in self.input_blocks:
            if isinstance(module, nn.ModuleList):
                for layer in module:
                    if isinstance(layer, ResBlock):
                        h = layer(h, emb)
                    elif isinstance(layer, AttentionBlock):
                        h = layer(h, context)
                    else:
                        h = layer(h)
            else:
                h = module(h)
            hs.append(h)
        
        # Middle
        for layer in self.middle_block:
            if isinstance(layer, ResBlock):
                h = layer(h, emb)
            elif isinstance(layer, AttentionBlock):
                h = layer(h, context)
            else:
                h = layer(h)
        
        # Decoder
        for module in self.output_blocks:
            h = torch.cat([h, hs.pop()], dim=1)
            for layer in module:
                if isinstance(layer, ResBlock):
                    h = layer(h, emb)
                elif isinstance(layer, AttentionBlock):
                    h = layer(h, context)
                else:
                    h = layer(h)
        
        return self.out(h)

def create_unet128() -> UNet128:
    """Create UNet-128 model with production settings"""
    return UNet128(
        in_channels=4,
        out_channels=4,
        model_channels=128,
        num_res_blocks=2,
        attention_resolutions=(4, 2),
        dropout=0.1,
        channel_mult=(1, 2, 4),
        num_heads=4,
        context_dim=768,
    )

if __name__ == "__main__":
    # Test model
    model = create_unet128()
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test forward pass
    x = torch.randn(2, 4, 64, 64)
    t = torch.randint(0, 1000, (2,))
    c = torch.randn(2, 768)
    
    with torch.no_grad():
        out = model(x, t, c)
        print(f"Input shape: {x.shape}")
        print(f"Output shape: {out.shape}")
        print("✓ UNet-128 forward pass successful")
