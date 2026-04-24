import MetaTrader5 as mt5
import pandas as pd
import yaml
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# --- 1. ROBUST PATH RESOLUTION ---
# Otomatis mendeteksi root folder "Gold-Regime-Detection"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
config_path = os.path.join(BASE_DIR, "configs", "data", "mt5_scraper.yaml")
env_path = os.path.join(BASE_DIR, ".env")

# 2. Load Environment & Config
load_dotenv(env_path)
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

def initialize_mt5():
    """Inisialisasi koneksi menggunakan kredensial dari .env"""
    if not mt5.initialize(
        login=int(os.getenv("MT5_LOGIN")),
        password=os.getenv("MT5_PASSWORD"),
        server=os.getenv("MT5_SERVER")
    ):
        logger.error(f"Gagal koneksi ke MT5: {mt5.last_error()}")
        return False
    logger.info("Koneksi ke MT5 Berhasil!")
    return True

def download_data():
    if not initialize_mt5():
        return

    symbol = config['symbol']
    # Map string ke konstanta MT5
    tf_map = {"M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15}
    timeframe = tf_map.get(config['timeframe'], mt5.TIMEFRAME_M5)
    
    # --- Penanganan Timezone (Penting untuk data Finansial) ---
    # Default pakai UTC kalau di yaml tidak ditulis
    tz_string = config.get('timezone', 'Etc/UTC') 
    tz = pytz.timezone(tz_string)
    
    start_dt = datetime.strptime(config['start_date'], "%Y-%m-%d")
    start_dt = tz.localize(start_dt) # Jadikan timezone-aware
    
    end_dt = datetime.strptime(config['end_date'], "%Y-%m-%d")
    end_dt = tz.localize(end_dt)

    logger.info(f"Menarik data {symbol} {config['timeframe']} dari {start_dt.date()} hingga {end_dt.date()} (Timezone: {tz_string})...")
    
    # --- Pengecekan Market Watch ---
    selected_symbols = mt5.symbols_get(symbol)
    if len(selected_symbols) == 0:
        logger.error(f"{symbol} tidak ditemukan. Klik kanan di Market Watch MT5 -> Show All.")
        mt5.shutdown()
        return

    # Pastikan simbol terpilih (select) agar data bisa ditarik
    if not mt5.symbol_select(symbol, True):
        logger.error(f"Gagal memilih {symbol}.")
        mt5.shutdown()
        return
    
    # --- Menarik data range ---
    # Fungsi copy_rates_range HANYA menerima 4 parameter utama
    rates = mt5.copy_rates_range(symbol, timeframe, start_dt, end_dt)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        logger.error("Gagal menarik data. Coba pancing pakai Strategy Tester dulu.")
        return

    # --- Transformasi ke DataFrame ---
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Pastikan folder output ada
    output_abs_path = os.path.join(BASE_DIR, config['output_path'])
    os.makedirs(os.path.dirname(output_abs_path), exist_ok=True)
    
    # Simpan ke CSV
    df.to_csv(output_abs_path, index=False)
    logger.success(f"Berhasil! {len(df)} baris data disimpan di {output_abs_path}")

if __name__ == "__main__":
    download_data()