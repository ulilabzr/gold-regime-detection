import numpy as np
import pandas as pd

df = pd.read_csv("R:\CODING\DATA SCIENCE\Gold-Regime-Detection\data\raw\mt5\xauusd_m5_raw.csv")

df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))