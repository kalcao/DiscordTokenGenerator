import asyncio
import random
import requests
import json, time, curl_cffi, string
from urllib.parse import urlparse
import warnings, sys
from camoufox.async_api import AsyncCamoufox
from pypresence    import Presence
from datetime      import datetime
from colorama      import *
from pystyle       import *

from mail import *
import threading
import platform
import ctypes
import signal

total = 0
unlocked = 0
locked = 0
genStartTime = time.time()

class Log:
    lock = threading.Lock()

    @staticmethod
    def success(text):
        time_now = datetime.fromtimestamp(time.time()).strftime('%H:%M')
        with Log.lock:
            print(Colors.gray + time_now + " " + Colorate.Horizontal(Colors.green_to_cyan, "SUCCESS", 1) + Colors.gray + " > " + Colors.light_gray + text + Colors.reset)

    @staticmethod
    def error(text):
        time_now = datetime.fromtimestamp(time.time()).strftime('%H:%M')
        with Log.lock:
            print(Colors.gray + time_now + " " + Colorate.Horizontal(Colors.red_to_purple, "ERROR", 1) + Colors.gray + " > " + Colors.light_gray + text + Colors.reset)

    @staticmethod
    def captcha(cap_token):
        time_now = datetime.fromtimestamp(time.time()).strftime('%H:%M')
        with Log.lock:
            print(Colors.gray + time_now + " " + Colorate.Horizontal(Colors.blue_to_cyan, "CAPTCHA", 1) + Colors.gray + " > " + Colors.light_gray + f"[{Colors.light_gray}{cap_token[:16]}...{Colors.gray}]" + Colors.reset)

    @staticmethod
    def humanized(data):
        time_now = datetime.fromtimestamp(time.time()).strftime('%H:%M')
        with Log.lock:
            print(Colors.gray + time_now + " " + Colorate.Horizontal(Colors.purple_to_blue, "HUMANIZED", 1) + Colors.gray + " > (" + Colors.light_gray + data + Colors.gray + ")" + Colors.reset)

    @staticmethod
    def unlocked(token):
        time_now = datetime.fromtimestamp(time.time()).strftime('%H:%M')
        with Log.lock:
            print(Colors.gray + time_now + " " + Colorate.Horizontal(Colors.green_to_cyan, "UNLOCKED", 1) + Colors.gray + " > " + Colors.light_gray + token[:30] + "..." + Colors.reset)

    @staticmethod
    def locked(token):
        time_now = datetime.fromtimestamp(time.time()).strftime('%H:%M')
        with Log.lock:
            print(Colors.gray + time_now + " " + Colorate.Horizontal(Colors.red_to_purple, "LOCKED", 1) + Colors.gray + " > " + Colors.light_gray + token[:30] + "..." + Colors.reset)

    @staticmethod
    def onlined(token):
        time_now = datetime.fromtimestamp(time.time()).strftime('%H:%M')
        with Log.lock:
            print(Colors.gray + time_now + " " + Colorate.Horizontal(Colors.blue_to_white, "ONLINED", 1) + Colors.gray + " > " + Colors.light_gray + token[:30] + "..." + Colors.reset)

    @staticmethod
    def verified(token, email):
        time_now = datetime.fromtimestamp(time.time()).strftime('%H:%M')
        with Log.lock:
            print(Colors.gray + time_now + " " + Colorate.Horizontal(Colors.yellow_to_red, "VERIFIED", 1) + Colors.gray + " > " + Colors.light_gray + f"[{Colors.light_gray}{token[:30]}...{Colors.gray}] [{Colors.light_gray}{email}{Colors.gray}]" + Colors.reset)

class Title:
    def __init__(self):
        self.lock = threading.Lock()
        self.update_title()

    def update_title(self):
        try:
            global unlocked, locked, total
            if (unlocked + locked == 0):
                unlock_rate = 0
            else:
                unlock_rate = round((unlocked / (unlocked + locked)) * 100)

            title = f'Total: {total} | Unlocked: {unlocked} | Locked: {locked} | Unlock Rate: {unlock_rate}% | Time Elapsed: {round(time.time() - genStartTime, 2)}s'
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception as e:
            pass

        threading.Timer(0.1, self.update_title).start()

class Status:
    def status():
        client_id = "clientid for rpc. get one from https://discord.dev"
        while True:
            try:
                RPC = Presence(client_id)
                RPC.connect()
                while True:
                    if unlocked + locked == 0:
                        unlock_rate = 0
                    else:
                        unlock_rate = round((unlocked / (unlocked + locked)) * 100)

                    RPC.update(
                        large_image="channels4_profile_1_",
                        large_text="Generator",
                        details=f"Unlocked: {unlocked} | Locked: {locked}",
                        state=f"Unlock Rate: {unlock_rate}%",
                        start=int(genStartTime),
                    )
                    time.sleep(1)
            except Exception as e:
                pass
                time.sleep(5)


async def ask(direction, query):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer groq_api_key',
        }
        json_data = {
            'messages': [
                {
                    'role': 'user',
                    'content': f'Do not include markdown format, or any additional explanations. {direction}: "{query}"'
                },
            ],
            'model': 'moonshotai/kimi-k2-instruct-0905',
            'temperature': 1,
            'max_completion_tokens': 7168,
            'top_p': 1,
            'stream': False,
            'stop': None,
        }
        response = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=json_data, timeout=10)
        try:
            return response.json()['choices'][0]["message"]["content"].replace(".","")
        except: print(response.json()); return "No"
    except Exception as e: 
        print(f"Ask error: {e}")
        return "No"

async def main(email, global_name, password, join="", alternative_mail = "", proxy=""):
    global total, unlocked, locked
    
    token = ""
    finished = False
    start_time = time.time()
    total_bandwidth = {"upload": 0, "download": 0}  
    
    uuid_result = None
    p = urlparse(proxy) if proxy else None
    proxy = {"server": f"{p.scheme}://{p.hostname}:{p.port}", "username": p.username, "password": p.password} if p else None
    created_server = False
    browser_closed = False

    email_to_use = alternative_mail or email

    context = None
    page = None
    _page = None

    try:
        async with AsyncCamoufox(headless=False, humanize=False) as browser: 
            context = await browser.new_context(locale=random.choice(['en-US', 'ko-KR', 'th-TH', 'vi-VN', 'ms-MY', 'pt-BR', 'fr-CA', 'ru-RU']))
            page = await context.new_page()
            await page.bring_to_front()

            def should_block(url):
                url_lower = url.lower()
                return 'discord.com' in url_lower and any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico', '.ttf', '.otf', '.woff', '.woff2', '.eot'])

            await page.route(should_block, lambda route: route.abort())

            async def solve_hcaptcha_logic(current_page):
                nonlocal uuid_result, browser_closed
                uuid_result = None
                try: 
                    await current_page.wait_for_selector('iframe[src*="frame=checkbox"]', timeout=5000)
                    frame = current_page.frame_locator('iframe[src*="frame=checkbox"]')
                    await frame.locator("#checkbox").click(timeout=5000)
                except: 
                    pass
                
                puzzle_ifr = None
                try:
                    puzzle_ifr = current_page.frame_locator('iframe[src*="frame=challenge"]')
                    Log.success("Solving captcha")
                    
                    max_attempts_menu = 10
                    attempts_menu = 0
                    
                    while attempts_menu < max_attempts_menu:
                        try:
                            await puzzle_ifr.locator("#menu-info").click(timeout=1000)
                        except:
                            pass
                        
                        try:
                            text_challenge_locator = puzzle_ifr.locator("#text_challenge")
                            await text_challenge_locator.wait_for(state="visible", timeout=2000)
                            await text_challenge_locator.click(timeout=5000)
                            break
                        except:
                            attempts_menu += 1
                            await asyncio.sleep(1)
                    
                    if attempts_menu >= max_attempts_menu:
                        Log.error("Max attempts reached for text_challenge visibility")
                        return
                    
                    # After selecting text challenge, wait for prompt to load
                    await puzzle_ifr.locator("#prompt > span").wait_for(state="visible", timeout=10000)
                    
                except Exception as e:
                    Log.error(f"Failed to locate or interact with puzzle elements: {str(e)}")
                    return

                if puzzle_ifr is None or browser_closed:
                    return

                last_q = ""
                max_attempts = 100
                attempts = 0
                    
                while uuid_result is None and attempts < max_attempts and not browser_closed:
                    try:
                        await puzzle_ifr.locator("#prompt > span").wait_for(state="visible", timeout=5000)
                        
                        direction = await puzzle_ifr.locator("#prompt > span").text_content(timeout=5000)
                        q = await puzzle_ifr.locator("#prompt-text > span").text_content(timeout=5000)
                        
                        if last_q != q:
                            last_q = q
                            a = await ask(direction, q)
                            await puzzle_ifr.locator("body > div > div.challenge-container > div > div > div.challenge-input > input").click(timeout=5000)
                            await puzzle_ifr.locator("body > div > div.challenge-container > div > div > div.challenge-input > input").fill(a)
                            await puzzle_ifr.locator(".button-submit").click(timeout=5000)
                        else: 
                            await current_page.wait_for_timeout(500)
                    except Exception as e:
                        Log.error(f"Captcha step error: {str(e)}")
                        if "closed" in str(e).lower() or "timeout" in str(e).lower():
                            break
                        
                        # Retry by refreshing the challenge
                        try:
                            await puzzle_ifr.locator("#menu-refresh").click(timeout=1000)
                            await asyncio.sleep(2)  # Wait for refresh to load
                        except:
                            Log.error("Failed to click refresh button")
                        
                        await asyncio.sleep(1)
                    
                    attempts += 1

                if puzzle_ifr is None or browser_closed:
                    return

                last_q = ""
                max_attempts = 100
                attempts = 0
                    
                while uuid_result is None and attempts < max_attempts and not browser_closed:
                    try:
                        prompt_span_locator = puzzle_ifr.locator("#prompt > span")
                        if not await prompt_span_locator.is_visible(timeout=2000):
                            Log.error("#prompt > span not visible - retrying menu-info and text_challenge")
                            try:
                                await puzzle_ifr.locator("#menu-info").click(timeout=1000)
                            except:
                                pass

                        direction = await prompt_span_locator.text_content(timeout=5000)
                        q = await puzzle_ifr.locator("#prompt-text > span").text_content(timeout=5000)
                        if last_q != q:
                            last_q = q
                            a = await ask(direction, q)
                            await puzzle_ifr.locator("body > div > div.challenge-container > div > div > div.challenge-input > input").click(timeout=5000)
                            await puzzle_ifr.locator("body > div > div.challenge-container > div > div > div.challenge-input > input").fill(a)
                            await puzzle_ifr.locator(".button-submit").click(timeout=5000)
                        else: 
                            await current_page.wait_for_timeout(500)
                    except Exception as e:
                        Log.error(f"Captcha step error: {str(e)}")
                        if "closed" in str(e).lower() or "timeout" in str(e).lower():
                            break
                        await asyncio.sleep(1)
                    
                    attempts += 1

            async def capture_response(response):
                nonlocal uuid_result, token, created_server, finished, browser_closed, _page
                
                if browser_closed:
                    return
                    
                try:
                    body = await response.body()
                    total_bandwidth["download"] += len(body or b"")
                    req_data = response.request.post_data
                    if req_data:
                        total_bandwidth["upload"] += len(req_data.encode())
                except:
                    pass

                try:
                        
                    if (
                        "api.hcaptcha.com/checkcaptcha/" in response.url
                        and response.request.method == "POST"
                    ):
                        if response.status == 200:
                            parsed = await response.json()
                            if parsed.get('pass') == True:
                                uuid_result = parsed.get('generated_pass_UUID')
                                Log.captcha(uuid_result)

                    if 'api/v9/invites/' in response.url and response.request.method == "POST":
                        resp = await response.json()
                        if 'captcha_rqdata' in str(resp):
                            await solve_hcaptcha_logic(page)
                        else:
                            created_server = True
                            finished = True

                    if 'eligibility' in response.url:
                        if(_page): 
                            return
                        else:
                            if(join):
                                try:
                                    res = curl_cffi.get("https://discord.com/api/v9/users/@me/guilds", headers={"authorization": token}, timeout=10)
                                    is_unlocked = (res.status_code == 200)
                                    if not is_unlocked:
                                        finished = True
                                        return
                                    Log.success("Joining server" + join)
                                    await page.click('a[class*="joinCTA"]', timeout=5000)
                                    await page.fill('input[data-mana-component*="text-input"]', join)
                                    await page.keyboard.press("Enter")
                                except Exception as e: pass

                    if "api/v9/auth/verify" in response.url:
                        resp = await response.json()
                        if 'token' in resp:
                            token = resp['token']
                            Log.verified(token, alternative_mail or email)
                            
                            if not join:
                                finished = True
                            else:
                                wait_count = 0
                                while not created_server and wait_count < 15:
                                    await asyncio.sleep(1)
                                    wait_count += 1
                        else:
                            Log.captcha(token)
                            await solve_hcaptcha_logic(_page if _page else page)

                    if "/auth/register" in response.url:
                        resp = await response.json()
                        
                        if "captcha-required" in str(resp):
                            await solve_hcaptcha_logic(page)
                        else:
                            if "token" in resp:
                                token = resp['token']
                                Log.onlined(token)
                                await page.wait_for_url("https://discord.com/channels/@me", timeout=10000)
                                
                                mail_check_count = 0
                                max_mail_checks = 5
                                verify_mail_found = False
                                while mail_check_count < max_mail_checks and not verify_mail_found:
                                    mail_check_count += 1
                                    try:
                                        mails = read(email_to_use)
                                        verifyMail = mails['emails'][0]['body'].split('Verify Email: ')[1]
                                        Log.success(verifyMail)
                                        
                                        _page = await context.new_page()
                                        _page.on("response", capture_response)
                                        verify_mail_found = True
                                        
                                        await _page.goto(verifyMail, timeout=10000)
                                        Log.success(str(total_bandwidth))
                                        break
                                    except Exception as e: 
                                        Log.error(f"Checking inbox {mail_check_count} - {str(e)}")
                                        await asyncio.sleep(1)

                                if not verify_mail_found:
                                    Log.error("Mail verification timeout")
                                    finished = True
                            else:
                                Log.error("auth/register err: " + str(resp))
                                if "invalid-response" in str(resp):
                                    await solve_hcaptcha_logic(page)
                except Exception as e:
                    if not browser_closed:
                        Log.error(f"Response capture error: {str(e)}")

            await page.goto('http://discord.com/register', timeout=30000)
            add(email_to_use)

            page.on("response", capture_response)
            
            await page.fill('input[name="email"]', email_to_use)
            await page.fill('input[name="global_name"]', global_name)
            await page.fill('input[name="username"]', ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10)))
            await page.fill('input[name="password"]', password)
            
            await page.click('div[class^="year_"]', timeout=5000)
            await page.get_by_role('option', name=str(random.randint(1990, 2010))).click(timeout=5000)
            await page.click('div[class^="day_"]', timeout=5000)
            await page.get_by_role("option").nth(random.randint(0, await page.get_by_role("option").count() - 7)).click(timeout=5000)
            await page.click('div[class^="month_"]', timeout=5000)
            await page.get_by_role("option").nth(random.randint(0, await page.get_by_role("option").count() - 7)).click(timeout=5000)
            await page.click('button[type^="submit"]', timeout=5000)
            timeout_count = 0
            while not finished and timeout_count < 180:
                await asyncio.sleep(1)
                timeout_count += 1
            
            if not finished:
                await page.screenshot(path="screenshot.png", full_page=True)
                Log.error("Timed out")
            
            if token:
                res = curl_cffi.get("https://discord.com/api/v9/users/@me/guilds", headers={"authorization": token}, timeout=10)

                if res.status_code == 429:
                    try:
                        data = json.loads(res.text)
                        retry = data.get("retry_after", 1)
                    except:
                        retry = 1
                    time.sleep(retry)
                    res = curl_cffi.get("https://discord.com/api/v9/users/@me/guilds", headers={"authorization": token}, timeout=10)

                is_unlocked = (res.status_code == 200)
            else:
                is_unlocked = False

            total += 1

            if is_unlocked:
                unlocked += 1
                Log.unlocked(token)
                with open("tokens.txt", "a") as f:
                    f.write(f"{alternative_mail or email}:{password}:{token}\n")
                    f.flush()
            else:
                locked += 1
                print(res.status_code)
                print(res.text)
                Log.locked(token)
                with open("locked.txt", "a") as f:
                    f.write(f"{alternative_mail or email}:{password}:{token}\n")
                    f.flush()
            
            end_time = time.time()
            duration = end_time - start_time
                
            result = {  
                "email": alternative_mail or email,
                "password": password,
                "took": round(duration, 2),
                "token": token,
                "unlocked": is_unlocked
            }
            return result
    finally:
        browser_closed = True
        
        if page:
            try:
                page.remove_listener("response", capture_response)
                page.remove_listener("request", capture_request)
            except:
                pass
        
        if _page:
            try:
                _page.remove_listener("response", capture_response)
            except:
                pass
        
        if context:
            for context_page in context.pages:
                try:
                    await context_page.close(timeout=5000)
                except:
                    pass
            try:
                await context.close()
            except Exception as e:
                print(f"Context close error: {str(e)}")
        
        try:
            await browser.close()
        except Exception as e:
            print(f"Browser close error: {str(e)}")

async def main_loop():
    while True:
        try:
            mail = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10)) + "@outlook.com" 
            nickname = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))

            try:
                result = await asyncio.wait_for(main(mail, nickname, mail + "A!@", join="invite code"), timeout=300) # join arg is optional. only if you want to make tokens join in a server.
                print(f"{result}")
            except Exception as e:
                print(f"gen err: {str(e)}")
        except Exception as e:
            print(f"main loop err: {str(e)}")

def signal_handler(sig, frame):
    print('bye')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    threading.Thread(target=Status.status, daemon=True).start()
    title = Title()
    asyncio.run(main_loop())
