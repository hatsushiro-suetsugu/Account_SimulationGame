import random

class Asset:
    def __init__(self, name, value, owner=None):
        """基本資産クラス"""
        self.name = name
        self.value = value
        self.owner = owner  # 資産所有者
        self.acquisition_date = None
        self.disposal_date = None
        self.disposal_value = None
        self.market_value = None  # 残存時価

    def acquire(self, owner, acquisition_date):
        """資産の取得を記録"""
        self.owner = owner
        self.acquisition_date = acquisition_date

    def dispose(self, disposal_value, disposal_date):
        """資産の処分を記録"""
        self.disposal_value = disposal_value
        self.disposal_date = disposal_date

    def update_market_value(self):
        """残存時価を更新（デフォルト実装）"""
        self.market_value = self.value  # デフォルトでは簿価

class TangibleAsset(Asset):
    def __init__(self, name, value, owner=None, useful_life=None):
        """固定資産クラス"""
        super().__init__(name, value, owner)
        self.useful_life = useful_life  # 耐用年数 (年単位)
        self.accumulated_depreciation = 0  # 減価償却累計額

    def calculate_depreciation(self):
        """1年分の減価償却を計算"""
        if self.useful_life is None or self.value <= 0:
            return 0
        annual_depreciation = self.value / self.useful_life
        return annual_depreciation

    def apply_depreciation(self):
        """減価償却を適用"""
        depreciation = self.calculate_depreciation()
        self.accumulated_depreciation += depreciation
        self.value -= depreciation
        if self.value < 0:
            self.value = 0
        return depreciation

    def update_market_value(self):
        """残存時価を更新"""
        if self.value <= 0:
            self.market_value = 0
        else:
            mean = self.value
            std_dev = mean / 6
            self.market_value = max(0, int(random.gauss(mean, std_dev)))

class InventoryAsset(Asset):
    def __init__(self, name, unit_price, quantity=0):
        """棚卸資産クラスの初期化"""
        super().__init__(name, unit_price * quantity)
        self.unit_price = unit_price  # 単価
        self.quantity = quantity  # 数量
        self.total_value = self.unit_price * self.quantity  # 合計価値

    def add_stock(self, quantity, unit_price):
        """在庫を追加"""
        self.unit_price = ((self.unit_price * self.quantity) + (unit_price * quantity)) / (self.quantity + quantity)
        self.quantity += quantity
        self.total_value = self.unit_price * self.quantity
        self.value = self.total_value

    def remove_stock(self, quantity):
        """在庫を削除"""
        if quantity > self.quantity:
            raise ValueError("在庫数量を超える削除はできません。")
        self.quantity -= quantity
        self.total_value = self.unit_price * self.quantity
        self.value = self.total_value

    def get_inventory_status(self):
        """現在の在庫状態を取得"""
        return {
            "name": self.name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "total_value": self.total_value,
        }