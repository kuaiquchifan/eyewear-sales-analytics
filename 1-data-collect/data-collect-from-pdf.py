import camelot
import pandas as pd

# 定义 PDF 文件路径和输出文件路径
pdf_path = "1-data-collect/2024 Annual Report.pdf"
output_excel = "1-data-collect/extracted_data1.xlsx"

# 页面尺寸（单位：点）
page_width = 1162.2  # 页面宽度
page_height = 842.5  # 页面高度

# 定义提取区域（左边部分）
table_areas = [f"0,{page_height},{page_width / 2},0"]  # 左边区域

# 提取 PDF 第2页的表格数据，仅限指定区域
tables = camelot.read_pdf(pdf_path, pages="2", flavor="stream", table_areas=table_areas)

# 检查是否成功提取表格
if tables.n > 0:
    print(f"成功提取到 {tables.n} 个表格！")

    # 选择第一个表格（左边的数据通常是第一个表格）
    table = tables[0].df

    # 清理数据（根据需要调整）
    table.columns = table.iloc[0]  # 将第一行设置为列名
    table = table[1:]  # 删除第一行（已作为列名）
    table.reset_index(drop=True, inplace=True)

    # 保存为 Excel 文件
    table.to_excel(output_excel, index=False)
    print(f"数据已保存到 Excel 文件：{output_excel}")
else:
    print("未能提取到任何表格，请检查 PDF 文件或尝试其他方法。")