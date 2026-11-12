#!/usr/bin/env python3
"""Local GitHub-to-Termux Proceed listener for PadippuPal."""
from __future__ import annotations
import argparse, datetime as dt, getpass, json, os, pathlib, re, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = "Prav1525/Padippupal"
API = "https://api.github.com"
TOKEN_FILE = pathlib.Path.home() / ".config/padippupal/github-token"
STATE_DIR = pathlib.Path.home() / ".local/state/padippupal-proceed-listener"
STATE_FILE = STATE_DIR / "state.json"
WORKTREES = pathlib.Path.home() / ".local/share/padippupal/proceed-worktrees"

class ListenerError(RuntimeError): pass

def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def owner_of(repo):
    parts = repo.split("/")
    if len(parts) != 2 or not all(parts): raise ListenerError("Repository must use owner/name format.")
    return parts[0]

class GitHub:
    def __init__(self, repo, token): self.repo, self.token = repo, token
    def request(self, method, path, payload=None):
        headers = {"Accept":"application/vnd.github+json","Authorization":"Bearer "+self.token,
                   "X-GitHub-Api-Version":"2022-11-28","User-Agent":"PadippuPal-Termux-Proceed-Listener"}
        data = json.dumps(payload).encode() if payload is not None else None
        if data is not None: headers["Content-Type"] = "application/json"
        req = urllib.request.Request(API+path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response: raw = response.read()
        except urllib.error.HTTPError as exc:
            raise ListenerError(f"GitHub API HTTP {exc.code}: {exc.read().decode(errors='replace')[:400]}") from exc
        except (urllib.error.URLError, TimeoutError) as exc: raise ListenerError(f"GitHub API failed: {exc}") from exc
        return json.loads(raw.decode()) if raw else None
    def comments_since(self, timestamp):
        result, page = [], 1
        while True:
            query = urllib.parse.urlencode({"since":timestamp,"per_page":100,"page":page,"sort":"created","direction":"asc"})
            batch = self.request("GET",f"/repos/{self.repo}/issues/comments?{query}")
            if not isinstance(batch,list): raise ListenerError("Invalid GitHub issue-comments response.")
            result.extend(batch)
            if len(batch) < 100: break
            page += 1
        return sorted(result,key=lambda x:(x.get("created_at",""),int(x.get("id",0))))
    def pull_request(self, number):
        value = self.request("GET",f"/repos/{self.repo}/pulls/{number}")
        if not isinstance(value,dict): raise ListenerError(f"Could not read PR #{number}.")
        return value
    def report(self, number, body):
        self.request("POST",f"/repos/{self.repo}/issues/{number}/comments",{"body":body})

def pull_number(comment):
    match = re.search(r"/issues/(\d+)$",str(comment.get("issue_url","")))
    return int(match.group(1)) if match else None

def is_owner_proceed(comment, owner):
    user = comment.get("user") or {}
    return str(comment.get("body","")).strip()=="/proceed" and str(user.get("login","")).lower()==owner.lower() and pull_number(comment) is not None

def validate_pr(pr, repo, owner):
    if pr.get("state")!="open": return "PR is not open."
    if str((pr.get("user") or {}).get("login","")).lower()!=owner.lower(): return "PR author is not repository owner."
    head_repo=(pr.get("head") or {}).get("repo") or {}
    if str(head_repo.get("full_name","")).lower()!=repo.lower(): return "Fork-originated PR refused."
    if not re.fullmatch(r"[0-9a-fA-F]{40}",str((pr.get("head") or {}).get("sha",""))): return "Invalid exact PR head SHA."
    return None

def load_state(path=STATE_FILE):
    if not path.exists(): return {"schema_version":1,"last_created_at":utc_now(),"processed":{}},True
    try: state=json.loads(path.read_text())
    except (OSError,ValueError) as exc: raise ListenerError(f"Cannot read listener state: {exc}") from exc
    if not isinstance(state,dict) or state.get("schema_version")!=1 or not isinstance(state.get("processed"),dict) or not state.get("last_created_at"):
        raise ListenerError("Listener state is malformed; refusing to reset it.")
    return state,False

def save_state(state,path=STATE_FILE):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp"); tmp.write_text(json.dumps(state,indent=2)+"\n")
    os.chmod(tmp,0o600); tmp.replace(path)

def record(state,comment,status,**details):
    state["processed"][str(comment["id"])]={"status":status,**details}
    created=comment.get("created_at")
    if created and dt.datetime.fromisoformat(created.replace("Z","+00:00"))>dt.datetime.fromisoformat(state["last_created_at"].replace("Z","+00:00")):
        state["last_created_at"]=created

def git(root,*args):
    result=subprocess.run(["git",*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode: raise ListenerError(result.stderr.strip() or "Git command failed.")
    return result.stdout.strip()

def make_worktree(number,sha,comment_id,root=ROOT):
    git(root,"fetch","--no-tags","origin",f"refs/pull/{number}/head")
    fetched=git(root,"rev-parse","FETCH_HEAD")
    if fetched.lower()!=sha.lower(): raise ListenerError(f"PR head moved: expected {sha}, fetched {fetched}; execution refused.")
    path=WORKTREES/f"pr-{number}-comment-{comment_id}"
    if path.exists(): raise ListenerError(f"Worktree already exists; refusing overwrite: {path}")
    path.parent.mkdir(parents=True,exist_ok=True); git(root,"worktree","add","--detach",str(path),sha)
    return path

def execute_codex(worktree,comment_id):
    artifacts=STATE_DIR/"artifacts"/str(comment_id); artifacts.mkdir(parents=True,exist_ok=True)
    log_path=artifacts/"executor.log"; env=os.environ.copy(); env["TMPDIR"]=str(artifacts)
    # Never pass the listener credential into the Codex child process.
    for secret_name in ("PADIPPUPAL_GITHUB_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"):
        env.pop(secret_name, None)
    command=[sys.executable,"tools/padippupal_local_executor.py","proceed"]
    with log_path.open("w") as log:
        proc=subprocess.Popen(command,cwd=worktree,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1)
        for line in proc.stdout:
            print(line,end="",flush=True); log.write(line); log.flush()
        code=proc.wait()
    output=log_path.read_text(errors="replace")
    def extract(pattern,default):
        match=re.search(pattern,output,re.MULTILINE); return match.group(1).strip() if match else default
    blocked="BLOCKED:" in output or "PREFLIGHT: BLOCKED" in output
    return {"status":"BLOCKED" if blocked else ("PASS" if code==0 else "FAIL"),"exit_code":code,
            "branch":extract(r"^Branch: (.+)$","not created"),"changed":extract(r"^Changed files: (.+)$","not reported"),
            "summary":extract(r"^Execution summary: (.+)$","not produced"),"patch":extract(r"^Patch: (.+)$","not produced"),
            "worktree":str(worktree),"log":str(log_path)}

def report_body(comment_id,number,sha,result):
    lines=[f"<!-- padippupal-local-proceed:{comment_id} -->","## PadippuPal local Termux Codex result","",
           f"- Trigger comment: `{comment_id}`",f"- PR: #{number}",f"- Exact PR head SHA: `{sha}`",
           f"- Result: **{result['status']}**",f"- Codex exit code: `{result['exit_code']}`",
           f"- Local branch: `{result['branch']}`",f"- Changed files: `{result['changed']}`",
           f"- Summary file: `{result['summary']}`",f"- Patch file: `{result['patch']}`",f"- Worktree: `{result['worktree']}`","",
           "The worktree and patch remain on the device. No commit, push, PR creation, merge, deployment, production write, or release was performed."]
    if result.get("error"): lines += ["", "**Blocker:** "+result["error"]]
    return "\n".join(lines)

def process_pending(repo,client,state,root=ROOT,executor=execute_codex,state_path=STATE_FILE):
    owner=owner_of(repo)
    cursor=dt.datetime.fromisoformat(state["last_created_at"].replace("Z","+00:00"))-dt.timedelta(seconds=1)
    timestamp=cursor.isoformat().replace("+00:00","Z")
    for comment in client.comments_since(timestamp):
        cid=str(comment.get("id",""))
        if not cid or cid in state["processed"]: continue
        if not is_owner_proceed(comment,owner):
            record(state,comment,"ignored"); save_state(state,state_path); continue
        number=pull_number(comment); pr=client.pull_request(number)
        rejection=validate_pr(pr,repo,owner)
        if rejection:
            record(state,comment,"rejected",reason=rejection); save_state(state,state_path); print(f"Ignoring /proceed {cid}: {rejection}"); continue
        sha=pr["head"]["sha"]; record(state,comment,"claimed",pr=number,sha=sha); save_state(state,state_path)
        try:
            worktree=make_worktree(number,sha,int(cid),root); result=executor(worktree,int(cid))
        except Exception as exc:
            result={"status":"BLOCKED","exit_code":2,"branch":"not created","changed":"unknown","summary":"not produced",
                    "patch":"not produced","worktree":"not created","error":str(exc)}
        try: client.report(number,report_body(int(cid),number,sha,result)); report="posted"
        except Exception as exc: report="failed: "+str(exc); print("Could not post result: "+str(exc),file=sys.stderr)
        record(state,comment,result["status"].lower(),pr=number,sha=sha,exit_code=result["exit_code"],
               worktree=result.get("worktree"),report=report); save_state(state,state_path)
        return result["status"]
    return None

def configure(repo):
    token=getpass.getpass("Fine-grained GitHub token (hidden): ").strip()
    if not token: print("BLOCKED: empty token",file=sys.stderr); return 2
    client=GitHub(repo,token)
    try:
        client.request("GET",f"/repos/{repo}")
        client.request("GET",f"/repos/{repo}/issues/comments?per_page=1")
        client.request("GET",f"/repos/{repo}/pulls?state=open&per_page=1")
    except ListenerError as exc: print(f"BLOCKED: token validation failed: {exc}",file=sys.stderr); return 2
    TOKEN_FILE.parent.mkdir(parents=True,exist_ok=True); os.chmod(TOKEN_FILE.parent,0o700)
    TOKEN_FILE.write_text(token+"\n"); os.chmod(TOKEN_FILE,0o600)
    print(f"Token saved at {TOKEN_FILE} with owner-only permissions.")
    print("Fine-grained permissions: Issues read/write; Pull requests read. Never share or commit the token.")
    return 0

def run_listener(repo,poll_seconds,once=False):
    if poll_seconds<30: raise ListenerError("Polling interval must be at least 30 seconds.")
    token=os.environ.get("PADIPPUPAL_GITHUB_TOKEN","").strip()
    if not token:
        try: token=TOKEN_FILE.read_text().strip()
        except OSError as exc: raise ListenerError("No token configured; run the configure command first.") from exc
    if not token: raise ListenerError("Saved GitHub token is empty.")
    client=GitHub(repo,token); STATE_DIR.mkdir(parents=True,exist_ok=True)
    lock=(STATE_DIR/"listener.lock").open("a+")
    try:
        try:
            import fcntl; fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except (ImportError,BlockingIOError) as exc: raise ListenerError("Another listener is already running.") from exc
        state,first=load_state()
        if first:
            save_state(state); print("LISTENER ARMED. Old comments will not be replayed. Post a new /proceed after this message.",flush=True)
        else: print(f"LISTENER ACTIVE for {repo}; polling every {poll_seconds}s.",flush=True)
        while True:
            try:
                outcome=process_pending(repo,client,state)
                if outcome: print(f"Local Proceed result: {outcome}",flush=True)
            except ListenerError as exc: print(f"Listener warning: {exc}",file=sys.stderr,flush=True)
            if once: return 0
            time.sleep(poll_seconds)
    finally: lock.close()

def main(argv=None):
    parser=argparse.ArgumentParser(description="Bridge GitHub /proceed comments to the local PadippuPal Codex executor.")
    parser.add_argument("--repository",default=REPO)
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("configure",help="Securely configure the fine-grained GitHub token.")
    start=sub.add_parser("start",help="Configure the token if needed, then start the listener.")
    start.add_argument("--poll-seconds",type=int,default=60); start.add_argument("--once",action="store_true")
    run=sub.add_parser("run",help="Poll GitHub and execute approved tasks through local Codex.")
    run.add_argument("--poll-seconds",type=int,default=60); run.add_argument("--once",action="store_true")
    args=parser.parse_args(argv)
    try:
        if args.command=="configure": return configure(args.repository)
        if args.command=="start" and not os.environ.get("PADIPPUPAL_GITHUB_TOKEN","").strip() and not TOKEN_FILE.exists():
            configured=configure(args.repository)
            if configured: return configured
        return run_listener(args.repository,args.poll_seconds,args.once)
    except ListenerError as exc: print(f"BLOCKED: {exc}",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
