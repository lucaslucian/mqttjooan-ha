import importlib.util,sys,tempfile,os
from pathlib import Path
p=Path(__file__).parents[1]/"mqttjooan-ha"/"app"/"main.py"
tmp=tempfile.mkdtemp(); os.environ["JOOAN_DATA_DIR"]=tmp; os.environ["JOOAN_OPTIONS"]=tmp+"/missing.json"
s=importlib.util.spec_from_file_location("mqttjooan_test",p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)

def test_remaining_length():
    assert m.enc_len(0)==b"\x00"
    assert m.enc_len(127)==b"\x7f"
    assert m.enc_len(128)==b"\x80\x01"
def test_mqtt_string():
    assert m.mstr("abc")==b"\x00\x03abc"
