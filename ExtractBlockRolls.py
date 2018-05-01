from bbrz_reader import extract_bbrz_dir, parse_raw_block_rolls
import argparse
from os import remove
from os.path import exists, isdir, isfile
from shutil import rmtree


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Takes a directory containing Bloodbowl 2 BBRZ replay files and extracts "
                                             "dice values from all block rolls.")
    parser.add_argument("-d", "--dir", type=str, required=True, help="Source directory containing 1 or more bbrz files")
    parser.add_argument("-o", "--out", type=str, required=True, help="Output file to save dice values")
    parser.add_argument("-f", action="store_true", help="Force overwrite of output file if it exists")
    args = parser.parse_args()
    in_dir = args.dir
    out_file = args.out
    force = args.f
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
        bbrz_reader = extract_bbrz_dir(in_dir)
        for bbrz in bbrz_reader:
            output.write(','.join(parse_raw_block_rolls(bbrz)))
            output.write('\n')
