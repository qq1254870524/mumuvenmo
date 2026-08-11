# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import importlib.util
import inspect
import pathlib
import sys
from unittest.mock import patch

parser=argparse.ArgumentParser()
parser.add_argument('--source-root',required=True)
parser.add_argument('--mode',choices=('baseline','modified'),required=True)
args=parser.parse_args()
root=pathlib.Path(args.source_root)
project=pathlib.Path(r'E:\mumuvenmo')
sys.path.insert(0,str(project))
import core
vspec=importlib.util.spec_from_file_location('core.venmo_login',root/'core'/'venmo_login.py')
vmod=importlib.util.module_from_spec(vspec); sys.modules['core.venmo_login']=vmod; vspec.loader.exec_module(vmod)
wspec=importlib.util.spec_from_file_location('fixture_worker_engine',root/'core'/'worker_engine.py')
wmod=importlib.util.module_from_spec(wspec); wspec.loader.exec_module(wmod)
class DummyProxy:
    def configure(self,**kwargs): pass
records=[]
engine=wmod.WorkerEngine(None,None,DummyProxy(),{},ui_log=records.append)
with patch.object(wmod.logger,'info',side_effect=records.append): engine.log('probe')
wsrc=(root/'core'/'worker_engine.py').read_text(encoding='utf-8-sig')
print(f"cancel_check_param={'cancel_check' in inspect.signature(vmod.VenmoLogin).parameters}")
print(f"worker_log_records={len(records)}")
print(f"cancel_releases_account={'except LoginCancelled:' in wsrc and 'self.store.release_without_result(acc)' in wsrc}")
print(f"start_clears_adb_cancel={'AdbClient.clear_cancel_all()' in wsrc}")
print(f"{args.mode.upper()}_EXIT=0")
