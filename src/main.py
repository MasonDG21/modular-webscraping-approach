import asyncio
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from scraper.async_engine import main as scrape_main
from validators.validate_data import DataValidator
from utils.csv_utils import CSVUtils
from utils.utils import load_env_variables

class ScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Web Scraper")

        self.label = tk.Label(master, text="Enter URLs (one per line):")
        self.label.pack()

        self.url_text = tk.Text(master, height=10, width=50)
        self.url_text.pack()

        self.scrape_button = tk.Button(master, text="Start Scraping", command=self.start_scraping)
        self.scrape_button.pack()

        self.log_text = scrolledtext.ScrolledText(master, height=20, width=80)
        self.log_text.pack()

        # Create a custom logger
        self.logger = logging.getLogger("ScraperGUI")
        self.logger.setLevel(logging.INFO)
        
        # Create a handler that writes log messages to the ScrolledText widget
        text_handler = TextHandler(self.log_text)
        self.logger.addHandler(text_handler)

    def start_scraping(self):
        urls = self.url_text.get("1.0", tk.END).splitlines()
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            messagebox.showerror("Error", "Please enter at least one URL.")
            return

        validator = DataValidator()
        
        self.log_text.delete(1.0, tk.END)  # Clear previous log
        self.logger.info("Starting scraping process...")
        
        asyncio.run(self.run_scraper(validator, urls))

    async def run_scraper(self, validator, urls):
        results = await scrape_main(urls)
        all_results = []
        for url, url_results in results.items():
            if url_results:
                validated_results = [result for result in url_results if validator.validate_contact_info(result)]
                for result in validated_results:
                    result['source_url'] = url  # Add source URL to each result
                all_results.extend(validated_results)
                self.logger.info(f"Found {len(validated_results)} valid results from {url}")
            else:
                self.logger.warning(f"No results found for {url}")

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
        logging.Handler.__init__(self)
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
    load_env_variables()
    root = tk.Tk()
    gui = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()