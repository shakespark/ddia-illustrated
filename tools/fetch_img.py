#!/usr/bin/env python3
"""从维基共享资源找图、取图。实现在 ~/tutorials-deploy/scripts/fetch_img.py（所有教程站共用，限流规则都在那里处理），这里只是转调。
  source/.venv/bin/python tools/fetch_img.py search "关键词"
  source/.venv/bin/python tools/fetch_img.py get <两位章号> <小写英文名> "File:标题" [--width 900]"""
import os, runpy, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
runpy.run_path(os.path.expanduser("~/tutorials-deploy/scripts/fetch_img.py"), run_name="__main__")
