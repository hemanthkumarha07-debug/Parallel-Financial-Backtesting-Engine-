# Financial Methodology & Backtesting Engine Specifications

## 1. Zero Look-Ahead Bias Execution Model

A critical flaw in naive backtesters is **look-ahead bias**, where a trade decision made at bar $t$ using the bar's closing price is filled at that exact same closing price. In real markets, the closing price is not known until the bar concludes, making instantaneous fill at that price physically impossible.

### PFSBE Execution Guarantee:
1. At candle $t$, the indicator values (e.g., MA, RSI, Donchian channels) are calculated using closing price $C_t$.
2. The trading signal $S_t \in \{-1, 0, 1\}$ is registered at the close of candle $t$.
3. The trade order is dispatched and executed at the **Open price of candle $t+1$** ($O_{t+1}$).
4. If an open position remains when the historical time-series terminates at candle $T$, the backtester performs an orderly liquidation at candle $T$ close ($C_T$) so that total return and portfolio cash are fully realized.

## 2. Trading Strategy Specifications

### 2.1 Moving Average Crossover (`MovingAverageCrossover`)
- **Fast Period ($L_{\text{fast}}$)**, **Slow Period ($L_{\text{slow}}$)**, Type $\in \{\text{SMA}, \text{EMA}\}$.
- Constraint: $1 \le L_{\text{fast}} < L_{\text{slow}}$.
- Signal Logic:
  - Enter Long ($+1$): When $\text{MA}_{\text{fast}}[t-1] \le \text{MA}_{\text{slow}}[t-1]$ and $\text{MA}_{\text{fast}}[t] > \text{MA}_{\text{slow}}[t]$.
  - Exit Position ($-1$): When $\text{MA}_{\text{fast}}[t-1] \ge \text{MA}_{\text{slow}}[t-1]$ and $\text{MA}_{\text{fast}}[t] < \text{MA}_{\text{slow}}[t]$.

### 2.2 RSI Mean Reversion (`RSIMeanReversion`)
- **Lookback Period ($P$)**, **Oversold Threshold ($\theta_{\text{os}}$)**, **Exit Threshold ($\theta_{\text{exit}}$)**.
- Constraint: $0 < \theta_{\text{os}} < \theta_{\text{exit}} < 100$.
- Formula:
  $$\Delta_t = C_t - C_{t-1}$$
  $$U_t = \max(\Delta_t, 0), \quad D_t = \max(-\Delta_t, 0)$$
  Using Wilder's exponential smoothing ($\alpha = 1/P$):
  $$\text{RSI}_t = 100 - \frac{100}{1 + \frac{\overline{U}_t}{\overline{D}_t}}$$
- Signal Logic:
  - Enter Long ($+1$): If not in position and $\text{RSI}_t \le \theta_{\text{os}}$.
  - Exit Position ($-1$): If in position and $\text{RSI}_t \ge \theta_{\text{exit}}$.

### 2.3 Donchian Channel Breakout (`DonchianBreakout`)
- **Entry Lookback ($N_{\text{entry}}$)**, **Exit Lookback ($N_{\text{exit}}$)**.
- Shifted Channel Formulation (eliminating lookahead bias):
  $$\text{Upper}_t = \max(H_{t-N_{\text{entry}}}, \dots, H_{t-1})$$
  $$\text{Lower}_t = \min(L_{t-N_{\text{exit}}}, \dots, L_{t-1})$$
- Signal Logic:
  - Enter Long ($+1$): If not in position and $C_t > \text{Upper}_t$.
  - Exit Position ($-1$): If in position and $C_t < \text{Lower}_t$.

## 3. Financial Performance & Risk Formulations

1. **Total Return ($R_{\text{total}}$)**:
   $$R_{\text{total}} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}} - 1\right) \times 100\%$$
2. **Annualized Return ($R_{\text{ann}}$)**:
   $$R_{\text{ann}} = \left[\left(1 + \frac{R_{\text{total}}}{100}\right)^{\frac{252}{N}} - 1\right] \times 100\%$$
3. **Maximum Peak-to-Trough Drawdown ($\text{MDD}$)**:
   $$\text{Drawdown}_t = \frac{V_t - \max_{0 \le s \le t} V_s}{\max_{0 \le s \le t} V_s} \times 100\%$$
   $$\text{MDD} = \min_{0 \le t \le N} \text{Drawdown}_t$$
4. **Annualized Sharpe Ratio ($S$)**:
   Given mark-to-market daily returns $r_t = \frac{V_t - V_{t-1}}{V_{t-1}}$ and risk-free rate $r_f$:
   $$S = \frac{\overline{r_t - r_f}}{\sigma(r_t - r_f)} \times \sqrt{252}$$
5. **Win Rate ($W$)**:
   $$W = \frac{\sum \mathbf{1}_{\{\text{PnL}_k > 0\}}}{K} \times 100\%$$
6. **Profit Factor ($PF$)**:
   $$PF = \frac{\sum_{k: \text{PnL}_k > 0} \text{PnL}_k}{\sum_{k: \text{PnL}_k < 0} |\text{PnL}_k|}$$
