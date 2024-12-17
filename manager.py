class Manager:
    def __init__(self, game_master, player):
        self.game_master = game_master
        self.player = player


class SalesManager(Manager):
    def __init__(self, game_master, player):
        """営業部門"""
        super().__init__(game_master, player)

class PurchaseManager(Manager):
    def __init__(self, game_master, player):
        """購買部門"""
        super().__init__(game_master, player)



class AssetManager(Manager):
    def __init__(self, game_master, player):
        """資産管理部門"""
        super().__init__(game_master, player)

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


    