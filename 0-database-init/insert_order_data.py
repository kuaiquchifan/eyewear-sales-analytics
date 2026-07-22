import random
from datetime import datetime, timedelta
from decimal import Decimal
from data_sheet_create_0_1 import Order, OrderItem, ProductInfo, CustomerInfo, session,StoreInfo

random.seed(2026)

QUARTER_PROFILES = [
    {"year": 2023, "q": 1, "weight": 0.11, "ai_share": 0.10, "promo": 0.27, "backlog_days": 1},
    {"year": 2023, "q": 2, "weight": 0.10, "ai_share": 0.12, "promo": 0.25, "backlog_days": 1},
    {"year": 2023, "q": 3, "weight": 0.14, "ai_share": 0.18, "promo": 0.28, "backlog_days": 2},
    {"year": 2023, "q": 4, "weight": 0.20, "ai_share": 0.35, "promo": 0.40, "backlog_days": 3},
    {"year": 2024, "q": 1, "weight": 0.08, "ai_share": 0.30, "promo": 0.33, "backlog_days": 2},
    {"year": 2024, "q": 2, "weight": 0.12, "ai_share": 0.45, "promo": 0.35, "backlog_days": 5},
    {"year": 2024, "q": 3, "weight": 0.10, "ai_share": 0.40, "promo": 0.32, "backlog_days": 3},
    {"year": 2024, "q": 4, "weight": 0.15, "ai_share": 0.50, "promo": 0.42, "backlog_days": 4},
]

ORDER_STATUSES = ["Completed", "Shipped", "Pending", "Cancelled"]
UNITS = ["pair"]

def load_all_stores():
    return session.query(StoreInfo).all()


# 计算门店权重的函数，考虑门店类型、州/区域权重和热门商业地点
def calculate_store_weight(store):

    weight = 1.0
    # ===========================
    # 1. 店铺类型
    # ===========================
    if store.store_type == "Ray-Ban Store":
        weight *= 1.5
    elif store.store_type == "Multi-brand Retail":
        weight *= 1.0

    # ===========================
    # 2. 州/区域权重
    # ===========================
    region_weights = {
        "California": 2.5,
        "New York": 2.0,
        "Florida": 1.8,
        "Texas": 1.6,
        "Illinois": 1.5,
        "Massachusetts": 1.3,
        "Washington": 1.3,

        "Nevada": 1.2,
        "Georgia": 1.1,

        "Colorado": 1.0,
        "Hawaii": 0.8,
        "New Jersey": 0.8,
        "Ohio": 0.7,
        "Tennessee": 0.7,
        "North Carolina": 0.7,
        "District of Columbia": 0.7
    }

    weight *= region_weights.get(store.store_region,1.0)

    # ===========================
    # 3. 热门商业地点
    # ===========================
    premium_locations = {
        # California
        "The Grove": 2.0,
        "The Americana": 1.8,
        "Abbot Kinney": 1.7,
        "Malibu": 1.6,
        "Newport Beach": 1.6,

        # New York
        "House New York": 2.0,
        "Hudson Yards": 1.8,
        "Soho": 1.8,
        "New York": 1.8,

        # Florida
        "Lincoln Road": 1.8,
        "Wynwood": 1.6,
        "Aventura": 1.5,

        # Texas
        "NorthPark Center": 1.6,
        "Domain Northside": 1.5,

        # Illinois
        "Chicago": 1.8,

        # Nevada
        "Las Vegas": 1.5
    }

    weight *= premium_locations.get(store.store_city,1.0)
    return weight

# 客户选择门店的逻辑：同城市的门店权重最高，同州的次之，其他州的最低
def weighted_choice(store_list):
    weights = [calculate_store_weight(s) for s in store_list]
    return random.choices(store_list, weights=weights, k=1)[0]

def choose_customer_store(customer, stores):
    same_city = [s for s in stores if s.store_city == customer.city]
    same_state = [s for s in stores if s.store_region == customer.region]
    other_state = [s for s in stores if s.store_region != customer.region]
    r=random.random()
    # 60% 同城市
    if same_city and r < 0.55:
        return weighted_choice(same_city)
    # 30% 同州
    elif same_state and r < 0.80:
        return weighted_choice(same_state)
    # 10% 跨州
    else:
        return weighted_choice(other_state)

def build_promotion_cache(promotions):
    cache = {}
    for profile in QUARTER_PROFILES:
        key = (profile["year"], profile["q"])
        start,end = quarter_range(profile["year"], profile["q"])

        cache[key] = [
            p for p in promotions
            if (p.start_date is None or p.start_date <= end.date())
            and (p.end_date is None or p.end_date >= start.date())
        ]

    return cache

# 新增：加载促销活动
def load_all_promotions():
    from data_sheet_create_0_1 import PromotionActivity
    return session.query(PromotionActivity).all()

def quarter_range(year, q):
    start_month = {1:1,2:4,3:7,4:10}[q]
    end_month = {1:3,2:6,3:9,4:12}[q]
    start = datetime(year, start_month, 1, 8, 0, 0)
    end = datetime(year, end_month, 28, 23, 59, 59)
    return start, end

def random_date(start, end):
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)

def choose_product(product_groups, ai_share):
    if random.random() < ai_share:
        candidates = [p for p in product_groups["AI Glasses"]]
    else:
        r = random.random()
        if r < 0.40:
            candidates = [p for p in product_groups["Sunglasses"]]
        elif r < 0.80:
            candidates = [p for p in product_groups["Eyeglasses"]]
        else:
            candidates = [p for p in product_groups["Lens"]]
    return random.choice(candidates)




def build_order_item(product, base_discount_rate=Decimal("1.00"), is_gift=False):
    unit_price = Decimal(product.retail_price)
    quantity = 1 if random.random() < 0.92 else random.choice([2, 3])
    # discount_rate 表示乘数，例如 0.80 表示八折
    discount_rate = Decimal(base_discount_rate).quantize(Decimal("0.01"))
    subtotal = (unit_price * Decimal(quantity) * discount_rate).quantize(Decimal("0.01"))

    return OrderItem(
        product_id=product.product_id,
        product_m3_code=product.product_m3_code,
        quantity=quantity,
        unit=random.choice(UNITS),
        unit_price=unit_price,
        discount_rate=discount_rate,
        line_price_before_tax=subtotal,
        line_price_after_tax=subtotal,
        product_name=product.product_name,
        is_free_gift = bool(is_gift),
    )

# 新增：函数
def apply_fixed_discount_to_items(items, fixed_amount_off):

    if fixed_amount_off <= 0:
        return items

    total_amount = sum(
        item.line_price_before_tax
        for item in items
    )

    if total_amount <= 0:
        return items


    for item in items:

        # 当前商品承担的折扣
        item_discount = (
            fixed_amount_off *
            item.line_price_before_tax /
            total_amount
        ).quantize(
            Decimal("0.01")
        )

        # 修改商品价格
        new_price = (
            item.line_price_before_tax -
            item_discount
        )

        if new_price < 0:
            new_price = Decimal("0.00")


        item.line_price_before_tax = new_price

        item.discount_rate = (
            new_price /
            (item.unit_price * item.quantity)
        ).quantize(
            Decimal("0.01")
        )

        tax_amount = (
            new_price *
            Decimal("0.095")
        ).quantize(
            Decimal("0.01")
        )

        item.line_price_after_tax = (
            new_price + tax_amount
        )

    return items




def build_order(profile, customer, store, items, order_date, seq, promotion=None, fixed_amount_off=Decimal("0.00"), total_price_before_discount_and_tax=Decimal("0.00")):
    # 1. items 已包含折后行价与 is_free_gift
    total_before_tax = sum(item.line_price_before_tax for item in items)
    
    # 2. 处理固定金额优惠
    if fixed_amount_off and fixed_amount_off > 0:
        fixed_amount_off = Decimal(fixed_amount_off)
        total_before_tax = max(total_before_tax - fixed_amount_off, Decimal("0.00"))

    # 3. 【关键】在这里统一计算一次税
    total_tax = (total_before_tax * Decimal("0.095")).quantize(Decimal("0.01"))

    shipping_fee = Decimal(0 if random.random() < 0.72 else random.choice([10.00, 15.00, 20.00]))
    total_price_before_tax = (total_before_tax + shipping_fee).quantize(Decimal("0.01"))
    total_price_after_tax = (total_before_tax + shipping_fee + total_tax).quantize(Decimal("0.01"))

    tax_rate = Decimal("0.095")
    for item in items:
        if item.line_price_before_tax > 0:                     # 赠品跳过
            item_tax = (item.line_price_before_tax * tax_rate).quantize(Decimal("0.01"))
            item.line_price_after_tax = item.line_price_before_tax + item_tax

    approval_delay = random.randint(0, profile["backlog_days"])
    delivery_delay = random.randint(2, 10)

    approval_date = order_date + timedelta(days=approval_delay)
    delivery_date = approval_date + timedelta(days=delivery_delay)
    status = random.choices(
        ORDER_STATUSES,
        weights=[0.72, 0.18, 0.08, 0.02] if profile["year"] != 2023 or profile["q"] != 1 else [0.60, 0.20, 0.10, 0.10],
        k=1
    )[0]

    return Order(
        customer_id=customer.customer_id,
        order_m3_code=f"RBORD{profile['year']}{profile['q']:01d}{seq:06d}",
        order_date=order_date,
        approval_date=approval_date,
        delivery_date=delivery_date,
        order_status=status,
        shipping_fee=shipping_fee,
        tax_amount=total_tax,
        total_price_before_discount_and_tax=total_price_before_discount_and_tax,
        total_price_before_tax=total_price_before_tax,
        total_price_after_tax=total_price_after_tax,
        store_id=store.store_id,
        is_shipping_free = shipping_fee == 0,
        is_reward_points = random.random() < 0.28,
        is_insurance = random.random() < 0.06,
        campaign_id = promotion.campaign_id if promotion is not None else None,
        items=items
    )


def build_order_items_without_discount(product_groups, ai_share):
    line_count = 1 if random.random() < 0.70 else random.choice([2,3])
    items = []
    chosen_ids = set()

    while len(items) < line_count:
        product = choose_product(product_groups,ai_share)
        if product.product_id in chosen_ids:
            continue
        
        chosen_ids.add(product.product_id)
        item = build_order_item(product,base_discount_rate=Decimal("1.00"),is_gift=False)
        items.append(item)
    return items



# 新增：促销应用函数
def apply_promotion_to_items(items, promotion,gift_products):
    if promotion is None:
        return items

    dtype = (promotion.discount_type or "").lower()

    # Percentage
    if "percentage" in dtype:
        discount_percent = Decimal(promotion.discount_value)
        discount_rate = (Decimal("1.00")-discount_percent)

        for item in items:
            old_price = (item.unit_price *item.quantity)
            new_price = (old_price *discount_rate).quantize(Decimal("0.01"))
            item.line_price_before_tax = new_price
            item.discount_rate = (new_price / old_price).quantize(Decimal("0.01"))

            tax = (new_price *Decimal("0.095")).quantize(Decimal("0.01"))
            item.line_price_after_tax = (new_price + tax)

    # Fixed Amount
    elif "fixed amount" in dtype:
        fixed_amount = Decimal(promotion.discount_value)
        apply_fixed_discount_to_items(items,fixed_amount)

    # Free Gift
    elif "free gift" in dtype:

        # 从ProductInfo中寻找赠品
        if gift_products:
            gift_product = random.choice(gift_products)
            gift_item = OrderItem(
                product_id=gift_product.product_id,
                product_m3_code=gift_product.product_m3_code,
                quantity=1,
                unit="piece",
                # 保留赠品原价
                unit_price=Decimal(gift_product.retail_price),
                # 免费赠送
                discount_rate=Decimal("0.00"),
                line_price_before_tax=Decimal("0.00"),
                line_price_after_tax=Decimal("0.00"),
                product_name=gift_product.product_name,
                is_free_gift=True
            )

            items.append(gift_item)


    # BOGO
    elif "buy one get one" in dtype:
        buy_item = random.choice(items)

        gift_item = OrderItem(
            product_id=buy_item.product_id,
            product_m3_code=buy_item.product_m3_code,
            quantity=1,
            unit=buy_item.unit,
            unit_price=buy_item.unit_price,
            discount_rate=Decimal("0.00"),
            line_price_before_tax=Decimal("0.00"),
            line_price_after_tax=Decimal("0.00"),
            product_name=buy_item.product_name,
            is_free_gift=True
        )

        items.append(gift_item)
    return items

def load_all_customers():
    return session.query(CustomerInfo).all()

def load_all_products():
    return session.query(ProductInfo).all()

# 修改 simulate_orders：加载 promotions，并在每笔订单上随机决定是否应用某个促销（且仅应用在活动有效期内）
def simulate_orders(total, batch_size):
    customers = load_all_customers()
    products = load_all_products()
    promotions = load_all_promotions()
    promotion_cache = build_promotion_cache(promotions)
    print(f"Loaded {len(promotions)} promotions.")
    stores = load_all_stores()
    if not customers or not products or not stores:
        raise RuntimeError(
            "请先插入 CustomerInfo、ProductInfo 和 StoreInfo 数据。"
        )
    # ===============================
    # 产品分类缓存（新增）
    # ===============================
    product_groups = {
        "AI Glasses": [],
        "Sunglasses": [],
        "Eyeglasses": [],
        "Lens": [],
        "Accessory": []
    }

    for p in products:
        if p.category in product_groups:
            product_groups[p.category].append(p)


    # Free Gift缓存（新增）
    gift_products = [
        p for p in products
        if p.category == "Accessory"
        and p.sub_category == "Free Gift"
    ]


    if not customers or not products:
        raise RuntimeError(
            "请先插入 CustomerInfo 和 ProductInfo 数据。"
        )

    seq = 1
    all_orders = []
    # 新增：为每个门店生成一个权重，用于模拟不同门店的订单量差异
    store_weights = [
        calculate_store_weight(s)
        for s in stores
    ]
    for profile in QUARTER_PROFILES:
        count = int(total * profile["weight"])
        start, end = quarter_range(profile["year"], profile["q"])
        for _ in range(count):
            customer = random.choice(customers)
            # store = random.choices(stores,weights=store_weights,k=1)[0]
            store = choose_customer_store(customer, stores)
            order_date = random_date(start, end)

            # 1. 首先,生成原价items
            items = build_order_items_without_discount(product_groups,profile["ai_share"])
            
            # 选择是否应用促销：在可选的 promotions 中挑选一个活动（且活动要覆盖这个 order_date）
            # 2. 找日期有效promotion
            applicable = promotion_cache[(profile["year"], profile["q"])]
           
            # 3. 计算原始金额
            original_total = sum(item.quantity * item.unit_price for item in items)

            # 4. 过滤Fixed Amount门槛
            valid_promotions = []
            for p in applicable:
                if (p.min_purchase_amount and original_total < Decimal(p.min_purchase_amount)):
                    continue
                valid_promotions.append(p)

            # 5. 随机选择promotion
            # 调试：显示当前订单时间和匹配到的促销
            promotion = None
            # 40% 的订单会被促销影响（可调整）
            promo_prob = profile.get("promo", 0.40)

            if (valid_promotions and random.random() < promo_prob):
                promotion = random.choice(valid_promotions)

            # 6. 应用promotion
            if promotion:
                items = apply_promotion_to_items(items,promotion,gift_products)

            # 7. 创建Order
            order = build_order(profile, customer, store, items, order_date, seq, promotion=promotion, fixed_amount_off=Decimal("0.00"),total_price_before_discount_and_tax=original_total)
            
            all_orders.append(order)
            seq += 1

            if len(all_orders) >= batch_size:
                session.add_all(all_orders)
                session.commit()
                all_orders.clear()

    if all_orders:
        session.add_all(all_orders)
        session.commit()
        
if __name__ == "__main__":
    simulate_orders(500000, 10000)  # 订单数量为500000，批量提交大小为10000