#!/usr/bin/env python3
"""Real Android emulator acceptance test for Beyond Earth original textbook images."""
from __future__ import annotations
import json, re, subprocess, sys, time
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops, ImageStat
from beyond_earth_emulator_profile import seed_profile_preferences

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
        time.sleep(6)
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
    # CBSE Class 6, English: seed preferences using safe adb shell argument handling.
    seed_profile_preferences(ADB, run)
    shell("am force-stop com.padippupal.app")
    # Wait for Android to report the first activity draw before invoking UiAutomation. On the no-KVM hosted runner, an immediate uiautomator dump can contend with startup and trigger a system-server ANR.
    launch_result = shell("am start -W -n com.padippupal.app/.MainActivity", timeout=180)
    print("MAIN ACTIVITY LAUNCH: " + " | ".join(line.strip() for line in launch_result.splitlines() if line.strip()), flush=True)
    if "Status: ok" not in launch_result and "Complete" not in launch_result:
        raise RuntimeError("Android did not confirm MainActivity launch: " + launch_result[-1000:])
    # Allow Compose and system accessibility services to settle before the first hierarchy dump.
    time.sleep(10)
    wait_dump("home",["YOUR LEARNING SPACE","YOUR PERSONAL TUTOR","Start learning"],90)
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
    if len(assets) != 19: raise RuntimeError(f"Expected all 19 original textbook images, got {len(assets)}")
    expected_modules=[f"module-{i}" for i in range(1,8)]
    module_keys={str(a.get("module_key","")).strip() for a in assets}
    missing_modules=[key for key in expected_modules if key not in module_keys]
    if missing_modules:
        raise RuntimeError("Original-image manifest has no mapped images for topic modules: "+", ".join(missing_modules))
    expected_labels={}
    for key in expected_modules:
        candidates=[str(a.get("title","")).strip() or str(a.get("alt_text","")).strip()
                    for a in assets if str(a.get("module_key","")).strip()==key]
        expected_labels[key]=[label for label in candidates if label]
        if not expected_labels[key]:
            raise RuntimeError(f"{key} has no labelled original image")
    # Scroll through the whole non-lazy lesson column, collecting accessibility
    # labels and a real device screenshot at each viewport (not just the first).
    observed=set(lesson_texts)
    for page in range(1,11):
        shell("input swipe 540 1600 540 500 450")
        time.sleep(1.2)
        screenshot(f"beyond-earth-scroll-{page:02d}")
        _,page_labels=dump(f"beyond-earth-scroll-{page:02d}")
        observed.update(page_labels)
    all_labels="\n".join(observed).casefold()
    missing_text=[]
    for i,text in enumerate([
        "Our universe contains many objects beyond Earth.",
        "Stars are huge, hot objects that produce their own light.",
        "The Moon is Earth's natural satellite.",
        "Planets travel around stars.",
        "Constellations are patterns of stars",
        "Telescopes collect light",
        "Space exploration uses spacecraft"
    ],1):
        if text.casefold() not in all_labels:
            missing_text.append(f"module-{i} narration")
    if missing_text:
        raise RuntimeError("Full topic narration not exposed after scrolling: "+", ".join(missing_text))
    missing_images=[]
    for module,labels in expected_labels.items():
        if not any(label.casefold() in all_labels for label in labels):
            missing_images.append(module)
    if missing_images:
        raise RuntimeError("Full-topic tutor feed did not expose mapped original image labels for: "+", ".join(missing_images))
    # Confirm the final viewport is not an empty tail after the last module.
    img=Image.open(OUT/"beyond-earth-scroll-10.png").convert("RGB")
    w,h=img.size
    crop=img.crop((int(w*.06),int(h*.18),int(w*.94),int(h*.83)))
    colors=len(crop.getcolors(maxcolors=2_000_000) or [])
    stat=ImageStat.Stat(crop)
    print(f"FULL TOPIC EVIDENCE: {len(assets)} original images; modules={expected_modules}; screenshots=11; final viewport={w}x{h}; unique_colors={colors}; stddev={stat.stddev}",flush=True)
    if colors < 120: raise RuntimeError("Final topic viewport lacks visible content; possible blank image region")
    print("PASS: Android emulator traversed the complete Beyond Earth topic; all seven narration modules and each module's mapped original textbook images were exposed while scrolling.",flush=True)
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
