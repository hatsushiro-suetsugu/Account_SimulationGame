class AssetManager:
    def __init__(self, game_master):
        self.game_master = game_master

    def get_asset(self, asset_id):
        """GameMasterから資産を取得"""
        return self.game_master.get_asset_by_id(asset_id)

    def acquire_asset(self, asset_id, ledger, cash_account):
        """資産を取得しLedgerに記録"""
        asset = self.get_asset(asset_id)
        if not asset:
            raise ValueError("指定された資産が見つかりません。")

        cost = asset.market_value
        ledger.execute_transaction([
            (cash_account, -cost),
            ("固定資産", cost)
        ], description=f"Acquired {asset.name}")
        print(f"資産 '{asset.name}' を取得しました（価格: {cost}）。")

    