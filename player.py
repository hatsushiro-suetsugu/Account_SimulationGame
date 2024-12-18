from datetime import datetime, timedelta
import uuid

import asset
import ledger
import manager


class GameMaster:
    ASSET_TYPES = {
        "tangible": {"class": asset.TangibleAsset, "description": "固定資産"},
        "building": {"class": asset.Building, "description": "建物"},
        "inventory": {"class": asset.Inventory, "description": "棚卸資産"}
    }
        
    def __init__(self, start_date="2024-01-01"):
        """ゲームマスターの初期化"""
        self.current_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.players = []
        self.event_log = []
        self.asset_registry = {}  # 全資産の管理
        
    def construct_instance(self, asset_type, name, *args, **kwargs):
        """資産を生成しデータベースに登録"""
        asset_id = str(uuid.uuid4())

        if asset_type == "building":
            asset_instance = asset.Building(name, *args, **kwargs)
        elif asset_type == "inventory":
            asset_instance = asset.Inventory(name, *args, **kwargs)
        else:
            raise ValueError(f"無効な資産タイプ: {asset_type}")

        self.asset_registry[asset_id] = asset_instance
        print(f"資産 '{name}' (ID: {asset_id}) が登録されました。")
        return asset_id, asset_instance

    def get_asset_by_id(self, asset_id):
        """資産IDを基に資産情報を取得"""
        return self.asset_registry.get(asset_id, None)

    def display_assets(self):
        """全資産を表示"""
        print("\n=== 登録済み資産 ===")
        for asset_id, asset in self.asset_registry.items():
            print(f"ID: {asset_id}, 名前: {asset.name}, 市場価格: {asset.market_value}")

    def advance_time(self, days=None, months=3, players=None):
        """
        ゲーム内時間を進める
        :param days: 日単位で進める（オプション）
        :param months: 月単位で進める（デフォルト: 3か月）
        :param players: プレイヤーリスト
        """
        if days:
            self.current_date += timedelta(days=days)
        elif months:
            self.current_date += timedelta(days=30 * months)  # 月を30日と仮定して進行

        print(f"ゲーム内時間が {self.current_date.strftime('%Y-%m-%d')} に進みました。")

        # 各プレイヤーの処理を実行
        if players:
            for player in players:
                self._process_player_ledger(player)

    def _process_player_ledger(self, player):
        """各プレイヤーのLedger処理"""
        print(f"プレイヤー {player.name} のトランザクションを処理中...")

        # 減価償却例 (固定資産の計算とLedgerへの記録)
        total_depreciation = 0
        for asset in player.tangible_asset_manager.assets:
            if isinstance(asset, asset.TangibleAsset) and asset.disposal_date is None:
                depreciation = asset.apply_depreciation()
                total_depreciation += depreciation

        if total_depreciation > 0:
            player.ledger_manager.execute_transaction([
                ("減価償却費", total_depreciation),
                ("減価償却累計額", -total_depreciation)
            ], description="Periodic depreciation")

        # 必要なら追加処理（例：収益、費用、資産の更新）

    def get_current_date(self):
        """現在のゲーム内日時を取得"""
        return self.current_date.strftime("%Y-%m-%d")

    def log_event(self, event):
        """ゲームイベントを記録"""
        self.event_log.append({"date": self.get_current_date(), "event": event})
        print(f"[{self.get_current_date()}] イベント記録: {event}")

    def display_event_log(self):
        """イベントログを表示"""
        print("\n--- ゲームイベントログ ---")
        for log in self.event_log:
            print(f"[{log['date']}] {log['event']}")

class Player:
    def __init__(self, name :chr, game_master: GameMaster, initial_cash=5000):
        """"Playerクラス"""
        self.name = name
        self.game_master = game_master
        self.ledger_manager = ledger.Ledger()
        # 各マネージャーオブジェクトの設定
        
        # Playerの保持するアセット情報
        self.assets = [] # {"name": name,"asset": product}
        self.debts = []
        self.product_lists = []

        # 初期現金の設定
        self.ledger_manager.execute_transaction([
            ("現金", initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    """プレイメソッド(Managerを介さず直接行う場合)"""

    def aquire_building(self, name: chr, value: int):
        """建物の(登録＆)取得"""
        if value <= 0 :
            raise ValueError("取得価額は0より大きくなければなりません")
        else:
            target = asset.Building(name, value, self)
            self.assets.append(target)
            self.ledger_manager.execute_transaction([
                ("建物", target.value),
                ("現金", -target.value)
            ], description=f"建物の取得　建物名：{name}")
    
    def redister_product(self, product:asset.Inventory, name):
        """商品の登録"""
        if product not in self.game_master.asset_registry:
            raise ("この商品は存在しません")
        product
        self.assets.append({"name": name, "asset": product})
            
    def purchase_product(self, product: asset.Inventory, 
                         quantity: int, price: int, fringe_cost = 0):
        """商品の購入"""
        if price <= 0 :
            raise ValueError("取得価額は0より大きくなければなりません")
    
        product.add_inventory(quantity, price, fringe_cost)
        purchase_cost = quantity * price + fringe_cost
        # 仕入帳、勘定元帳への記入
        self.product_lists.append({"name": product.name, "quantity": purchase_cost})
        self.ledger_manager.execute_transaction([
            ("仕入", purchase_cost),
            ("現金", -purchase_cost)
        ], description=f"商品の仕入れ　商品名：{product.name} 個数：{quantity} 単価：{price}")
        
    def sale_product(self, product: asset.Inventory, 
                     quantity: int, sale_price: int, revert = 0):
        """商品の販売"""
        if sale_price <= 0 :
            print("警告：売価が0になっています") 
        product.subtract_inventory(quantity)   
        sale_value = quantity * sale_price - revert 
        # 勘定元帳への記入
        self.ledger_manager.execute_transaction([
            ("現金", sale_value),
            ("売上高", -sale_value)
        ])
    
    def take_inventory(self, product: asset.Inventory, loss = 0):
        """
        商品の棚卸し
        棚卸減耗・商品評価損は売上原価に入れる(暫定)
        """ 
        old_price = product.price
        old_quantity = product.quantity
        new_price = product.market_price
        new_quantity = old_quantity - loss
        if old_price < new_price:
            new_value = new_price * new_quantity
        else:
            new_value = old_price * new_quantity
        # 棚卸減耗の記録
        inventory_shortage = old_price * loss    
        product.quantity -= loss
        
        # 商品評価損の記録
        appraisal_loss = (old_price - new_price) * new_quantity
        
        purchase_for_the_product = 0
        for list in self.product_lists:
            if list["name"] == product.name:
                purchase_for_the_product += list["quantity"]
                
        cost_of_sales = purchase_for_the_product - new_value 
        self.ledger_manager.execute_transaction([
            ("売上原価", cost_of_sales),
            ("仕入", -purchase_for_the_product),
            ("棚卸資産", new_value)
        ])
        
        self.product_lists = []
        
def main():
    # サンプルコード
    game_master = GameMaster()
    player1 = Player("player1",game_master)
    player2 = Player("player2",game_master)
    
    game_master.construct_instance("building", 
                                   "building_1", 
                                   value = 6000,
                                   owner = "")
    
    
if __name__ == "__main__":
    main()




