from datetime import datetime

class Account:
    VALID_CATEGORIES = {"資産", "負債", "純資産", "収益", "費用"}

    def __init__(self, name, category):
        """会計勘定クラス"""
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"無効なカテゴリー: {category}. 有効なカテゴリーは {', '.join(self.VALID_CATEGORIES)} です。")
        self.name = name
        self.category = category  # 資産, 負債, 純資産, 収益, 費用
        self.balance = 0  # 純額

    def update(self, amount):
        """金額を更新 (正: 借方, 負: 貸方)"""
        self.balance += amount

    def net_balance(self):
        """純額を返す"""
        return self.balance


class Ledger:
    def __init__(self) -> dict:
        """勘定元帳クラス"""
        self._accounts = {}
        self._transactions = []  # 全トランザクション履歴
        self._initialize_essential_accounts()

    # 勘定科目の初期設定
    def _initialize_essential_accounts(self):
        essential_accounts = [
            ("現金", "資産"),
            ("固定資産", "資産"),
            ("減価償却費","費用"),
            ("減価償却累計額","資産"),
            ("固定資産売却益","収益"),
            ("固定資産売却損","費用"),
            ("売上高", "収益"),
            ("仕入","費用"),
            ("棚卸資産","資産"),
            ("売上原価", "費用"),
            ("借入金", "負債"),
            ("利益剰余金", "純資産"),
            ("資本金", "純資産")
        ]
        for name, category in essential_accounts:
            self.add_account(Account(name, category))

    def add_account(self, account):
        """新しい勘定を追加"""
        self._accounts[account.name] = account

    def _update_account(self, name, amount):
        """(内部使用) 指定された勘定を更新"""
        if name not in self._accounts:
            raise ValueError(f"勘定名： {name} が存在しません。")
        # 勘定の残高を更新
        self._accounts[name].update(amount)

    def execute_transaction(self, updates, timestamp = "ゲーム内時間", description=""):
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
            "timestamp": timestamp  # ゲーム上の時間を仮定
        }
        self._transactions.append(transaction)

    def get_balance_summary(self) -> dict:
        """財務状況を取得"""
        summary = {}
        for account in self._accounts.values():
            summary[account.name] = account.net_balance()

        # 残高合計の制約確認
        total_balance = sum(summary.values())
        if total_balance != 0:
            print("警告: 財務諸表の残高合計が0ではありません。")
        return summary

    def display_balance(self):
        """財務状況を表示(残高試算表の作成)"""
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
        summary = self.get_balance_summary()
    
        balance_sheet = {"資産": {}, "負債": {}, "純資産": {}}
        income_statement = {"収益": {}, "費用": {}}

        # summaryを各カテゴリーごとに振り分け
        for account in self._accounts.values():
            balance = summary[account.name]
            if account.category in balance_sheet:
                balance_sheet[account.category][account.name] = balance
            elif account.category in income_statement:
                income_statement[account.category][account.name] = balance

        # 貸借対照表の表示
        print("\n貸借対照表:")
        for category, accounts in balance_sheet.items():
            print(f"  {category}:")
            for name, balance in accounts.items():
                if balance > 0:
                    print(f"    {name}  : {balance}")
                elif balance == 0:
                    pass
                else:
                    print(f"    {name}  : ({-balance})")

        # 損益計算書の表示
        print("\n損益計算書:")
        total_revenue = sum(income_statement["収益"].values())
        total_expense = sum(income_statement["費用"].values())
        net_income = total_revenue + total_expense

        print("  収益:")
        for name, balance in income_statement["収益"].items():
            if balance == 0:
                pass
            else:
                print(f"    {name}: ({-balance})")

        print("  費用:")
        for name, balance in income_statement["費用"].items():
            if balance == 0:
                pass
            else:
                print(f"    {name}: {balance}")
                    
        print(f"\n  純損益: ({-net_income})")

    def _get_transaction_history(self):
        """トランザクション履歴を取得"""
        return [
            {
                "timestamp": tx["timestamp"],
                "updates": tx["updates"],
                "description": tx["description"]
            }
            for tx in self._transactions
        ]

    def display_transaction_history(self):
        """全トランザクション履歴(総勘定元帳)を表示"""
        print("\nTransaction History:")
        for tx in self._get_transaction_history():
            timestamp = tx["timestamp"]
            updates_str = ", ".join([f"{name}: {amount}" for name, amount in tx["updates"]])
            description = tx["description"] if tx["description"] else "No description"
            print(f"  [{timestamp}]")
            print(f"    仕訳: {updates_str}")
            print(f"    摘要: {description}")




def main():
    # サンプルコード
    ledger = Ledger()

    # 勘定の追加は初期化時に実行済み

    # 取引の実行
    try:
        ledger.execute_transaction([
            ("現金", 1000),
            ("資本金", -1000)
        ], description = "会社の設立")

        ledger.execute_transaction([
            ("現金", -200),
            ("固定資産", 200)
        ], description = "固定資産の取得")
        
        ledger.execute_transaction([
            ("仕入", 450),
            ("現金", -450)
        ], description = "商品の仕入")
        
        ledger.execute_transaction([
            ("現金", 500),
            ("売上高", -500)
        ], description = "売上の発生")

        ledger.execute_transaction([
            ("売上原価", 400),
            ("仕入", -450),
            ("棚卸資産", 50)
        ], description="商品の棚卸し")
        
        ledger.execute_transaction([
            ("減価償却費", 10),
            ("減価償却累計額", -10)
        ], description="減価償却の実行")
        

    except ValueError as e:
        print(f"エラー: {e}")

    # 仕訳の表示
    ledger.display_transaction_history()
    
    # 財務諸表を表示
    ledger.display_financial_statements()

if __name__ == "__main__":
    main()
