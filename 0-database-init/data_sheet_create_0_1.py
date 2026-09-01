from sqlalchemy import (
    create_engine, Column, Integer, String, Float,Text, Date, Numeric, ForeignKey, TIMESTAMP,inspect,CheckConstraint, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker,relationship

# 创建基础类
Base = declarative_base()

# 定义 CustomerInfo 表
class CustomerInfo(Base):
    __tablename__ = 'CustomerInfo'
    customer_id = Column(Integer, primary_key=True, autoincrement=True, comment="客户ID")
    customer_m3_code = Column(String(50), unique=True, nullable=False, comment="客户的唯一m3身份编码")
    customer_name = Column(String(100), comment="客户名称")
    gender = Column(String(10), comment="性别")
    age = Column(Integer, comment="年龄")
    birth_date = Column(Date, comment="出生日期")                    
    region = Column(String(50), comment="地区")
    country = Column(String(50), comment="国家")                
    city = Column(String(50), comment="城市")                  
    registration_date = Column(Date, comment="注册时间")
    last_purchase_date = Column(Date, comment="最后购买时间")            
    total_orders = Column(Integer, default=0, comment="累计订单数")    
    total_spend = Column(Numeric(12, 2), default=0, comment="累计消费")  
    customer_type = Column(String(50), comment="客户类型（B2B/B2C/Professional）")
    customer_hierarchy = Column(String(20), comment="客户层级（T1、T2、T3）")
    channel_source = Column(String(20), comment="渠道来源（广告、自然、线下等）")
    preferred_store_id = Column(Integer, ForeignKey('StoreInfo.store_id'), comment="关联门店")         
    is_active = Column(Boolean, default=True, comment="是否活跃客户")   
    preferred_store = relationship("StoreInfo")
    
    

# 定义 ProductInfo 表
class ProductInfo(Base):
    __tablename__ = 'ProductInfo'
    product_id = Column(Integer, primary_key=True, autoincrement=True, comment="商品ID")
    product_m3_code = Column(String(50), unique=True, nullable=False, comment="商品的唯一erp-m3编码") 
    product_name = Column(String(100), comment="商品名称")
    category = Column(String(50), comment="类目（如Frame / Lens / Sunglass / Contact / Accessory）")
    sub_category = Column(String(50), comment="子类目（如渐进镜片、单光镜片、偏光太阳镜等）")  
    brand = Column(String(50), comment="品牌")  # Ray-Ban,Essilor 等
    sub_brand = Column(String(50), comment="子品牌")
    product_type = Column(String(20), comment="产品类型（Prescription / Non-prescription）")  
    lens_brand = Column(String(20),comment="镜片品牌（Essilor, Ray-Ban 等）")  
    lens_color = Column(String(20),comment="镜片颜色（Clear, Blue 等）") 
    lens_type = Column(String(50), comment="镜片类型（Single Vision, Progressive, Blue Light, Photochromic...）")               
    lens_thickness = Column(String(10),comment="镜片厚度（1.5, 1.56, 1.61, 1.67, 1.74 等）")              
    frame_gender = Column(String(10),comment="镜架性别（Men / Women / Unisex）")
    frame_material = Column(String(30), comment="镜架材质（Acetate, Titanium, TR90, Metal...）")          
    frame_size = Column(String(20), comment="镜架尺寸（50-20-140 等）")              
    cost_price = Column(Numeric(10, 2), comment="成本价")
    retail_price = Column(Numeric(10, 2), comment="建议零售价")
    launch_date = Column(Date, comment="上市时间")
    season = Column(String(20), comment="季节（Spring/Summer/AW/Year-round）")                  
    is_discount = Column(Boolean, default=False, nullable=False, comment="是否参与促销活动，True为是，False为否")
    

# 定义 Order 表
class Order(Base):
    __tablename__ = 'Order'
    order_id = Column(Integer, primary_key=True, autoincrement=True, comment="订单ID")
    customer_id = Column(Integer, ForeignKey('CustomerInfo.customer_id'), comment="客户ID")
    order_m3_code = Column(String(50), unique=True, nullable=False, comment="订单的唯一erp-m3编码")
    order_date = Column(TIMESTAMP, comment="下单时间")
    approval_date = Column(TIMESTAMP, comment="审批时间")
    delivery_date = Column(TIMESTAMP, comment="发货时间")
    order_status = Column(String(20), comment="订单状态（待审批、已审批、已发货、已完成、已取消）")
    shipping_fee = Column(Numeric(10, 2), comment="运费")
    tax_amount = Column(Numeric(10, 2), comment="税费")
    total_price_before_discount_and_tax = Column(Numeric(10, 2), comment="折扣前和税前总价")
    total_price_before_tax = Column(Numeric(10, 2), comment="税前总价")
    total_price_after_tax = Column(Numeric(10, 2), comment="税后总价")
    is_shipping_free = Column(Boolean, default=False, nullable=False, comment="是否包邮，True为是，False为否")
    is_reward_points = Column(Boolean, default=False, nullable=False, comment="是否有积分奖励，True为是，False为否")
    is_insurance = Column(Boolean, default=False, nullable=False, comment="是否有保险，True为是，False为否")
    store_id = Column(Integer,ForeignKey('StoreInfo.store_id'), nullable=False,comment="下单门店ID")

    campaign_id = Column(Integer,ForeignKey("PromotionActivity.campaign_id"),nullable=True)
    campaign = relationship("PromotionActivity")
    # 关系映射
    customer = relationship("CustomerInfo")
    store = relationship("StoreInfo")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
class OrderItem(Base):
    __tablename__ = 'OrderItem'
    order_item_id = Column(Integer, primary_key=True, autoincrement=True, comment="订单明细ID")
    order_id = Column(Integer, ForeignKey('Order.order_id'), comment="订单ID")
    product_id = Column(Integer, ForeignKey('ProductInfo.product_id'), comment="商品ID")
    product_m3_code = Column(String(50), comment="商品的唯一erp-m3编码")
    product_name = Column(String(100), comment="商品名称")
    quantity = Column(Integer, comment="数量")
    unit = Column(String(20), comment="商品单位")
    unit_price = Column(Numeric(10, 2), comment="单价")
    line_price_before_tax = Column(Numeric(10, 2), comment="行税前总价")
    line_price_after_tax = Column(Numeric(10, 2), comment="行税后总价")
    discount_rate = Column(Numeric(5, 2), comment="折扣率")
    is_free_gift = Column(Boolean, default=False, nullable=False, comment="是否有赠品，True为是，False为否")
    order = relationship("Order", back_populates="items")
    product = relationship("ProductInfo")


# 定义 PromotionActivity 表
class PromotionActivity(Base):
    __tablename__ = 'PromotionActivity'
    campaign_id = Column(Integer, primary_key=True, autoincrement=True, comment="活动ID")
    campaign_type = Column(String(50), comment="活动类型（Holiday、Seasonal、Member）")
    campaign_name = Column(String(100), nullable=False, comment="活动名称")
    target_audience = Column(String(100), comment="覆盖人群（标签）,如：All customers、couples、Young customers、VIP客户等")
    region = Column(String(50), comment="促销活动的地区信息") 
    start_date = Column(Date, comment="活动开始时间")
    end_date = Column(Date, comment="活动结束时间")       
    discount_type = Column(String(30),comment="折扣类型（Percentage, Fixed Amount, Buy One Get One, Free Gift）")
    discount_value = Column(Numeric(10,2),comment="折扣值（如20%折扣、固定金额折扣等）")
    min_purchase_amount = Column(Float, comment="最低购买金额")
    expected_sales_lift = Column(Float, comment="预期销售提升")
    status = Column(String(20), default="active", comment="活动状态")
    

class CustomerReview(Base):
    __tablename__ = 'CustomerReview'
    review_id = Column(Integer, primary_key=True, autoincrement=True, comment="评论ID")
    customer_id = Column(Integer, ForeignKey('CustomerInfo.customer_id'), comment="客户ID")
    product_id = Column(Integer, ForeignKey('ProductInfo.product_id'), comment="商品ID")
    order_id = Column(Integer, ForeignKey('Order.order_id'), nullable=True, comment="关联订单ID（可为空）")
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False, comment="评分（1-5）")
    review_title = Column(Text, comment="评论标题")
    review_text = Column(Text, comment="评论内容")
    review_date = Column(Date, comment="评论时间")

    # 关系映射
    customer = relationship("CustomerInfo")
    product = relationship("ProductInfo")
    order = relationship("Order")

# 定义 Complaint 表
class CustomerComplaint(Base):
    __tablename__ = 'CustomerComplaint'
    complaint_id = Column(Integer, primary_key=True, autoincrement=True, comment="投诉ID")
    customer_id = Column(Integer, ForeignKey('CustomerInfo.customer_id'), comment="客户ID")
    product_id = Column(Integer, ForeignKey('ProductInfo.product_id'), comment="商品ID")
    order_id = Column(Integer, ForeignKey('Order.order_id'), nullable=True, comment="关联订单ID（可为空）")
    complaint_type = Column(String(50), comment="投诉类型（度数不准、镜架断裂、镜片划痕、物流等）")
    complaint_text = Column(Text, nullable=False, comment="客户投诉原文")
    complaint_date = Column(Date, comment="投诉时间")
    complaint_severity = Column(String(20), comment="投诉严重程度（Low / Medium / High）")
    resolution_status = Column(String(50), comment="处理结果")
    resolution_date = Column(Date, comment="处理时间")
    # 关系映射
    customer = relationship("CustomerInfo")
    product = relationship("ProductInfo")
    order = relationship("Order")

class StoreInfo(Base):
    __tablename__ = 'StoreInfo'
    store_id = Column(Integer, primary_key=True, autoincrement=True, comment="门店ID")
    store_name = Column(String(100), comment="门店名称")
    store_region = Column(String(50), comment="门店所在地区")
    store_city = Column(String(50), comment="门店所在城市")
    store_country = Column(String(50), comment="门店所在国家")
    store_opening_date = Column(Date, comment="开业日期")
    store_type = Column(String(20), comment="门店类型（直营/加盟）")
    latitude = Column(Float, comment="门店纬度")
    longitude = Column(Float, comment="门店经度")

# 定义 CompetitorInfo 表
class CompetitorInfo(Base):
    __tablename__ = 'CompetitorInfo'
    competitor_id = Column(Integer, primary_key=True, autoincrement=True, comment="竞品ID")
    brand = Column(String(50), comment="品牌")
    competitor_price = Column(Numeric(10, 2), comment="竞品价格")
    market_share = Column(Numeric(5, 2), comment="市场份额（模拟）")

# 数据库连接
DATABASE_URL = "postgresql://XXXXXX:YYYYYY@localhost:5432/eyewear-data"
engine = create_engine(DATABASE_URL)
print("engine.url=", engine.url)
Session = sessionmaker(bind=engine)
session = Session()

# Only create tables if they do not exist
def create_tables_if_not_exist(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required_tables = [
        'CustomerInfo',
        'ProductInfo',
        'Order',
        'OrderItem',
        'PromotionActivity',
        'CustomerComplaint',
        'StoreInfo',
        'CompetitorInfo',
        'CustomerReview'
    ]
    missing_tables = [t for t in required_tables if t not in tables]
    if missing_tables:
        Base.metadata.create_all(engine)



if __name__ == "__main__":
    create_tables_if_not_exist(engine)
    print("All tables are created successfully!")