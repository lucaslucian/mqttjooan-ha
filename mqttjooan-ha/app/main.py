#!/usr/bin/env python3
from __future__ import annotations
import base64,json,os,socket,ssl,struct,threading,time,urllib.parse
from collections import deque
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

VERSION="0.1.0"; PREFIX="qaiot/mqtt/"
OPT={}
try: OPT=json.loads(Path(os.getenv("JOOAN_OPTIONS","/data/options.json")).read_text())
except Exception: pass
MQTT_HOST=os.getenv("JOOAN_MQTT_HOST","0.0.0.0"); MQTT_PORT=int(os.getenv("JOOAN_MQTT_PORT","1883"))
WEB_HOST=os.getenv("JOOAN_WEB_HOST","0.0.0.0"); WEB_PORT=int(os.getenv("JOOAN_WEB_PORT","8098"))
MAX=int(OPT.get("max_messages",1000)); MAXPKT=int(OPT.get("max_packet_size",65536)); PERSIST=bool(OPT.get("persist_messages",True))
CERT=os.getenv("JOOAN_TLS_CERT",""); KEY=os.getenv("JOOAN_TLS_KEY",""); DATA=Path("/data"); DATA.mkdir(parents=True,exist_ok=True); LOG=DATA/"messages.jsonl"
LOCK=threading.RLock(); MSG=deque(maxlen=MAX); CLIENTS={}; SEQ=0

def iso(): return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def enc_len(n):
    out=bytearray()
    while True:
        d=n%128;n//=128
        if n:d|=128
        out.append(d)
        if not n:return bytes(out)
def mstr(s):
    b=s.encode(); return struct.pack("!H",len(b))+b
def rex(s,n):
    b=b""
    while len(b)<n:
        c=s.recv(n-len(b))
        if not c: raise EOFError
        b+=c
    return b
def rlen(s):
    v=0;m=1
    for _ in range(4):
        d=rex(s,1)[0];v+=(d&127)*m
        if not d&128:return v
        m*=128
    raise ValueError("bad remaining length")
def pstr(b,o=0):
    if o+2>len(b): raise ValueError("short string")
    n=struct.unpack_from("!H",b,o)[0];o+=2
    if o+n>len(b): raise ValueError("short string")
    return b[o:o+n].decode("utf-8","replace"),o+n
def add(x):
    global SEQ
    with LOCK:
        SEQ+=1;x["seq"]=SEQ;MSG.append(x)
        if PERSIST:
            with LOG.open("a",encoding="utf-8") as f:f.write(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n")
def status():
    with LOCK:
        return {"version":VERSION,"mqtt":{"listen":f"{MQTT_HOST}:{MQTT_PORT}","tls":bool(CERT and KEY),"clients":[c.public() for c in CLIENTS.values()]},"messages":{"total":SEQ,"buffered":len(MSG),"persist":PERSIST}}

class Session:
    def __init__(self,c,a):
        self.c=c;self.a=a;self.id=f"{a[0]}:{a[1]}-{time.time_ns()}";self.client_id="";self.topic="";self.subs=[];self.lock=threading.Lock()
    def public(self): return {"session_id":self.id,"remote":f"{self.a[0]}:{self.a[1]}","client_id":self.client_id,"command_topic":self.topic or None,"subscriptions":self.subs}
    def send(self,b):
        with self.lock:self.c.sendall(b)
    def publish(self,topic,payload):
        body=mstr(topic)+payload;self.send(b"\x30"+enc_len(len(body))+body)

class Broker:
    def __init__(self):
        self.ctx=None
        if CERT and KEY:
            self.ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            try:self.ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
            except ssl.SSLError:pass
            self.ctx.load_cert_chain(CERT,KEY)
    def run(self):
        s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind((MQTT_HOST,MQTT_PORT));s.listen(16)
        print(f"[mqtt] {MQTT_HOST}:{MQTT_PORT} tls={'on' if self.ctx else 'off'}",flush=True)
        while True:
            c,a=s.accept()
            if self.ctx:
                try:c=self.ctx.wrap_socket(c,server_side=True)
                except ssl.SSLError as e: print(f"[mqtt] TLS failed {a}: {e}",flush=True);c.close();continue
            threading.Thread(target=self.client,args=(c,a),daemon=True).start()
    def client(self,c,a):
        x=Session(c,a)
        with LOCK:CLIENTS[x.id]=x
        add({"time":iso(),"direction":"system","event":"client_connected","session_id":x.id,"remote":f"{a[0]}:{a[1]}"})
        try:
            while True:
                h=rex(c,1)[0];n=rlen(c)
                if n>MAXPKT:raise ValueError("packet too large")
                b=rex(c,n) if n else b"";t=h>>4;flags=h&15
                if t==1:self.connect(x,b)
                elif t==3:self.publish(x,flags,b)
                elif t==8:self.subscribe(x,b)
                elif t==12:x.send(b"\xd0\x00")
                elif t==14:break
        except Exception as e:add({"time":iso(),"direction":"system","event":"client_error","session_id":x.id,"error":str(e)})
        finally:
            try:c.close()
            except:pass
            with LOCK:CLIENTS.pop(x.id,None)
            add({"time":iso(),"direction":"system","event":"client_disconnected","session_id":x.id})
    def connect(self,x,b):
        proto,o=pstr(b,0)
        if o+4>len(b):raise ValueError("short CONNECT")
        level=b[o];flags=b[o+1];keep=struct.unpack_from("!H",b,o+2)[0];o+=4
        cid,o=pstr(b,o);x.client_id=cid
        add({"time":iso(),"direction":"rx","event":"connect","session_id":x.id,"client_id":cid,"protocol":proto,"protocol_level":level,"flags":flags,"keepalive":keep})
        x.send(b"\x20\x02\x00\x00")
    def subscribe(self,x,b):
        if len(b)<3:raise ValueError("short SUBSCRIBE")
        pid=b[:2];o=2;topics=[];grants=bytearray()
        while o<len(b):
            topic,o=pstr(b,o)
            if o>=len(b):raise ValueError("short SUBSCRIBE qos")
            q=b[o];o+=1;topics.append(topic);grants.append(min(q,1))
            if not x.topic and topic.startswith(PREFIX):x.topic=topic
        x.subs.extend(t for t in topics if t not in x.subs)
        add({"time":iso(),"direction":"rx","event":"subscribe","session_id":x.id,"topics":topics,"command_topic":x.topic or None})
        rb=pid+bytes(grants or b"\x00");x.send(b"\x90"+enc_len(len(rb))+rb)
    def publish(self,x,flags,b):
        topic,o=pstr(b,0);q=(flags>>1)&3;pid=None
        if q:
            if o+2>len(b):raise ValueError("short PUBLISH")
            pid=struct.unpack_from("!H",b,o)[0];o+=2
        p=b[o:]
        try:txt=p.decode();obj=json.loads(txt)
        except Exception:
            try:txt=p.decode()
            except:txt=None
            obj=None
        ev={"time":iso(),"direction":"rx","event":"publish","session_id":x.id,"topic":topic,"qos":q,"length":len(p)}
        if txt is not None:ev["payload_text"]=txt
        else:ev["payload_base64"]=base64.b64encode(p).decode()
        if isinstance(obj,dict):ev["payload_json"]=obj;ev["cmd"]=obj.get("cmd");ev["cmd_type"]=obj.get("cmd_type")
        add(ev)
        if q==1 and pid is not None:x.send(b"\x40\x02"+struct.pack("!H",pid))

HTML='''<!doctype html><meta charset="utf-8"><title>MQTT JOOAN HA</title><style>body{font-family:system-ui;background:#111827;color:#eee;padding:20px}pre,textarea{width:100%;background:#0b1020;color:#eee;padding:10px;box-sizing:border-box}button{padding:8px 14px}</style><h1>MQTT JOOAN HA</h1><div id=s></div><h3>Enviar DP</h3><textarea id=p rows=4>{"cmd":66486,"cmd_type":"request"}</textarea><button onclick=go()>Enviar</button><pre id=m></pre><script>async function r(){let s=await fetch('api/status').then(x=>x.json());document.querySelector('#s').textContent=JSON.stringify(s,null,2);let m=await fetch('api/messages?limit=100').then(x=>x.json());document.querySelector('#m').textContent=m.messages.map(x=>JSON.stringify(x,null,2)).join('\n\n')}async function go(){let payload=JSON.parse(document.querySelector('#p').value);alert(await fetch('api/dp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({payload})}).then(x=>x.text()));r()}setInterval(r,2000);r()</script>'''

class Web(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def out(self,code,obj):
        b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        u=urllib.parse.urlsplit(self.path);p=u.path.rstrip("/")
        if p.endswith("/api/status"):return self.out(200,status())
        if p.endswith("/api/health"):return self.out(200,{"ok":True,"version":VERSION})
        if p.endswith("/api/messages"):
            try:n=int(urllib.parse.parse_qs(u.query).get("limit",["100"])[0])
            except:n=100
            with LOCK:r=list(MSG)[-max(1,min(n,MAX)):]
            return self.out(200,{"messages":r})
        b=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html;charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_POST(self):
        if not self.path.rstrip("/").endswith("/api/dp"):return self.out(404,{"error":"not_found"})
        try:
            n=int(self.headers.get("Content-Length","0"));req=json.loads(self.rfile.read(n));payload=req.get("payload",req)
            if not isinstance(payload,dict):raise ValueError("payload must be object")
            with LOCK:
                ready=[c for c in CLIENTS.values() if c.topic]
            if not ready:return self.out(503,{"error":"camera_unavailable"})
            x=ready[0];topic=req.get("topic") or x.topic;raw=json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode();x.publish(topic,raw)
            add({"time":iso(),"direction":"tx","event":"publish","session_id":x.id,"topic":topic,"qos":0,"length":len(raw),"cmd":payload.get("cmd"),"cmd_type":payload.get("cmd_type"),"payload_json":payload,"payload_text":raw.decode()})
            return self.out(202,{"accepted":True,"session_id":x.id,"topic":topic})
        except Exception as e:return self.out(400,{"error":"invalid_request","message":str(e)})

def web():ThreadingHTTPServer((WEB_HOST,WEB_PORT),Web).serve_forever()
if __name__=="__main__":
    print("MQTT JOOAN HA",VERSION,flush=True);threading.Thread(target=web,daemon=True).start();Broker().run()
