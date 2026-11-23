"""Punto de entrada; el directorio de dependencias de investigación es opcional."""
import sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
from palimpsesto.server import main
if __name__=='__main__':main()
