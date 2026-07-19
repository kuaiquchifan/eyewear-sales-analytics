# 这是模拟ray-ban镜架和镜片的产品信息数据生成脚本，主要用于数据库初始化和测试。
# 已完成。
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_sheet_create_0_1 import ProductInfo, Base, DATABASE_URL, create_tables_if_not_exist

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

import random
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_sheet_create_0_1 import ProductInfo, create_tables_if_not_exist, DATABASE_URL

random.seed(2026)

FRAME_COUNT = 160
LENS_COUNT = 40
ACCESSORY_COUNT = 20
genders = ["Man", "Women", "Kid"]
categories = ["Sunglasses", "AI Glasses"]
prescription_flags = [True, False]
promos = ["none", "30% OFF", "50% OFF"]
frame_shapes = ["pilot", "Square", "oval", "Round", "Geometrical", "Rectangle"]
frame_colors = [
    "Brown", "Beige", "Black", "Blue", "Clear", "Copper", "Gold",
    "Gunmetal", "Havana", "Multicolor", "Orange", "Red", "Silver",
    "Tortoise", "White", "Yellow", "Green", "Grey", "Pink", "Violet"
]
frame_materials = ["Metal", "Nylon & Propionate", "Acetate", "Innovative", "Premium Materials"]
lens_brands = ["Ray-Ban", "essilor"]
lens_colors = [
    "Green", "Black", "Blue", "Brown", "Clear", "Demo Lens", "Grey",
    "Red", "Gold", "Orange", "Pink", "Silver", "Violet", "White", "Yellow"
]
lens_types = [
    "Solid Color", "Transitions", "Gradient", "Clear", "Violet",
    "Polarized+", "Polarized S", "Mirror", "Evolve", "Chromance"
]
lens_visions = ["Single vision", "Progressive"]
lens_thicknesses = [1.60, 1.67, 1.74]
insurance_flags = [True, False]
frame_fits = ["Standard", "Petite", "Generous"]
bridge_nosepads = ["Universal Fit", "High Bridge Fit", "Low Bridge Fit", "Petite"]

classic_rayban_models = ["Aviator Classic", "Original Wayfarer", "New Wayfarer", "Clubmaster", "Round Metal",
                         "Bill", "Sam", "Flacko", "Kai", "Mega Wayfarer Optics"]
ai_rayban_models = ["Ray-Ban Reverse", "Ray-Ban Meta"]

# 赠品的配件类型列表
accessory_types = ["Cleaning Cloth","Lens Spray","Eyeglass Case","Hard Case","Neck Strap","Clip"]


def random_accessory_price(accessory_type):
    price_ranges = {
        "Cleaning Cloth": (5,10),
        "Lens Spray": (8,15),
        "Eyeglass Case": (15,30),
        "Hard Case": (20,40),
        "Neck Strap": (10,25),
        "Clip": (15,35)
    }

    low, high = price_ranges[accessory_type]
    return round(random.uniform(low,high),2)



def random_lens_price(lens_type: str, lens_thickness: float) -> float:
    price_ranges = {
        "Clear": (45, 90),
        "Solid Color": (55, 110),
        "Violet": (55, 110),
        "Gradient": (120, 180),
        "Mirror": (130, 190),
        "Transitions": (160, 250),
        "Evolve": (180, 300),
        "Polarized S": (220, 280),
        "Polarized+": (240, 320),
        "Chromance": (260, 360),
    }
    low, high = price_ranges.get(lens_type, (90, 150))

    if lens_thickness == 1.60:
        thickness_surcharge = 0
    elif lens_thickness == 1.67:
        thickness_surcharge = 50
    elif lens_thickness == 1.74:
        thickness_surcharge = 120
    else:
        thickness_surcharge = 0

    return round(random.uniform(low, high) + thickness_surcharge, 2)


def random_frame_price(frame_material: str, category: str, is_prescription: bool) -> float:
    price_ranges = {
        "Nylon & Propionate": (150, 170),
        "Metal": (160, 210),
        "Acetate": (170, 220),
        "Innovative": (230, 350),
        "Premium Materials": (300, 500),
    }
    low, high = price_ranges.get(frame_material, (160, 220))

    # AI Glasses 属于高端智能镜架，价格进一步上浮
    if category == "AI Glasses":
        low *= 1.15
        high *= 1.25

    # 处方镜通常价格还会稍高一些
    if is_prescription:
        low *= 1.05
        high *= 1.15

    return round(random.uniform(low, high), 2)

def random_launch_date():
    year = random.choice([2020, 2024])
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


# 新增: 配件
def build_accessory_product(index):
    accessory_type=random.choice(accessory_types)
    retail_price=random_accessory_price(accessory_type)

    return ProductInfo(
        product_m3_code=f"RB-AC-{index:04d}",
        product_name=f"Ray-Ban {accessory_type}",
        category="Accessory",
        sub_category="Free Gift",
        brand="Ray-Ban",
        sub_brand=accessory_type,
        product_type="Accessory",
        cost_price=round(retail_price*random.uniform(0.3,0.5),2),
        retail_price=retail_price,
        launch_date=random_launch_date(),
        season="Year-round",
        is_discount=0
    )



def build_frame_product(index: int, category: str, is_prescription: bool) -> ProductInfo:
    if category == "AI Glasses":
        model = random.choice(ai_rayban_models)
        sub_category = "AI Smart Glasses"
    elif category == "Eyeglasses":
        model = random.choice(classic_rayban_models)
        sub_category = "Eyeglasses"
    else:
        model = random.choice(classic_rayban_models)
        sub_category = "Classic Sunglasses"

    frame_gender = random.choice(genders)

    if frame_gender == "Kid":
        frame_size_options = ["46-180-140", "49-18-140"]
    else:
        frame_size_options = ["49-18-140", "51-18-140", "52-18-145", "54-20-145"]

    frame_size = random.choice(frame_size_options)
    retail_price = random_frame_price(random.choice(frame_materials), category, is_prescription)
    cost_price = round(retail_price * random.uniform(0.35, 0.55), 2)

    return ProductInfo(
        product_m3_code=f"RB-FR-{index:04d}",
        product_name=f"Ray-Ban {model} {'Prescription' if is_prescription else 'Non-prescription'}",
        category=category,
        sub_category=sub_category,
        brand="Ray-Ban",
        sub_brand=model,
        product_type="Prescription" if is_prescription else "Non-prescription",
        lens_type="N/A",
        frame_material=random.choice(frame_materials),
        frame_size=frame_size,
        frame_gender=frame_gender,
        cost_price=cost_price,
        retail_price=retail_price,
        launch_date=random_launch_date(),
        season=random.choice(["Spring/Summer", "AW", "Year-round"]),
        is_discount=0 if random.choice(promos) == "none" else 1
    )

def build_lens_product(index: int) -> ProductInfo:
    lens_brand = random.choice(lens_brands)
    lens_color = random.choice(lens_colors)
    lens_thickness = random.choice(lens_thicknesses)
    lens_type = random.choice(lens_types)
    vision = random.choice(lens_visions)
    
    if index % 3 == 0:
        lens_color = "Clear"
    else:
        lens_color = random.choice([c for c in lens_colors if c != "Clear"])
        
    retail_price = random_lens_price(lens_type, lens_thickness)
    
    return ProductInfo(
        product_m3_code=f"RB-LS-{index:04d}",
        product_name=f"{lens_brand.title()} {lens_type} {vision}",
        category="Lens",
        sub_category=f"{lens_type} Lens",
        brand=lens_brand.title(),
        sub_brand=lens_type,
        product_type="Prescription",
        lens_brand = lens_brand,
        lens_type=lens_type,
        lens_color=lens_color,
        lens_thickness=lens_thickness,
        frame_material="N/A",
        frame_size="N/A",
        cost_price=round(retail_price * random.uniform(0.3, 0.55), 2),
        retail_price=retail_price,
        launch_date=random_launch_date(),
        season=random.choice(["Spring/Summer", "AW", "Year-round"]),
        is_discount=0
    )

def generate_products():
    products = []
    for i in range(1, FRAME_COUNT + 1):
        category = random.choice(["Sunglasses"] * 4 + ["AI Glasses"] * 2 + ["Eyeglasses"] * 4)
        is_prescription = random.choice([True, False])
        products.append(build_frame_product(i, category, is_prescription))

    for i in range(1, LENS_COUNT + 1):
        products.append(build_lens_product(i))
    
    for i in range(1, ACCESSORY_COUNT + 1):
        products.append(
            build_accessory_product(i)
        )


    return products

def seed_product_info(session):
    products = generate_products()
    session.add_all(products)
    session.commit()
    print(f"Inserted {len(products)} products.")

if __name__ == "__main__":
    create_tables_if_not_exist(engine)
    seed_product_info(session)