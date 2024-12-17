import asset
import ledger
import manager
import master

class Player:
    def __init__(self, name, game_master, initial_cash=5000):
        self.name = name
        self.game_master = game_master
        self.ledger_manager = ledger.Ledger()
        self.asset_manager = manager.AssetManager(game_master)
        self.cash_account = "現金"

        # 初期現金の設定
        self.ledger_manager.execute_transaction([
            (self.cash_account, initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    def aquire_building(self, name):
        self.game_master.
def main():
    # サンプルコード
    game_master = master.GameMaster()
    player1 = Player("player1",game_master)
    player2 = Player("player2",game_master)
    
    game_master.construct_instance("building", "building_1", value = 6000)
    
    
if __name__ == "__main__":
    main()




