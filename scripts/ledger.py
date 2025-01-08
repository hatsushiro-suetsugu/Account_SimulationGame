"""会計帳簿システム"""
import json
import openpyxl
import pandas as pd
import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

class Account(Base):
    """勘定科目テーブル"""
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    statement = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    sub_category = Column(String(255))
    balance = Column(Integer, default=0)
    
    def update(self, amount):
        """勘定の更新"""
        self.balance += amount

    def clear(self):
        """勘定の残高を0にリセット"""
        self.balance = 0

class Transaction(Base):
    """取引テーブル"""
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    description = Column(String)
    updates = relationship("TransactionUpdate", back_populates="transaction")

class TransactionUpdate(Base):
    """取引更新テーブル"""
    __tablename__ = "transaction_updates"
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    account_name = Column(String, ForeignKey('accounts.name'), nullable=False)
    amount = Column(Float, nullable=False)
    transaction = relationship("Transaction", back_populates="updates")

class Ledger:
    """勘定元帳クラス"""
    FILE_PATH = "database"
    
    def __init__(self, db_path="ledger.db", current_date="ゲーム内時間"):
        """勘定元帳の初期化"""
        self.current_date = current_date
        self._transactions = []
        # データベースの初期化
        self.engine = create_engine(f"sqlite:///{self.FILE_PATH}/{db_path}")
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
        # 勘定科目の初期設定
        self._initialize_essential_accounts(file_path="database/essential_account.json")

    def _initialize_essential_accounts(self, file_path):
        """勘定科目の初期設定:essential_account.jsonで管理"""
        with open(file_path, "r", encoding="UTF-8") as file:
            data = json.load(file)
            accounts = data["essential_accounts"]

        for account in accounts:
            existing_account = self.session.query(Account).filter_by(name=account["name"]).first()
            if existing_account:
                continue  # 既に存在する場合はスキップ
            new_account = Account(
                name=account["name"],
                statement=account["statement"],
                category=account["category"],
                sub_category=account.get("sub_category", ""),
                balance=account.get("balance", 0.0)
            )
            self.session.add(new_account)
        self.session.commit()
        
    def add_account(self, name:str, statement:str, category:str, sub_category=None, balance=0):
        """新しい勘定を追加"""
        new_account = Account(
            name=name,
            statement=statement,
            category=category,
            sub_category=sub_category,
            balance=balance
        )
        self.session.add(new_account)
        self.session.commit()

    def _update_account(self, name, amount):
        """(内部使用) 指定された勘定を更新"""
        account = self.session.query(Account).filter_by(name=name).first()
        if not account:
            raise ValueError(f"勘定名： {name} が存在しません。")
        account.update(amount)
        self.session.commit()

    def _clear_account(self, name):
        account = self.session.query(Account).filter_by(name=name).first()
        if not account:
            raise ValueError(f"勘定名： {name} が存在しません。")
        account.clear()
        self.session.commit()

    def _clear_transactions(self):
        self._transactions = []

    def reset_ledger(self):
        """全勘定科目の残高を0にリセット"""
        accounts = self.session.query(Account).all()
        for account in accounts:
            account.clear()
        self.session.commit()

    def execute_transaction(self, updates, description=""):
        """取引を実行し、制約を確認"""
        if not isinstance(updates, list) or len(updates) < 2:
            raise ValueError(f"取引には2つ以上の更新が必要です。{updates}")

        total_amount = sum(update[1] for update in updates)
        if total_amount != 0:
            raise ValueError("取引の合計金額は0である必要があります。")

        # トランザクションを適用
        for name, amount in updates:
            self._update_account(name, amount)

        # トランザクション履歴を記録
        transaction = Transaction(
            timestamp=datetime.now(),
            description=description
        )
        self.session.add(transaction)
        self.session.commit()

        for name, amount in updates:
            transaction_update = TransactionUpdate(
                transaction_id=transaction.id,
                account_name=name,
                amount=amount
            )
            self.session.add(transaction_update)

        self.session.commit()

    def execute_settlement(self) -> dict:
        """
        (決算整理)
        剰余金の計算
        帳簿の閉鎖：Ledgerの初期化
        """
        summary, total_revenue, total_expense = self._get_trial_balance()

        # 当期純利益を計算
        net_income = total_revenue + total_expense  # 費用は正値なので足す
        
        self._update_account("利益剰余金", net_income)
        summary["当期純利益"] = -net_income
        
        # 帳簿の閉鎖 -> PLの初期化
        accounts = self.session.query(Account).all()
        for account in accounts:
            if account.statement == "損益計算書":
                self._clear_account(account.name)
        return summary
    
    def _get_trial_balance(self) -> dict:
        """残高試算表の作成"""
        summary = {}
        total_revenue = 0
        total_expense = 0
        
        # 勘定残高を集計し、収益と費用を分けて計算
        accounts = self.session.query(Account).all()
        for account in accounts:
            summary[account.name] = account.balance
            if account.category == "収益":
                total_revenue += account.balance
            elif account.category == "費用":
                total_expense += account.balance
                
        # 残高合計の制約確認
        total_balance = sum(summary.values())
        if total_balance != 0:
            print("警告: 財務諸表の残高合計が0ではありません。")
            
        return summary, total_revenue, total_expense
    
    def display_trial_balance(self, summary: dict):
        """財務状況を表示(残高試算表の作成)"""
        summary = self.execute_settlement()
        print("\n\n残高試算表:\n")
        for name, balance in summary.items():
            if balance > 0:
                print(f"{name}: {balance:,}")
            elif balance < 0:
                print(f"{name}: ({-balance:,})")
            else:
                print(f"{name}: 0")
            
    def _get_financial_statements(self, summary:dict) -> dict:
        """貸借対照表と損益計算書を作成"""
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
        accounts = self.session.query(Account).all()
        for account in accounts:
            balance = summary.get(account.name, 0)
            category = account.category

            if category in ["資産", "負債", "純資産"]:
                statement = statements["貸借対照表"]
                statement[category][account.sub_category][account.name] = balance

            elif category in ["収益", "費用"]:
                statement = statements["損益計算書"]
                statement[category][account.sub_category][account.name] = balance
                
        return statements

    def display_financial_statements(self, summary:dict):
        """貸借対照表と損益計算書を表示"""
        statements = self._get_financial_statements(summary)
         
        # 貸借対照表の表示
        print("\n=== 貸借対照表 ===")
        for category, subcategories in statements["貸借対照表"].items():
            print(f"{category}:")
            for sub_category, accounts in subcategories.items():
                print(f"  {sub_category}:")
                for name, balance in accounts.items():
                    if balance > 0:
                        print(f"        {name}: {balance:,}")
                    elif balance < 0:
                        print(f"        {name}: ({-balance:,})")
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
                        print(f"        {name}: {balance:,}")
                    elif balance < 0:
                        print(f"        {name}: ({-balance:,})")
                    else:
                        pass
        # 当期純利益の表示
        print(f"\n当期純利益: {summary['当期純利益']:,}")

    def export_financial_statements_to_excel(self, summary, file_path):
        """財務諸表をExcelファイルにエクスポート"""
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        statements = self._get_financial_statements(summary)
        
        with pd.ExcelWriter(file_path) as writer:
            # 貸借対照表と損益計算書をDataFrameに変換して書き込む
            balance_sheet = pd.DataFrame(statements["貸借対照表"])
            income_statement = pd.DataFrame(statements["損益計算書"])
            balance_sheet.to_excel(writer, sheet_name="貸借対照表")
            income_statement.to_excel(writer, sheet_name="損益計算書")

    def _get_transaction_history(self):
        """トランザクション履歴を取得"""
        transactions = self.session.query(Transaction).all()
        history = []
        for tx in transactions:
            updates = [(update.account_name, update.amount) for update in tx.updates]
            history.append({
                "timestamp": tx.timestamp,
                "updates": updates,
                "description": tx.description
            })
        return history
        
    def display_transaction_history(self):
        """全トランザクション履歴(総勘定元帳)を表示"""
        print("\n\n取引一覧:\n")
        for tx in self._get_transaction_history():
            timestamp = tx["timestamp"]
            updates_str = ", ".join([f"{name}: {amount:,}" for name, amount in tx["updates"]])
            description = tx["description"] if tx["description"] else "No description"
            print(f"  [{timestamp}]")
            print(f"    仕訳: {updates_str}")
            print(f"    摘要: {description}")

def main():
    # サンプルコード
    ledger = Ledger(db_path="sample_ledger.sqlite3", current_date="2021-01-01")

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
        print(f"エラー(第1期): {e}")
    
    # 第1期の終了
    print("----第1期が終了しました！----")
    end_1 = ledger.execute_settlement() 
    
    # 仕訳の表示
    ledger.display_transaction_history()
    
    # 残高試算表の表示
    ledger.display_trial_balance(end_1)
        
    # 財務諸表を表示
    ledger.display_financial_statements(end_1)
    ledger.export_financial_statements_to_excel(end_1, "output/financial_statements1.xlsx")
    
    try:    
        ledger.execute_transaction([
            ("仕入", 600),
            ("現金", -600)
        ], description = "商品の仕入")
        
        ledger.execute_transaction([
            ("現金", 750),
            ("売上高", -750)
        ], description = "売上の発生")

        ledger.execute_transaction([
            ("売上原価", 600),
            ("仕入", -600),
            ("棚卸資産", 0)
        ], description="商品の棚卸し")
         
        ledger.execute_transaction([
            ("現金", 210),
            ("建物", -200),
            ("減価償却累計額", 10),
            ("固定資産売却益", -20)
        ], description="建物の売却")
        
    except ValueError as e:
        print(f"エラー(第2期): {e}")
    
    # 第2期が終了
    print("----第2期が終了しました！----")
    end_2 = ledger.execute_settlement()
    
    # 仕訳の表示
    ledger.display_transaction_history()
    
    # 残高試算表の表示
    ledger.display_trial_balance(end_2)
        
    # 財務諸表を表示
    ledger.display_financial_statements(end_2)
    ledger.export_financial_statements_to_excel(end_2, "output/financial_statements2.xlsx")

if __name__ == "__main__":
    main()
