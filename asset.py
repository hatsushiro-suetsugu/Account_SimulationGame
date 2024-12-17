import random

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
        """固定資産クラス"""
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
    def __init__(self, name, value, useful_life=30, salvage_value=0, owner, address):
        super().__init__(name, value, useful_life, salvage_value)
        self.address = address # 住所
        


class Inventory(Asset):
    def __init__(self, name, value):
        super().__init__(name, value)

def main():
    