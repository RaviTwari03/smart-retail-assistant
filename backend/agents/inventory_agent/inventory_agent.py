def inventory_agent(stock):
    
    if stock < 15:
        return "Critical Stock Alert"

    elif stock < 50:
        return "Moderate Inventory Warning"

    return "Inventory Stable"