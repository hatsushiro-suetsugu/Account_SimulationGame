import asset
import ledger


import ledger
from asset import TangibleAsset, Asset

class AssetManager:
    def __init__(self):
        self.assets = []

    def acquire_asset(self, asset_name, value, acquisition_date, owner):
        """汎用資産の取得"""
        print(f"{owner}が{asset_name}を{value}で取得します。")
        asset_instance = Asset(asset_name, value, owner)
        asset_instance.acquire(owner, acquisition_date)
        self.assets.append(asset_instance)
        return asset_instance

    def display_assets(self):
        """資産を表示"""
        print("保有資産:")
        for asset in self.assets:
            asset.update_market_value()
            status = "処分済み" if asset.disposal_date else "保有中"
            print(f"  - {asset.name}: 残存価値 {asset.value}, 残存時価 {asset.market_value} ({status})")

class TangibleAssetManager(AssetManager):
    def acquire_asset(self, asset_name, value, acquisition_date, owner, useful_life):
        """固定資産の取得"""
        print(f"{owner}が固定資産 {asset_name} を {value} で取得します。")
        asset_instance = TangibleAsset(asset_name, value, owner, useful_life)
        asset_instance.acquire(owner, acquisition_date)
        self.assets.append(asset_instance)
        return asset_instance

    def dispose_asset(self, asset_name, disposal_date):
        """固定資産を処分"""
        asset_to_dispose = None

        for asset in self.assets:
            if isinstance(asset, TangibleAsset) and asset.name == asset_name and asset.disposal_date is None:
                asset_to_dispose = asset
                break

        if not asset_to_dispose:
            raise ValueError(f"エラー: 固定資産 {asset_name} が見つからないか、既に処分済みです。")

        asset_to_dispose.update_market_value()
        disposal_value = asset_to_dispose.market_value
        profit_or_loss = disposal_value - asset_to_dispose.value
        asset_to_dispose.dispose(disposal_value, disposal_date)

        return {
            "disposal_value": disposal_value,
            "profit_or_loss": profit_or_loss,
            "asset": asset_to_dispose,
        }

class Player:
    def __init__(self, name, initial_cash=1000):
        """プレイヤークラスの初期化"""
        self.name = name
        self.ledger_manager = ledger.Ledger()
        self.tangible_asset_manager = TangibleAssetManager()
        self.cash_account = "現金"

        # 初期現金を設定
        self.ledger_manager.execute_transaction([
            (self.cash_account, initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

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

    # 減価償却を適用
    print("\n--- 減価償却の適用 ---")
    total_depreciation = 0
    for asset in player1.tangible_asset_manager.assets:
        if isinstance(asset, TangibleAsset) and asset.disposal_date is None:
            depreciation = asset.apply_depreciation()
            total_depreciation += depreciation

    player1.ledger_manager.execute_transaction([
        ("減価償却費", total_depreciation),
        ("固定資産", -total_depreciation)
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



