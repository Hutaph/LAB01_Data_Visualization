import csv
with open('data/Processed/data_tmp.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    h = next(reader)
    idx = h.index('delivery_date_text')
    for i, row in enumerate(reader):
        print(row[idx])
        if i > 50: break
