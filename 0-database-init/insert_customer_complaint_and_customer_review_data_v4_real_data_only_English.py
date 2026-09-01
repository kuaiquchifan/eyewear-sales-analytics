# 优先使用这个文件
import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from faker import Faker
from data_sheet_create_0_1 import CustomerInfo,CustomerReview, CustomerComplaint, Order, session
import os
from langdetect import detect, DetectorFactory
import re

fake = Faker('en_US')
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ====================== Config ======================
REVIEW_COUNT = 50000
COMPLAINT_COUNT = 8000
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 6, 30)

default_status_dist = {
    "Resolved": 0.72,
    "In Progress": 0.15,
    "Unresolved": 0.08,
    "Escalated": 0.05
}

BASE = r"6-NLP"  


DetectorFactory.seed = 0

def is_english(text, min_alpha_ratio=0.6):
    if not isinstance(text, str) or not text.strip():
        return False
    # 优先使用 langdetect（对较长文本更可靠）
    try:
        if len(text) >= 50:
            return detect(text) == "en"
    except Exception:
        pass
    # 回退到字母比率判断（适用于短文本）
    letters = re.findall(r"[A-Za-z]", text)
    tokens = re.findall(r"\w", text)
    if not tokens:
        return False
    return (len(letters) / len(tokens)) >= min_alpha_ratio


def load_real_reviews():
    # 从 notebook 里已经筛选好的 4 个 df（建议 notebook 最后保存成 parquet）
    df_ai = pd.read_parquet(os.path.join(BASE,"Amazon-Fashion-2023-output-parquet" ,"merged_ai_clean.parquet"))          # 或者直接从 notebook 导出
    df_sunglasses = pd.read_parquet(os.path.join(BASE, "Amazon-Fashion-2023-output-parquet", "merged_sunglasses_clean.parquet"))
    df_lens = pd.read_parquet(os.path.join(BASE, "Amazon-Fashion-2023-output-parquet", "merged_lens_clean.parquet"))
    df_eyeglasses = pd.read_parquet(os.path.join(BASE, "Amazon-Fashion-2023-output-parquet", "merged_eyeglasses_clean.parquet"))

    # 统一字段（根据你实际列名调整）
    # 常见 Amazon 字段：rating, title, text, asin, parent_asin, date 等
    def standardize(df, category):
        df = df.copy()
        df["category"] = category
        # 映射列名（按你 notebook 实际列名改）
        rename_map = {
            "title": "review_title",
            "text": "review_text",          # 或 "review"
            "rating": "rating",
            "asin": "asin",                 # 如果有
            "parent_asin": "parent_asin",
            "date": "review_date"           # 或 timestamp
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        # 保证必需列存在
        for col in ["review_title", "review_text", "rating"]:
            if col not in df.columns:
                raise ValueError(f"{category} 缺少列 {col}")
        return df[["category", "review_title", "review_text", "rating"] + 
                  [c for c in ["asin", "parent_asin", "review_date"] if c in df.columns]]

    dfs = [
        standardize(df_ai, "AI Glasses"),
        standardize(df_sunglasses, "Sunglasses"),
        standardize(df_lens, "Lens"),
        standardize(df_eyeglasses, "Eyeglasses"),
    ]

    # 只保留英文 review_text
    real_reviews = pd.concat(dfs, ignore_index=True)
    real_reviews = real_reviews.dropna(subset=["review_text"]).reset_index(drop=True)
    # 如果希望 title 必须也是英文，则使用下面两行；否则只按 review_text 过滤即可
    mask_text = real_reviews["review_text"].apply(is_english)
    mask_title = real_reviews.get("review_title", pd.Series([""]*len(real_reviews))).apply(is_english)
    real_reviews = real_reviews[mask_text & mask_title].reset_index(drop=True)

    return real_reviews


def load_meta_glasses_reviews():
    path = os.path.join(BASE,"meta-smart-glasses-review", "Meta-Glasses-Reviews.parquet")
    df = pd.read_parquet(path)
    # 按实际列名调整（通常是 title / review 或 review_title / review_text）
    df = df.rename(columns={
        "title": "review_title",
        "review": "review_text",
    })
    df["category"] = "AI Glasses"

    df = df.dropna(subset=["review_text"]).reset_index(drop=True)
    mask_text = df["review_text"].apply(is_english)
    mask_title = df.get("review_title", pd.Series([""]*len(df))).apply(is_english)
    df = df[mask_text & mask_title].reset_index(drop=True)
    return df[["category", "review_title", "review_text"] + ([c for c in ["rating"] if c in df.columns])]


def load_real_complaints():
    path = os.path.join(BASE, "hblim-customer-complaints", "customer-complaints-merged.parquet")
    df = pd.read_parquet(path)
    # 按实际列名调整
    df = df.rename(columns={
        "text": "complaint_text",
        "complaint_type": "complaint_type"
    })
    df = df.dropna(subset=["complaint_text"]).reset_index(drop=True)
    return df[["complaint_text", "complaint_type"]]



def weighted_choice(dist):
    return random.choices(list(dist.keys()), weights=list(dist.values()), k=1)[0]


def get_customer_review_stats(review_summary_by_customer, customer_id):
    stats = (review_summary_by_customer or {}).get(customer_id, {})
    count = stats.get("count", 0)
    avg_rating = stats.get("avg_rating", 3.5)
    low_rating_count = stats.get("low_rating_count", 0)
    low_ratio = low_rating_count / max(count, 1)
    return count, avg_rating, low_ratio


# ====================== Build Order Pools ======================
def build_order_pools():
    rows = session.query(
        Order.order_id,
        Order.customer_id,
        Order.order_status,
        Order.delivery_date
    ).all()

    all_order_ids = []
    completed_by_customer = {}
    issue_by_customer = {}
    order_delivery_map = {}

    for order_id, customer_id, order_status, delivery_date in rows:
        all_order_ids.append(order_id)
        order_delivery_map[order_id] = delivery_date

        if order_status == "Completed":
            completed_by_customer.setdefault(customer_id, []).append(order_id)

        if order_status in ("Completed", "Shipped"):
            issue_by_customer.setdefault(customer_id, []).append(order_id)

    return all_order_ids, completed_by_customer, issue_by_customer, order_delivery_map

# ==================== pick valid event date ======================
def pick_valid_event_date(order_id, order_delivery_map, start_date, end_date):
    """
    生成合理的事件日期（评论/投诉日期）
    - 优先在 delivery_date 之后
    - 严格限制在 [start_date, end_date] 内
    - 永远返回 datetime 对象
    """
    delivery_date = order_delivery_map.get(order_id)

    # 1. 没有配送日期 → 直接在全局范围内随机
    if delivery_date is None:
        delta_days = (end_date - start_date).days
        return start_date + timedelta(days=random.randint(0, max(delta_days, 0)))

    # 2. 统一转成 date 方便比较
    if isinstance(delivery_date, datetime):
        min_date = delivery_date.date()
    else:
        min_date = delivery_date

    lower = max(start_date.date(), min_date)
    upper = end_date.date()

    # 3. 如果配送日期已经超过 end_date，强制回落到全局范围
    if lower > upper:
        delta_days = (end_date - start_date).days
        return start_date + timedelta(days=random.randint(0, max(delta_days, 0)))

    # 4. 正常情况：在 [max(start, delivery), end] 之间随机
    random_days = random.randint(0, (upper - lower).days)
    return datetime.combine(lower + timedelta(days=random_days), datetime.min.time())

# ==================== pick order id ======================
def pick_order_id(customer_id, preferred_pool_by_customer, fallback_order_ids=None, allow_fallback=True):
    """
    优先用客户自己的订单，取不到时可选 fallback
    """
    candidate_ids = preferred_pool_by_customer.get(customer_id, [])
    if candidate_ids:
        return random.choice(candidate_ids)
    
    if allow_fallback and fallback_order_ids:
        return random.choice(fallback_order_ids)
    
    return None

def build_customer_type_maps(customer_ids=None, preferred_orders_by_customer=None):
    """
    构建客户类型映射，并返回优先可用的客户ID列表
    :param customer_ids: 候选客户ID列表
    :param preferred_orders_by_customer: 有订单的客户字典（completed 或 issue）
    :return: (customer_type_map, valid_customer_ids)
    """
    # 1. 构建 customer_id → customer_type 映射（排除空值）
    customer_type_map = {
        cid: ctype
        for cid, ctype in session.query(
            CustomerInfo.customer_id,
            CustomerInfo.customer_type
        ).filter(
            CustomerInfo.is_active == True,
            CustomerInfo.customer_type.isnot(None)
        ).all()
    }

    # 2. 优先使用：有类型 + 有对应订单的客户
    preferred_orders_by_customer = preferred_orders_by_customer or {}
    valid_customer_ids = [
        cid for cid in (customer_ids or [])
        if cid in customer_type_map and cid in preferred_orders_by_customer
    ]

    # 3. 兜底：如果有效客户太少，就用所有有类型的客户
    if len(valid_customer_ids) < 50:
        valid_customer_ids = list(customer_type_map.keys())

    return customer_type_map, valid_customer_ids


# ====================== 1. CompetitorInfo ======================

# ====================== 2. CustomerReview (50,000) ======================
def generate_customer_reviews(
        n=50000, customer_ids=None, 
        product_info=None,customer_completed_orders=None,
        all_order_ids=None, order_delivery_map=None,
        real_reviews_df=None,
        meta_ai_reviews_df=None):

    # 不同客户类型对应的评分倾向（核心接入点）
    type_rating_dist = {
        "VIP Loyal Customers": {
            5: 0.55, 4: 0.30, 3: 0.10, 2: 0.03, 1: 0.02
        },
        "Regular Customers": {
            5: 0.38, 4: 0.28, 3: 0.15, 2: 0.10, 1: 0.09
        },
        "Promotional Sensitive Customers": {
            5: 0.30, 4: 0.25, 3: 0.20, 2: 0.15, 1: 0.10
        },
        "Lens Customers": {
            5: 0.42, 4: 0.30, 3: 0.15, 2: 0.08, 1: 0.05
        },
        "One-time Customers": {
            5: 0.22, 4: 0.20, 3: 0.18, 2: 0.20, 1: 0.20
        }
    }

    # 备用分布（仅当客户没有类型时使用）
    fallback_rating_dist = {
        5: 0.38, 4: 0.28, 3: 0.15, 2: 0.10, 1: 0.09
    }

    category_dist = {
        "Eyeglasses": 0.32,
        "Lens": 0.26,
        "Sunglasses": 0.22,
        "AI Glasses": 0.12,
        "Accessory": 0.08
    }

    # English templates - North American style
    positive_titles = [
        "Great quality!", "Very satisfied", "Excellent purchase", "Highly recommend",
        "Perfect fit", "Clear vision", "Worth every penny", "Love these glasses"
    ]
    neutral_titles = [
        "It's okay", "Average experience", "Nothing special", "Decent but not great",
        "As expected", "Fair quality"
    ]
    negative_titles = [
        "Disappointed", "Not recommended", "Poor quality", "Waste of money",
        "Had issues", "Would not buy again"
    ]

    positive_bodies = [
        "The lenses are very clear and the frame feels sturdy. Comfortable for all-day wear.",
        "Really happy with the quality. Vision is sharp and the fit is perfect.",
        "Fast shipping and the glasses look exactly like the photos. Great value.",
        "Prescription is accurate and I had no problem adjusting to them.",
        "Excellent build quality. Already received compliments on the style.",
        "Very comfortable and lightweight. Will definitely purchase again."
    ]
    neutral_bodies = [
        "The glasses are okay for the price. Nothing exceptional but they get the job done.",
        "Average quality. Fit is acceptable and vision is fine, but not amazing.",
        "Received them on time. Performance is as expected, no major complaints.",
        "Decent pair of glasses. Not the best I've owned, but acceptable."
    ]
    negative_bodies = [
        "Lenses came with scratches and the prescription seems slightly off. Very disappointed.",
        "Frame feels cheap and loose after only a few weeks of use.",
        "Had trouble with the fit. Not comfortable for long wear.",
        "Shipping took much longer than expected and customer service was unhelpful.",
        "Quality does not match the price. Would not recommend.",
        "The coating started peeling after a month. Poor durability."
    ]

    # 按 category 分组真实评论，方便快速抽样
    real_by_cat = {}
    if real_reviews_df is not None:
        for cat, group in real_reviews_df.groupby("category"):
            real_by_cat[cat] = group.reset_index(drop=True)

    # AI Glasses 专用池（优先 Meta）
    ai_pool = None
    if meta_ai_reviews_df is not None and len(meta_ai_reviews_df) > 0:
        ai_pool = meta_ai_reviews_df.reset_index(drop=True)
    elif "AI Glasses" in real_by_cat:
        ai_pool = real_by_cat["AI Glasses"]

    reviews = []
    review_summary = {}
    low_rating_orders = []          # 存放 (customer_id, order_id) 的差评订单

    # 预先从数据库构建：customer_id → customer_type 的映射
    customer_type_map, valid_customer_ids = build_customer_type_maps(
        customer_ids=customer_ids,
        preferred_orders_by_customer=customer_completed_orders
    )

    for i in range(n):
        if valid_customer_ids:
            customer_id = random.choice(valid_customer_ids)
        else:
            customer_id = random.choice(customer_ids) if customer_ids else random.randint(1, 160000)

        customer_type = customer_type_map.get(customer_id)

        if customer_type in type_rating_dist:
            rating = weighted_choice(type_rating_dist[customer_type])
        else:
            rating = weighted_choice(fallback_rating_dist)

        category = weighted_choice(category_dist)

        # 4. 获取评论标题和正文（优先真实数据）
        title, body, real_rating = None, None, None
        use_real = False

        if category == "AI Glasses" and ai_pool is not None and len(ai_pool) > 0:
            row = ai_pool.sample(1).iloc[0]
            title = row.get("review_title")
            body = row.get("review_text")
            real_rating = row.get("rating")
            use_real = True
        elif category != "Accessory" and category in real_by_cat and len(real_by_cat[category]) > 0:
            # Accessory 强制走模拟，其他品类优先真实
            row = real_by_cat[category].sample(1).iloc[0]
            title = row.get("review_title")
            body = row.get("review_text")
            real_rating = row.get("rating")
            use_real = True

        # 5. 如果没有真实数据，使用模拟模板
        if not use_real or body is None or (isinstance(body, float) and pd.isna(body)):
            if rating >= 4:
                title = random.choice(positive_titles)
                body = random.choice(positive_bodies)
            elif rating == 3:
                title = random.choice(neutral_titles)
                body = random.choice(neutral_bodies)
            else:
                title = random.choice(negative_titles)
                body = random.choice(negative_bodies)

        # 6. 如果真实数据有 rating，优先使用真实 rating
        if real_rating is not None and not pd.isna(real_rating):
            try:
                rating = int(round(float(real_rating)))
                rating = max(1, min(5, rating))  # 强制限制在 1-5
            except (ValueError, TypeError):
                pass  # 转换失败则保持原来的模拟 rating

        # 7. 如果真实 title 为空，用模拟 title 兜底
        if not title or (isinstance(title, float) and pd.isna(title)):
            if rating >= 4:
                title = random.choice(positive_titles)
            elif rating == 3:
                title = random.choice(neutral_titles)
            else:
                title = random.choice(negative_titles)

        if random.random() < 0.35:
            body += " " + random.choice([
                "Service was friendly.", "Packaging was secure.",
                "Would buy from this brand again.", "Hope they improve quality control."
            ])

        if product_info:
            candidates = [p for p in product_info if p.get("category") == category]
            product_id = random.choice(candidates or product_info)["product_id"]
        else:
            product_id = random.randint(1, 220)

        order_id = pick_order_id(
            customer_id,
            customer_completed_orders or {}
        )

        review_date = pick_valid_event_date(
            order_id, order_delivery_map, start_date, end_date
        )

        summary = review_summary.setdefault(customer_id, {
            "count": 0,
            "sum_rating": 0,
            "low_rating_count": 0
        })
        summary["count"] += 1
        summary["sum_rating"] += rating
        if rating <= 2:
            summary["low_rating_count"] += 1

        # ========== 收集差评订单 ==========
        if rating <= 2 and order_id is not None:
            low_rating_orders.append((customer_id, order_id))
        # ======================================

        reviews.append({
            "review_id": i + 1,
            "customer_id": customer_id,
            "product_id": product_id,
            "order_id": order_id,
            "rating": rating,
            "review_title": title,
            "review_text": body,
            "review_date": review_date.strftime("%Y-%m-%d")
        })

    for customer_id, summary in review_summary.items():
        summary["avg_rating"] = summary["sum_rating"] / max(summary["count"], 1)
        summary["low_ratio"] = summary["low_rating_count"] / max(summary["count"], 1)

    # 修改返回值：多返回 low_rating_orders
    return reviews, review_summary, low_rating_orders

# ====================== 3. CustomerComplaint (8,000) ======================
def generate_customer_complaints(
        n=8000, customer_ids=None, product_info=None,
        issue_orders_by_customer=None, all_order_ids=None,
        order_delivery_map=None, review_summary_by_customer=None,
        low_rating_orders=None,real_complaints_df=None):

    complaint_type_dist = {
        "Incorrect Prescription": 0.22,
        "Frame Broken": 0.18,
        "Lens Scratches": 0.15,
        "Shipping Issue": 0.14,
        "Customer Service": 0.12,
        "Uncomfortable Fit": 0.10,
        "Other": 0.09
    }

    complaint_text_templates = {
        "Incorrect Prescription": [
            "The prescription seems incorrect and my vision is blurry.",
            "The lenses do not match my prescription and I am very disappointed."
        ],
        "Frame Broken": [
            "The frame broke shortly after delivery.",
            "The glasses frame cracked and became unusable."
        ],
        "Lens Scratches": [
            "The lenses have scratches and the quality is poor.",
            "The lens surface is scratched and affects visibility."
        ],
        "Shipping Issue": [
            "The package arrived late and the item was damaged.",
            "Shipping was delayed and the product arrived in poor condition."
        ],
        "Customer Service": [
            "Customer service was unhelpful and did not resolve my issue.",
            "I contacted support but received no proper response."
        ],
        "Uncomfortable Fit": [
            "The glasses are uncomfortable and do not fit well.",
            "The fit is poor and they hurt after wearing them briefly."
        ],
        "Other": [
            "I am unhappy with the product and would like a resolution.",
            "The experience did not meet my expectations."
        ],
    }

    # 不同客户类型的严重程度倾向（让数据更有层次）
    type_severity_dist = {
        "VIP Loyal Customers": {
            "Low": 0.60, "Medium": 0.30, "High": 0.10
        },
        "Regular Customers": {
            "Low": 0.50, "Medium": 0.35, "High": 0.15
        },
        "Promotional Sensitive Customers": {
            "Low": 0.45, "Medium": 0.35, "High": 0.20
        },
        "Lens Customers": {
            "Low": 0.48, "Medium": 0.37, "High": 0.15
        },
        "One-time Customers": {
            "Low": 0.35, "Medium": 0.35, "High": 0.30
        }
    }

    # 兜底严重程度分布
    fallback_severity_dist = {"Low": 0.50, "Medium": 0.35, "High": 0.15}

    status_dist = {
        "Resolved": 0.72,
        "In Progress": 0.15,
        "Unresolved": 0.08,
        "Escalated": 0.05
    }

    category_dist = {
        "Eyeglasses": 0.30,
        "Lens": 0.28,
        "Sunglasses": 0.20,
        "AI Glasses": 0.12,
        "Accessory": 0.10
    }
    # ====================== 真实投诉预处理 ======================
    real_complaint_pool = None
    if real_complaints_df is not None and len(real_complaints_df) > 0:
        real_complaint_pool = real_complaints_df.reset_index(drop=True)

    complaints = []

    customer_type_map, valid_customer_ids = build_customer_type_maps(
        customer_ids=customer_ids,
        preferred_orders_by_customer=issue_orders_by_customer
    )

    customer_pool = valid_customer_ids if valid_customer_ids else (
        customer_ids if customer_ids else list(customer_type_map.keys())
    )

    if not customer_pool:
        customer_pool = list(range(1, 160001))

    review_summary_by_customer = review_summary_by_customer or {}
    low_rating_orders = low_rating_orders or []
    # 把差评订单转成「客户 → 差评订单列表」方便快速取用
    low_orders_by_customer = {}
    for cid, oid in low_rating_orders:
        low_orders_by_customer.setdefault(cid, []).append(oid)

    # ========== 预先计算权重（核心修复） ==========
    precomputed_weights = None
    if review_summary_by_customer:
        precomputed_weights = []
        for cid in customer_pool:
            count, avg_rating, low_ratio = get_customer_review_stats(review_summary_by_customer, cid)

            if count > 0:
                risk = 1.0 + (5.0 - avg_rating) * 1.35 + low_ratio * 2.2
                risk += min(count / 30.0, 1.0) * 0.2
            else:
                risk = 0.45

            precomputed_weights.append(max(risk, 0.05))
    # ==================================================

    for i in range(n):
        # 选客户（使用预计算权重）
        if precomputed_weights is not None:
            customer_id = random.choices(customer_pool, weights=precomputed_weights, k=1)[0]
        else:
            customer_id = random.choice(customer_pool)

        customer_type = customer_type_map.get(customer_id)
        count, avg_rating, low_ratio = get_customer_review_stats(review_summary_by_customer, customer_id)

        if avg_rating <= 2.5 or low_ratio >= 0.35:
            severity_dist = {"Low": 0.18, "Medium": 0.35, "High": 0.47}
            status_dist = {"Resolved": 0.44, "In Progress": 0.18, "Unresolved": 0.22, "Escalated": 0.16}
        elif avg_rating >= 4.2 and low_ratio <= 0.12:
            severity_dist = {"Low": 0.68, "Medium": 0.22, "High": 0.10}
            status_dist = {"Resolved": 0.82, "In Progress": 0.10, "Unresolved": 0.05, "Escalated": 0.03}
        elif customer_type in type_severity_dist:
            severity_dist = type_severity_dist[customer_type]
            status_dist = default_status_dist
        else:
            severity_dist = fallback_severity_dist
            status_dist = default_status_dist

        severity = weighted_choice(severity_dist)
        status = weighted_choice(status_dist)
        category = weighted_choice(category_dist)

        # 3. 获取投诉类型和文本（优先真实数据）
        if real_complaint_pool is not None and len(real_complaint_pool) > 0:
            row = real_complaint_pool.sample(1).iloc[0]
            # 优先使用真实数据的 complaint_type，没有则随机
            ctype = row.get("complaint_type") or row.get("label") or weighted_choice(complaint_type_dist)
            complaint_text = row.get("complaint_text") or row.get("text")
            
            # 如果真实文本为空，回退到模拟
            if complaint_text is None or (isinstance(complaint_text, float) and pd.isna(complaint_text)):
                ctype = weighted_choice(complaint_type_dist)
                complaint_text = random.choice(
                    complaint_text_templates.get(ctype, complaint_text_templates["Other"])
                )
        else:
            # 完全没有真实数据时使用模拟
            ctype = weighted_choice(complaint_type_dist)
            complaint_text = random.choice(
                complaint_text_templates.get(ctype, complaint_text_templates["Other"])
            )

        if product_info:
            candidates = [p for p in product_info if p.get("category") == category]
            product_id = random.choice(candidates or product_info)["product_id"]
        else:
            product_id = random.randint(1, 220)

        # ========== 核心：优先绑定差评订单 ==========
        order_id = None

        # 1. 最高优先级：该客户自己的差评订单（强关联）
        if customer_id in low_orders_by_customer and random.random() < 0.65:
            order_id = random.choice(low_orders_by_customer[customer_id])

        # 2. 其次：该客户自己的 issue 订单
        if order_id is None:
            order_id = pick_order_id(
                customer_id,
                issue_orders_by_customer or {}
            )

        # 3. 最后兜底：全局随机订单（大幅减少 None）
        if order_id is None and all_order_ids:
            order_id = random.choice(all_order_ids)
        # ==========================================

        complaint_date = pick_valid_event_date(
            order_id, order_delivery_map, start_date, end_date
        )

        if severity == "Low":
            resolve_days = random.randint(2, 8)
        elif severity == "Medium":
            resolve_days = random.randint(7, 18)
        else:
            resolve_days = random.randint(12, 35)

        resolution_date = None
        if status in ["Resolved", "Escalated"]:
            resolution_date = (complaint_date + timedelta(days=resolve_days)).strftime("%Y-%m-%d")

        complaints.append({
            "complaint_id": i + 1,
            "customer_id": customer_id,
            "product_id": product_id,
            "order_id": order_id,
            "complaint_type": ctype,
            "complaint_text": complaint_text,
            "complaint_date": complaint_date.strftime("%Y-%m-%d"),
            "complaint_severity": severity,
            "resolution_status": status,
            "resolution_date": resolution_date
        })

    return complaints


# ====================== Save to CSV ======================
def save_to_csv(data, filename):
    if not data:
        return
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"Saved: {filename} ({len(data)} rows)")

# ===================== Save to Database ======================
def save_to_db(data,Model):
    if not data:
        return
    df = pd.DataFrame(data)
    records = df.to_dict(orient="records")
    session.bulk_insert_mappings(Model,records)
    session.commit()
    print(f"PostgreSQL inserted: {len(records)} rows")



# ===================== Main Execution ======================
if __name__ == "__main__":
    print("Generating English simulation data for North American market...")

    print("Loading real review & complaint data...")
    real_reviews = load_real_reviews()
    meta_ai = load_meta_glasses_reviews()
    real_complaints = load_real_complaints()

    print(f"Real reviews: {len(real_reviews)}")
    print(f"Meta AI reviews: {len(meta_ai)}")
    print(f"Real complaints: {len(real_complaints)}")

    customer_ids = [
        customer_id
        for (customer_id,) in session.query(CustomerInfo.customer_id).filter(CustomerInfo.is_active == True).all()
    ]

    # fetch product_info from the database
    category_specs = [
        ("AI Glasses", 42),
        ("Eyeglasses", 65),
        ("Lens", 40),
        ("Sunglasses", 53),
        ("Accessory", 20),
    ]

    product_info = []
    current_id = 1
    for category, count in category_specs:
        for _ in range(count):
            product_info.append({"product_id": current_id, "category": category})
            current_id += 1

    all_order_ids, completed_by_customer, issue_by_customer, order_delivery_map = build_order_pools()

    reviews, review_summary, low_rating_orders = generate_customer_reviews(
        REVIEW_COUNT, customer_ids, product_info,
        completed_by_customer,
        all_order_ids,
        order_delivery_map,
        real_reviews_df=real_reviews,          
        meta_ai_reviews_df=meta_ai            
    )
    save_to_csv(reviews, "CustomerReview_sim.csv")
    save_to_db(reviews, CustomerReview)
    print("Customer reviews inserted into database.")

    complaints = generate_customer_complaints(
        COMPLAINT_COUNT, customer_ids, product_info,
        issue_by_customer,
        all_order_ids,
        order_delivery_map,
        review_summary_by_customer=review_summary,
        low_rating_orders=low_rating_orders,
        real_complaints_df=real_complaints  
    )
    save_to_csv(complaints, "CustomerComplaint_sim.csv")
    save_to_db(complaints, CustomerComplaint)
    print("Customer complaints inserted into database.")

    print("All done!")