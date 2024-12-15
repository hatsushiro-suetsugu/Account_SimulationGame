from datetime import datetime

class Account:
    VALID_CATEGORIES = {"資産", "負債", "純資産", "収益", "費用"}

    def __init__(self, name, category):
        """会計勘定クラス"""
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"無効なカテゴリー: {category}. 有効なカテゴリーは {', '.join(self.VALID_CATEGORIES)} です。")
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
        self._initialize_essential_accounts()

    def _initialize_essential_accounts(self):
        essential_accounts = [
            ("現金", "資産"),
            ("売上高", "収益"),
            ("売上原価", "費用"),
            ("借入金", "負債"),
            ("資本金", "純資産")
        ]
        for name, category in essential_accounts:
            self.add_account(Account(name, category))

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
            "timestamp": "仮のゲーム内時間"  # ゲーム上の時間を仮定
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

    def display_financial_statements(self):
        """貸借対照表と損益計算書を表示"""
        balance_sheet = {"資産": {}, "負債": {}, "純資産": {}}
        income_statement = {"収益": {}, "費用": {}}

        for account in self.accounts.values():
            if account.category in balance_sheet:
                balance_sheet[account.category][account.name] = account.net_balance()
            elif account.category in income_statement:
                income_statement[account.category][account.name] = account.net_balance()

        print("\n貸借対照表:")
        for category, accounts in balance_sheet.items():
            print(f"  {category}:")
            for name, balance in accounts.items():
                print(f"    {name}: {balance}")

        print("\n損益計算書:")
        total_revenue = sum(income_statement["収益"].values())
        total_expense = sum(income_statement["費用"].values())
        net_income = total_revenue - total_expense

        print("  収益:")
        for name, balance in income_statement["収益"].items():
            print(f"    {name}: {balance}")

        print("  費用:")
        for name, balance in income_statement["費用"].items():
            print(f"    {name}: {balance}")

        print(f"\n  純損益: {net_income}")

    def display_transaction_history(self):
        """全トランザクション履歴を表示"""
        print("\nTransaction History:")
        for tx in self.transactions:
            timestamp = tx["timestamp"]
            updates_str = ", ".join([f"{name}: {amount}" for name, amount in tx["updates"]])
            print(f"  [{timestamp}] Updates: {updates_str}, Description: {tx['description']}")


def main():
    # サンプルコード
    ledger = Ledger()

    # 勘定の追加は初期化時に実行済み

    # 取引の実行
    try:
        ledger.execute_transaction([
            ("現金", 1000),
            ("資本金", -1000)
        ], "Initial deposit")

        ledger.execute_transaction([
            ("現金", -200),
            ("固定資産", 200)
        ], "Office supplies")

    except ValueError as e:
        print(f"エラー: {e}")

    # 財務諸表を表示
    ledger.display_financial_statements()

if __name__ == "__main__":
    main()
