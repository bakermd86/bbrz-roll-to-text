from bbrz_reader import ReplayReader
import argparse
from os import remove
from os.path import exists, isdir, isfile
from shutil import rmtree
from collections import defaultdict


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Takes a directory containing Bloodbowl 2 BBRZ replay files and extracts "
                                             "dice values from all block rolls.")
    parser.add_argument("-d", "--dir", type=str, required=True, help="Source directory containing 1 or more bbrz files")
    parser.add_argument("-o", "--out", type=str, required=True, help="Output file to save dice values")
    parser.add_argument("-f", action="store_true", help="Force overwrite of output file if it exists")
    parser.add_argument("-s", action="store_true", help="Sort by replay file, default is to merge into a single CSV list")
    parser.add_argument("-r", action="store_true", help="Raw dice results per player (default displays each roll discreetly)")
    args = parser.parse_args()
    in_dir = args.dir
    out_file = args.out
    force = args.f
    sort_replay = args.s
    raw = args.r
    if raw and sort_replay:
        print("Raw mode and sort by replay mode are not mutually compatible, choose only one.")
        exit(3)
    if exists(out_file):
        if not force:
            print("Output file %s already exists, specify a different output file." % out_file)
            exit(1)
        else:
            if isfile(out_file):
                remove(out_file)
            elif isdir(out_file):
                rmtree(out_file)
    if not exists(in_dir) or not isdir(in_dir):
        print("Input directory %s not found, specify a different input directory" % in_dir)
        exit(2)
    with open(out_file, "w") as output:
        rolls = []
        player_map = defaultdict(list)
        bbrz_reader = ReplayReader(in_dir)
        for bbrz in bbrz_reader.extract_bbrz_dir():
            if sort_replay:
                output.write(bbrz.name+'\n----------------------------------------------\n')
                output.write(''.join(sorted(bbrz_reader.parse_raw_block_rolls(bbrz))))
                output.write('----------------------------------------------\n')
            else:
                rolls += sorted(bbrz_reader.parse_raw_block_rolls(bbrz))
        if raw:
            results_by_player = map(lambda x: x.rstrip('\n').split(', '), rolls)
            for player, *roll in results_by_player:
                player_map[player] += roll
            for player, rolls in player_map.items():
                output.write(player + ', ' + ', '.join(rolls) + '\n')
        elif not sort_replay:
            output.writelines(sorted(rolls))
