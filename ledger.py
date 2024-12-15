from datetime import datetime

class Account:
    def __init__(self, name, category):
        """会計勘定クラス"""
        self.name = name
        self.category = category  # 資産, 負債, 純資産, 収益, 費用
        self.balance = 0.0  # 純額

    def update(self, amount):
        """金額を更新 (正: 借方, 負: 貸方)"""
        self.balance += amount

    def net_balance(self):
        """純額を返す"""
        return self.balance


class Ledger:
    def __init__(self) -> dict:
        """勘定元帳クラス"""
        self.accounts = {}
        self.transactions = []  # 全トランザクション履歴

    def add_account(self, account):
        """新しい勘定を追加"""
        self.accounts[account.name] = account

    def _update_account(self, name, amount):
        """(内部使用) 指定された勘定を更新"""
        if name not in self.accounts:
            raise ValueError(f"勘定名： {name} が存在しません。")
        # 勘定の残高を更新
        self.accounts[name].update(amount)

    def execute_transaction(self, updates, description=""): 
        """取引を実行し、制約を確認"""
        if not isinstance(updates, list) or len(updates) < 2:
            raise ValueError("取引には2つ以上の更新が必要です。")

        total_amount = sum(update[1] for update in updates)
        if total_amount != 0:
            raise ValueError("取引の合計金額は0である必要があります。")

        # トランザクションを適用
        for name, amount in updates:
            self._update_account(name, amount)

        # トランザクション履歴を記録
        transaction = {
            "updates": updates,
            "description": description,
            "timestamp": datetime.now()
        }
        self.transactions.append(transaction)

    def get_balance_summary(self):
        """財務状況を取得"""
        summary = {}
        for account in self.accounts.values():
            summary[account.name] = account.net_balance()

        # 残高合計の制約確認
        total_balance = sum(summary.values())
        if total_balance != 0:
            print("警告: 財務諸表の残高合計が0ではありません。")
        return summary

    def display_balance(self):
        """財務状況を表示"""
        summary = self.get_balance_summary()
        for name, balance in summary.items():
            if balance > 0:
                print(f"{name} (Debit): {balance}")
            elif balance < 0:
                print(f"{name} (Credit): {-balance}")
            else:
                print(f"{name}: 0")

    def display_transaction_history(self):
        """全トランザクション履歴を表示"""
        print("\nTransaction History:")
        for tx in self.transactions:
            timestamp = tx["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            updates_str = ", ".join([f"{name}: {amount}" for name, amount in tx["updates"]])
            print(f"  [{timestamp}] Updates: {updates_str}, Description: {tx['description']}")


def main():
    # サンプルコード
    ledger = Ledger()

    # 勘定の追加
    cash_account = Account("現金", "資産")
    ledger.add_account(cash_account)

    revenue_account = Account("売上", "収益")
    ledger.add_account(revenue_account)

    expense_account = Account("売上原価", "費用")
    ledger.add_account(expense_account)

    # 取引の実行
    try:
        ledger.execute_transaction([
            ("現金", 1000),
            ("売上", -1000)
        ], "Initial deposit")

        ledger.execute_transaction([
            ("現金", -200),
            ("売上原価", 200)
        ], "Office supplies")

    except ValueError as e:
        print(f"エラー: {e}")

    # 残高と履歴を表示
    ledger.display_balance()
    ledger.display_transaction_history()

if __name__ == "__main__":
    main()

