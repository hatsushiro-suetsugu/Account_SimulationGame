from datetime import datetime, timedelta
import uuid

import asset
import ledger
import manager


class GameMaster:
    ASSET_TYPES = {
        "tangible": {"class": asset.Tangible, "description": "固定資産"},
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
        """
        資産を生成しデータベースに登録
        :pram asset_type: 資産タイプ
            "inventory" :棚卸資産
            "tangible"  :有形固定資産
            "building"  :建物
        """
        asset_id = str(uuid.uuid4())
        
        match asset_type:
            case "inventory":
                asset_instance = self._construct_inventory(name, *args, **kwargs)
            case "tangible":
                asset_instance = self._construct_tangible(name, *args, **kwargs)
            case "building":
                asset_instance = self._construct_building(name, *args, **kwargs)
            case "machine" :
                pass
            case _:
                raise ValueError(f"無効な資産タイプ: {asset_type}")                

        # if asset_type == "tangible":
        #     asset_instance = self._construct_tangible(name, *args, **kwargs)
        # elif asset_type == "inventory":
        #     asset_instance = self._construct_inventory(name, *args, **kwargs)
        # else:
        #     raise ValueError(f"無効な資産タイプ: {asset_type}")

        self.asset_registry[asset_id] = asset_instance
        print(f"資産 '{name}' (ID: {asset_id}, クラス: {asset_type}) が登録されました。")
        return {"ID":asset_id, "instance":asset_instance}
    
    def _construct_tangible(self, name, value, owner, useful_life, salvage_value):
        asset_instance = asset.Tangible(name, value, owner, useful_life, salvage_value)
        return asset_instance
    
    def _construct_building(self, name, value, owner, address):
        asset_instance = asset.Building(name, value, owner, address)
        return asset_instance
    
    def _construct_inventory(self, name, valuation = "FIFO"):
        asset_instance = asset.Inventory(name, quantity=0, price=0, valuation = valuation)
        return asset_instance
    
    def get_asset_by_id(self, asset_id):
        """資産IDを基に資産情報を照合＆取得"""
        if asset_id not in self.asset_registry.keys():
            raise IndexError(f"ID:'{id}'に該当するアセットが登録されていません")
    
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
        self.portfolio = []    # list({"name": name,"asset": product})
        self.product_lists = []
        self.ends = [] #決算情報

        # 初期現金の設定
        self.ledger_manager.execute_transaction([
            ("現金", initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    """プレイメソッド(Managerを介さず直接行う場合)"""

    def aquire_building(self, id : chr, value: int):
        """建物の(登録＆)取得"""
        try:
            target = self.game_master.get_asset_by_id(id)
        except IndexError as e:
            print("エラー(建物の取得)：{e}")
        
        if value <= 0 :
            raise ValueError("取得価額は0より大きくなければなりません")
    
        
        
        self.portfolio.append({"name": target.name,
                                "asset_type": target.__class__})
        self.ledger_manager.execute_transaction([
            ("建物", target.value),
            ("現金", -target.value)
        ], description=f"建物の取得　建物名：{target.name}")
    
    def redister_product(self, id, valuation="FIFO"):
        """商品の登録"""
        try:
            product = self.game_master.get_asset_by_id(id)
        except IndexError as e:
            print("エラー(建物の取得)：{e}")
        self.portfolio.append({"name": product.name, 
                               "asset_type" : product.__class__})
        print(f"[{self.name}]**商品が登録されました** 商品名：{product.name}")
        return product
            
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
                     quantity: int, sales_price = None, revert = 0):
        """商品の販売"""
        if sales_price:
            print(f"[{self.name},{product.name}]**売価が更新されました**　更新後：{sales_price}")
            if sales_price <= 0 :
                print("警告：売価が0以下になっています") 
        product.subtract_inventory(quantity, sales_price)   
        sale_value = quantity * sales_price - revert 
        # 勘定元帳への記入
        self.ledger_manager.execute_transaction([
            ("現金", sale_value),
            ("売上高", -sale_value)
        ],  description=f"商品の売上 商品名：{product.name} 個数：{quantity} 単価：{product.sales_price}")
        
        
    
    def perform_inventory_audit(self, product: asset.Inventory, loss=0):
        """棚卸調整と売上原価計算"""
        inventory_shortage, appraisal_loss, new_value = product.perform_inventory_adjustment(loss)

        # 売上原価計算
        total_purchase = sum(item["quantity"] for item in self.product_lists if item["name"] == product.name)
        cost_of_sales = total_purchase - new_value

        # 勘定元帳への記録
        self.ledger_manager.execute_transaction([
            ("売上原価", cost_of_sales),
            ("仕入", -total_purchase),
            ("棚卸資産", new_value)
        ], description=f"棚卸調整 商品: {product.name}")
        
        self.product_lists = []
        
def main():
    # サンプルコード
    game_master = GameMaster()
    player1 = Player("player1",game_master)
    player2 = Player("player2",game_master)
    
    product_A = game_master.construct_instance("inventory","product_A")
    product_A = player1.redister_product(name="Product_A")
    
    player1.purchase_product(product_A, 100, 150)
    player1.purchase_product(product_A, 200, 120, 15)
    player1.sale_product(product_A, 80, 200)
    player1.purchase_product(product_A, 30, 160)
    player1.sale_product(product_A, 100, 225)
    player1.sale_product(product_A, 100, 210, 500)
    
    player1.perform_inventory_audit(product_A, 5)
    
    ledger1 = player1.ledger_manager
    
    end_1 = ledger1.execute_settlement()
    
    ledger1.display_transaction_history()
    ledger1.display_trial_balance(end_1)
    ledger1.display_financial_statements(end_1)
    
    
    
    
if __name__ == "__main__":
    main()




