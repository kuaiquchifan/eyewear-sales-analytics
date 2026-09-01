# generate_nlp_data_en.py
import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from faker import Faker
from data_sheet_create_0_1 import CompetitorInfo, session

fake = Faker('en_US')
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ====================== Config ======================
COMPETITOR_COUNT = 30

def weighted_choice(dist):
    return random.choices(list(dist.keys()), weights=list(dist.values()), k=1)[0]


# ====================== 1. CompetitorInfo ======================
def generate_competitor_info(n=30):
    brands = [
        "Oakley", "Persol", "Oliver Peoples", "Zeiss", "Hoya",
        "Warby Parker", "Zenni Optical", "GlassesUSA", "Coastal", "EyeBuyDirect",
        "Maui Jim", "Costa Del Mar", "Other Brand"
    ]
    categories = (["Eyeglasses"] * 10 + ["Sunglasses"] * 8 +
                  ["Lens"] * 7 + ["AI Glasses"] * 3 + ["Accessory"] * 2)
    random.shuffle(categories)

    data = []
    for i in range(n):
        category = categories[i]
        if category in ["Lens", "AI Glasses"]:
            price = round(random.uniform(80, 600), 2)
        elif category == "Eyeglasses":
            price = round(random.uniform(50, 450), 2)
        else:
            price = round(random.uniform(40, 350), 2)

        data.append({
            "competitor_id": i + 1,
            "brand": random.choice(brands),
            "competitor_price": price,
            "market_share": round(random.uniform(0.5, 12.0), 2)
        })
    return data


# ====================== 2. CustomerReview (50,000) ======================


# ====================== 3. CustomerComplaint (8,000) ======================


# ====================== Save to CSV ======================
def save_to_csv(data, filename):
    if not data:
        return
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"Saved: {filename} ({len(data)} rows)")

# ===================== Save to Database ======================
def save_to_db(data):
    if not data:
        return
    df = pd.DataFrame(data)
    records = df.to_dict(orient="records")
    session.bulk_insert_mappings(CompetitorInfo,records)
    session.commit()
    print(f"PostgreSQL inserted: {len(records)} rows")



# ===================== Main Execution ======================
if __name__ == "__main__":
    print("Generating English simulation data for North American market...")

    competitors = generate_competitor_info(COMPETITOR_COUNT)
    save_to_csv(competitors, "CompetitorInfo_sim.csv")
    save_to_db(competitors)

    print("All done!")