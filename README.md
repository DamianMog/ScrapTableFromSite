# ScrapTableFromSite
### This script is designed to:
- Scrape HotWheels Fandom Wiki pages – extracting tables from specified pages.
- Export data to CSV files – each table is saved as a separate CSV file following the naming convention:
- <NAME>_tab<NUM>_<TABLE_NAME (if exists)>.csv (e.g., 2013_tab1_Mix 1.csv).
- Download images (IMG) – images found in the tables are downloaded locally into an img folder with names following the naming convention:
- <NAME>_tab<NUM>_<TABLE_NAME (if exists)>_img<NUM>.jpeg.
- Generate an HTML page – a file named tables.html is created that displays all the tables using the locally saved images.

### How It Works
The script retrieves the specified Wiki pages from HotWheels.
It parses tables from each page, handling merged cells (rowspan/colspan) appropriately.
Data from each table is saved into CSV files containing the original image links.
Images embedded in the tables are downloaded and stored locally.
Finally, an HTML file is generated which displays all tables with images referencing the local img folder.

### Requirements
Python 3.x
Libraries: requests, beautifulsoup4

### You can install the required libraries via:
```
pip install requests beautifulsoup4
```

All generated files (CSV files, Everything.csv, tables.html, and the img folder with images) will be saved in the **same directory** as the script.
