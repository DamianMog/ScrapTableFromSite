import requests
from bs4 import BeautifulSoup
import csv
import os
import glob

# Ustalamy ścieżkę do folderu, w którym jest uruchamiany skrypt
script_dir = os.path.dirname(os.path.abspath(__file__))


# Lista stron: każdy element to krotka (URL, NAZWA)
# pages = [
#     ("https://hotwheels.fandom.com/wiki/2012_Hot_Wheels_Boulevard", "2012"),
#     ("https://hotwheels.fandom.com/wiki/2013_Hot_Wheels_Boulevard", "2013"),
#     ("https://hotwheels.fandom.com/wiki/2020_Hot_Wheels_Boulevard", "2020"),
#     ("https://hotwheels.fandom.com/wiki/2021_Hot_Wheels_Boulevard", "2021"),
#     ("https://hotwheels.fandom.com/wiki/2022_Hot_Wheels_Boulevard", "2022"),
#     ("https://hotwheels.fandom.com/wiki/2023_Hot_Wheels_Boulevard", "2023"),
#     ("https://hotwheels.fandom.com/wiki/2024_Hot_Wheels_Boulevard", "2024"),
#     ("https://hotwheels.fandom.com/wiki/2025_Hot_Wheels_Boulevard", "2025")
# ]

pages = [
    ("https://hotwheels.fandom.com/wiki/List_of_2025_Hot_Wheels", "2025"),
    ("https://hotwheels.fandom.com/wiki/List_of_2024_Hot_Wheels", "2024"),
    ("https://hotwheels.fandom.com/wiki/List_of_2023_Hot_Wheels", "2023"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2022_Hot_Wheels", "2022"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2021_Hot_Wheels", "2021"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2020_Hot_Wheels", "2020"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2019_Hot_Wheels", "2019"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2018_Hot_Wheels", "2018"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2017_Hot_Wheels", "2017"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2016_Hot_Wheels", "2016"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2015_Hot_Wheels", "2015"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2014_Hot_Wheels", "2014"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2013_Hot_Wheels", "2013"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2012_Hot_Wheels", "2012"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2011_Hot_Wheels", "2011"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2010_Hot_Wheels", "2010"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2009_Hot_Wheels", "2009"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2008_Hot_Wheels", "2008"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2007_Hot_Wheels", "2007"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2006_Hot_Wheels", "2006"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2005_Hot_Wheels", "2005"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2004_Hot_Wheels", "2004"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2003_Hot_Wheels", "2003"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2002_Hot_Wheels", "2002"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2001_Hot_Wheels", "2001"),
    # ("https://hotwheels.fandom.com/wiki/List_of_2000_Hot_Wheels", "2000"),
]

# Globalna mapa: zewnętrzny URL -> lokalna nazwa pliku (dla obrazków)
image_mapping = {}

def download_image(url, local_filename):
    """Pobiera obrazek z URL i zapisuje do pliku lokalnego."""
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        print(f"Pobrano obrazek: {local_filename}")
    except Exception as e:
        print(f"Błąd pobierania obrazka {url}: {e}")

def extract_table_name(table):
    """
    Szuka najbliższego poprzedzającego elementu H1 lub H2,
    w którym znajduje się element <span> zawierający tekst.
    """
    for tag in table.find_all_previous():
        if tag.name in ["h1", "h2"]:
            span = tag.find("span")
            if span:
                text = span.get_text(strip=True)
                if text:
                    return text
    return ""

def extract_cell_text(cell):
    """
    Zwraca oryginalny tekst komórki.
    Jeśli komórka zawiera obrazek, zwraca:
      - link z elementu <a> (jeśli istnieje), lub
      - atrybut src z <img>.
    W przeciwnym razie zwraca czysty tekst.
    """
    img = cell.find("img")
    if img:
        parent_a = cell.find("a")
        if parent_a and parent_a.has_attr("href"):
            return parent_a["href"]
        if img.has_attr("src"):
            return img["src"]
    return cell.get_text(strip=True)

def parse_table_expanded(table, cell_text_func):
    """
    Parsuje tabelę, rozwijając komórki z atrybutami rowspan/colspan.
    Używa funkcji cell_text_func(cell) do pobrania zawartości komórki.
    Zwraca listę wierszy (każdy wiersz to lista komórek).
    """
    rows = table.find_all("tr")
    grid = []
    spans = {}  # (row_index, col_index) -> wartość

    for r, row in enumerate(rows):
        current_row = []
        cells = row.find_all(["td", "th"])
        col = 0
        cell_index = 0
        # Wstawienie "zaległych" komórek z poprzednich rowspan/colspan
        while (r, col) in spans:
            current_row.append(spans[(r, col)])
            del spans[(r, col)]
            col += 1
        while cell_index < len(cells):
            cell = cells[cell_index]
            cell_index += 1
            text = cell_text_func(cell)
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))
            for j in range(colspan):
                current_row.append(text)
                if rowspan > 1:
                    for k in range(1, rowspan):
                        spans[(r + k, col + j)] = text
            col += colspan
            while (r, col) in spans:
                current_row.append(spans[(r, col)])
                del spans[(r, col)]
                col += 1
        grid.append(current_row)
    return grid

def save_table_to_csv(rows, filename):
    """Zapisuje listę wierszy do pliku CSV."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def merge_csv_files():
    """
    Łączy wszystkie pliki CSV utworzone przez skrypt w jeden duży plik Everything.csv.
    Pomija plik 'Everything.csv', jeśli istnieje.
    """
    everything_path = os.path.join(script_dir, "Everything.csv")
    if os.path.exists(everything_path):
        os.remove(everything_path)
    
    csv_files = glob.glob(os.path.join(script_dir, "*.csv"))
    csv_files = [f for f in csv_files if f != everything_path]
    
    with open(everything_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        for file in csv_files:
            with open(file, "r", newline="", encoding="utf-8") as infile:
                reader = csv.reader(infile)
                for row in reader:
                    writer.writerow(row)
            writer.writerow([])  # separator pustego wiersza
    print("Utworzono plik Everything.csv ze scaloną zawartością wszystkich CSV.")

def modify_table_html(table, table_base):
    """
    Modyfikuje HTML tabeli – dla każdego <img>:
      - pobiera obrazek (jeśli jeszcze nie został pobrany),
      - zmienia atrybut src, aby wskazywał na lokalny plik w folderze img,
      - dodaje styl (max-width:100px).
    """
    img_dir = os.path.join(script_dir, "img")
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    
    img_counter = 1
    for img in table.find_all("img"):
        parent_a = img.find_parent("a")
        if parent_a and parent_a.has_attr("href"):
            img_url = parent_a["href"]
        else:
            img_url = img.get("src", "")
        if not img_url:
            continue
        if img_url in image_mapping:
            local_filename = image_mapping[img_url]
        else:
            local_filename = f"{table_base}_img{img_counter}.jpeg"
            img_counter += 1
            image_mapping[img_url] = local_filename
            download_image(img_url, os.path.join(img_dir, local_filename))
        img["src"] = os.path.join("img", local_filename)
        img["style"] = "max-width:100px; height:auto;"
    return str(table)

def generate_html_file(tables_html):
    """
    Generuje plik tables.html zawierający wszystkie tabele.
    Tabele są ostylowane w stylu MUI i wycentrowane.
    """
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Wszystkie tabele</title>
<link rel="stylesheet" href="https://cdn.muicss.com/mui-0.9.43/css/mui.min.css">
<style>
    body {{
        display: flex;
        justify-content: center;
        padding: 20px;
    }}
    .table-container {{
        width: 100%;
        max-width: 1200px;
    }}
    table {{
        margin: 20px auto;
        border-collapse: collapse;
        width: 100%;
    }}
    table, th, td {{
        border: 1px solid #ccc;
    }}
    th, td {{
        padding: 8px;
        text-align: center;
    }}
</style>
</head>
<body>
<div class="table-container">
{"".join(tables_html)}
</div>
</body>
</html>
"""
    with open(os.path.join(script_dir, "tables.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Utworzono plik tables.html zawierający wszystkie tabele.")

def main():
    all_tables_html = []  # Lista zmodyfikowanych tabel HTML

    # Dla każdej strony inicjujemy licznik tabel
    for url, page_name in pages:
        print(f"Pobieram stronę: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            print(f"Błąd pobierania {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        table_counter = 1
        for table in tables:
            # Pobieramy nagłówek tabeli
            header = extract_table_name(table)
            if header:
                table_base = f"{page_name}_tab{table_counter}_{header}"
            else:
                table_base = f"{page_name}_tab{table_counter}"
            print(f"Zapisuję tabelę: {table_base}")
            
            # Przetwarzanie tabeli do CSV (z oryginalnymi linkami)
            table_rows = parse_table_expanded(table, extract_cell_text)
            csv_filename = os.path.join(script_dir, f"{table_base}.csv")
            save_table_to_csv(table_rows, csv_filename)
            
            # Modyfikacja HTML tabeli (tutaj obrazki będą wskazywały na lokalne pliki)
            table_html_copy = BeautifulSoup(str(table), "html.parser")
            modified_html = modify_table_html(table_html_copy, table_base)
            all_tables_html.append(modified_html)
            
            table_counter += 1

    # Scal wszystkie CSV do pliku Everything.csv
    merge_csv_files()
    # Generuj stronę HTML z tabelami
    generate_html_file(all_tables_html)

if __name__ == "__main__":
    main()