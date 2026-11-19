"""Punto de entrada; el directorio de dependencias de investigación es opcional."""
import sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
research_deps=ROOT.parent.parent/'work/pydeps'
if research_deps.exists():sys.path.insert(0,str(research_deps))
from palimpsesto.server import main
if __name__=='__main__':main()
