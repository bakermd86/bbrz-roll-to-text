import zipfile
import itertools
from os import listdir
from os.path import join
from xml.etree import ElementTree


def extract_bbrz_dir(dir_name: str):
    while dir_name.endswith('\\'):
        dir_name = dir_name[:-1]
    bbrz_files = list(filter(lambda x: x.endswith('.bbrz'), listdir(dir_name)))
    for filename in bbrz_files:
        yield from extract_bbrz(join(dir_name, filename))


def extract_bbrz(filename: str):
    with zipfile.ZipFile(filename, "r", compression=zipfile.ZIP_DEFLATED) as zipped_bbrz:
        unzipped_replays = list(map(lambda x: zipped_bbrz.open(x, "r"), zipped_bbrz.namelist()))
        return unzipped_replays


def parse_raw_block_rolls(unzipped_bbrz: zipfile.ZipExtFile):
    bbr_doc = ElementTree.parse(unzipped_bbrz).getroot()
    replay_steps = bbr_doc.findall('ReplayStep')
    board_actions = walk_tree_list(replay_steps, 'RulesEventBoardAction')
    results = walk_tree_list(board_actions, 'Results')
    action_results = walk_tree_list(results, 'BoardActionResult')
    block_rolls = list(filter(is_block_roll, action_results))
    coach_check_thing = list(filter(is_block_coach_test, action_results))

    coach_choices = walk_tree_list(block_rolls, 'CoachChoices')
    list_dices = walk_tree_list(coach_choices, 'ListDices')
    # list(map(lambda x: print(x.text), list_dices))
    all_rolls = list(itertools.chain.from_iterable(list(map(lambda x: clean_block_dice_list(x.text), list_dices))))
    # print(len([val for val in all_rolls if val == '0']))

    coach_choises_test2 = walk_tree_list(coach_check_thing, 'CoachChoices')
    list_dices_test_2 = walk_tree_list(coach_choises_test2, 'ListDices')
    choach_confirms = list(itertools.chain.from_iterable(list(map(lambda x: x.text.strip('(').rstrip(')').split(','), list_dices_test_2))))
    print(all_rolls)
    print(choach_confirms)


def clean_block_dice_list(dice_str: str):

    # return dice_str.strip('(').rstrip(')').split(',')[1::2]
    res = dice_str.strip('(').rstrip(')').split(',')
    ref = int(len(res) / 2)
    return res[ref:ref*-1]
    # return res[0:int(len(res)/2)]


def is_block_roll(elem: ElementTree.Element):
    try:
        res = elem.find("RollType").text == '5' and elem.find("ResultType").text == '2'
    except AttributeError:
        res = False
    return res


def is_block_coach_test(elem: ElementTree.Element):
    try:
        res = elem.find("RollType").text == '5' and elem.find("IsOrderCompleted").text == '1'
    except AttributeError:
        res = False
    return res


def walk_tree_list(tree_list: list, step_text: str):
    return list(itertools.chain.from_iterable([res for res in list(map(lambda x: x.findall(step_text), tree_list)) if res]))


if __name__ == '__main__':
    test_dir = r'E:\HomeShare'
    bbrz1 = r'E:\HomeShare\Coach-232104-48b70fb5b965a6f02f536d3da958314b_2018-04-17_01_37_40.bbrz'
    bbrz2 = r'E:\HomeShare\Coach-233327-25f1d6a8cda4ade777d762e7804540ab_2018-05-01_01_44_13.bbrz'
    extractor = extract_bbrz_dir(test_dir)
    for file in extractor:
        parse_raw_block_rolls(file)
