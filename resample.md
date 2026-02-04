# Sampling L2 Order Book Events into 1s / 5s Bars

A clean, practical guide to turn raw L2 events (order book updates) into time-based bars without common pitfalls.

Assumes you have event-time updates with timestamps and (at least) best bid/ask and maybe depth.

---

## 0. Decide Your "Clock"

You need to pick one of these as the book value for each bar:

### A) End-of-Interval Snapshot (Recommended Baseline)

For each interval $[t, t+\Delta)$, take the last book state observed at or before $t+\Delta$.

- Stable, easy, matches "what did the book look like right after the interval."
- Works great for features like spread, imbalance, microprice, depth.

### B) Time-Weighted Average (TWAP) of Book States

Average a feature $x(\cdot)$ by time spent in each state:

$\overline{x}_{[t,t+\Delta)}=\frac{1}{\Delta}\int_{t}^{t+\Delta} x(u)\,du$

Implementation uses piecewise-constant states between updates.

- Better when updates are bursty (event clustering).
- Slightly more work but often superior for noisy symbols.

### C) Event-Count Sampling (Not Wall-Clock Aligned)

Every $N$ events. Not aligned to wall-clock; skip unless you have a reason.

**For 1s/5s, use A or B.**

---

## 1. Build a "Book State Stream" First (Important)

Raw feeds can include partial updates ("only level 3 ask changed"). You want a clean state:

- Maintain the latest full book $S(t)$ in memory.
- Each incoming event updates $S(t)$.
- Now you effectively have a piecewise-constant process $S(t)$.

From $S(t)$, compute features like:

$m(t)=\frac{a_1(t)+b_1(t)}{2},\quad s(t)=a_1(t)-b_1(t),\quad \text{Imb}_1(t)=\frac{q^b_1-q^a_1}{q^b_1+q^a_1}$

---

## 2. Define the Bar Grid and Timestamp Rules

Let $\Delta\in\{1s,5s\}$. Define grid times:

$t_i = t_0 + i\Delta$

**Interval convention**: Use half-open bins $[t_i, t_{i+1})$. This avoids double-counting events that fall exactly on boundaries.

**Timestamp alignment**: Pick one and be consistent:
- Floor to seconds (e.g., 12:00:03.9 → 12:00:03)
- Ceil (rare)
- Nearest (can be messy)

Most people use floor.

---

## 3. Snapshot Sampling (A): "Last Observation Carried Forward" (LOCF)

For each grid endpoint $t_{i+1}$, take the most recent state at or before it:

$x_{i} = x(t_{i+1}^-)$

Practically:
- For each bar, the value is the last feature value seen in that bar.
- If no update occurs during the bar, you carry forward the last known value.

**Good for**: spread, depth, imbalance, microprice, book shape.

**Edge cases**:
- If your file starts at time $t_0$ and there's no prior state: you'll have NaNs until first update (or you seed from an initial snapshot).

---

## 4. Time-Weighted Sampling (B): TWAP Over Each Interval

Since $x(t)$ is piecewise constant between event times, you can compute:

Let updates occur at times $u_0 < u_1 < \dots < u_n$ within/around the interval.

If the state holds value $x_j$ on $[u_j, u_{j+1})$, then over $[t_i,t_{i+1})$:

$\overline{x}_i=\frac{1}{\Delta}\sum_{j} x_j \cdot \left(\min(u_{j+1},t_{i+1})-\max(u_j,t_i)\right)$

**Good for**: noisy or bursty markets, "average" liquidity conditions, stable training signals.

**Note**: For some features (like imbalance), TWAP tends to be nicer than last-tick.

---

## 5. Flow Features: Sample Changes Within Each Bar

For event-driven quantities, you don't want TWAP; you want aggregation.

Let $\Delta q^b_1(e)$ and $\Delta q^a_1(e)$ be changes per event $e$.

### Net Order Flow Imbalance per Bar

$\text{NOFI}_i=\sum_{e\in [t_i,t_{i+1})} \left(\Delta q^b_1(e)-\Delta q^a_1(e)\right)$

### Update Count / Intensity

$N_i = \#\{e: e\in [t_i,t_{i+1})\},\quad \text{UpdRate}_i=\frac{N_i}{\Delta}$

### Best Quote Changes Within Bar

$\Delta b_{1,i} = b_1(t_{i+1}^-)-b_1(t_i^-)$

(similarly for ask)

These are often the features that improve 1s/5s prediction.

---

## 6. What the Final Bar Usually Contains (Clean Schema)

For each bar end time $t_{i+1}$, you typically store:

### Snapshot-Type (LOCF or TWAP):
- $m_i$, $s_i$
- $\text{Imb}_{1,i}$, $\text{Imb}_{K,i}$
- Microprice premium $\mu_i - m_i$
- Depth sums $Q^b_i$, $Q^a_i$, slopes/shape proxies

### Flow-Type (Aggregated Within Bar):
- $\text{NOFI}_i$
- Cancels/adds per side (if available)
- Update count $N_i$

### Label (Future Return):

For horizon $h$ bars:

$y_i = \log m(t_{i+1}+h\Delta)-\log m(t_{i+1})$

(Or use mid-change in ticks.)

---

## 7. Microstructure Gotchas (That Matter a Lot)

- **Don't sample directly from raw messages** without building a coherent state.
- **Use half-open intervals** to avoid boundary double-count.
- **Carry-forward is not "cheating"**; it's how piecewise-constant state works.
- **Locked/crossed markets**: Decide whether to drop bars where $a_1 \le b_1$ or fix using feed rules.
- **Outages / gaps**: Add a feature like gap length since last update; consider dropping huge gaps.
- **Training leakage**: If you label using $m(t_{i+1})$, make sure your feature snapshot uses $t_{i+1}^-$ (pre-close), not post-close.

---

## Simple Recommended Setup (Works Well)

### For 1s:
- **Snapshot features**: End-of-second LOCF
- **Flow features**: Sum over events inside the second
- **Add a "seconds since last update" feature**

### For 5s:
- **Snapshot features**: TWAP (often better)
- **Flow features**: Sum over the 5s window
- **Also keep end-of-window snapshot** (both can help)

---

## Next Steps

If you tell me what your raw data looks like (e.g., "MBP-10 updates with full depth each event" vs "incremental MBO updates"), I can give you the exact sampling logic that matches it—because the "correct" way to compute $\Delta q$ and cancels vs trades depends on the feed structure.