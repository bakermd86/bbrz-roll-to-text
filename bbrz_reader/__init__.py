import zipfile
import itertools
from os import listdir
from os.path import join
from xml.etree import ElementTree
from enum import Enum


class BlockResults(Enum):
    AD = 0
    BD = 1
    P = 2
    DS = 3
    DD = 4


class NBlockResult:
    def __init__(self, results: list, player: str):
        self.results = results
        self.player = player
        self.die_count = len(results)
        self.results_names = list(map(lambda x: BlockResults(int(x)).name, self.results))

    def result_str(self):
        return self.player + ', ' + ', '.join(self.results_names) + '\n'


class CoachesData:
    def __init__(self, coach_home_name: str, coach_home_id: str, coach_away_name: str, coach_away_id: str):
        self.coach_map = {coach_home_id: coach_home_name, coach_away_id: coach_away_name}

    def get(self, coach_id):
        return self.coach_map.get(coach_id, "Unknown")


class ReplayReader:
    def __init__(self, dir_name: str):
        self.dir_name = dir_name
        self.player_map = {}
        while self.dir_name.endswith('\\'):
            self.dir_name = self.dir_name[:-1]

    def extract_bbrz_dir(self):
        bbrz_files = list(filter(lambda x: x.endswith('.bbrz'), listdir(self.dir_name)))
        for filename in bbrz_files:
            yield from self.extract_bbrz(join(self.dir_name, filename))

    @staticmethod
    def extract_bbrz(filename: str):
        with zipfile.ZipFile(filename, "r", compression=zipfile.ZIP_DEFLATED) as zipped_bbrz:
            unzipped_replays = list(map(lambda x: zipped_bbrz.open(x, "r"), zipped_bbrz.namelist()))
            return unzipped_replays

    @staticmethod
    def parse_team_info(replay_steps: list):
        game_finished_info = ReplayReader.walk_tree_list(replay_steps, 'RulesEventGameFinished')
        match_result = ReplayReader.walk_tree_list(game_finished_info, 'MatchResult')
        coaches_results = ReplayReader.walk_tree_list(match_result, 'CoachResults')

        row_result = ReplayReader.walk_tree_list(match_result, 'Row')[0]
        id_coach_home = row_result.find('IdCoachHome').text
        id_coach_away = row_result.find('IdCoachAway').text
        name_coach_home = row_result.find('CoachHomeName').text
        name_coach_away = row_result.find('CoachAwayName').text
        coach_data = CoachesData(name_coach_home, id_coach_home, name_coach_away, id_coach_away)

        coach_results = ReplayReader.walk_tree_list(coaches_results, 'CoachResult')
        player_map = {}
        for coach_result in coach_results:
            coach_id = coach_result.find("IdCoach").text
            coach_name = coach_data.get(coach_id)
            player_results = coach_result.find("TeamResult").find("PlayerResults").findall("PlayerResult")
            for player in player_results:
                player_id = player.find("PlayerData").find("Id").text
                player_map[player_id] = coach_name
        return player_map

    def parse_block_roll_info(self, board_action: ElementTree.Element):
        try:
            player_id = board_action.find("PlayerId").text
            block_action_results = list(filter(self.is_block_roll, self.walk_tree_list(board_action.findall("Results"),
                                                                                       "BoardActionResult")))
            list_dices = self.walk_tree_list(self.walk_tree_list(block_action_results, "CoachChoices"), "ListDices")
            return list(map(lambda x: NBlockResult(self.clean_block_dice_list(x.text), self.player_map.get(player_id)), list_dices))
        except AttributeError:
            return

    def parse_raw_block_rolls(self, unzipped_bbrz: zipfile.ZipExtFile):
        bbr_doc = ElementTree.parse(unzipped_bbrz).getroot()
        replay_steps = bbr_doc.findall('ReplayStep')
        self.player_map = self.parse_team_info(replay_steps)

        board_actions = self.walk_tree_list(replay_steps, 'RulesEventBoardAction')
        block_actions = [result for result in list(map(self.parse_block_roll_info, board_actions)) if result]
        block_results = list(itertools.chain.from_iterable(block_actions))
        return list(map(lambda x: x.result_str(), block_results))
        # results = self.walk_tree_list(board_actions, 'Results')
        # action_results = self.walk_tree_list(results, 'BoardActionResult')
        # block_rolls = list(filter(self.is_block_roll, action_results))
        # coach_choices = self.walk_tree_list(block_rolls, 'CoachChoices')
        # list_dices = self.walk_tree_list(coach_choices, 'ListDices')
        #
        #
        # # list(map(lambda x: print(x.result_str()), test_objs))
        # return list(itertools.chain.from_iterable(list(map(lambda x: self.clean_block_dice_list(x.text), list_dices))))

    @staticmethod
    def clean_block_dice_list(dice_str: str):
        res = dice_str.strip('(').rstrip(')').split(',')
        return res[0:int(len(res) / 2)]

    @staticmethod
    def is_block_roll(elem: ElementTree.Element):
        try:
            res = elem.find("RollType").text == '5' and elem.find("ResultType").text == '2'
        except AttributeError:
            res = False
        return res

    @staticmethod
    def walk_tree_list(tree_list: list, step_text: str):
        return list(itertools.chain.from_iterable([res for res in list(map(lambda x: x.findall(step_text), tree_list)) if res]))
