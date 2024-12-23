"""プレイヤーの各種管理クラスの記述"""
from scripts import (
    asset, 
    player
    )

class Manager:
    """一般マネージャークラス"""
    def __init__(self, game_master:player.GameMaster, owner_player:player.Player):
        self.game_master = game_master
        self.player = owner_player


class SalesManager(Manager):
    """販売マネージャークラス"""
    def __init__(self, game_master, owner_player):
        super().__init__(game_master, owner_player)
    
    def sale_product(self, product_id:chr, 
                     quantity:int, sales_price:int = None, revert:int = 0):
        """商品の販売"""
        product : asset.Inventory = self.game_master.get_asset_by_id(product_id) 
        if sales_price:
            print(f"[{self.player.name},{product.name}]**売価が更新されました**　更新後：{sales_price}")
            if sales_price <= 0 :
                print("警告：売価が0以下になっています") 
        else:
            sales_price = product.sales_price
        
        product.subtract_inventory(quantity, sales_price)   
        sale_value = quantity * sales_price - revert 
        # 勘定元帳への記入
        self.player.ledger_manager.execute_transaction([
            ("現金", sale_value),
            ("売上高", -sale_value)
        ],  description=f"商品の売上 商品名：{product.name} 個数：{quantity} 単価：{product.sales_price}")
    

class PurchaseManager(Manager):
    """購買部門"""
    def __init__(self, game_master, owner_player):
        super().__init__(game_master, owner_player)
        
    def purchase_product(self, product_id:chr,
                         quantity:int, price:int, fringe_cost:int = 0):
        """商品の購入"""
        if price < 0 :
            raise ValueError("取得価額は0以上でなければなりません")
        product : asset.Inventory = self.game_master.get_asset_by_id(product_id)
        
        product.add_inventory(quantity, price, fringe_cost)
        purchase_cost = quantity * price + fringe_cost
        # 仕入帳、勘定元帳への記入
        self.player.product_lists.append({"name": product.name, "quantity": purchase_cost})
        self.player.ledger_manager.execute_transaction([
            ("仕入", purchase_cost),
            ("現金", -purchase_cost)
        ], description=f"商品の仕入れ　商品名：{product.name} 個数：{quantity} 単価：{price}")



class BuildingManager(Manager):
    """建物管理マネージャー"""
    def __init__(self, game_master, owner_player):
        super().__init__(game_master, owner_player)

    def aquire_building(self, asset_id: chr, value: int):
        """建物の(登録＆)取得"""
        target : asset.Building = self.game_master.get_asset_by_id(asset_id)

        if value <= 0:
            raise ValueError("取得価額は0より大きくなければなりません")

        # 所有者の登録
        target.set_owner(self.player.name)

        asset_info = {"ID": asset_id, "instance": target}
        self.player.portfolio.append(asset_info)

        self.player.ledger_manager.execute_transaction([
            ("建物", target.value),
            ("現金", -target.value)
        ], description=f"建物の取得　建物名：{target.name}")
        
        print(f"Building instance type: {type(target)}")

    def dispose_building(self, asset_id: str, sales_price: int = None):
        """
        プレイヤーが所有する建物を売却または除却する。
        
        :param asset_id: 売却対象の資産ID
        :param sales_price: 売却価額 (デフォルトは建物の市場価値)
        """
        # 対象資産を取得
        asset_info = next((item for item in self.player.portfolio if item["ID"] == asset_id), None)

        if not asset_info:
            raise ValueError(f"指定された資産ID({asset_id})はポートフォリオに存在しません。")

        # 資産インスタンスを取得
        target_asset : asset.Building = asset_info.get("instance")

        if not isinstance(target_asset, asset.Building):
            raise ValueError("指定された資産は建物ではありません。")

        # 売却価額の設定 (デフォルトは市場価値)
        if sales_price is None:
            sales_price = target_asset.market_value

        # 簿価と売却損益の計算
        book_value = target_asset.value
        accumulated_depreciation = target_asset.accumulated_depreciation
        net_book_value = book_value - accumulated_depreciation

        if sales_price >= net_book_value:
            gain = sales_price - net_book_value
            self.player.ledger_manager.execute_transaction([
                ("現金", sales_price),
                ("建物", -book_value),
                ("減価償却累計額", accumulated_depreciation),
                ("固定資産売却益", -gain)
            ], description=f"建物の売却: {target_asset.name}")
        else:
            loss = net_book_value - sales_price
            self.player.ledger_manager.execute_transaction([
                ("現金", sales_price),
                ("建物", -book_value),
                ("減価償却累計額", accumulated_depreciation),
                ("固定資産売却損", loss)
            ], description=f"建物の売却: {target_asset.name}")

        # ポートフォリオから削除
        self.player.portfolio = [item for item in self.player.portfolio if item["ID"] != asset_id]

        print(f"建物 '{target_asset.name}' が売却されました。")


    