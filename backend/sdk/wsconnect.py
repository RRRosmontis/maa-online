import asyncio
import websockets
import base64
import time
import json
import requests
from aiortc.sdp import candidate_from_sdp, candidate_to_sdp
from aiortc.contrib.signaling import object_from_string, object_to_string
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay

relay = MediaRelay()
sub_key = None

def login(phonenumber, code=None, token_file="token"):
    """Request an SMS code (when code is None) or exchange it for a token."""
    if "-" not in phonenumber:
        raise ValueError("phone number must use the '<country-code>-<number>' form")

    if code is None:
        response = requests.post(
            "https://n.cg.163.com/api/v1/phone-captchas/" + phonenumber,
            timeout=15,
        )
        response.raise_for_status()
        print("input the code received by your phone")
        code = input().strip()

    country_code, phone = phonenumber.split("-", 1)
    headers = {"Content-Type": "application/json;charset=utf-8"}
    data = {
        "auth_method": "phone-captcha",
        "ctcode": country_code,
        "phone": phone,
        "captcha": str(code).strip(),
        "device_info": {
            "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
            "appVersion": "5.0 (X11)",
            "codecs": ["h264", "vp8", "vp9"],
        },
    }
    response = requests.post(
        "https://n.cg.163.com/api/v1/tokens",
        headers=headers,
        json=data,
        timeout=15,
    )
    response.raise_for_status()
    user_obj = response.json()
    token = user_obj.get("token")
    if not token:
        raise RuntimeError("login response did not contain a token")

    with open(token_file, "w", encoding="utf-8") as token_handle:
        token_handle.write(token)
    try:
        import os
        os.chmod(token_file, 0o600)
    except OSError:
        pass
    print("login ok!")
    return token


def encode_mess(message):
    global sub_key
    mess = str.encode(message)
    m = b""
    for i in mess:
        m += ((i+sub_key)%256).to_bytes(1, byteorder='big')
    res = base64.b64encode(m)
    return res

def decode_mess(message):
    try:
        mess = base64.b64decode(message)
    except:
        return message
    global sub_key
    if sub_key == None:
        fbyte = mess[0]
        sbyte = mess[1]
        for j in range(0, 256):
            if(chr((fbyte-j)%256)=="[" and chr((sbyte-j)%256) == "{" and chr((mess[2]-j)%256) == "\""):
                sub_key = j
                break
            if chr((fbyte-j)%256) == "{" and chr((sbyte-j)%256) == "\"":
                sub_key = j
                break
    m = ""
    for i in mess:
         m += chr((i-sub_key)%256)
    return m

def get_basic_info(token):
    headers = {"Authorization": "Bearer " + token}
    response = requests.get(
        "https://n.cg.163.com/api/v2/users/@me",
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()
    info = json.loads(decode_mess(response.text))
    return info["yunxin_account"]["accid"]

def request_ticket(token, game_code, regions=None, codecs=None, width=1280, height=720):
    if regions is None:
        regions = ["hdcz", "hbsjz"]
    if codecs is None:
        codecs = ["h264", "vp8", "vp9"]
    req_obj = {
        "regions": regions,
        "game_code": game_code,
        "codecs": codecs,
        "width": width,
        "height": height
    }
    global sub_key
    
    req_str = encode_mess(json.dumps(req_obj).replace("'","\""))
    headers = {
        "Authorization": "Bearer " +token,
        "Content-Type": "application/octet-stream" 
    }
    response = requests.post(
        "https://n.cg.163.com/api/v2/tickets",
        headers=headers,
        data=req_str,
        timeout=15,
    )
    if not response.ok:
        try:
            detail = decode_mess(response.text)
        except Exception:
            detail = ""
        raise RuntimeError(f"ticket request failed with HTTP {response.status_code}: {detail[:500]}")
    info_obj = json.loads(decode_mess(response.text))
    return info_obj["gateway_url"]

def find_region(token, game_code):
    headers = {"Authorization": "Bearer " + token}
    response = requests.get(
        "https://n.cg.163.com/api/v2/media-servers",
        params={"game_code": game_code},
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()
    regions = json.loads(decode_mess(response.text))
    return [item["region"] for item in regions]

def exit_game(token, game_code):
    headers = {"Authorization": "Bearer " + token}
    response = requests.delete(
        f"https://n.cg.163.com/api/v2/users/@me/games-playing/{game_code}",
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()
    return response.text

async def connect(token, game_code, w=1280, h=720, quality="high", codecs=None, platform=0, fps="30"):
        if codecs is None:
            codecs = ["h264", "vp8", "vp9"]
        user_id = await asyncio.to_thread(get_basic_info, token)
        regions = await asyncio.to_thread(find_region, token, game_code)
        uri = await asyncio.to_thread(
            request_ticket,
            token,
            game_code,
            regions,
            codecs,
            w,
            h,
        )
        websocket = await websockets.connect(uri)
        auth_obj = { 
            "id": str(int(round(time.time() * 1000))),
            "op": "auth",
            "data": {
                "user_id": user_id,
                "token": token,
                "game_code": game_code,
                "w": w,
                "h": h,
                "quality": quality,
                "codecs": codecs,
                "platform": platform,
                "fps": fps
            }
        }
        auth_str = json.dumps(auth_obj)
        await websocket.send(auth_str)
        auth_res = await websocket.recv()
        auth_res = decode_mess(auth_res)
        try:
            de_res = json.loads(auth_res)
        except (TypeError, json.JSONDecodeError) as exc:
            await websocket.close()
            raise RuntimeError("failed to decode cloud-game auth response") from exc
        if de_res.get("op") != "offer":
            error_message = de_res.get("data", {}).get("errmsg", "unexpected signaling response")
            await websocket.close()
            raise RuntimeError(error_message)
        new_sdp = {}
        new_sdp["type"] = de_res["op"]
        new_sdp["sdp"] = de_res["data"]["sdp"]
        new_sdp = json.dumps(new_sdp)
        return new_sdp, websocket


def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))

async def send_action(sock, action):

    action = encode_mess(json.dumps(action).replace("'","\""))
    await sock.send(action)
    pong_waiter = await sock.ping()
    await pong_waiter

def pack_message(cmd, data):
    if cmd == "mm": # move mouse, data: x, y
        action = {"id":str(int(round(time.time() * 1000))),"op":"input","data":{"cmd":"1 %d %d 0" % (data["x"], data["y"])}}
    elif cmd == "cm": # click mouse, data: x, y
        action = {"id":str(int(round(time.time() * 1000))),"op":"input","data":{"cmd":"3 %d %d 0" % (data["x"], data["y"])}}
    elif cmd == "ip": # keyboard input, data: single keyborad word
        action = {"id":str(int(round(time.time() * 1000))),"op":"input","data":{"cmd":"5 %s" % data["word"]}}
    else:
        action = {}
    return action

#print(decode_mess("2YDHwoCYgI+VlI6SlpeTk4+Uj5eAioDNzoCYgMfMztPSgIqAwr/Sv4CY2YDBy8KAmICRfpaOln6TkZB+joDb2w=="))