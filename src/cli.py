import sys
from sort import sort_photos
# from map import 
import os
from pathlib import Path

def main():

    if len(sys.argv) < 2:
        print("Usage : photobot --sort <source> <destination> | --map <source>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "--sort":
        if len(sys.argv) < 4:
            print("❌ Utilisation : photobot --sort <dossier_source> <dossier_destination>")
            sys.exit(1)

        dossier_source = Path(sys.argv[2])
        dossier_destination = Path(sys.argv[3])

        if not dossier_source.exists():
            print(f"❌ Dossier {dossier_source} introuvable.")
            sys.exit(1)

        sort_photos(dossier_source, dossier_destination)
        print("✅ Tri terminé avec succès !")

    elif cmd == "--map":
        if len(sys.argv) < 3:
            print("❌ Utilisation : photobot --map <dossier_source>")
            sys.exit(1)
        dossier_source = sys.argv[2]
        #generer_carte(dossier_source, "carte_groupes.html")

    else:
        print(f"❌ Commande inconnue : {cmd}")
        print("Options : --sort ou --map")
        sys.exit(1)
