import re, datetime, random, calendar
from pathlib import Path

from data_sheet_create_0_1 import StoreInfo, session

random.seed(43)

INPUT_FILE = Path("lencrafter-store的文本2.txt")
OUTPUT_FILE = Path("lencrafter-store的文本2-processed.txt")


def random_date(start_year: int, end_year: int) -> datetime.date:
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)

def simulate_opening_date(store_name: str) -> datetime.date:
    name = store_name.lower()

    # 旗舰店 / 大店倾向早开业
    if any(token in name for token in [
        "flagship",
        "galleria",
        "mall",
        "plaza",
        "outlet",
        "town center",
        "shopping center",
        "premium outlets",
        "center",
        "ave","avenue",
        "blvd","boulevard",
        "westfield",
    ]):
        weights = [10, 50, 30, 10]  # 更倾向 2015-2019
    else:
        weights = [5, 40, 35, 20]

    period = random.choices(
        ["pre2010", "2015_2019", "2020_2022", "2023_2024"],
        weights=weights,
        k=1
    )[0]

    if period == "pre2010":
        return random_date(2000, 2009)
    if period == "2015_2019":
        return random_date(2015, 2019)
    if period == "2020_2022":
        return random_date(2020, 2022)
    return random_date(2023, 2024)


def normalize_line(line: str) -> str:
    return line.strip()


def parse_store_records(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        raw_lines = [normalize_line(line) for line in f if normalize_line(line)]

    records = []
    i = 0
    while i < len(raw_lines):
        if i + 5 >= len(raw_lines):
            break

        state = raw_lines[i]
        raw_store_name = raw_lines[i + 1]
        hours_line1 = raw_lines[i + 2]
        hours_line2 = raw_lines[i + 3]
        address_line1 = raw_lines[i + 4]
        address_line2 = raw_lines[i + 5]
        i += 6

        store_name = f"LensCrafters {raw_store_name}"

        city = ""
        match = re.search(r"(?P<city>[^,]+),\s*[A-Z]{2}", address_line2)
        if match:
            city = match.group("city").strip()

        records.append({
            "store_name": store_name,
            "store_region": state,
            "store_city": city,
            "store_country": "United States",
            "store_opening_date": simulate_opening_date(raw_store_name),
            "store_type": "Multi-brand Retail",
            "hours": f"{hours_line1} / {hours_line2}",
            "address": f"{address_line1} {address_line2}",
        })

    return records


def write_processed_file(records, output_path: Path):
    with output_path.open("w", encoding="utf-8") as f:
        for rec in records:
            hours = rec['hours'].replace(' / ', '\n')
            address = rec['address'].replace(' ', '\n', 1)
            f.write(f"{rec['store_region']}\n")
            f.write(f"{rec['store_name']}\n")
            f.write(f"{hours}\n")
            f.write(f"{address}\n")
            f.write("\n")


def insert_store_records(records):
    store_objs = []
    seen_names = set()

    for rec in records:
        name_key = rec["store_name"].strip().lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        store = StoreInfo(
            store_name=rec["store_name"],
            store_region=rec["store_region"],
            store_city=rec["store_city"],
            store_country=rec["store_country"],
            store_opening_date=rec["store_opening_date"],
            store_type=rec["store_type"],
        )
        store_objs.append(store)

    if store_objs:
        session.add_all(store_objs)
        session.commit()
        print(f"已插入 {len(store_objs)} 条 StoreInfo 记录。")
    else:
        print("未解析到任何门店记录。")


if __name__ == "__main__":
    records = parse_store_records(INPUT_FILE)
    write_processed_file(records, OUTPUT_FILE)
    print(f"已写入处理后文件：{OUTPUT_FILE}")
    insert_store_records(records)