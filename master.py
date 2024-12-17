from datetime import datetime, timedelta
import uuid

from asset import  TangibleAsset, InventoryAsset
from player import Player

class GameMaster:
    ASSET_TYPES = {
        "tangible": {"class": TangibleAsset, "description": "固定資産"},
        "inventory": {"class": InventoryAsset, "description": "棚卸資産"}
    }
        
    def __init__(self, start_date="2024-01-01"):
        """ゲームマスターの初期化"""
        self.current_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.event_log = []
        self.asset_registry = {}  # 全資産の管理
        
    def construct_instance(self, asset_type, name, value, useful_life=None):
        """資産を生成しデータベースに登録"""
        asset_id = str(uuid.uuid4())

        if asset_type == "tangible":
            asset_instance = TangibleAsset(name, value, useful_life)
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
            if isinstance(asset, TangibleAsset) and asset.disposal_date is None:
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


def main():
    # プレイヤーを作成
    player1 = Player("プレイヤー1", initial_cash=5000)
    player2 = Player("プレイヤー2", initial_cash=3000)
    players = [player1, player2]

    # GameMaster の初期化
    game_master = GameMaster()

    # デフォルトで3か月進行
    print("\n--- 四半期進行 ---")
    game_master.advance_time(players=players)

    # 各プレイヤーの財務状況確認
    for player in players:
        print(f"\nプレイヤー {player.name} の財務状況:")
        player.ledger_manager.display_balance()
        player.ledger_manager.display_transaction_history()

    # 特定の日数を進行（例: 60日）
    print("\n--- 60日進行 ---")
    game_master.advance_time(days=60, players=players)

if __name__ == "__main__":
    main()

