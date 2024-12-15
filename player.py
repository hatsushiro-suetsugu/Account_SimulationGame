import ledger
import asset

class Player:
    def __init__(self, name, initial_cash=1000):
        """プレイヤークラスの初期化"""
        self.name = name
        self.ledger = ledger.Ledger()
        self.cash_account = "現金"
        self.assets = []  # 所有資産リスト

        # 初期現金を設定
        self.ledger.execute_transaction([
            (self.cash_account, initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    def acquire_asset(self, asset_name, value, acquisition_date, useful_life=None):
        """固定資産を取得"""
        print(f"\n{self.name}が{asset_name}を{value}で取得します。")

        # 資産を元帳とリストに追加
        self.ledger.execute_transaction([
            (self.cash_account, -value),
            ("固定資産", value)
        ], description=f"Acquired {asset_name}")

        asset_instance = asset.Asset(asset_name, value, self.name, useful_life)
        asset_instance.acquire(self.name, acquisition_date)
        self.assets.append(asset_instance)

    def dispose_asset(self, asset_name, disposal_date):
        """固定資産を処分"""
        asset_to_dispose = None

        # 処分する資産を特定
        for asset in self.assets:
            if asset.name == asset_name and asset.owner == self.name and asset.disposal_date is None:
                asset_to_dispose = asset
                break

        if not asset_to_dispose:
            print(f"\nエラー: 資産 {asset_name} が見つからないか、既に処分済みです。")
            return

        # 残存時価を更新
        asset_to_dispose.update_market_value()
        disposal_value = asset_to_dispose.market_value

        # 処分価額と残存時価の差額を収益または費用として記録
        profit_or_loss = disposal_value - asset_to_dispose.value
        if profit_or_loss > 0:
            self.ledger.execute_transaction([
                ("固定資産", -asset_to_dispose.value),
                (self.cash_account, disposal_value),
                ("固定資産売却益", -profit_or_loss)
            ], description=f"Profit on disposal of {asset_name}")
        elif profit_or_loss < 0:
            self.ledger.execute_transaction([
                ("固定資産", -asset_to_dispose.value),
                ("固定資産売却損", -profit_or_loss),
                (self.cash_account, disposal_value)
            ], description=f"Loss on disposal of {asset_name}")

        # 資産の処分を記録
        asset_to_dispose.dispose(disposal_value, disposal_date)
        print(f"\n{self.name}が{asset_name}を{disposal_value:.2f}で処分しました。")

    def display_assets(self):
        """現在の資産を表示"""
        print(f"\n{self.name}の保有資産:")
        for asset in self.assets:
            asset.update_market_value()
            status = "処分済み" if asset.disposal_date else "保有中"
            print(f"  - {asset.name}: 残存価値 {asset.value}, 減価償却累計 {asset.accumulated_depreciation}, 残存時価 {asset.market_value:.2f} ({status})")

# テストコード
if __name__ == "__main__":
    player = Player("プレイヤー1", 5000)

    # 資産を取得
    player.acquire_asset("オフィスビル", 3000, "2024-12-15", useful_life=10)

    # 現在の資産を表示
    player.display_assets()

    # ゲームマスターが減価償却を適用
    print("\n減価償却を適用:")
    total_depreciation = 0
    for asset in player.assets:
        if asset.disposal_date is None:  # 処分済みの資産は除外
            depreciation = asset.apply_depreciation()
            total_depreciation += depreciation

            # 減価償却を元帳に記録
            player.ledger.execute_transaction([
                ("減価償却費", depreciation),
                ("固定資産", -depreciation)
            ], description=f"Depreciation for {asset.name}")
    print(f"\n総減価償却費: {total_depreciation}")

    # 減価償却後の資産を表示
    player.display_assets()

    # 資産を処分
    player.dispose_asset("オフィスビル", "2025-01-01")

    # 処分後の資産を表示
    player.display_assets()

    # 財務状況を表示
    player.ledger.display_balance()
    player.ledger.display_transaction_history()

