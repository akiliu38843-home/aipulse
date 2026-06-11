"""POST /api/personalize — 用户输入背景，LLM (deepseek-chat) 输出个人差距+学习顺序。
真实数据 anchor 来自 data/personalize_inputs.json (CI 每周更新)。
环境变量：DEEPSEEK_API_KEY (Vercel project env)。"""
import json, os, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler

MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com/v1"
TIMEOUT = 45     # LLM 单次最长 45s（Vercel hobby maxDuration 60s）
MAX_RESUME = 4000
MAX_SKILLS = 800

def load_inputs():
    """读 personalize_inputs.json。文件可能在 api/ 或 ../data/"""
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, "personalize_inputs.json"),
              os.path.join(here, "..", "data", "personalize_inputs.json"),
              "data/personalize_inputs.json"):
        if os.path.exists(p):
            return json.load(open(p))
    raise FileNotFoundError("personalize_inputs.json not found")

def build_prompt(user, data):
    """user = {skills, target_role, years, resume?}"""
    sal = data.get("salary", {})
    fore = data.get("foresight", [])
    fore_lines = "\n".join(f"  - {f['theme']} ({f['sources']} sources cross-confirmed)" for f in fore)
    jd_top = data.get("jd_top_skills", [])
    baseline = data.get("baseline_skills", [])
    skills_input = str(user.get("skills","")).strip()[:MAX_SKILLS] or "(用户未填)"
    target = str(user.get("target_role","AI Engineer")).strip()
    years = user.get("years", 0)
    resume = str(user.get("resume","")).strip()[:MAX_RESUME]
    return f"""You are NorthStar's North America AI career compass. Output STRICT JSON ONLY.

USER:
- Self-described skills: {skills_input}
- Target role: {target}
- Years of professional experience: {years}
- Resume excerpt (optional, may be empty): {resume[:500] if resume else "(none)"}

NORTH AMERICA AI MARKET DATA (real, as of {data.get('as_of','recent')}):
- Median salary: ${sal.get('median_k',185)}k/yr; observed range ${sal.get('low_k',63)}-${sal.get('high_k',267)}k (n={sal.get('n',22)}); remote share {sal.get('remote_pct',11)}%. Source: {sal.get('source','W1 baseline')}.
- Baseline must-have skills (default required): {', '.join(baseline)}
- Top JD-frequency skills (ordered by demand): {', '.join(jd_top)}
- Foresight signals (≥2-source cross-confirmed — what's becoming a hard bar):
{fore_lines}

TASK: Produce a JSON object with this EXACT schema:
{{
  "fit_score": <int 0-100, how close user is to target role>,
  "baseline_gap": [<missing baseline skills, prioritized by impact>],
  "foresight_gap": [<missing foresight signals that matter for {target}>],
  "learn_order": [
    {{"skill": "<name>",
      "why": "<≤25 word rationale tying user's current skills × market signal>",
      "resource_hint": "<free/open starting point, e.g., 'LangGraph tutorial', 'deepeval quickstart'; NEVER paid bootcamps>"}}
  ],
  "next_3_actions": ["<concrete week-1 action>", "<concrete week-2 action>", "<concrete week-3 action>"],
  "reality_check": "<1 sentence on competition/salary/remote-availability given user's stage>"
}}

RULES:
- learn_order: 3-6 items, ordered by ROI for THIS user (consider what they already have).
- If user already has all baseline + most foresight signals, focus learn_order on depth/portfolio/specialization.
- Be specific to {target}; avoid generic "study LLMs" advice.
- All resource_hint must be free/open-source.
- Output the JSON object ONLY, no surrounding text."""

def call_llm(api_key, prompt):
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role":"system","content":"You output strict JSON only. No markdown, no commentary."},
            {"role":"user","content":prompt}
        ]
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        method="POST", data=body,
        headers={"Authorization":f"Bearer {api_key}", "Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        resp = json.load(r)
    return resp

class handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def do_GET(self):
        # health check
        try:
            d = load_inputs()
            self._send(200, {"ok":True, "model":MODEL, "as_of":d.get("as_of"),
                             "foresight_count":len(d.get("foresight",[])),
                             "salary_baseline":d.get("salary",{}).get("median_k")})
        except Exception as e:
            self._send(500, {"ok":False, "error":f"{type(e).__name__}: {e}"})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length","0"))
            user = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            data = load_inputs()
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                self._send(500, {"error":"LLM env not configured (DEEPSEEK_API_KEY missing)"}); return
            prompt = build_prompt(user, data)
            resp = call_llm(api_key, prompt)
            content = resp["choices"][0]["message"]["content"]
            try:
                result = json.loads(content)
            except Exception as je:
                self._send(502, {"error":"LLM returned non-JSON", "raw":content[:600]}); return
            self._send(200, {
                "result": result,
                "meta": {
                    "model": resp.get("model", MODEL),
                    "usage": resp.get("usage", {}),
                    "data_as_of": data.get("as_of"),
                }
            })
        except urllib.error.HTTPError as he:
            self._send(502, {"error":f"LLM HTTP {he.code}: {he.read()[:200].decode('utf-8','replace')}"})
        except Exception as e:
            self._send(500, {"error":f"{type(e).__name__}: {e}"})
