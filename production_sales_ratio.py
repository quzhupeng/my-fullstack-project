import pandas as pd

def calculate_production_sales_ratio():
    # Load data sources
    sales_data = pd.read_excel("Excel文件夹/销售发票执行查询.xlsx")
    inventory_data = pd.read_excel("Excel文件夹/收发存汇总表查询.xlsx")

    # Calculate Production Department Ratio
    # Filter sales data for Production Department
    prod_dept_sales = sales_data[
        (sales_data["责任部门"] == "生品部") &
        (~sales_data["物料分类"].isin(["空白", "副产品", "生鲜品其他"])) &
        (~sales_data["物料名称"].str.contains("鲜", na=False))
    ]
    prod_dept_sales_volume = prod_dept_sales["主数量"].sum()

    # Filter inventory data for Production Department
    prod_dept_inventory = inventory_data[
        (inventory_data["责任部门"] == "生品部") &
        (~inventory_data["物料分类名称"].isin(["空白", "副产品", "生鲜品其他"])) &
        (~inventory_data["物料名称"].str.contains("鲜", na=False))
    ]
    prod_dept_production_volume = prod_dept_inventory["入库"].sum()

    # Calculate ratio for Production Department
    prod_dept_ratio = (prod_dept_sales_volume / prod_dept_production_volume) * 100

    # Calculate All Departments Ratio
    # Filter sales data for all departments
    all_dept_sales = sales_data[
        (~sales_data["物料分类"].isin(["空白", "副产品", "生鲜品其他"])) &
        (~sales_data["物料名称"].str.contains("鲜", na=False))
    ]
    all_dept_sales_volume = all_dept_sales["主数量"].sum()

    # Filter inventory data for all departments
    all_dept_inventory = inventory_data[
        (~inventory_data["物料分类名称"].isin(["空白", "副产品", "生鲜品其他"])) &
        (~inventory_data["物料名称"].str.contains("鲜", na=False))
    ]
    all_dept_production_volume = all_dept_inventory["入库"].sum()
    
    # Calculate ratio for All Departments
    all_dept_ratio = (all_dept_sales_volume / all_dept_production_volume) * 100
    
    # Print results
    print(f"Production-to-Sales Ratio (Production Department): {prod_dept_ratio:.2f}%")
    print(f"Production-to-Sales Ratio (All Departments): {all_dept_ratio:.2f}%")

if __name__ == "__main__":
    calculate_production_sales_ratio()