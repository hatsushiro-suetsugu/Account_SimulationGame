import ledger

class Player:
    def __init__(self, name, initial_cash=1000):
        """プレイヤークラスの初期化"""
        self.name = name
        self.ledger = ledger.Ledger()
        self.cash_account = "現金"

        # 初期現金を設定
        self.ledger.execute_transaction([
            (self.cash_account, initial_cash),
            ("資本金", -initial_cash)
        ], description="Initial capital")

    def get_balance(self):
        """現在の財務状況を取得"""
        return self.ledger.get_balance_summary()

    def display_balance(self):
        """現在の財務状況を表示"""
        print(f"\n{self.name}の財務状況:")
        self.ledger.display_balance()

    def execute_transaction(self, updates, description=""):
        """取引を実行"""
        try:
            self.ledger.execute_transaction(updates, description)
            print(f"\n取引成功: {description}")
        except ValueError as e:
            print(f"\n取引失敗: {e}")

    def purchase_asset(self, asset_name, amount):
        """資産を購入"""
        print(f"\n{self.name}が{asset_name}を{amount}で購入します。")
        self.execute_transaction([
            (self.cash_account, -amount),
            (asset_name, amount)
        ], description=f"Purchase {asset_name}")

    def display_financial_statements(self):
        """財務諸表を表示"""
        print(f"\n{self.name}の財務諸表:")
        self.ledger.display_financial_statements()

    def display_transaction_history(self):
        """トランザクション履歴を表示"""
        print(f"\n{self.name}の取引履歴:")
        self.ledger.display_transaction_history()

# サンプル実行コード
def main():
    # プレイヤーを初期化
    player1 = Player("プレイヤー1", 5000)

    # 財務状況を表示
    player1.display_balance()

    # 資産を購入
    player1.purchase_asset("固定資産", 2000)

    # 財務諸表を表示
    player1.display_financial_statements()

    # トランザクション履歴を表示
    player1.display_transaction_history()

if __name__ == "__main__":
    main()

