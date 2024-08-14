import asyncio
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from scraper.async_engine import main as start_engine
from validators.validate_data import DataValidator
from utils.csv_utils import CSVUtils
from utils.utils import load_env_variables
from src.utils.logging_utils import setup_logging, get_logger

setup_logging(log_level=logging.INFO)
logger = get_logger(__name__)

class ScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Nick Shirpley - Web Scraper")
        self.label = tk.Label(master, text="Enter URLs (one per line):")
        self.label.pack()
        
        # create the text widget for input URLs
        self.url_text = tk.Text(master, height=10, width=50, border=2, borderwidth=2)
        self.url_text.pack()

        # create the button to start scraping
        self.scrape_button = tk.Button(master, text="Start Scraping", command=self.key)
        self.scrape_button.pack()

        # create scrollable text widget for logging
        self.log_text = scrolledtext.ScrolledText(master, height=15, width=60)
        self.log_text.pack()

        # Create a custom logger for the GUI
        self.logger = get_logger(self.__class__.__name__)
        
        # Write logs to widget
        text_handler = TextHandler(self.log_text)
        text_handler.setLevel(logging.INFO)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add handler to logger utility (in logger_utils.py)
        self.logger.addHandler(text_handler)

    def key(self):
        urls = self.url_text.get("1.0", tk.END).splitlines()
        fuel = [url.strip() for url in urls if url.strip()]
        
        if not fuel:
            messagebox.showerror("Error", "Add URLs")
            return
        self.logger.info("Async Ignition...")
        
        # initialize entry-point for async execution
        asyncio.run(self.ignition(fuel))

    async def ignition(self, fuel):
        
        # Create a DataValidator object
        qualityControl = DataValidator()
        self.logger.info(f"{len(fuel)} URL(s) Recieved. Async Engine Running...")
        
        # Call the main function from async_engine.py to start AsyncEngine
        results = await start_engine(fuel)
        self.logger.info(f"Received reuslts for {len(results)} URLs.")
        
        all_results = []
        
        for url, url_results in results.items():
            self.logger.info(f"Processing results for URL: {url}")
            self.logger.info(f"Number of results for this URL: {len(url_results)}")
            
            if url_results:
                self.logger.info(f"url_results (in main.py) contains data.")
                
                for result in url_results:
                    self.logger.info(f"Validating result: {result}")
                    
                    if isinstance(result, dict) and qualityControl.validate_contact_info(result):
                        is_valid = qualityControl.validate_contact_info(result)
                        self.logger.info(f"Validataion Result: {is_valid}")
                        
                        if is_valid:
                            result['source_url'] = url
                            all_results.append(result)
                    else:
                        self.logger.warning(f"Unexpected result type: {type(result)}")
                self.logger.info(f"Found {len(url_results)} results from {url}")
            else:
                self.logger.warning(f"No results found for {url}")
        self.logger.info(f"Total Valid Results: {len(all_results)}")
        
        if all_results:
            filename = filedialog.asksaveasfilename(defaultextension=".csv")
            if filename:
                CSVUtils.write_to_csv(all_results, filename)
                self.logger.info(f"Results saved to {filename}")
                messagebox.showinfo("Success", f"Results saved to {filename}")
            else:
                self.logger.warning("No file selected. Results not saved.")
                messagebox.showwarning("Warning", "No file selected. Results not saved.")
        else:
            self.logger.info("No valid results found.")
            messagebox.showinfo("Info", "No valid results found.")

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

def main():
    logger.info("Loading environment variables...")
    load_env_variables()
    
    logger.info("Starting GUI...")
    root = tk.Tk()
    logger.info("GUI started.")
    
    logger.info("Creating ScraperGUI object...")
    gui = ScraperGUI(root)
    logger.info("ScraperGUI object created.")
    
    logger.info("Running main loop...")
    root.mainloop()
    logger.info("GUI closed.")

if __name__ == "__main__":
    main()