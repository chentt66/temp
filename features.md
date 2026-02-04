# Microstructure Features from Level 2 Order Book Data

A comprehensive menu of reusable features built from order-book data (top-of-book + multiple depth levels).

---

## Notation (at time $t$)

Let the book have levels $k=1,\dots,K$.

- **Best bid/ask**: $b_1(t)$, $a_1(t)$
- **Depth at level $k$**: bid size $q^b_k(t)$, ask size $q^a_k(t)$
- **Prices at level $k$**: $b_k(t)$, $a_k(t)$
- **Midprice**: $m(t)=\frac{a_1(t)+b_1(t)}{2}$
- **Spread**: $s(t)=a_1(t)-b_1(t)$
- **Tick size**: $\tau$ (if relevant)
- **Total depth** (up to $K$):

$Q^b(t)=\sum_{k=1}^K q^b_k(t),\quad Q^a(t)=\sum_{k=1}^K q^a_k(t)$

---

## 1. Top-of-Book State Features

These are baseline but surprisingly strong.

### Spread & Relative Spread

$s(t)=a_1(t)-b_1(t), \quad \text{relSpread}(t)=\frac{s(t)}{m(t)}$

**Meaning**: Instantaneous transaction cost / tightness. Relative spread makes instruments comparable.

### Midprice Returns

Over horizon $\Delta$:

$r_\Delta(t)=\log m(t+\Delta)-\log m(t)$

**Meaning**: Your target (future move) or a contemporaneous feature.

### Tick-Scaled Spread

$s_\tau(t)=\frac{s(t)}{\tau}$

**Meaning**: "How many ticks wide" the market is; useful across regimes.

---

## 2. Depth / Imbalance Features (Multi-Level)

### Best-Level Imbalance

$\text{Imb}_1(t)=\frac{q^b_1(t)-q^a_1(t)}{q^b_1(t)+q^a_1(t)}$

**Meaning**: Pressure at the touch; often predictive of short-horizon direction.

### Multi-Level (Weighted) Imbalance

Choose weights $w_k$ (common: $w_k=\exp(-\lambda(k-1))$ or $w_k=1/k$):

$\text{Imb}_K(t)=\frac{\sum_{k=1}^K w_k\, q^b_k(t)-\sum_{k=1}^K w_k\, q^a_k(t)}{\sum_{k=1}^K w_k\, q^b_k(t)+\sum_{k=1}^K w_k\, q^a_k(t)}$

**Meaning**: Uses deeper book; tends to be more stable than level-1.

### Cumulative Depth Ratios

$\text{DepthRatio}_K(t)=\log\frac{Q^b(t)+\epsilon}{Q^a(t)+\epsilon}$

**Meaning**: Asymmetric liquidity; the log makes it symmetric and scale-friendly.

---

## 3. Price "Shape" of the Book (Slope/Convexity)

These capture how quickly liquidity gets expensive as you walk the book.

### Distance-from-Mid per Level

$d^a_k(t)=a_k(t)-m(t),\quad d^b_k(t)=m(t)-b_k(t)$

### Book Slope (Simple Proxy)

One practical form: regression-style slope of price distance vs cumulative depth.

Let cumulative ask depth $C^a_k(t)=\sum_{i=1}^k q^a_i(t)$ (similarly $C^b_k$).

Define:

$\text{Slope}^a(t)=\frac{\sum_{k=1}^K d^a_k(t)}{\sum_{k=1}^K C^a_k(t)+\epsilon},\quad \text{Slope}^b(t)=\frac{\sum_{k=1}^K d^b_k(t)}{\sum_{k=1}^K C^b_k(t)+\epsilon}$

**Meaning**: Higher slope = thinner book / higher marginal impact.

### Convexity / Curvature (One Proxy)

Compare near vs far depth:

$\text{Conv}^a(t)=\frac{\sum_{k=1}^{K/2} q^a_k(t)}{\sum_{k=K/2+1}^{K} q^a_k(t)+\epsilon}$

(and similarly for bid)

**Meaning**: Whether liquidity is concentrated near the touch or deeper.

---

## 4. Microprice and Related Features

Microprice shifts the mid toward the "heavier" side at the touch.

### Microprice

$\mu(t)=\frac{a_1(t)\,q^b_1(t)+b_1(t)\,q^a_1(t)}{q^b_1(t)+q^a_1(t)}$

### Microprice Premium

$\text{MicroPrem}(t)=\mu(t)-m(t)$

**Meaning**: A signed signal of short-term pressure; often cleaner than raw imbalance.

---

## 5. Order-Flow from L2 Updates (Add/Cancel/Replace)

From successive book states, infer queue changes. For each level $k$:

$\Delta q^b_k(t)=q^b_k(t)-q^b_k(t^-),\quad \Delta q^a_k(t)=q^a_k(t)-q^a_k(t^-)$

A common decomposition (implementation depends on event flags you have):
- $\Delta q>0$: add liquidity (limit add)
- $\Delta q<0$: cancel or execute (liquidity removal)

### Net Order-Flow Imbalance (NOFI) at the Touch

$\text{NOFI}(t)=\Delta q^b_1(t)-\Delta q^a_1(t)$

Or normalized:

$\text{nNOFI}(t)=\frac{\Delta q^b_1(t)-\Delta q^a_1(t)}{q^b_1(t)+q^a_1(t)+\epsilon}$

**Meaning**: Captures changes in pressure, not just static depth.

### Multi-Level Net Flow

$\text{Flow}_K(t)=\sum_{k=1}^K w_k\,\Delta q^b_k(t)-\sum_{k=1}^K w_k\,\Delta q^a_k(t)$

**Meaning**: Broader view of adds/cancels across the book.

---

## 6. Book Dynamics / "Stability" Features

### Quote Update Intensity

Count events in a window $[t-\Delta,t]$:

$\text{UpdRate}_\Delta(t)=\frac{N_{\text{updates}}(t-\Delta,t)}{\Delta}$

**Meaning**: Activity regime / toxic flow proxy.

### Spread Duration / Mid Duration

Time since last spread change:

$\text{AgeSpread}(t)=t-\max\{u<t: s(u)\neq s(u^-)\}$

**Meaning**: Stable vs jumpy liquidity.

### Imbalance Volatility

$\text{VolImb}_\Delta(t)=\sqrt{\operatorname{Var}\left(\text{Imb}_1(u)\;:\;u\in[t-\Delta,t]\right)}$

**Meaning**: Unstable queue pressure tends to be less reliable.

---

## 7. Price-Level Movement / Queue Position Style Features

### Best Price Changes (Quote Direction)

$\Delta b_1(t)=b_1(t)-b_1(t^-),\quad \Delta a_1(t)=a_1(t)-a_1(t^-)$

Turn into categorical features:
- bid up / bid down / unchanged
- ask up / ask down / unchanged

**Meaning**: Quote revisions are informative about short-term intent and adverse selection.

### Queue Depletion Proxies

If best bid stays but $q^b_1$ drops fast:

$\text{Deplete}^b_\Delta(t)= -\sum_{u\in[t-\Delta,t]} \min(\Delta q^b_1(u),0)$

(similarly for ask)

**Meaning**: Approaching level wipeout → higher chance of price move through that level.

---

## 8. Liquidity Cost / "Book Price Impact" Proxies

Approximate the cost to execute a market order of size $V$ by walking depth.

### Average Execution Price on the Ask for Buy Size $V$

Let $x_k$ be the filled quantity at each level with $\sum x_k=V$, $0\le x_k\le q^a_k$.

$P^{buy}_V(t)=\frac{\sum_{k=1}^K a_k(t)\,x_k}{V}$

Then define impact relative to mid:

$\text{Imp}^{buy}_V(t)=P^{buy}_V(t)-m(t)$

(similarly for sell)

**Meaning**: A direct, economically interpretable liquidity measure; great for cross-asset comparability if $V$ is notional-scaled.

---

## 9. Normalizations That Usually Matter

Raw sizes are not comparable across symbols/time. Common fixes:

- Divide by rolling volume $\widehat{Vol}_\Delta(t)$ or median top depth
- Z-score within day: $z(t)=\frac{x(t)-\mu_{day}}{\sigma_{day}+\epsilon}$
- Notional depth: $q \times \text{price}$ for cross-instrument comparability

---

## Practical "Starter Set" (If You Only Build ~10)

1. $m(t)$, $s(t)$, $s(t)/m(t)$
2. $\text{Imb}_1(t)$, $\text{Imb}_K(t)$ (exp-decay weights)
3. Microprice premium $\mu(t)-m(t)$
4. $\text{NOFI}(t)$ or nNOFI
5. Update rate in last $\Delta$
6. Depletion proxy on bid/ask in last $\Delta$
7. Buy/sell impact for a fixed $V$ (or $V$ as fraction of top depth)

This bundle is small, interpretable, and tends to generalize.

---

## Next Steps

If you specify your instrument type (equities vs futures vs crypto) and sampling choice (event-time vs 1s bars vs 5s), I can provide a "canonical" feature table with exact implementation choices (weights, $K$, normalization, and horizons) that won't blow up on edge cases like crossed markets, locked quotes, or feed resets.