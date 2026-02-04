import sys
from pathlib import Path
import argparse
from photobot.sort import sort_medias
from importlib import resources
import streamlit.web.bootstrap

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

        with resources.as_file(resources.files("photobot") / "map.py") as app_path:
            streamlit.web.bootstrap.run(
                main_script_path=str(app_path), 
                is_hello=False,
                args=[str(args.source), "-r" if args.recursive else ""], 
                flag_options={}
            )

    elif args.command == "date" :

        with resources.as_file(resources.files("photobot") / "date.py") as app_path:
            streamlit.web.bootstrap.run(
                main_script_path=str(app_path),
                is_hello=False,
                args=[],
                flag_options={}
            )
