#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from anemometer import anemometer
import argparse, os, sys, time

def arg_parser():
    """ parse aruguments """
    global ARGS

    parser = argparse.ArgumentParser(description='Retrieve realtime data from Bonvision digital hotwire anemometer')
    parser.add_argument(
        'outfile', nargs='?',
        help='filname to save to (optional)')
    parser.add_argument(
        '--overwrite', '-o', action='store_true',
        help='overwrite outfile if exists')
    parser.add_argument(
        '--number', '-n', type=int, default=1,
        help='number of samples to retrieve (default=1, 0 for infinity)')
    parser.add_argument(
        '--interval', '-i', type=int, default=1,
        help='sampling interval in sec (default=1)')

    ARGS = parser.parse_args()
    if ARGS.outfile and '.' not in ARGS.outfile:
        ARGS.outfile += '.csv'

    last_msg = ""
    if ARGS.outfile:
        last_msg = "\n"
        print("Wrtitng data to %s"%ARGS.outfile, file=sys.stderr)
        if os.path.exists(ARGS.outfile):
            if ARGS.overwrite:
                print("Existing file %s being overwritten."%ARGS.outfile, file=sys.stderr)
            else:
                print("Stop!", file=sys.stderr)
                print("%s eixsts but -o/--overwrite not spacified..."%ARGS.outfile, file=sys.stderr)
                sys.exit(-1)
    if not ARGS.number:
        last_msg = "\n"
        print("Infinity number specified. Use Ctrl+C to stop.", file=sys.stderr)
    print(last_msg, end="", file=sys.stderr)

def main():
    num = 0
    chkpnt = time.time()

    with anemometer() as a:

        if ARGS.outfile:
            with open(ARGS.outfile, "w") as f:
                pass

        while True:
            data, v1, v2, s = a.get_current()
            sttng, v1u, v2u = a.format_setting(s, 1)
            ts = time.strftime("%Y/%m/%d %H:%M:%S")
            print("%s %6g %s %6g %s"%(ts, v1, v1u, v2, v2u) )
            if ARGS.outfile:
                with open(ARGS.outfile, "a") as f:
                    print('"%s",%6g,"%s",%6g,"%s"'%(ts, v1, v1u, v2, v2u), file=f)

            try:
                num += 1
                if ARGS.number and num >= ARGS.number:
                    break
                chkpnt += ARGS.interval
                while True:
                    if time.time() >= chkpnt:
                        break
                    time.sleep(0.05)
            except KeyboardInterrupt:
                print("Ctrl+C", file=sys.stderr)
                break

if __name__ == '__main__':
    arg_parser()
    main()
