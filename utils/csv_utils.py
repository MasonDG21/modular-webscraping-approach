import csv

class CSVUtils:
    @staticmethod
    def write_to_csv(data, filename):
        if not data:
            return

        fieldnames = ["name", "title", "email", "linkedin", "src_url"]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    @staticmethod
    def read_from_csv(filename):
        data = []
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        return data