from datetime import datetime
import json

class Account:
    VALID_CATEGORIES = ["資産", "負債", "純資産", "収益", "費用"]

    def __init__(self, name, category, sub_category=None):
        """会計勘定クラス"""
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"無効なカテゴリー: {category}. 有効なカテゴリーは {', '.join(self.VALID_CATEGORIES)} です。")
        self.name = name
        self.category = category  # 資産, 負債, 純資産, 収益, 費用
        self.sub_category = sub_category # (BS)流動/固定、(PL)営業/非営業
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

    # 勘定科目の初期設定:essential_account.jsonで管理(12/17)
    def _initialize_essential_accounts(self, file_path = "essential_account.json"):
        with open(file_path, "r", encoding="UTF-8") as file:
            data = json.load(file)
            accounts = data["essential_accounts"]

        for account in accounts:
            name = account["name"]
            category = account["category"]
            sub_category = account["sub_category"]
            
            self.add_account(Account(name, category, sub_category))

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

    def _get_balance_summary(self) -> dict:
        """財務状況を取得し、純損益を計算して利益剰余金に反映(決算整理)"""
        summary = {}
        total_revenue = 0
        total_expense = 0

        # 勘定残高を集計し、収益と費用を分けて計算
        for account in self._accounts.values():
            summary[account.name] = account.net_balance()
            if account.category == "収益":
                total_revenue += account.net_balance()
            elif account.category == "費用":
                total_expense += account.net_balance()
                
        # 残高合計の制約確認
        total_balance = sum(summary.values())
        if total_balance != 0:
            print("警告: 財務諸表の残高合計が0ではありません。")

        # 純損益を計算
        net_income = total_revenue + total_expense  # 費用は正値なので足す

        # 利益剰余金に純損益を反映
        if net_income != 0:
            self._update_account("利益剰余金", net_income)
            
        # 純損益を含めたデータを返す
        summary["純損益"] = -net_income
        return summary

    def display_credit_and_debit(self, name, balance):
        if balance > 0:
                print(f"{name}: {balance}")
        elif balance < 0:
            print(f"{name}: ({-balance})")
        else:
            print(f"{name}: 0")
    
    def display_balance(self):
        """財務状況を表示(残高試算表の作成)"""
        print("\n\n残高試算表:\n")
        summary = self._get_balance_summary()
        for name, balance in summary.items():
            if balance > 0:
                print(f"{name}: {balance}")
            elif balance < 0:
                print(f"{name}: ({-balance})")
            else:
                print(f"{name}: 0")
            
    def display_financial_statements(self):
        """貸借対照表と損益計算書を表示"""
        summary = self._get_balance_summary()

        # 表示用の辞書を初期化
        statements = {
            "貸借対照表": {
                "資産": {"流動資産": {}, "固定資産": {}, "繰延資産": {}},
                "負債": {"流動負債": {}, "固定負債": {}},
                "純資産": {"株主資本": {}, "評価・換算差額": {}}
            },
            "損益計算書": {
                "収益": {"営業収益": {}, "営業外収益": {}},
                "費用": {"営業費用": {}, "営業外費用": {}}
            }
        }

        # 勘定科目をループして各カテゴリー・サブカテゴリーに振り分け
        for account in self._accounts.values():
            balance = summary.get(account.name, 0)
            category = account.category

            # 貸借対照表 (BS) の処理
            if category in ["資産", "負債", "純資産"]:
                statement = statements["貸借対照表"]
                statement[category][account.sub_category][account.name] = balance

            # 損益計算書 (PL) の処理
            elif category in ["収益", "費用"]:
                statement = statements["損益計算書"]
                statement[category][account.sub_category][account.name] = balance

        # 貸借対照表の表示
        print("\n=== 貸借対照表 ===")
        for category, subcategories in statements["貸借対照表"].items():
            print(f"{category}:")
            for sub_category, accounts in subcategories.items():
                print(f"  {sub_category}:")
                for name, balance in accounts.items():
                    if balance > 0:
                        print(f"        {name}: {balance}")
                    elif balance < 0:
                        print(f"        {name}: ({-balance})")
                    else:
                        pass

        # 損益計算書の表示
        print("\n=== 損益計算書 ===")
        for category, subcategories in statements["損益計算書"].items():
            print(f"{category}:")
            for sub_category, accounts in subcategories.items():
                print(f"  {sub_category}:")
                for name, balance in accounts.items():
                    if balance > 0:
                        print(f"        {name}: {balance}")
                    elif balance < 0:
                        print(f"        {name}: ({-balance})")
                    else:
                        pass
        # 純損益の表示
        print(f"\n純損益: {summary['純損益']:,}")


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
            print("\n\n取引一覧:\n")
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
            ("建物", 200)
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
    
    # 残高試算表の表示
    ledger.display_balance()
    
    # 財務諸表を表示
    ledger.display_financial_statements()

if __name__ == "__main__":
    main()
