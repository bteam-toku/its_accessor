from abc import ABCMeta, abstractmethod

class AbstractItsAccessor(metaclass=ABCMeta):
    """Issue管理システムアクセス抽象クラス
    """
    def __init__(self) -> None:
        """コンストラクタ
        """
        pass

    def __del__(self) -> None:
        """デストラクタ
        """
        pass

    @abstractmethod
    def load_issues(self, project_name:str) -> any:
        """Issue管理データ一括読み取り

        Args:
            project_name (str): プロジェクト名
        """
        pass

    @abstractmethod
    def load_issue(self, issue_id:int) -> any:
        """Issue管理データ読み取り

        Args:
            issue_id (int): IssueID
        """
        pass

    @abstractmethod
    def update_issue(self, issue:any, issue_data:dict) -> bool:
        """Issue管理データ更新

        Args:
            issue (any): 更新対象のIssue
            issue_data (dict): 更新データ
        Returns:
            bool: 更新結果(True:成功、False:失敗)
        """
        pass

    @abstractmethod
    def create_issue(self, issue_data:dict) -> int:
        """Issue管理データ新規作成

        Args:
            issue_data (dict): 作成データ
        Returns:
            int: 作成したIssueID
        """
        pass
