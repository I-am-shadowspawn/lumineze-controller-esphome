"""Validate schedule ownership/editor failures with the real ESPHome validator."""
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
base=(ROOT/'ci/schedule-generic.yaml').read_text()
cases=[
 ('valid schedule',base,None),
 ('wrong engine',base.replace('engine_family: schedule','engine_family: seasonal'),'selected engine'),
 ('wrong provider',base.replace('engine_family: schedule','engine_family: schedule\n  input_provider: development'),'selected snapshot provider'),
 ('unused role editor',base.replace('schedule_role: visible','schedule_role: uv'),'only used role editors'),
 ('seasonal context',base.replace('context-schedule.yaml','context-seasonal.yaml'),"Couldn't find ID 'topology_seasonal_settings'"),
 ('unsupported temporary capability',base.replace('fixture-luminize-schedule.yaml','fixture-luminize.yaml'),'seasonal temporary controls'),
 ('restoring staged number',base+'\nnumber:\n  - id: !extend shared_visible_point_1_level\n    restore_value: true\n','staging must not restore'),
 ('restoring staged enable',base+'\nswitch:\n  - id: !extend shared_visible_point_1_enabled\n    restore_mode: RESTORE_DEFAULT_ON\n','point enables must reset off'),
 ('restoring staged mode',base+'\nselect:\n  - id: !extend shared_visible_schedule_mode\n    restore_value: true\n','staging must not restore'),
]
for name,source,error in cases:
 with tempfile.NamedTemporaryFile(mode='w',suffix='.yaml',dir=ROOT/'ci') as f:
  f.write(source);f.flush()
  result=subprocess.run([*sys.argv[1:],'config',f.name],capture_output=True,text=True)
  output=result.stdout+result.stderr
  if error is None:
   assert result.returncode==0,(name,output[-1500:])
  else:
   assert result.returncode!=0 and error in output,(name,output[-1500:])
 print('PASS '+name)
