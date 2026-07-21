import pandas as pd
import numpy as np
from faker import Faker
from sdv.metadata import Metadata
from sdv.single_table import GaussianCopulaSynthesizer
from datetime import datetime, timedelta,date
from data_sheet_create_0_1 import CustomerInfo, session
import random, os,re
import pycountry
import geonamescache

random.seed(43)

CUSTOMER_LOCATION_WEIGHTS = {
    "California": {
        "Los Angeles":0.35,
        "San Diego":0.20,
        "Santa Clara":0.15,
        "Newport Beach":0.10,
        "Malibu":0.05,
        "Brea":0.05,
        "La Jolla":0.05,
        "Northridge":0.03,
        "Other":0.17
    },
    "New York":{
        "New York":0.60,
        "Buffalo":0.10,
        "Garden City":0.10,
        "Other":0.20
    },
    "Florida":{
        "Miami":0.35,
        "Orlando":0.20,
        "Tampa":0.15,
        "Jacksonville":0.10,
        "Other":0.20
    },
    "Texas":{
        "Houston":0.35,
        "San Antonio":0.20,
        "Other":0.45
    },
    "Illinois":{
        "Chicago":0.60,
        "Oak Brook":0.20,
        "Other":0.20
    },
    "Massachusetts":{
        "Boston":0.60,
        "Other":0.40
    },
    "Washington":{
        "Bellevue":0.50,
        "Other":0.50
    }
}



REGION_WEIGHTS = {
    "California":0.25,
    "New York":0.15,
    "Florida":0.12,
    "Texas":0.10,
    "Illinois":0.08,
    "Massachusetts":0.05,
    "Washington":0.05,
    "Georgia":0.04,
    "Nevada":0.04,
    "Colorado":0.03,
    "Hawaii":0.02,
    "New Jersey":0.02,
    "Ohio":0.02,
    "Tennessee":0.02,
    "North Carolina":0.01,
    "District of Columbia":0.01
}


COUNTRY_LOCALE = {
    'US': 'en_US',
    'CA': 'en_CA',
    'MX': 'es_MX',
    # 继续补充你需要的国家
}

fake_us = Faker('en_US')

def get_name_by_country(country_code, gender=None):
    if gender == 'Male':
        return fake_us.name_male()
    elif gender == 'Female':
        return fake_us.name_female()
    else:
        return fake_us.name()

# 生成客户所在的州和城市
def generate_customer_location():
    regions=list(REGION_WEIGHTS.keys())
    region=random.choices(regions, weights=list(REGION_WEIGHTS.values()), k=1)[0]
    cities=CUSTOMER_LOCATION_WEIGHTS.get(region,{"Other":1})
    city=random.choices(list(cities.keys()), weights=list(cities.values()), k=1)[0]

    return region,city



# 自定义业务区域映射
BUSINESS_REGIONS = {
    'North America': {'US', 'CA', 'MX'},
}

def get_country_region_city():
    gc = geonamescache.GeonamesCache()
    countries = list(pycountry.countries)
    region_country_city = {region: {} for region in BUSINESS_REGIONS.keys()}

    for country in countries:
        try:
            alpha_2 = country.alpha_2
            for region, country_codes in BUSINESS_REGIONS.items():
                if alpha_2 in country_codes:
                    # 按人口降序排序，取前5个最大城市
                    cities_data = [
                        city for city in gc.get_cities().values()
                        if city['countrycode'] == alpha_2
                    ]
                    cities_data.sort(key=lambda x: x.get('population', 0), reverse=True)
                    cities = [city['name'] for city in cities_data[:5]]
                    if cities:
                        region_country_city[region][country.name] = cities
        except Exception:
            continue
    return region_country_city

region_country_city = get_country_region_city()



# ====================== 第一阶段：生成 Customer ======================
def generate_customer_features(n):
    data = []
    region_list = ['North America']
    print("Region List:", region_list)
    # region_weights = [1]
    end_date = date(2024, 12, 1)
    start_date = date(end_date.year - 10, end_date.month, end_date.day)
    for i in range(n):
        region, city = generate_customer_location()
        birth_date = fake_us.date_of_birth(minimum_age=18, maximum_age=65)
        age = datetime.today().year - birth_date.year - (
            (datetime.today().month, datetime.today().day) < (birth_date.month, birth_date.day)
        )

        registration_date = fake_us.date_between(start_date=start_date, end_date=end_date)

        data.append({
            'customer_m3_code': f"CUST-{10000 + i}",
            'customer_name': get_name_by_country('US'),
            'gender': random.choice(['Male', 'Female']),
            'age': age,
            'birth_date': birth_date,
            'region': region,
            'country': "United States",
            'registration_date': registration_date,
            'city': city,
            'is_active': 1
        })
    return pd.DataFrame(data)


# ====================== DataFrame转ORM对象 ======================
def df_to_customer_dict(df):
    customers = []

    for row in df.itertuples(index=False):
        customers.append({
            "customer_m3_code": row.customer_m3_code,
            "customer_name": row.customer_name,
            "gender": row.gender,
            "age": int(row.age),
            "region": row.region,
            "country": row.country,
            "city": row.city,
            "birth_date": row.birth_date,
            "registration_date": row.registration_date,
            "preferred_store_id": None,
            "is_active": int(row.is_active)
        })

    return customers

# ====================== 数据验证 ======================
def validate_customer(df):
    df = df.copy()

    df['birth_date'] = pd.to_datetime(df['birth_date']).dt.date
    df['registration_date'] = pd.to_datetime(df['registration_date']).dt.date
    # df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date']).dt.date

    if (df['age'] < 18).any():
        raise Exception("age < 18 found")
    if (df['age'] > 65).any():
        raise Exception("age > 65 found")

    print("PASS")
    return True


# ====================== 主流程 ======================
def insert_sample_data():
    # 1. 生成DataFrame
    features_df = generate_customer_features(160000) # 增加到16万个客户
    # 2. 数据验证
    validate_customer(features_df)
    # 3. 转为ORM对象并批量插入
    customers = df_to_customer_dict(features_df)
    batch_size = 10000
    for i in range(0, len(customers), batch_size):
        batch = customers[i:i + batch_size]
        session.bulk_insert_mappings(CustomerInfo, batch)
        session.commit()
        
    print(f"Inserted {len(customers)} customers with SDV-enhanced realism.")

if __name__ == "__main__":
    insert_sample_data()