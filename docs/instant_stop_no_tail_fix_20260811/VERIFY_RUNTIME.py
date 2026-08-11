# -*- coding: utf-8 -*-
from __future__ import annotations
import inspect
import pathlib
import sys
import threading
import time
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from core.adb_client import AdbClient
from core.venmo_login import LoginCancelled, VenmoLogin
from core.worker_engine import WorkerEngine

class DummyProxy:
    def configure(self, **kwargs): pass
    def release(self, key): pass

records=[]
eng_log=WorkerEngine(None,None,DummyProxy(),{},ui_log=records.append)
with patch('core.worker_engine.logger.info',side_effect=records.append): eng_log.log('once')
ev=threading.Event(); state=[]; login=VenmoLogin(object(),cancel_check=ev.is_set)
def sleep_job():
    try:
        try: login._sleep(30)
        except Exception: state.append('swallowed')
    except LoginCancelled: state.append('cancelled')
t=threading.Thread(target=sleep_job); t.start(); time.sleep(.05); started=time.perf_counter(); ev.set(); t.join(1); latency=time.perf_counter()-started
eng=WorkerEngine(None,None,DummyProxy(),{},ui_log=lambda _m:None)
login2=VenmoLogin(object(),cancel_check=eng._force_stop_event.is_set)
def worker():
    try: login2._sleep(30)
    except LoginCancelled: pass
wt=threading.Thread(target=worker); wt.start(); eng._threads=[wt]; eng.running=True
result=eng.stop_and_shutdown(join_timeout=.2,shutdown_vms=False,force=True)
AdbClient.clear_cancel_all()
print(f'cancel_check_param={"cancel_check" in inspect.signature(VenmoLogin).parameters}')
print(f'worker_log_records={len(records)}')
print(f'cancel_outcome={state[0] if state else "missing"}')
print(f'cancel_bypasses_exception={issubclass(LoginCancelled, BaseException) and not issubclass(LoginCancelled, Exception)}')
print(f'cancel_thread_alive={t.is_alive()}')
print(f'cancel_latency_lt_0_35={latency < .35}')
print(f'engine_stop_joined={result["joined"]}')
print(f'engine_stop_alive_left={result["alive_left"]}')
print(f'engine_stop_running={eng.running}')
print('PRODUCTION_RUNTIME_EXIT=0')
