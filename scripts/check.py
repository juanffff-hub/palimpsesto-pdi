from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
deps=ROOT.parent.parent/'work/pydeps'
if deps.exists():sys.path.insert(0,str(deps))
sys.path.insert(0,str(ROOT))
import pytest
if __name__=='__main__':raise SystemExit(pytest.main([str(ROOT/'tests'),'-q',*sys.argv[1:]]))
