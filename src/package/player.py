"""
プレイヤー＆ゲームマスタの記述
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
import uuid



from sqlalchemy import (
    create_engine, 
    Column, 
    Integer, 
    String,
    Float,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import (
    declarative_base, 
    sessionmaker,
    relationship
)

from . import asset, ledger, manager

class GameMaster:
    """ゲームマスタークラス
    """
    ASSET_TYPES = {
        "tangible": {"class": asset.Tangible, "description": "固定資産"},
        "building": {"class": asset.Building, "description": "建物"},
        "inventory": {"class": asset.Inventory, "description": "棚卸資産"}
    }
        
    def __init__(self, start_date="2024-01-01", db_path="database/master.sqlite3"):
        """ゲームマスターの初期化"""
        self.current_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.players = []
        self.event_log = []
        self.asset_registry = {} # 全資産の管理
        
        # データベースの初期化
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Base = declarative_base()
        self.Base.metadata.drop_all(self.engine)
        self.Base.metadata.create_all(self.engine)
        
        # セッションの作成
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
    def construct_instance(self, asset_type, name, *args, **kwargs) -> dict:
        """
        資産を生成しデータベースに登録
        :pram asset_type: 資産タイプ
                "inventory":    棚卸資産
                    :param  name:   名前
                "tangible":     有形固定資産
                    :param  name:                   名前
                            value:                  取得価額
                            useful_liffe:           耐用年数
                            salvage_value_ratio:    残存価額比率
                            method:                 減価償却方法
                            
                    
                "building":     建物
                    :param  name:   名前
                            value:  取得価額
                            address:住所
        """
        asset_id = str(uuid.uuid4())
        
        match asset_type:
            case "inventory":
                asset_instance = self._construct_inventory(name, *args, **kwargs)
            case "tangible":
                asset_instance = self._construct_tangible(name, *args, **kwargs)
            case "building":
                asset_instance = self._construct_building(name, *args, **kwargs)
            case _:
                raise ValueError(f"無効な資産タイプ: {asset_type}")                

        self.asset_registry[asset_id] = asset_instance
        print(f"資産 '{name}' (ID: {asset_id}, クラス: {asset_instance.__class__}) が登録されました。")
        asset_info = {"ID": asset_id, "class": asset_instance.__class__, "instance": asset_instance}
        return asset_info
    
    def _construct_tangible(self, name, value, useful_life, salvage_value_ratio, method, owner=None) -> asset.Tangible:
        asset_instance = asset.Tangible(name, value, owner, useful_life, salvage_value_ratio, method)
        return asset_instance
    
    def _construct_building(self, name, value, address, owner=None) -> asset.Building:
        asset_instance = asset.Building(name, value, owner, address)
        
        return asset_instance
    
    def _construct_inventory(self, name, valuation="FIFO") -> asset.Inventory:
        asset_instance = asset.Inventory(name, quantity=0, price=0, valuation=valuation)
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
        for asset_id, asset_obj in self.asset_registry.items():
            print(f"ID: {asset_id}, 名前: {asset_obj.name}, 市場価格: {asset_obj.market_value}")

    def advance_time(self, days: int):
        """
        ゲーム全体の時間を進め、各プレイヤーや資産の状態を更新。

        :param days: 進める日数
        """
        # 時間を進める
        self.current_date += timedelta(days=days)

        # イベントログに記録
        self.log_event({
            "date": self.get_current_date(),
            "event": f"{days}日進行",
            "details": {}
        })

        # 各プレイヤーの時間経過処理を呼び出す
        for player in self.players:
            player.process_time(days)

        # 各資産の時間経過処理(?)
        for asset_id, asset_instance in self.asset_registry.items():
            if hasattr(asset_instance, "update_with_time"):
                asset_instance.update_with_time(days)

        print(f"{days}日間時間が進行しました。現在日時: {self.current_date.strftime('%Y-%m-%d')}")

    def log_event(self, event):
        """
        ゲーム内イベントを記録
        
        :param event: 記録するイベントデータ
        """
        self.event_log.append(event)
        print(f"イベント記録: {event}")

    def get_current_date(self):
        """
        現在のゲーム内日時を取得
        
        :return: 現在のゲーム内日時 (文字列)
        """
        return self.current_date.strftime("%Y-%m-%d")


class Player:
    """Playerクラス
    """
    def __init__(self, name: chr, game_master: GameMaster, initial_cash=5000):
        self.name = name
        self.game_master = game_master
        self.ledger_manager = ledger.Ledger(db_path=f"{self.name}_ledger.sqlite3", current_date=game_master.current_date)
        # 各マネージャーオブジェクトの設定
        self.building_manager = manager.BuildingManager(game_master, self)
        self.purchase_manager = manager.PurchaseManager(game_master,self)
        self.sales_manager = manager.SalesManager(game_master, self)
        
        # Playerの保持するアセット情報
        self.portfolio = []  # e.g. list({"ID": id, "instance": asset_instance})
        self.product_lists = []
        self.ends = []  # 決算情報

        # 初期現金の設定
        self.ledger_manager.execute_transaction([
            ("現金", initial_cash),
            ("資本金", -initial_cash)
        ], description=f"会社設立 資本金: {initial_cash:,}")

    def process_time(self, days: int):
        """
        プレイヤーが管理する資産の時間経過を処理

        :param days: 時間経過の日数
        """
        for asset_info in self.portfolio:
            asset_obj: asset.Asset = asset_info.get("instance")
            asset_id: chr = asset_info.get("ID")

            # Tangible 資産の場合は減価償却を実行
            if isinstance(asset_obj, asset.Tangible):
                depreciation = asset_obj.apply_depreciation(days)
                self.ledger_manager.execute_transaction([
                    ("減価償却費", depreciation),
                    ("減価償却累計額", -depreciation)
                ], description=f"{asset_obj.name} の減価償却 ({days}日)")

            # Inventory: 実地棚卸の手続きを実行
            if isinstance(asset_obj, asset.Inventory):
                self.perform_inventory_audit(product_id=asset_id)
                
            # 他の資産タイプに対応したロジックを追加する場合はここに記述
            
        # ledger の〆切
        end = self.ledger_manager.execute_settlement()
        self.ends.append({"date": self.game_master.current_date,
                          "end" : end})

        print(f"[{self.name}]時間経過が処理されました ({days}日)。")

    def aquire_building(self, asset_id: chr, value: int):
        """建物の(登録＆)取得"""
        target : asset.Building = self.game_master.get_asset_by_id(asset_id)

        if value <= 0:
            raise ValueError("取得価額は0より大きくなければなりません")

        # 所有者の登録
        target.set_owner(self.name)

        asset_info = {"ID": asset_id, "instance": target}
        self.portfolio.append(asset_info)

        self.ledger_manager.execute_transaction([
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
        asset_info = next((item for item in self.portfolio if item["ID"] == asset_id), None)

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
        
    
    def redister_product(self, product_id:chr) -> asset.Inventory:
        """商品の登録"""
        product : asset.Inventory = self.game_master.get_asset_by_id(product_id)
        
        asset_info = {"ID" : product_id, "asset_type": product.__class__, "name": product.name}
        self.portfolio.append(asset_info)
        
        print(f"[{self.name}]**商品が登録されました** 商品名：{product.name}")
        return product
            
    def purchase_product(self, product_id:chr,
                         quantity:int, price:int, fringe_cost:int = 0):
        """商品の購入"""
        if price < 0 :
            raise ValueError("取得価額は0以上でなければなりません")
        product : asset.Inventory = self.game_master.get_asset_by_id(product_id)
        
        product.add_inventory(quantity, price, fringe_cost)
        purchase_cost = quantity * price + fringe_cost
        # 仕入帳、勘定元帳への記入
        self.product_lists.append({"name": product.name, "quantity": purchase_cost})
        self.ledger_manager.execute_transaction([
            ("仕入", purchase_cost),
            ("現金", -purchase_cost)
        ], description=f"商品の仕入れ　商品名：{product.name} 個数：{quantity} 単価：{price}")
        
    def sale_product(self, product_id:chr, 
                     quantity:int, sales_price:int = None, revert:int = 0):
        """商品の販売"""
        product : asset.Inventory = self.game_master.get_asset_by_id(product_id) 
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
        
    def perform_inventory_audit(self, product_id:chr, loss:int=0):
        """棚卸調整と売上原価計算"""
        product : asset.Inventory = self.game_master.get_asset_by_id(product_id)  
        inventory_shortage, appraisal_loss, new_value, initial_value = product.perform_inventory_adjustment(loss)

        # 売上原価計算
        total_purchase = sum(item["quantity"] for item in self.product_lists if item["name"] == product.name)
        cost_of_sales = initial_value + total_purchase - new_value - inventory_shortage - appraisal_loss

        # 勘定元帳への記録・決算作業の実行
        self.ledger_manager.execute_transaction([
            ("売上原価", cost_of_sales),
            ("仕入", -total_purchase),
            ("棚卸減耗", inventory_shortage),
            ("商品評価損", appraisal_loss),
            ("棚卸資産", new_value)
        ], description=f"棚卸調整 商品: {product.name}")
        
        product.update_initial_value()
        
def main():
    # ゲームマスターを初期化
    game_master = GameMaster()

    # プレイヤーを作成して登録
    player = Player(name="Player1", game_master=game_master)
    game_master.players.append(player)

    # 資産の生成と登録
    building_asset = game_master.construct_instance(
        asset_type="building",
        name="Office Building",
        value=1000000,
        address="Downtown City"
    )

    # プレイヤーに建物資産を取得させる
    player.aquire_building(asset_id=building_asset["ID"], value=1000000)

    # ゲーム内時間を進める
    print("\n=== 90日進行 ===")
    game_master.advance_time(days=90)

    # 資産の確認
    print("\n=== プレイヤーのポートフォリオ ===")
    for asset_info in player.portfolio:
        asset_obj = asset_info.get("instance")
        print(f"資産名: {asset_obj.name}, 帳簿価額: {int(asset_obj.value)}, 累計減価償却額: {int(asset_obj.accumulated_depreciation)}")

    # 勘定元帳の記録を確認
    print("\n=== プレイヤーの勘定元帳 ===")
    player.ledger_manager.display_transaction_history()

if __name__ == "__main__":
    main()
