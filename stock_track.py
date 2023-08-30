import os
import pandas as pd
import schedule
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from plyer import notification
import matplotlib.pyplot as plt
# Global variable to keep track of the last processed time
last_processed_time = {}

class Watcher:
    def __init__(self, directory_to_watch):
        self.DIRECTORY_TO_WATCH = directory_to_watch
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()

class Handler(FileSystemEventHandler):
    def process(self, event):
        if event.is_directory:
            return

        # If a new file is created or a file is modified
        if event.event_type == 'created' or event.event_type == 'modified':
            check_for_signals()

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

def check_for_signals():
    # Loop through each CSV file in the directory
     for file_name in os.listdir('stocks'):
        if file_name.endswith(".csv"):
            stock_name = file_name.split('.')[0]

            # Load the data
            data_path = os.path.join('stocks', file_name)
            data = pd.read_csv(data_path, parse_dates=['Date'], index_col='Date')

            # Trading strategy logic
            # Calculate short-term and long-term moving averages
            short_window = 50
            long_window = 200
            data['SMA50'] = data['Adj Close'].rolling(window=short_window).mean()
            data['SMA200'] = data['Adj Close'].rolling(window=long_window).mean()

            # Calculate RSI
            delta = data['Adj Close'].diff()
            gain = (delta.where(delta > 0, 0)).fillna(0)
            loss = (-delta.where(delta < 0, 0)).fillna(0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            data['RSI'] = 100 - (100 / (1 + rs))

            # Calculate average volume
            data['Avg Volume'] = data['Volume'].rolling(window=14).mean()

            # Define buy/sell signals based on the strategy
            data['Buy Signal'] = (data['SMA50'] > data['SMA200']) & (data['RSI'] < 30) & (data['Volume'] > data['Avg Volume'])
            data['Sell Signal'] = (data['SMA50'] < data['SMA200']) & (data['RSI'] > 70) & (data['Volume'] > data['Avg Volume'])

            # Plot the graph after processing the signals
            plt.figure(figsize=(15, 10))
            data['Adj Close'].plot(label='Stock Price', alpha=0.5)
            data['SMA50'].plot(label='50-Day Moving Average', alpha=0.8)
            data['SMA200'].plot(label='200-Day Moving Average', alpha=0.8)

            # Highlighting buy signals
            plt.scatter(data[data['Buy Signal']].index, data['Adj Close'][data['Buy Signal']], 
                        marker='^', color='g', s=100, label='Buy Signal')

            # Highlighting sell signals
            plt.scatter(data[data['Sell Signal']].index, data['Adj Close'][data['Sell Signal']], 
                        marker='v', color='r', s=100, label='Sell Signal')

            plt.title(f'Stock Price of {stock_name} with Buy/Sell Signals')
            plt.xlabel('Date')
            plt.ylabel('Stock Price')
            plt.legend(loc='best')
            plt.grid(True)
            plt.tight_layout()
            plt.show()

if __name__ == '__main__':
    #schedule.every().day.at("10:28").do(check_for_signals)  # Schedule the check for 8pm daily

    # Start the folder watcher
    watch = Watcher("stocks")
    watch.run()
