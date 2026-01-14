import sys
import subprocess
from pathlib import Path
import argparse
from photobot.sort import sort_medias
from photobot.parameters import SRC_PATH

def main():
    parser = argparse.ArgumentParser(
        description="Photobot – tri et cartographie des médias"
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Cherche les média récursivement"
    )
    
    # Sous-commandes : --sort et --map
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Sous-commande : sort ---
    sort_parser = subparsers.add_parser(
        "sort",
        help="Trie les médias d’un dossier vers un autre"
    )
    sort_parser.add_argument("source", type=Path, help="Dossier source")
    sort_parser.add_argument("destination", type=Path, help="Dossier destination")

    # --- Sous-commande : map ---
    map_parser = subparsers.add_parser(
        "map",
        help="Affiche la carte des médias d’un dossier"
    )
    map_parser.add_argument("source", type=Path, help="Dossier source")

    # --- Sous-commande : date ---
    date_parser = subparsers.add_parser(
        "date",
        help="Ouvre la liste des groupes par date"
    )

    args = parser.parse_args()

    # --- Traitement des commandes ---
    if args.command == "sort":
        if not args.source.exists():
            print(f"❌ Dossier {args.source} introuvable.")
            sys.exit(1)

        sort_medias(args.source, args.destination, recursive=args.recursive)
        print("✅ Tri terminé avec succès !")

    elif args.command == "map":
        if not args.source.exists():
            print(f"❌ Dossier {args.source} introuvable.")
            sys.exit(1)

        subprocess.run([
            "streamlit",
            "run",
            f"{SRC_PATH / 'photobot' / 'map.py'}",
            "--",
            str(args.source),
            "-r" if args.recursive else ""
        ])
    
    elif args.command == "date" :
        subprocess.run([
            "streamlit",
            "run",
            f"{SRC_PATH / 'photobot' / 'date.py'}"
        ])
