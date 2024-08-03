import tkinter as tk
from tkinter import filedialog, messagebox
from scraper import ScraperEngine
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

    def start_scraping(self):
        urls = self.url_text.get("1.0", tk.END).splitlines()
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            messagebox.showerror("Error", "Please enter at least one URL.")
            return

        scraper = ScraperEngine()
        results = scraper.scrape_urls(urls)

        if results:
            filename = filedialog.asksaveasfilename(defaultextension=".csv")
            if filename:
                CSVUtils.write_to_csv(results, filename)
                messagebox.showinfo("Success", f"Results saved to {filename}")
            else:
                messagebox.showwarning("Warning", "No file selected. Results not saved.")
        else:
            messagebox.showinfo("Info", "No results found.")

def main():
    load_env_variables()
    root = tk.Tk()
    gui = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()