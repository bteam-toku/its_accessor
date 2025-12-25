from .abstract_its_accessor import AbstractItsAccessor
from redminelib import Redmine
import redminelib.resources as Resource
from redminelib.resources import Issue
from redminelib.resultsets import ResourceSet
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BaseRedmineAccessor(AbstractItsAccessor):
    """Redmineアクセス抽象クラス
    """
    #
    # protected members
    #
    _redmine:Redmine = None # Redmineオブジェクト
    _project_name:str = '' # プロジェクト名
    _project_id:int = -1 # プロジェクトID
    _user_info:dict = {} # ユーザ情報
    _priority_info:dict = {} # 優先度情報辞書
    _version_info:dict = {} # バージョン情報辞書
    _issues:ResourceSet = None # Issue管理データ一覧
    _issue:Issue = None # Issue管理データ
    
    #
    # constructor/destructor
    #
    def __init__(self, project_name:str, url:str, key_string:str) -> None:
        """コンストラクタ
        """
        self._redmine = Redmine(url, key=key_string, requests={'verify': False})
        self._project_name = project_name
        self._get_user_info()
        self._get_priority_info()
        super().__init__()

    def __del__(self) -> None:
        """デストラクタ
        """
        pass

    #
    # public methods
    #
    def load_project(self) -> bool:
        """プロジェクト情報読み取り

        Args:
            project_name (str): プロジェクト名

        Returns:
            bool: 読み取り結果(True:成功、False:失敗)
        """
        try:
            self._project_id = self._get_project_id(self._project_name)
            self._get_version_info()
            return True
        except Exception as e:
            return False

    def load_issues(self) -> ResourceSet:
        """Issue管理データ一括読み取り

        Args:
            project_name (str): プロジェクト名
        """
        self._issues = self._redmine.issue.filter(project_id=self._project_name, status_id='*', include=['custom_fields'])
        return self._issues

    def load_issue(self, issue_id:int) -> Issue:
        """Issue管理データ読み取り

        Args:
            issue_id (int): IssueID
        """
        self._issue = self._redmine.issue.get(issue_id, include=['custom_fields'])
        return self._issue

    def update_issue(self, input_issue:Issue, input_data:dict) -> bool:
        """Issue管理データ更新
    
        Args:
            input_issue (Issue): 更新対象のIssue
            input_data: 更新データ

        Returns:
            bool: 更新結果(True:成功、False:失敗)
        """
        # プロジェクト識別子が不一致の場合は更新しない
        if hasattr(input_issue, 'project') and \
            self._project_id != input_issue.project.id:
            return False
            
        # IssueIDが不一致の場合は更新しない
        if input_data['#'] != '':
            if hasattr(input_issue, 'id') and \
               input_data['#'] != str(input_issue.id):
                print('Issue ID not match.', input_data['#'], input_issue.id) # for debug
                return False
        
        # Issueペイロード設定
        output_issue = self._set_issue_payload(input_issue, input_data)

        try:
            # Issue更新実行
            output_issue.save()
            return True
        except Exception as e:
            # Issue更新失敗
            print(f'Issue update error:', e) # for debug
            return False

    def create_issue(self, issue_data:dict) -> int:
        """Issue管理データ新規作成

        Args:
            issue_data (dict): 作成データ

        Returns:
            int: 作成したIssueID
        """
        # Issueペイロード設定
        new_issue = self._redmine.issue.new()
        output_issue = self._set_issue_payload(new_issue, issue_data)

        try:
            # Issue新規作成実行
            created_issue = output_issue.save()
            return created_issue.id
        except Exception as e:
            # Issue新規作成失敗
            print(f'Issue creation error:', e) # for debug
            return -1

    def latest_update(self) -> datetime:
        """Issue管理データ最終更新日付取得
        """
        issue_update = max((issue.updated_on for issue in self._issues), default=None)
        return issue_update
    
    def idtosubject_dict(self) -> dict:
        """IssueIDと題名のDictionary取得

        Returns:
            dict: IssueIDと題名のDictionary
        """
        id_subject_dict = {}
        for issue in self._issues:
            id_subject_dict.setdefault(int(issue.id), str(issue.subject))
        return id_subject_dict
    
    #
    # protected methods
    #
    def _get_project_id(self, project_name:str) -> int:
        """プロジェクトID取得

        Args:
            project_name (str): プロジェクト名

        Returns:
            int: プロジェクトID
        """
        try:
            all_projects = self._redmine.project.all(as_list=True)
            for project in all_projects:
                if project.identifier == project_name:
                    return project.id
            return -1
        except Exception as e:
            print(f'Project ID get error:', e) # for debug
            return -1
    
    def _get_user_info(self) -> None:
        """ユーザ情報取得
        """
        try:
            allusers = self._redmine.user.filter(status='*')
            for user in allusers:
                fullname = f'{user.lastname} {user.firstname}'
                self._user_info[fullname] = user.id
        except Exception as e:
                print(f'User info get error:', e) # for debug

    def _get_priority_info(self) -> None:
        """優先度情報取得
        """
        try:
            priorities = self._redmine.enumeration.filter(resource='issue_priorities')
            self._priority_info = {}
            for priority in priorities:
                self._priority_info[priority.name] = priority.id
        except Exception as e:
                print(f'Priority info get error:', e) # for debug

    def _get_version_info(self) -> None:
        """バージョン情報取得
        """
        versions = self._redmine.version.filter(project_id=self._project_id)
        self._version_info = {}
        for version in versions:
            self._version_info[version.name] = version.id
    
    def _has_custom_field(self, field_id:int=None, filed_value:str=None) -> bool:
        """カスタムフィールド存在確認

        Args:
            field_id (int): カスタムフィールドID
            filed_value (str): カスタムフィールド値

        Returns:
            bool: 存在確認結果(True:存在、False:不存在)
        """
        # カスタムフィールド一覧取得
        fields = {cf.id: cf for cf in self._redmine.custom_field.all()}
        # カスタムフィールドID確認
        cf = fields.get(field_id)
        if cf is None:
            print("cf is None =", field_id) # for debug
            return False
        # カスタムフィールドValue確認
        if hasattr(cf, "possible_values") and cf.possible_values is not None:
            if str(filed_value) not in [v['value'] for v in cf.possible_values]:
                return False
        # カスタムフィールド存在確認OK
        return True

    def _set_issue_payload(self, input_issue:Issue, input_data:dict) -> Issue:
        """Issue作成ペイロード設定

        Args:
            input_issue (Issue): 入力Issue情報
            input_data (dict): 入力データ

        Returns:
            Issue: Issue作成ペイロード
        """
        output_issue = input_issue

        # プロジェクト識別子
        if self._project_id != -1:
            output_issue.project_id = self._project_id
        # IssueID
        ## ReadmineではIssueIDは更新不可
        # トラッカー
        ## 具象化クラスで実装
        # 親IssueID
        if input_data['親チケット'] != '':
            output_issue.parent_id = input_data['親チケット']
        # ステータス
        ## 具象化クラスで実装
        # 題名
        if input_data['題名'] != '':
            output_issue.subject = input_data['題名']
        # 担当者
        if input_data['担当者'] != '':
            output_issue.assigned_to_id = self._user_info.get(input_data['担当者'])
        # 対象バージョン
        if input_data['対象バージョン'] != '':
            output_issue.fixed_version_id = self._version_info.get(input_data['対象バージョン'])
        # 開始日
        if input_data['開始日'] != '':
            output_issue.start_date = input_data['開始日']
        # 期限日
        if input_data['期日'] != '':
            output_issue.due_date = input_data['期日']
        # 予定時間
        if input_data['予定工数'] != '':
            output_issue.estimated_hours = input_data['予定工数']
        # 合計予定時間
        if input_data['合計予定工数'] != '':
            output_issue.total_estimated_hours = input_data['合計予定工数']
        # 作業時間
        ## Readmineでは作業時間は更新不可
        # 合計作業時間
        if input_data['合計作業時間'] != '':
            output_issue.total_spent_hours = input_data['合計作業時間']
        # 進捗率
        if input_data['進捗率'] != '':
            output_issue.done_ratio = input_data['進捗率']
        # 優先度
        if input_data['優先度'] != '':
            output_issue.priority_id = self._priority_info.get(input_data['優先度'])
        # 説明
        if input_data['説明'] != '':
            output_issue.description = input_data['説明']

        return output_issue
 

