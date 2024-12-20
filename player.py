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
        
    def construct_instance(self, asset_type, name, *args, **kwargs) -> dict:
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

        self.asset_registry[asset_id] = asset_instance
        print(f"資産 '{name}' (ID: {asset_id}, クラス: {asset_instance.__class__}) が登録されました。")
        asset_info = {"ID":asset_id,
                      "class":asset_instance.__class__,
                      "instance":asset_instance}
        return asset_info
    
    def _construct_tangible(self, name, value, useful_life, salvage_value, owner=None) -> asset.Tangible:
        asset_instance = asset.Tangible(name, value, owner, useful_life, salvage_value)
        return asset_instance
    
    def _construct_building(self, name, value, address, owner=None) -> asset.Building:
        asset_instance = asset.Building(name, value, owner, address)
        return asset_instance
    
    def _construct_inventory(self, name, valuation = "FIFO") -> asset.Inventory:
        asset_instance = asset.Inventory(name, quantity=0, price=0, valuation = valuation)
        return asset_instance
    
    def get_asset_by_id(self, asset_id) -> any:
        """資産IDを基に資産情報を照合＆取得"""
        if asset_id not in self.asset_registry.keys():
            raise IndexError(f"ID:'{id}'に該当するアセットが登録されていません")
        asset_instance = self.asset_registry.get(asset_id)
        
        return asset_instance

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
        self.portfolio = []    # e.g. list({"name": name, "class": asset.Inventory, "asset": product})
        self.product_lists = []
        self.ends = [] #決算情報

        # 初期現金の設定
        self.ledger_manager.execute_transaction([
            ("現金", initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    """プレイメソッド(Managerを介さず直接行う場合)"""

    def aquire_building(self, asset_id : chr, value: int):
        """建物の(登録＆)取得"""
        target = self.game_master.get_asset_by_id(asset_id)
        
        if value <= 0 :
            raise ValueError("取得価額は0より大きくなければなりません")
        
        # 所有者の登録
        if target.owner is not None:
            raise ValueError(f"この資産はすでに {target.owner} が所有しています。")
        
        target.set_owner(self.name)  # 所有者を登録

        asset_info = {"ID" : asset_id, "asset_type": target.__class__, "name": target.name}
        self.portfolio.append(asset_info)
        
        self.ledger_manager.execute_transaction([
            ("建物", target.value),
            ("現金", -target.value)
        ], description=f"建物の取得　建物名：{target.name}")
        
    def perform_depreciation(self):
        """減価償却の実行"""
        for asset_id, asset_type, name in self.portfolio:
            if asset_type == asset.Tangible:
                building = self.game_master.get_asset_by_id(asset_id)
                depreciation = building.apply_depreciation()
                self.ledger_manager.execute_transaction([
                    ("減価償却費", depreciation),
                    ("減価償却累計額", depreciation)
                ], description= f"{asset.name}の減価償却の実行")
    
    def dispose_building(self, asset_id: str, sales_price: int = None):
        """
        プレイヤーが所有する建物を売却または除却する。
        
        :param asset_id: 売却対象の資産ID
        :param sales_price: 売却価額 (デフォルトは建物の市場価値)
        """
        # 対象資産を取得
        asset_info = next((item for item in self.portfolio if item["ID"] == asset_id), None)
        
        if not asset_info:
            raise ValueError(f"指定された資産ID({asset_id})はポートフォリオに存在しません。")

        # 資産インスタンスを取得
        target_asset = self.game_master.get_asset_by_id(asset_id)["instance"]
        
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
            self.ledger_manager.execute_transaction([
                ("現金", sales_price),
                ("建物", -book_value),
                ("減価償却累計額", accumulated_depreciation),
                ("固定資産売却益", -gain)
            ], description=f"建物の売却: {target_asset.name}")
        else:
            loss = net_book_value - sales_price
            self.ledger_manager.execute_transaction([
                ("現金", sales_price),
                ("建物", -book_value),
                ("減価償却累計額", accumulated_depreciation),
                ("固定資産売却損", loss)
            ], description=f"建物の売却: {target_asset.name}")

        # ポートフォリオから削除
        self.portfolio = [item for item in self.portfolio if item["ID"] != asset_id]

        print(f"建物 '{target_asset.name}' が売却されました。")

        
    
    def redister_product(self, product_id:chr, valuation="FIFO") -> asset.Inventory:
        """商品の登録"""
        product = self.game_master.get_asset_by_id(product_id)
        
        asset_info = {"ID" : product_id, "asset_type": product.__class__, "name": product.name}
        self.portfolio.append(asset_info)
        
        print(f"[{self.name}]**商品が登録されました** 商品名：{product.name}")
        return product
            
    def purchase_product(self, product_id:chr,
                         quantity: int, price: int, fringe_cost = 0):
        """商品の購入"""
        if price < 0 :
            raise ValueError("取得価額は0以上でなければなりません")
        product = self.game_master.get_asset_by_id(product_id)
        
        product.add_inventory(quantity, price, fringe_cost)
        purchase_cost = quantity * price + fringe_cost
        # 仕入帳、勘定元帳への記入
        self.product_lists.append({"name": product.name, "quantity": purchase_cost})
        self.ledger_manager.execute_transaction([
            ("仕入", purchase_cost),
            ("現金", -purchase_cost)
        ], description=f"商品の仕入れ　商品名：{product.name} 個数：{quantity} 単価：{price}")
        
    def sale_product(self, product_id:chr, 
                     quantity: int, sales_price = None, revert = 0):
        """商品の販売"""
        product = self.game_master.get_asset_by_id(product_id) 
        if sales_price:
            print(f"[{self.name},{product.name}]**売価が更新されました**　更新後：{sales_price}")
            if sales_price <= 0 :
                print("警告：売価が0以下になっています") 
        else:
            sales_price = product.sales_price
        
        product.subtract_inventory(quantity, sales_price)   
        sale_value = quantity * sales_price - revert 
        # 勘定元帳への記入
        self.ledger_manager.execute_transaction([
            ("現金", sale_value),
            ("売上高", -sale_value)
        ],  description=f"商品の売上 商品名：{product.name} 個数：{quantity} 単価：{product.sales_price}")
        
        
    
    def perform_inventory_audit(self, product_id:chr, loss=0):
        """棚卸調整と売上原価計算"""
        product = self.game_master.get_asset_by_id(product_id) 
        inventory_shortage, appraisal_loss, new_value = product.perform_inventory_adjustment(loss)

        # 売上原価計算
        total_purchase = sum(item["quantity"] for item in self.product_lists if item["name"] == product.name)
        cost_of_sales = total_purchase - new_value - inventory_shortage - appraisal_loss

        # 勘定元帳への記録
        self.ledger_manager.execute_transaction([
            ("売上原価", cost_of_sales),
            ("仕入", -total_purchase),
            ("棚卸減耗", inventory_shortage),
            ("商品評価損", appraisal_loss),
            ("棚卸資産", new_value)
        ], description=f"棚卸調整 商品: {product.name}")
        
        self.product_lists = []
        
def main():
    # サンプルコード
    game_master = GameMaster()
    player1 = Player("player1",game_master)
    ledger1 = player1.ledger_manager
        # (ゲームマスタ)アセットのコンストラクト
    product_A = game_master.construct_instance("inventory","product_A").get("instance")
    building_B = game_master.construct_instance("building", "building_B")
    asset_list = list(game_master.asset_registry.keys())
    product_A = product_A.get("instance")
    building_B = building_B.get("instance")
        # (プレイヤーA)の動き(商品売買)
    player1.redister_product(asset_list[0])
    player1.aquire_building(building_B)

    player1.purchase_product(product_A, 100, 150)
    player1.purchase_product(product_A, 200, 120, 15)

    player1.sale_product(product_A, 80)

    player1.purchase_product(product_A, 30, 160)
    player1.sale_product(product_A, 100, 225)

    player1.sale_product(product_A, 100, 210, 500)

    player1.perform_inventory_audit(product_A, 5)

    end_1 = ledger1.execute_settlement()

    ledger1.display_transaction_history()
    ledger1.display_trial_balance(end_1)
    ledger1.display_financial_statements(end_1)
if __name__ == "__main__":
    main()




