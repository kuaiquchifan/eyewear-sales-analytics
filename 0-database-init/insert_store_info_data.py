# 0-database-init/insert_rayban_store_info.py
import re, datetime, random, calendar
from data_sheet_create_0_1 import StoreInfo, session

random.seed(43)

STATE_NAMES = [
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
    "Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa",
    "Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan",
    "Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada",
    "New Hampshire","New Jersey","New Mexico","New York","North Carolina",
    "North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island",
    "South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
    "Virginia","Washington","West Virginia","Wisconsin","Wyoming",
    "District of Columbia"
]

STATE_PATTERN = re.compile(
    r"^(?P<state>" + "|".join(re.escape(s) for s in STATE_NAMES) + r")\s+(?P<store>Ray-Ban.*)$",
    re.IGNORECASE
)

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

def split_state_and_store(line: str):
    match = STATE_PATTERN.match(line)
    if match:
        return match.group("state").strip(), match.group("store").strip()
    return None, None

def parse_store_records(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        raw_lines = [normalize_line(line) for line in f if normalize_line(line)]

    records = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        state, store_name = split_state_and_store(line)
        if state and store_name:
            # 该行是“州名 + 店名”混在一起
            i += 1
            hours = raw_lines[i] if i < len(raw_lines) else ""
            i += 1
            address = raw_lines[i] if i < len(raw_lines) else ""
            i += 1
        else:
            # 正常 4 行一组
            state = line
            store_name = raw_lines[i + 1] if i + 1 < len(raw_lines) else ""
            hours = raw_lines[i + 2] if i + 2 < len(raw_lines) else ""
            address = raw_lines[i + 3] if i + 3 < len(raw_lines) else ""
            i += 4

        if not store_name:
            continue

        city = store_name
        if store_name.lower().startswith("ray-ban "):
            city = store_name[7:].strip()

        records.append({
            "store_name": store_name,
            "store_region": state,
            "store_city": city,
            "store_country": "United States",
            "store_opening_date": simulate_opening_date(address),
            "store_type": "Ray-Ban Store",
            "address": address,
            "hours": hours,
        })

    return records

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
    path = "rayban-store的文本.txt"
    records = parse_store_records(path)
    insert_store_records(records)