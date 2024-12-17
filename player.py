from asset import TangibleAsset, InventoryAsset
import ledger
import manager

class Player:
    def __init__(self, name, game_master, initial_cash=1000):
        self.name = name
        self.ledger_manager = ledger.Ledger()
        self.asset_manager = manager.AssetManager(game_master)
        self.cash_account = "現金"

        # 初期現金の設定
        self.ledger_manager.execute_transaction([
            (self.cash_account, initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    def acquire_asset(self, asset_id):
        """AssetManagerを通じて資産を取得"""
        self.asset_manager.acquire_asset(asset_id, self.ledger_manager, self.cash_account)




