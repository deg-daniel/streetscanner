import argparse
import asyncio
import os
import sys
from street_scanner import StreetScanner

async def main(args):
    scanner = StreetScanner()

    if not os.getenv("GOOGLE_MAPS_API_KEYx"):
        parser.print_help()
        print("\n⚠️⚠️ set GOOGLE_MAPS_API_KEY before run ⚠️⚠️\n")
        sys.exit(1)

    if args.getimages:
        async for event in scanner.process(args.a, args.b):
            print(f"{event['index']}/{event['total']} filename={event['filename']}")

    if args.getandanalyze:
        async for event in scanner.process(args.a, args.b, args.desc):
            print(f"{event['index']}/{event['total']} score={event['score']} match={event['match']} filename={event['filename']}")
            
    if args.analyze:
        async for event in scanner.analyze_exist_images(args.desc):
            print(f"{event['index']}/{event['total']} score={event['score']} match={event['match']} filename={event['filename']}")        
        
    if args.itinary:
        pins = scanner.get_itinary(args.a, args.b)
        print(pins)
        return

    parser.print_help()
        
if __name__ == "__main__":        
    parser = argparse.ArgumentParser(
    description="Streetview processing and image analysis tool.",
    formatter_class=argparse.RawTextHelpFormatter,
    epilog=f"""
Usage:

- Get google street images and/or analyse images :
   python main.py --getimages --from "Louvre, paris" --to "Tour effeil, paris"
   
   python main.py --analyze --desc "la tour effeil"

   python main.py --getandanalyze --from "Louvre, paris" --to "Tour effeil, paris" --analyse --desc "la tour effeil"

- Display only itinary (without images)
   python main.py --itinary --from "Louvre, paris" --to "Tour effeil, paris"

""")    
    parser.add_argument("--getimages", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--getandanalyze", action="store_true")    
    parser.add_argument("--itinary", action="store_true")
    
    parser.add_argument("--from", dest="a")
    parser.add_argument("--to", dest="b")
    parser.add_argument("--desc")
    
    args = parser.parse_args()
    
    asyncio.run(main(args))