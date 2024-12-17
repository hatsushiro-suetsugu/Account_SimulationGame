import random

class Asset:
    def __init__(self, name, value):
        """基本資産クラス"""
        self.name = name
        self.value = value
        self.market_value = value  # 市場価格を初期設定

    def update_market_value(self):
        """市場価格をランダムに更新"""
        mean = self.value
        std_dev = mean / 6
        self.market_value = max(0, int(random.gauss(mean, std_dev)))

class TangibleAsset(Asset):
    def __init__(self, name, value, useful_life=None, salvage_value=0):
        super().__init__(name, value)
        self.useful_life = useful_life
        self.salvage_value = salvage_value
        self.accumulated_depreciation = 0

    def apply_depreciation(self):
        """減価償却を適用"""
        depreciation = self.value - self.salvage_value / self.useful_life
        self.accumulated_depreciation += depreciation
        self.value = max(self.salvage_value, self.value - depreciation)
        return depreciation

class Inventory(Asset):
    def __init__(self, name, value):
        super().__init__(name, value)

def main():
    