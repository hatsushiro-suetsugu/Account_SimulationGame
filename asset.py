import random
from datetime import datetime, timedelta

class Asset:
    def __init__(self, name, value):
        """基本資産クラス"""
        self.name = name
        self.value = value # 帳簿価額
        self.market_value = value  # 市場価格を初期設定

    def update_market_value(self):
        """市場価格をランダムに更新"""
        mean = self.value
        std_dev = mean / 6
        self.market_value = max(0, int(random.gauss(mean, std_dev)))

class TangibleAsset(Asset):
    def __init__(self, name, value, owner, useful_life, salvage_value=0):
        """有形固定資産クラス"""
        super().__init__(name, value)
        self.owner = owner
        self.useful_life = useful_life  # 耐用年数 (年単位)
        self.salvage_value = salvage_value # 残存価額
        self.accumulated_depreciation = 0  # 減価償却累計額

    def apply_depreciation(self):
        """減価償却を適用：(帳簿価額-残存価額:デフォルトでゼロ)/耐用年数"""
        depreciation = self.value - self.salvage_value / self.useful_life
        self.accumulated_depreciation += depreciation
        self.value = max(self.salvage_value, self.value - depreciation)
        return depreciation

class Building(TangibleAsset):
    def __init__(self, name, value, owner, useful_life = 30, salvage_value=0):
        super().__init__(name, value, owner, useful_life, salvage_value)
        


class Inventory(Asset):
    VALUATIONS = ["FIFO", "GAM", "MAM"] # 先入先出法、総平均法、移動平均法
    def __init__(self, name, quantity, price, valuation):
        """
        棚卸資産クラス
        評価方法　FIFO: 先入先出法　GAM: 総平均法　MAM: 移動平均法
        (個別法は個別にインスタンスを作ればいいのでは？)
        """
        super().__init__(name, value = quantity*price)
        self.quantity = quantity
        self.price = price
        self.market_price = price # 正味売却価額(予定)
        self.market_value = self.market_price * price
        self.valuation = valuation
        self.transactions = [] # 在庫の追加履歴
        if valuation not in self.VALUATIONS:
            raise ValueError("正しい評価方法を選択してください")

        if self.valuation == "FIFO":
            # FIFO用のリストデータ構造を初期化
            self.inventory_data = [{"quantity": quantity, "price": price}]
            
        if self.valuation == "GAM":
            # GAM用のデータ構造を初期化
            self.total_quantity = quantity
            self.total_value = quantity * price
    
    def _record_transaction(self, time:datetime, description):
        transaction = {time : description}
        self.transactions.append(transaction)
    
    def update_value(self, new_value):
        """簿価の更新（決算時の評価損などで使用予定）"""
        self.value = new_value
        self.price = self.value / self.quantity
       
    def update_market_value(self): 
        pass
        
    def update_market_price(self, new_price):
        """市場価格の更新"""
        self.market_price = new_price
        self.market_value = self.market_price * self.quantity
    
    def add_inventory(self, quantity: int, price: int, fringe_cost = 0):
        """棚卸資産の増加"""
        add_value = quantity * price + fringe_cost
        self.value += add_value
        self.quantity += quantity

        if self.valuation == "FIFO":
            # FIFOの場合はリストデータに追加
            self.inventory_data.append({"quantity": quantity, "price": price})
        elif self.valuation == "MAM":
            # MAMの場合は新しい平均単価を計算
            self.price = self.value / self.quantity
        elif self.valuation == "GAM":
            # GAMの場合は合計数量と金額を更新
            self.total_quantity += quantity
            self.total_value += add_value
        
        # 市場価値の再計算(仮で設定)
        self.market_value = self.market_price * self.quantity

        
        if self.valuation == "MAM":
            self.price = self.value / self.quantity
            description= f"add_inventory: {quantity}, update_price(MAM): {self.price}"
        else:
            description = f"add_inventory: {quantity}"
        self._record_transaction(datetime.today(), description= description)
        
    def subtract_inventory(self, quantity: int):
        """棚卸資産の減少"""
        if self.valuation == "FIFO":
            self._subtract_inventory_FIFO(quantity)
        elif self.valuation == "MAM":
            self._subtract_inventory_MAM(quantity)
        elif self.valuation == "GAM":
            self._subtract_inventory_GAM(quantity)
        
    def _subtract_inventory_FIFO(self, quantity: int):
        """FIFOによる棚卸資産の減少"""
        if quantity > self.quantity:
            raise ValueError("在庫不足です。指定された数量を引き出せません。")

        remaining_quantity = quantity
        total_cost = 0

        # FIFOの順に在庫を減少
        while remaining_quantity > 0:
            if not self.inventory_data:
                raise ValueError("在庫履歴が不足しています。")

            oldest_transaction = self.inventory_data[0]
            trans_quantity = oldest_transaction["quantity"]
            trans_price = oldest_transaction["price"]

            if trans_quantity <= remaining_quantity:
                # このトランザクション全体を消費
                total_cost += trans_quantity * trans_price
                remaining_quantity -= trans_quantity
                self.inventory_data.pop(0)
            else:
                # 一部のみ消費
                total_cost += remaining_quantity * trans_price
                oldest_transaction["quantity"] -= remaining_quantity
                remaining_quantity = 0

        self.value -= total_cost
        self.quantity -= quantity

        # 減少トランザクションを記録
        description = f"Subtracted {quantity} units (FIFO)"
        self._record_transaction(datetime.now(), description)
        print(f"在庫が {quantity} 単位減少しました。総コスト: {total_cost}")
    
    def _subtract_inventory_MAM(self, quantity):
        """MAMによる棚卸資産の減少"""
        if quantity > self.quantity:
            raise ValueError("在庫不足です。指定された数量を引き出せません。")

        # 移動平均法で単価を計算
        average_price = self.value / self.quantity
        total_cost = average_price * quantity

        self.value -= total_cost
        self.quantity -= quantity

        # 減少トランザクションを記録
        description = f"Subtracted {quantity} units (MAM) at average price {average_price}"
        self._record_transaction(datetime.now(), description)
        print(f"在庫が {quantity} 単位減少しました。平均単価: {average_price}, 総コスト: {total_cost}")
    
    def _subtract_inventory_GAM(self, quantity: int):
        """GAMによる棚卸資産の減少"""
        if quantity > self.quantity:
            raise ValueError("在庫不足です。指定された数量を引き出せません。")

        # 総平均単価を計算
        average_price = self.total_value / self.total_quantity
        total_cost = average_price * quantity

        # 更新
        self.total_value -= total_cost
        self.total_quantity -= quantity
        self.value -= total_cost
        self.quantity -= quantity

        # 減少トランザクションを記録
        description = f"Subtracted {quantity} units (GAM) at average price {average_price}"
        self._record_transaction(datetime.now(), description)
        print(f"在庫が {quantity} 単位減少しました。平均単価: {average_price}, 総コスト: {total_cost}")
    
class Debt:
    # リスクフリーレートの設定(将来的にランダムに動くように関数化)
    RFR = 0.01
    def __init__(self, name, bank, value):
        self.name = name
        self.bank = bank
        self.value = value
        self.risk_premium = 0.05
        self.rate = self.RFR + self.risk_premium # 利率
        
    def repay_debt(self, repay_value):
        self.value =- repay_value
        
    def add_interest(self):
        interest = (self.value * self.rate) * days / years
    
def main():
    # FIFOのテスト
    print("\n=== FIFO テスト ===")
    fifo_inventory = Inventory("FIFO Product", 100, 50, "FIFO")
    fifo_inventory.add_inventory(50, 55)
    fifo_inventory.add_inventory(100, 60)
    print("在庫減少前の在庫数:", fifo_inventory.quantity)
    print("在庫減少前の在庫内容:", fifo_inventory.inventory_data)

    try:
        fifo_inventory.subtract_inventory(120)
    except ValueError as e:
        print("エラー:", e)
    
    fifo_inventory.add_inventory(75, 65)

    print("在庫減少後の在庫数:", fifo_inventory.quantity)
    print("在庫減少後の在庫内容:", fifo_inventory.inventory_data)

    # MAMのテスト
    print("\n=== MAM テスト ===")
    mam_inventory = Inventory("MAM Product", 100, 50, "MAM")
    mam_inventory.add_inventory(50, 55)
    mam_inventory.add_inventory(100, 60)
    print("在庫減少前の在庫数:", mam_inventory.quantity)
    print("在庫減少前の平均単価:", mam_inventory.price)

    try:
        mam_inventory.subtract_inventory(120)
    except ValueError as e:
        print("エラー:", e)
        
    mam_inventory.add_inventory(75, 65)

    print("在庫減少後の在庫数:", mam_inventory.quantity)
    print("在庫減少後の平均単価:", mam_inventory.price)

    # GAMのテスト
    print("\n=== GAM テスト ===")
    gam_inventory = Inventory("GAM Product", 100, 50, "GAM")
    gam_inventory.add_inventory(50, 55)
    gam_inventory.add_inventory(100, 60)
    print("在庫減少前の在庫数:", gam_inventory.quantity)
    print("在庫減少前の総価値:", gam_inventory.total_value)
    print("在庫減少前の平均単価:", gam_inventory.total_value / gam_inventory.total_quantity)

    try:
        gam_inventory.subtract_inventory(120)
    except ValueError as e:
        print("エラー:", e)

    gam_inventory.add_inventory(75, 65)

    print("在庫減少後の在庫数:", gam_inventory.quantity)
    print("在庫減少後の総価値:", gam_inventory.total_value)

if __name__ == "__main__":
    main()
