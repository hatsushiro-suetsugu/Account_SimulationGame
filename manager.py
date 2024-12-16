import asset

class AssetManager:
    def __init__(self):
        self.assets = []

    def acquire_asset(self, asset_name, value, acquisition_date, owner):
        """汎用資産の取得"""
        print(f"{owner}が{asset_name}を{value}で取得します。")
        asset_instance = asset.Asset(asset_name, value, owner)
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
        asset_instance = asset.TangibleAsset(asset_name, value, owner, useful_life)
        asset_instance.acquire(owner, acquisition_date)
        self.assets.append(asset_instance)
        return asset_instance

    def dispose_asset(self, asset_name, disposal_date):
        """固定資産を処分"""
        asset_to_dispose = None

        for asset in self.assets:
            if isinstance(asset, asset.TangibleAsset) and asset.name == asset_name and asset.disposal_date is None:
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
        
class InventoryManager(AssetManager):
    def acquire_inventory(self, name, unit_price, quantity, owner):
        """棚卸資産を取得"""
        print(f"{owner}が棚卸資産 {name} を {quantity} 単位、単価 {unit_price} で取得します。")
        inventory_asset = asset.InventoryAsset(name, unit_price, quantity)
        inventory_asset.acquire(owner, acquisition_date=None)  # 棚卸資産に取得日を設定しない
        self.assets.append(inventory_asset)
        return inventory_asset

    def sell_inventory(self, name, quantity, selling_price):
        """棚卸資産を販売"""
        for asset in self.assets:
            if isinstance(asset, asset.InventoryAsset) and asset.name == name:
                result = asset.sell(quantity, selling_price)
                return result
        raise ValueError(f"エラー: 棚卸資産 {name} が見つかりません。")

    def discard_inventory(self, name, quantity):
        """棚卸資産を廃棄"""
        for asset in self.assets:
            if isinstance(asset, asset.InventoryAsset) and asset.name == name:
                result = asset.discard(quantity)
                return result
        raise ValueError(f"エラー: 棚卸資産 {name} が見つかりません。")

    def update_inventory_price(self, name, new_unit_price):
        """棚卸資産の単価を更新"""
        for asset in self.assets:
            if isinstance(asset, asset.InventoryAsset) and asset.name == name:
                asset.update_market_price(new_unit_price)
                return
        raise ValueError(f"エラー: 棚卸資産 {name} が見つかりません。")