"""アセット関連の設定ファイル"""
import random
from datetime import datetime

class Asset:
    def __init__(self, name, value):
        """基本資産クラス"""
        self.name = name
        self.value = value # 帳簿価額
        self.market_value = value  # 市場価格を初期設定

    def update_market_value(self):
        """市場価格をランダムに更新"""
        mean = self.value
        std_dev = mean / 10
        self.market_value = max(0, int(random.gauss(mean, std_dev)))

class Tangible(Asset):
    METHODS = {"straight_line", "accelarated"}
    
    def __init__(
        self,
        name:chr,
        value:int,
        owner:chr,
        useful_life:int,
        salvage_value_ratio:float, 
        method:str
        ):
        """有形固定資産クラス

        Args:
            name (chr): 資産名
            value (int): 取得価額
            owner (chr): 所有者
            useful_life (int): 耐用年数
            salvage_value_ratio (float): 残存価額比率
            method (chr): 減価償却方法(定額法, 定率法(予定))

        Raises:
            ValueError: 無効な減価償却方法です
        """
        super().__init__(name, value)
        self.owner = owner
        self.method = method 
        self.useful_life = useful_life  # 耐用年数 (年単位)
        self.salvage_value = value * salvage_value_ratio # 残存価額
        self.accumulated_depreciation = 0  # 減価償却累計額
        
        if self.method not in self.METHODS :
            raise ValueError("無効な減価償却方法です")

    def set_owner(self, owner_name: str):
        """資産の所有者を設定"""
        if self.owner:
            raise ValueError(f"{self.name} はすでに所有者 {self.owner} が登録されています。")
        self.owner = owner_name
        print(f"{self.name} の所有者が {owner_name} に設定されました。")
        
    def get_owner(self):
        """資産の所有者を取得"""
        return self.owner
    
    def apply_depreciation(self, days: int = 365):
        """
        減価償却を適用。指定された日数に基づいて減価償却額を計算。

        :param days: 時間経過の日数（デフォルトは1年=365日）
        :return: 減価償却額
        """
        if self.method == "straight_line":
            depreciation_per_day = (self.value - self.salvage_value) / (self.useful_life * 365)
        elif self.method == "accelarated":
            depreciation_per_day = ((self.value - self.accumulated_depreciation) * 2) / (self.useful_life * 365)
        else:
            raise ValueError("無効な減価償却方法です")

        total_depreciation = int(depreciation_per_day * days)
        self.accumulated_depreciation += total_depreciation
        self.value = max(self.salvage_value, self.value - total_depreciation)
        print(f"{self.name} の減価償却が適用されました: {total_depreciation} 減価償却累計額: {self.accumulated_depreciation} 残存価額: {self.value}")
        return total_depreciation

class Building(Tangible):
    def __init__(self, name, value, owner, address, 
                 useful_life=40, salvage_value_ratio=0, method="straight_line"):
        super().__init__(name, value, owner, 
                         useful_life, salvage_value_ratio, method)
        self.address = address

class Machine(Tangible):
    def __init__(self, name, value, owner, method, 
                 useful_life, salvage_value_ratio=0):
        super().__init__(name, value, owner, useful_life, salvage_value_ratio, method)

class Inventory(Asset):
    VALUATIONS = ["FIFO", "GAM", "MAM"] # 先入先出法、総平均法、移動平均法
    def __init__(self, name, quantity, price, valuation):
        """
        棚卸資産クラス
        評価方法　FIFO: 先入先出法　GAM: 総平均法　MAM: 移動平均法
        (個別法は個別にインスタンスを作ればいいのでは？)
        """
        super().__init__(name, value = quantity*price)
        self.quantity = quantity                                    # 現在の数量
        self.initial_value = 0                                   # 期首の数量
        self.price = price                                          # 購買単価
        self.sales_price = price                                    # 売価
        self.market_sales_price = self.sales_price                  # 正味売却単価(予定)
        self.market_sales_value = self.market_sales_price * price   # 正味売却価額(予定)
        self.valuation = valuation                                  # 棚卸資産の評価方法
        self.transactions = []                                      # 在庫の追加履歴 list({})
        if valuation not in self.VALUATIONS:
            raise ValueError("正しい評価方法を選択してください")

        if self.valuation == "FIFO":
            # FIFO用のリストデータ構造を初期化
            self.inventory_data = [{"quantity": quantity, "price": price}]
            
        if self.valuation == "GAM":
            # GAM用のデータ構造を初期化
            self.total_quantity = quantity
            self.total_value = quantity * price
    
    def _record_transaction(self, description):
        transaction = {
            "time": datetime.now(),
            "description": description,
            "quantity": self.quantity,
            "value": self.value
        }
        self.transactions.append(transaction)
    
    def update_value(self, new_value):
        """簿価の更新"""
        self.value = new_value
        self.price = self.value / self.quantity

    def update_market_sales_price(self):
        """市場売価をランダムに更新"""
        mean = self.sales_price  # 売価を基準にする
        std_dev = mean / 10
        self.market_sales_price = max(0, int(random.gauss(mean, std_dev))) 
        description = (f"市場売価が更新されました: {self.market_sales_price}")
        self._record_transaction(description)        
    
    def update_sales_price(self, new_price):
        """売価の更新"""
        old_price = self.sales_price
        self.sales_price = new_price
        description = (f"売価更新: 旧売価 {old_price}, 新売価 {new_price}, 在庫数量 {self.quantity}, "
                       f"在庫簿価 {self.value}")
        self._record_transaction(description)
    
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
                
        if self.valuation == "MAM":
            self.price = self.value / self.quantity
            description= f"商品の追加: {quantity}, 更新原価(MAM): {self.price}"
        else:
            description = f"商品の追加: {quantity}"
        self._record_transaction(description)
        
    def subtract_inventory(self, quantity: int, sales_price = None):
        """棚卸資産の減少"""
        if self.valuation == "FIFO":
            self._subtract_inventory_fifo(quantity)
        elif self.valuation == "MAM":
            self._subtract_inventory_mam(quantity)
        elif self.valuation == "GAM":
            self._subtract_inventory_gam(quantity)
            
        # 売価の更新
        if sales_price:
            self.update_sales_price(new_price=sales_price)
            self.update_market_sales_price() 
        
    def _subtract_inventory_fifo(self, quantity: int):
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
        description = f"在庫が {quantity} 単位減少しました。総コスト: {total_cost}"
        self._record_transaction(description)
        # print(f"在庫が {quantity} 単位減少しました。総コスト: {total_cost}")
    
    def _subtract_inventory_mam(self, quantity):
        """MAMによる棚卸資産の減少"""
        if quantity > self.quantity:
            raise ValueError("在庫不足です。指定された数量を引き出せません。")

        # 移動平均法で単価を計算
        average_price = self.value / self.quantity
        total_cost = average_price * quantity

        self.value -= total_cost
        self.quantity -= quantity

        # 減少トランザクションを記録
        description = f"在庫が {quantity} 単位減少しました。平均単価: {average_price}, 総コスト: {total_cost}"
        self._record_transaction(description)
        
    def _subtract_inventory_gam(self, quantity: int):
        """
        GAMによる棚卸資産の減少
        todo:期末に単価を評価する方法を確立する
        """
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
        description = f"在庫が {quantity} 単位減少しました。平均単価: {average_price}, 総コスト: {total_cost}"
        self._record_transaction(description)
        # print(f"在庫が {quantity} 単位減少しました。平均単価: {average_price}, 総コスト: {total_cost}")
        
    def perform_inventory_adjustment(self, loss):
        """棚卸調整: 減耗や評価損を計算し在庫を更新"""
        old_price = self.price
        new_price = self.market_sales_price  # 市場価格を更新
        old_quantity = self.quantity
        new_quantity = old_quantity - loss
        
        # 棚卸減耗の計算, 現在数量の更新
        inventory_shortage = old_price * loss 
        self.quantity = new_quantity
        
        # 商品評価損の計算, 簿価の切下げ・更新(あれば)
        if old_price > new_price:
            appraisal_loss = max(0, (old_price - new_price) * new_quantity) 
            self.value = new_price * new_quantity      
        
        return inventory_shortage, appraisal_loss, self.value, self.initial_value
    
    def update_initial_value(self):
        """期首簿価の更新(決算の実行時)"""
        self.initial_value = self.value
    
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
        
    def add_interest(self, days):
        interest = (self.value * self.rate) * days / 365
    
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
    print("在庫減少前の平均単価:", gam_inventory.total_value / gam_inventory.total_quantity)

if __name__ == "__main__":
    main()
