#!/usr/bin/env python3
"""Real Android emulator acceptance test for Beyond Earth original textbook images."""
from __future__ import annotations
import json, re, subprocess, sys, time
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops, ImageStat

ADB = ["adb", "-s", "emulator-5554"]
OUT = Path("ui-screenshots/beyond-earth")
OUT.mkdir(parents=True, exist_ok=True)
LESSON_ID = "10d13a36-87e9-5f3b-8210-f62eb95e8854"

def run(args, timeout=30, **kw):
    # Hosted software emulators can briefly drop the ADB shell transport while
    # Android services start. Retry only ADB operations; never mask app/test
    # assertion failures or retry unrelated subprocesses.
    attempts = 6 if args and str(args[0]).endswith("adb") else 1
    last = None
    for attempt in range(attempts):
        try:
            return subprocess.run(args, check=True, timeout=timeout, **kw)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            last = exc
            if attempt + 1 >= attempts:
                raise
            print(f"Transient ADB failure ({attempt + 1}/{attempts}): {exc}", file=sys.stderr, flush=True)
            subprocess.run(["adb", "start-server"], check=False, timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(min(2 + attempt, 6))
    raise last
def shell(command, timeout=30):
    return run(ADB + ["shell"] + command.split(), timeout=timeout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
def dump(name):
    remote = f"/data/local/tmp/{name}.xml"
    run(ADB + ["shell","uiautomator","dump",remote], timeout=25, stdout=subprocess.DEVNULL)
    run(ADB + ["pull",remote,str(OUT/f"{name}.xml")], timeout=15, stdout=subprocess.DEVNULL)
    root=ET.parse(OUT/f"{name}.xml").getroot()
    nodes=list(root.iter("node"))
    texts=[n.attrib.get("text","").strip() for n in nodes if n.attrib.get("text","").strip()]
    descriptions=[n.attrib.get("content-desc","").strip() for n in nodes if n.attrib.get("content-desc","").strip()]
    labels=list(dict.fromkeys(texts+descriptions))
    print(f"{name.upper()} TEXT: " + " | ".join(texts[:80]), flush=True)
    print(f"{name.upper()} CONTENT_DESC: " + " | ".join(descriptions[:80]), flush=True)
    return nodes,labels
def screenshot(name):
    run(ADB+["exec-out","screencap","-p"],timeout=15,stdout=open(OUT/f"{name}.png","wb"))
def tap_node(node):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",node.attrib.get("bounds",""))
    if not m: raise RuntimeError(f"Node has no usable bounds: {node.attrib}")
    x1,y1,x2,y2=map(int,m.groups())
    run(ADB+["shell","input","tap",str((x1+x2)//2),str((y1+y2)//2)],timeout=15)
def tap_text(nodes, target, occurrence="first"):
    candidates=[n for n in nodes if n.attrib.get("text","").strip().casefold()==target.casefold() and re.fullmatch(r"\[\d+,\d+\]\[\d+,\d+\]",n.attrib.get("bounds",""))]
    if not candidates:
        raise RuntimeError(f"Could not find tappable label {target!r}")
    tap_node(candidates[-1] if occurrence=="last" else candidates[0])
def tap_numbered(nodes, number=1):
    candidates=[]
    for n in nodes:
        label=n.attrib.get("text","").strip()
        if re.match(rf"^{number}[.)]\s*\S",label) and re.fullmatch(r"\[\d+,\d+\]\[\d+,\d+\]",n.attrib.get("bounds","")):
            candidates.append(n)
    if not candidates: raise RuntimeError(f"Could not find numbered option {number}")
    tap_node(next((n for n in candidates if n.attrib.get("clickable")=="true"),candidates[0]))
def wait_dump(name, expected, timeout=120):
    end=time.time()+timeout
    last=None
    while time.time()<end:
        try:
            nodes,texts=dump(name)
            joined="\n".join(texts).casefold()
            if all(term.casefold() in joined for term in expected):
                return nodes,texts
            last=" | ".join(texts[:60])
        except Exception as exc: last=str(exc)
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for {expected}; last UI={last}")

try:
    print("Waiting for Android and installing exact debug APK",flush=True)
    run(ADB+["wait-for-device"],timeout=30)
    deadline=time.time()+180
    while time.time()<deadline:
        if shell("getprop sys.boot_completed").strip()=="1": break
        time.sleep(3)
    else: raise RuntimeError("Android emulator did not boot")
    run(ADB+["install","-r","app/build/outputs/apk/debug/app-debug.apk"],timeout=90)
    shell("run-as com.padippupal.app rm -f shared_prefs/padippupal_profile.xml")
    shell("run-as com.padippupal.app rm -f shared_prefs/padippupal_tutor_sessions.xml")
    # CBSE Class 6, English: the supported curriculum profile for this acceptance flow.
    run(ADB+["shell","run-as","com.padippupal.app","sh","-c","mkdir -p shared_prefs && echo PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiIHN0YW5kYWxvbmU9InllcyIgPz48bWFwPjxzdHJpbmcgbmFtZT0iZ3JhZGUiPjY8L3N0cmluZz48c3RyaW5nIG5hbWU9ImJvYXJkIj5DQlNFPC9zdHJpbmc+PHN0cmluZyBuYW1lPSJtZWRpdW0iPkVuZ2xpc2g8L3N0cmluZz48c3RyaW5nIG5hbWU9Imxhbmd1YWdlIj5FbmdsaXNoPC9zdHJpbmc+PC9tYXA+ | base64 -d > shared_prefs/padippupal_profile.xml"])
    shell("am force-stop com.padippupal.app")
    shell("am start -n com.padippupal.app/.MainActivity")
    wait_dump("home",["YOUR LEARNING SPACE","YOUR PERSONAL TUTOR","Start learning"],60)
    screenshot("home")
    nodes,_=dump("home"); tap_text(nodes,"Start learning")
    time.sleep(4)
    nodes,texts=wait_dump("settings",["Set up your lesson","Done"],40)
    if not any(t.casefold()=="science" for t in texts): raise RuntimeError("Science subject is missing from setup screen")
    tap_text(nodes,"Science"); time.sleep(4)
    nodes,texts=wait_dump("science-chapter-picker",["Choose chapter"],40)
    if any("no chapter list is available" in t.casefold() for t in texts): raise RuntimeError("Science curriculum outline is empty")
    tap_text(nodes,"Choose chapter"); time.sleep(2)
    nodes,texts=wait_dump("science-chapter-menu",["Beyond Earth"],30)
    tap_numbered(nodes,1); time.sleep(2)
    nodes,texts=wait_dump("science-chapter-selected",["Beyond Earth"],30)
    # Open the topic field; if no placeholder is shown, use the last matching chapter/topic label.
    if any(n.attrib.get("text","").strip().casefold()=="choose concept" for n in nodes): tap_text(nodes,"Choose concept")
    else: tap_text(nodes,"Beyond Earth",occurrence="last")
    time.sleep(2)
    nodes,texts=wait_dump("science-topic-menu",["Beyond Earth"],30)
    tap_numbered(nodes,1); time.sleep(2)
    nodes,texts=wait_dump("science-topic-selected",["Done"],30)
    screenshot("science-topic-selected")
    tap_text(nodes,"Done"); time.sleep(2)
    nodes,texts=wait_dump("tutor-ready",["Teach"],40)
    screenshot("tutor-ready")
    # Prefer exact accessible Teach button, avoiding similarly named prose.
    teach=[n for n in nodes if n.attrib.get("text","").strip().casefold() in {"teach","▶ teach"} and n.attrib.get("bounds")]
    if not teach: raise RuntimeError("Tutor ready screen has no Teach action")
    tap_node(teach[-1])
    # Wait for the actual lesson and mapped original image to be in the active player.
    end=time.time()+150
    lesson_nodes=[]; lesson_texts=[]
    while time.time()<end:
        try:
            lesson_nodes,lesson_texts=dump("beyond-earth-live")
            joined="\n".join(lesson_texts).casefold()
            if "our universe contains many objects beyond earth" in joined and "beyond earth" in joined:
                screenshot("beyond-earth-live")
                # contentDescription of Compose Image should expose title/alt text from the live manifest.
                break
            if any(e in joined for e in ["could not answer right now","no matching textbook passage","connection failed","invalid response"]):
                raise RuntimeError("Tutor returned a lesson-start error: "+joined[:1200])
        except RuntimeError: raise
        except Exception: pass
        time.sleep(3)
    else: raise RuntimeError("Tutor never displayed the Beyond Earth lesson text")
    manifest=json.loads(__import__("urllib.request",fromlist=["urlopen"]).urlopen("http://127.0.0.1:8765/chapter-lessons/"+LESSON_ID+"/images",timeout=10).read())
    assets=manifest.get("images",[])
    mapped=[a for a in assets if a.get("module_key")=="module-1"]
    if not mapped: raise RuntimeError("Live image manifest has no module-1 mapped original")
    alt_candidates=[str(a.get("title","")).strip() or str(a.get("alt_text","")).strip() for a in mapped]
    joined="\n".join(lesson_texts).casefold()
    exposed=[label for label in alt_candidates if label and label.casefold() in joined]
    if not exposed:
        raise RuntimeError("No mapped original image contentDescription was exposed in the tutor accessibility tree; image data exists but inline rendering is not proven")
    # Verify screenshot has substantial non-background detail in the central teaching viewport.
    img=Image.open(OUT/"beyond-earth-live.png").convert("RGB")
    w,h=img.size
    crop=img.crop((int(w*.06),int(h*.18),int(w*.94),int(h*.83)))
    colors=len(crop.getcolors(maxcolors=2_000_000) or [])
    stat=ImageStat.Stat(crop)
    print(f"SCREENSHOT dimensions={w}x{h}; viewport unique_colors={colors}; stddev={stat.stddev}",flush=True)
    if colors < 120: raise RuntimeError("Tutor screenshot teaching viewport lacks visible image/detail; possible blank image region")
    print("PASS: Android emulator selected CBSE Class 6 Science > Beyond Earth; active tutor screen exposes a module-mapped original image label; screenshot captured.",flush=True)
except Exception as exc:
    print("FAIL: "+str(exc),file=sys.stderr,flush=True)
    # Preserve evidence even when navigation/assertions fail before the main
    # screenshot: screenshot, UI hierarchy, logcat and current activity.
    try: screenshot("failure")
    except Exception as capture_exc: print(f"Could not capture failure screenshot: {capture_exc}",file=sys.stderr,flush=True)
    for name, command in [
        ("failure-hierarchy.xml", ADB+["shell","uiautomator","dump","/data/local/tmp/beyond-earth-failure.xml"]),
        ("failure-logcat.txt", ADB+["logcat","-d","-v","threadtime"]),
        ("failure-activity.txt", ADB+["shell","dumpsys","activity","activities"]),
    ]:
        try:
            subprocess.run(command,check=False,timeout=45,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if name.endswith(".xml"):
                subprocess.run(ADB+["pull","/data/local/tmp/beyond-earth-failure.xml",str(OUT/name)],
                               check=False,timeout=20,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            else:
                result=subprocess.run(command,check=False,timeout=45,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                (OUT/name).write_text(result.stdout,encoding="utf-8")
        except Exception as capture_exc:
            print(f"Diagnostic capture {name} failed: {capture_exc}",file=sys.stderr,flush=True)
    sys.exit(1)
