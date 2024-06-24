#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from anemometer import anemometer
import argparse, os, sys, time

def arg_parser():
    """ parse aruguments """
    global ARGS

    parser = argparse.ArgumentParser(description='Retrieve recorded data from Bonvoisin digital hotwire anemometer')
    parser.add_argument(
        'outfile', nargs='?',
        help='filname to save to (optional)')
    parser.add_argument(
        '--overwrite', '-o', action='store_true',
        help='overwrite outfile if exists')

    ARGS = parser.parse_args()
    if ARGS.outfile and '.' not in ARGS.outfile:
        ARGS.outfile += '.csv'
    if ARGS.outfile:
        print("Wrtitng data to %s"%ARGS.outfile, file=sys.stderr)
        if os.path.exists(ARGS.outfile):
            if ARGS.overwrite:
                print("Existing file %s being overwritten."%ARGS.outfile, file=sys.stderr)
            else:
                print("Stop!", file=sys.stderr)
                print("%s eixsts but -o/--overwrite not spacified..."%ARGS.outfile, file=sys.stderr)
                sys.exit(-1)
        print(file=sys.stderr)

def main():
    with anemometer() as a:
        a.open_records()

        if ARGS.outfile:
            with open(ARGS.outfile, "w") as f:
                pass

        n = 1
        while True:
            res = a.get_a_record()
            if not res:
                break
            data, v1, v2, s = res
            sttng, v1u, v2u = a.format_setting(s, 1)
            print("%3d: %6g [%s] %6g [%s]"%(n, v1, v1u, v2, v2u) )
            if ARGS.outfile:
                with open(ARGS.outfile, "a") as f:
                    print('%3d,%6g,"%s",%6g,"%s"'%(n, v1, v1u, v2, v2u), file=f)
            n += 1

if __name__ == '__main__':
    arg_parser()
    main()
