import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import requests
import tkinter as tk
from tkinter import ttk

def get_stock_data(tickers, start, end):
    """Scarica i dati storici di più azioni da Twelve Data gestendo eventuali errori."""
    API_KEY = "API_KEY"
    all_data = {}
    
    for ticker in tickers:
        url = f"https://api.twelvedata.com/time_series?symbol={ticker}&interval=1day&apikey={API_KEY}&start_date={start}&end_date={end}&outputsize=5000&format=JSON"
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"❌ Errore HTTP {response.status_code} nel recupero dati per {ticker}.")
                continue
            
            data = response.json()
            if "values" not in data:
                print(f"⚠️ Dati non disponibili per {ticker}. Verifica il simbolo, la chiave API o prova più tardi.")
                continue
            
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            })
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime").sort_index()
            df = df.astype(float)
            all_data[ticker] = df
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore di connessione: {e}")
        except ValueError as e:
            print(f"❌ Errore nella decodifica JSON: {e}")
        except Exception as e:
            print(f"❌ Errore sconosciuto: {e}")
    
    return all_data

def calculate_indicators(df):
    """Aggiunge indicatori tecnici al dataframe."""
    if not df.empty:
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['Percent_Change'] = df['Close'].pct_change() * 100
    return df

def save_to_sqlite(data):
    """Salva i dati nel database SQLite."""
    conn = sqlite3.connect("stocks.db")
    for ticker, df in data.items():
        if not df.empty:
            df.to_sql(ticker, conn, if_exists='replace', index=True)
    conn.close()

def plot_stock_data(data):
    """Genera un grafico dell'andamento del prezzo con indicatori e mostra le percentuali di variazione."""
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12,6))
    
    for ticker, df in data.items():
        if not df.empty:
            ax.plot(df.index, df['Close'], label=f'{ticker} Chiusura')
            ax.plot(df.index, df['SMA_20'], label=f'{ticker} SMA 20', linestyle='dashed')
    
    ax.set_title('Andamento Azioni')
    ax.set_xlabel('Data')
    ax.set_ylabel('Prezzo')
    ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
    ax.legend()
    
    percent_text = "\n".join([f"{ticker}: {df['Percent_Change'].iloc[-1]:.2f}%" for ticker, df in data.items() if not df.empty])
    plt.figtext(0.85, 0.5, percent_text, fontsize=12, color='white', ha='left', va='center', bbox=dict(facecolor='gray', alpha=0.5))
    
    plt.show()

def main():
    root = tk.Tk()
    root.title("Tracker Azioni Finanziarie")
    root.geometry("400x350")
    root.configure(bg='#2e2e2e')
    
    ttk.Label(root, text="Inserisci i simboli delle azioni (es. AAPL, TSLA):", background='#2e2e2e', foreground='white').pack(pady=5)
    ticker_entry = ttk.Entry(root, width=40)
    ticker_entry.pack(pady=5)
    
    ttk.Label(root, text="Data Inizio (YYYY-MM-DD):", background='#2e2e2e', foreground='white').pack(pady=5)
    start_entry = ttk.Entry(root, width=20)
    start_entry.insert(0, "2024-01-01")
    start_entry.pack(pady=5)
    
    ttk.Label(root, text="Data Fine (YYYY-MM-DD):", background='#2e2e2e', foreground='white').pack(pady=5)
    end_entry = ttk.Entry(root, width=20)
    end_entry.insert(0, "2024-02-01")
    end_entry.pack(pady=5)
    
    def fetch_data():
        tickers = ticker_entry.get().split(',')
        tickers = [t.strip().upper() for t in tickers if t.strip()]
        start_date = start_entry.get()
        end_date = end_entry.get()
        
        if not tickers:
            tk.messagebox.showerror("Errore", "Nessuna azione selezionata.")
            return
        
        data = get_stock_data(tickers, start_date, end_date)
        if data:
            data = {ticker: calculate_indicators(df) for ticker, df in data.items()}
            save_to_sqlite(data)
            plot_stock_data(data)
        else:
            tk.messagebox.showerror("Errore", "Impossibile completare l'operazione. Dati non disponibili.")
    
    ttk.Button(root, text="Scarica e Analizza", command=fetch_data).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
