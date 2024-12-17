import unittest
from manager import AssetManager, TangibleAssetManager, InventoryManager
from ledger import Ledger, Account
from player import Player
from master import GameMaster

class TestManager(unittest.TestCase):
    def setUp(self):
        self.asset_manager = AssetManager()
        self.tangible_manager = TangibleAssetManager()
        self.inventory_manager = InventoryManager()

    def test_acquire_asset(self):
        asset = self.asset_manager.acquire_asset("TestAsset", 1000, "2024-01-01", "TestOwner")
        self.assertEqual(asset.name, "TestAsset")
        self.assertEqual(asset.value, 1000)

    def test_tangible_asset_disposal(self):
        asset = self.tangible_manager.acquire_asset("Building", 5000, "2024-01-01", "Owner", 10)
        result = self.tangible_manager.dispose_asset("Building", "2024-06-01")
        self.assertEqual(result["asset"].name, "Building")

    def test_inventory_operations(self):
        inventory = self.inventory_manager.acquire_inventory("Item", 50, 10, "Owner")
        self.assertEqual(inventory.name, "Item")
        self.inventory_manager.update_inventory_price("Item", 60)
        result = self.inventory_manager.sell_inventory("Item", 5, 70)
        self.assertEqual(result["revenue"], 350)

class TestLedger(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()

    def test_transaction_execution(self):
        self.ledger.execute_transaction([
            ("現金", 1000),
            ("資本金", -1000)
        ], "Initial capital")
        balance = self.ledger._get_balance_summary()
        self.assertEqual(balance["現金"], 1000)

    def test_balance_sheet(self):
        self.ledger.execute_transaction([
            ("現金", 1000),
            ("資本金", -1000)
        ])
        summary = self.ledger._get_balance_summary()
        self.assertIn("現金", summary)
        self.assertEqual(summary["現金"], 1000)

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player("TestPlayer", initial_cash=5000)

    def test_acquire_tangible_asset(self):
        self.player.acquire_tangible_asset("Machine", 2000, "2024-01-01", useful_life=5)
        balance = self.player.ledger_manager._get_balance_summary()
        self.assertEqual(balance["現金"], 3000)
        self.assertEqual(balance["固定資産"], 2000)

    def test_sell_inventory(self):
        self.player.acquire_inventory("Widget", 20, 10)
        self.player.sell_inventory("Widget", 5, 30)
        balance = self.player.ledger_manager._get_balance_summary()
        self.assertIn("売上高", balance)

class TestGameMaster(unittest.TestCase):
    def setUp(self):
        self.game_master = GameMaster("2024-01-01")

    def test_time_advance(self):
        self.game_master.advance_time(days=10)
        self.assertEqual(self.game_master.get_current_date(), "2024-01-11")

    def test_event_logging(self):
        self.game_master.log_event("Test Event")
        self.assertEqual(len(self.game_master.event_log), 1)
        self.assertEqual(self.game_master.event_log[0]["event"], "Test Event")

if __name__ == "__main__":
    unittest.main()
