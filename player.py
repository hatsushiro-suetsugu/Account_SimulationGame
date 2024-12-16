import ledger
import asset

class AssetManager:
    def __init__(self):
        self.assets = []

    def acquire_asset(self, asset_name, value, acquisition_date, owner, useful_life=None):
        """資産の取得処理"""
        print(f"{owner}が{asset_name}を{value}で取得します。")
        
        asset_instance = asset.Asset(asset_name, value, owner, useful_life)
        asset_instance.acquire(owner, acquisition_date)
        self.assets.append(asset_instance)

        return asset_instance

    def dispose_asset(self, asset_name, disposal_date):
        """資産の処分処理"""
        asset_to_dispose = None

        for asset in self.assets:
            if asset.name == asset_name and asset.owner and asset.disposal_date is None:
                asset_to_dispose = asset
                break

        if not asset_to_dispose:
            raise ValueError(f"エラー: 資産 {asset_name} が見つからないか、既に処分済みです。")

        asset_to_dispose.update_market_value()
        disposal_value = asset_to_dispose.market_value

        profit_or_loss = disposal_value - asset_to_dispose.value
        asset_to_dispose.dispose(disposal_value, disposal_date)

        return {
            "disposal_value": disposal_value,
            "profit_or_loss": profit_or_loss,
            "asset": asset_to_dispose
        }

    def apply_depreciation(self):
        """資産の減価償却処理"""
        total_depreciation = 0
        for asset in self.assets:
            if asset.disposal_date is None:  # 処分済みの資産を除外
                depreciation = asset.apply_depreciation()
                total_depreciation += depreciation
        
        return total_depreciation

    def display_assets(self):
        """保有資産の表示"""
        print("保有資産:")
        for asset in self.assets:
            asset.update_market_value()
            status = "処分済み" if asset.disposal_date else "保有中"
            print(f"  - {asset.name}: 残存価値 {asset.value}, 減価償却累計 {asset.accumulated_depreciation}, 残存時価 {asset.market_value:.2f} ({status})")

class LedgerManager:
    def __init__(self):
        self.ledger = ledger.Ledger()

    def record_transaction(self, updates, description):
        """取引を記録"""
        try:
            self.ledger.execute_transaction(updates, description)
        except ValueError as e:
            print(f"取引エラー: {e}")

    def display_balance(self):
        """勘定残高を表示"""
        print("勘定残高:")
        self.ledger.display_balance()

    def display_financial_statements(self):
        """財務諸表を表示"""
        print("財務諸表:")
        self.ledger.display_financial_statements()

    def display_transaction_history(self):
        """トランザクション履歴を表示"""
        print("トランザクション履歴:")
        self.ledger.display_transaction_history()

class Player:
    def __init__(self, name, initial_cash=1000):
        """プレイヤークラスの初期化"""
        self.name = name
        self.ledger_manager = LedgerManager()
        self.asset_manager = AssetManager()
        self.cash_account = "現金"

        # 初期現金を設定
        self.ledger_manager.record_transaction([
            (self.cash_account, initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    def acquire_asset(self, asset_name, value, acquisition_date, useful_life=None):
        """固定資産を取得"""
        asset = self.asset_manager.acquire_asset(
            asset_name, value, acquisition_date, self.name, useful_life
        )

        # 元帳に記録
        self.ledger_manager.record_transaction([
            (self.cash_account, -value),
            ("固定資産", value)
        ], description=f"Acquired {asset_name}")

    def dispose_asset(self, asset_name, disposal_date):
        """固定資産を処分"""
        result = self.asset_manager.dispose_asset(asset_name, disposal_date)

        # 処分結果を元帳に記録
        disposal_value = result["disposal_value"]
        profit_or_loss = result["profit_or_loss"]
        asset_value = result["asset"].value

        if profit_or_loss > 0:
            self.ledger_manager.record_transaction([
                ("固定資産", -asset_value),
                (self.cash_account, disposal_value),
                ("固定資産売却益", -profit_or_loss)
            ], description=f"Profit on disposal of {asset_name}")
        elif profit_or_loss < 0:
            self.ledger_manager.record_transaction([
                ("固定資産", -asset_value),
                ("固定資産売却損", -profit_or_loss),
                (self.cash_account, disposal_value)
            ], description=f"Loss on disposal of {asset_name}")

    def apply_depreciation(self):
        """減価償却を適用"""
        total_depreciation = self.asset_manager.apply_depreciation()

        # 減価償却費を元帳に記録
        self.ledger_manager.record_transaction([
            ("減価償却費", total_depreciation),
            ("固定資産", -total_depreciation)
        ], description="Depreciation applied")

    def display_assets(self):
        """現在の資産を表示"""
        self.asset_manager.display_assets()

    def display_financial_summary(self):
        """財務状況を表示"""
        self.ledger_manager.display_balance()
        self.ledger_manager.display_financial_statements()

    def display_transaction_history(self):
        """取引履歴を表示"""
        self.ledger_manager.display_transaction_history()

# テストコード
def main():
    # プレイヤーを作成
    player1 = Player("プレイヤー1", 5000)

    # 初期資本の確認
    print("\n--- 初期財務状況 ---")
    player1.display_financial_summary()

    # 資産を取得
    print("\n--- 資産の取得 ---")
    player1.acquire_asset("オフィスビル", 3000, "2024-12-15", useful_life=10)
    player1.display_assets()
    player1.display_financial_summary()

    # 減価償却を適用
    print("\n--- 減価償却の適用 ---")
    player1.apply_depreciation()
    player1.display_assets()
    player1.display_financial_summary()

    # 資産を処分
    print("\n--- 資産の処分 ---")
    player1.dispose_asset("オフィスビル", "2025-01-01")
    player1.display_assets()
    player1.display_financial_summary()

    # トランザクション履歴の表示
    print("\n--- トランザクション履歴 ---")
    player1.display_transaction_history()

if __name__ == "__main__":
    main()


