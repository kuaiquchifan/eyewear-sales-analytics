# eyewear-sales-predict

### 0-database-init 执行顺序

### `data_sheet_create_0_1.py`
作用：定义 ORM 表结构、数据库连接、并创建所有表。

### `insert_product_info_data.py`
作用：生成并插入 ProductInfo 商品数据。

### `insert_store_info_data.py`
作用：解析 rayban-store的文本.txt，插入 StoreInfo 门店数据。
说明：如果你还要导入 LensCrafters 门店，则也可以接着运行第 4 步。

### `insert_store_info_data_step2.py`
作用：解析 lencrafter-store的文本2.txt，生成 lencrafter-store的文本2-processed.txt，并插入 StoreInfo。
说明：这是第二类门店数据的处理脚本。

### `insert_promotion_activity_data.py`
作用：插入 PromotionActivity 促销活动数据。
说明：不一定是订单生成必需，但建议先初始化完整数据库数据。

### `insert_customer_info_data.py`
作用：生成并插入 CustomerInfo 客户数据。
说明：订单生成依赖已有客户数据。

### `insert_order_data.py`
作用：生成并插入 Order 和 OrderItem 订单数据。
说明：最后运行，依赖 CustomerInfo、ProductInfo，并可能关联 PromotionActivity。

