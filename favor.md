
# FAVOR+ (Fast Attention Via positive Orthogonal Random features)

FAVOR+ (Fast Attention Via positive Orthogonal Random features) is the mechanism behind the **Performer** architecture. It approximates the standard Softmax attention mechanism to reduce time and space complexity from quadratic $O(L^2)$ to linear $O(L)$.

Here is the concise walkthrough.

## 1. The Bottleneck: Quadratic Complexity

Standard attention computes an $L \times L$ attention matrix $(A)$ first:

$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d}}\right) V$

- $Q, K$ **multiply first**: Creates an $L \times L$ matrix.
- **Memory/Time:** $O(L^2)$. If sequence length $L$ doubles, cost quadruples.

## 2. The Solution: Kernel Associativity

FAVOR+ relies on the property that matrix multiplication is associative: $(A \times B) \times C = A \times (B \times C)$.

If we can decompose the softmax kernel $\exp(q \cdot k)$ into dot products of feature maps $\phi(q)^\top\phi(k)$, we can rewrite attention:

$\text{ApproxAttention} = D^{-1}(Q'(K'^{\top}V))$

- $Q' = \phi(Q)$ and $K' = \phi(K)$.
- $K'$ **and** $V$ **multiply first**: Result is $d \times d$ (independent of length $L$).
- **Time:** $O(L \times d^2)$. Since $d$ (head dimension) is usually small and fixed, this is linear with respect to sequence length $L$.

## 3. The Feature Map $\phi$ (The "Positive Orthogonal" Part)

To make this valid for Softmax attention, the approximation must satisfy two conditions handled by the "P" and "O" in FAVOR+:

1. **Positive (Stability):** Standard Random Fourier Features (using sine/cosine) can be negative, leading to unstable attention. FAVOR+ uses the approximation:

   $\exp(x^\top y) \approx \mathbb{E}_{\omega \sim \mathcal{N}}[\exp(\omega^\top x - \frac{\|x\|^2}{2}) \exp(\omega^\top y - \frac{\|y\|^2}{2})]$

   Since exp is strictly positive, the attention weights remain valid probability distributions.

2. **Orthogonal (Variance Reduction):** Instead of sampling the random projection vectors $\omega$ from a standard Gaussian (IID), FAVOR+ enforces **orthogonality** on the random matrix. This strictly reduces the variance of the estimator, converging faster to the true Softmax.

## 4. Algorithm Summary

1. **Projections:** Generate orthogonal random matrix $W$.
2. **Kernelize:** Compute feature maps $Q' = \phi(Q)$ and $K' = \phi(K)$ using $W$ and element-wise exponentials.
3. **Linear Accumulation:**
   - Compute global context matrix: $\Lambda = K'^{\top}V$ (Size $d \times d$).
   - Compute normalizer: $z = K'^{\top}\mathbf{1}_L$.
4. **Query Update:** Multiply $Q'$ by $\Lambda$ and normalize by $Q'z$.

## 5. Python Implementation

Here is a simplified NumPy implementation of the FAVOR+ mechanism.

```python
import numpy as np

def favor_plus_attention(Q, K, V, num_features=256):
    """
    Q, K, V: Input tensors of shape (Batch, Seq_Len, Dim)
    num_features: Number of random features (m)
    """
    B, L, D = Q.shape
    
    # 1. Generate Orthogonal Random Matrix W
    # We create a block-orthogonal matrix to match num_features
    num_blocks = int(np.ceil(num_features / D))
    blocks = []
    for _ in range(num_blocks):
        # QR decomposition generates an orthogonal matrix Q_mat
        q_mat, _ = np.linalg.qr(np.random.randn(D, D))
        blocks.append(q_mat)
    
    W = np.concatenate(blocks, axis=0)[:num_features].T # (D, m)
    # Scaling factor for the Gaussian kernel approximation
    W = W * np.sqrt(num_features) 

    # 2. Define Feature Map phi(x)
    # phi(x) = (1/sqrt(m)) * exp(W.T @ x - ||x||^2 / 2)
    def feature_map(X):
        # Calculate squared norm element-wise
        # X_norm_sq: (B, L, 1)
        X_norm_sq = np.sum(X ** 2, axis=-1, keepdims=True)
        
        # Random projection
        # projection: (B, L, m)
        projection = X @ W 
        
        # Apply nonlinearity and scaling
        data = np.exp(projection - 0.5 * X_norm_sq)
        return data / np.sqrt(num_features)

    # 3. Transform Q and K
    Q_prime = feature_map(Q) # (B, L, m)
    K_prime = feature_map(K) # (B, L, m)

    # 4. Compute Linear Attention
    # Denominator (Normalizer)
    # Sum over sequence length L for K_prime: (B, m)
    k_sum = np.sum(K_prime, axis=1) 
    # (B, L, m) dot (B, m) -> (B, L)
    denom = Q_prime @ k_sum[..., None]
    
    # Numerator
    # Contract K' and V first: O(L) operation
    # (B, m, L) @ (B, L, D) -> (B, m, D)
    kv_context = K_prime.transpose(0, 2, 1) @ V 
    
    # Apply to Q': (B, L, m) @ (B, m, D) -> (B, L, D)
    num = Q_prime @ kv_context

    # Final Output
    return num / (denom + 1e-6) # Add epsilon for stability

# Example Usage
# L=1000, D=64. Standard attention would imply 1000x1000 matrix.
# FAVOR+ keeps intermediate matrices at size 64x64 (or m x m).
Q = np.random.randn(1, 1000, 64)
K = np.random.randn(1, 1000, 64)
V = np.random.randn(1, 1000, 64)

output = favor_plus_attention(Q, K, V)
print("Output shape:", output.shape) # (1, 1000, 64)
```