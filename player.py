import asset
import ledger
import manager

class Player:
    def __init__(self, name, initial_cash=1000):
        """プレイヤークラスの初期化"""
        self.name = name
        self.ledger_manager = ledger.Ledger()
        self.tangible_asset_manager = manager.TangibleAssetManager()
        self.ineentory_manager = manager.InventoryManager()
        self.cash_account = "現金"

        # 初期現金を設定
        self.ledger_manager.execute_transaction([
            (self.cash_account, initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    """固定資産に関する活動"""   
    def acquire_tangible_asset(self, asset_name, value, acquisition_date, useful_life):
        """固定資産を取得"""
        asset = self.tangible_asset_manager.acquire_asset(
            asset_name, value, acquisition_date, self.name, useful_life
        )
        self.ledger_manager.execute_transaction([
            (self.cash_account, -value),
            ("固定資産", value)
        ], description=f"Acquired {asset_name}")

    def dispose_tangible_asset(self, asset_name, disposal_date):
        """固定資産を処分"""
        result = self.tangible_asset_manager.dispose_asset(asset_name, disposal_date)
        disposal_value = result["disposal_value"]
        profit_or_loss = result["profit_or_loss"]
        asset_value = result["asset"].value

        if profit_or_loss > 0:
            self.ledger_manager.execute_transaction([
                ("固定資産", -asset_value),
                (self.cash_account, disposal_value),
                ("固定資産売却益", -profit_or_loss)
            ], description=f"Profit on disposal of {asset_name}")
        elif profit_or_loss < 0:
            self.ledger_manager.execute_transaction([
                ("固定資産", -asset_value),
                (self.cash_account, disposal_value),
                ("固定資産売却損", -profit_or_loss)
            ], description=f"Loss on disposal of {asset_name}")
            
    """棚卸資産に関する活動"""
    def acquire_inventory(self, name, unit_price, quantity):
        """棚卸資産を取得"""
        inventory = self.inventory_manager.acquire_inventory(name, unit_price, quantity, self.name)
        self.ledger_manager.execute_transaction([
            (self.cash_account, -(unit_price * quantity)),
            ("棚卸資産", unit_price * quantity)
        ], description=f"Acquired inventory {name}")

    def sell_inventory(self, name, quantity, selling_price):
        """棚卸資産を販売"""
        result = self.inventory_manager.sell_inventory(name, quantity, selling_price)
        self.ledger_manager.execute_transaction([
            ("棚卸資産", -(quantity * self.inventory_manager.assets[0].unit_price)),
            ("売上高", result["revenue"]),
            ("利益", result["profit"])
        ], description=f"Sold inventory {name}")

    def discard_inventory(self, name, quantity):
        """棚卸資産を廃棄"""
        result = self.inventory_manager.discard_inventory(name, quantity)
        self.ledger_manager.execute_transaction([
            ("棚卸資産", -result["loss"]),
            ("廃棄損", result["loss"])
        ], description=f"Discarded inventory {name}")
        
        
    def display_assets(self):
        """現在の資産を表示"""
        self.tangible_asset_manager.display_assets()

# テストコード
def main():
    # プレイヤーを作成
    player1 = Player("プレイヤー1", 5000)

    # 初期資本の確認
    print("\n--- 初期財務状況 ---")
    player1.ledger_manager.display_balance()

    # 資産を取得
    print("\n--- 資産の取得 ---")
    player1.acquire_tangible_asset("オフィスビル", 3000, "2024-12-15", useful_life=10)
    player1.display_assets()

    # 減価償却を適用(ゲームマスターによる実行)
    print("\n--- 減価償却の適用 ---")
    total_depreciation = 0
    for asset in player1.tangible_asset_manager.assets:
        if isinstance(asset, asset.TangibleAsset) and asset.disposal_date is None:
            depreciation = asset.apply_depreciation()
            total_depreciation += depreciation

    player1.ledger_manager.execute_transaction([
        ("減価償却費", total_depreciation),
        ("減価償却累計額", -total_depreciation)
    ], description="Depreciation applied")

    player1.display_assets()
    player1.ledger_manager.display_balance()

    # 資産を処分
    print("\n--- 資産の処分 ---")
    player1.dispose_tangible_asset("オフィスビル", "2025-01-01")
    player1.display_assets()
    player1.ledger_manager.display_balance()

    # トランザクション履歴の表示
    print("\n--- トランザクション履歴 ---")
    player1.ledger_manager.display_transaction_history()

if __name__ == "__main__":
    main()



