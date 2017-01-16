#coding:utf-8
import time
from apns import APNs, Frame, Payload
from EasyFind.config import  PUSH_PATH

apns = APNs(use_sandbox=True, cert_file=PUSH_PATH, key_file=PUSH_PATH)

# Send a notification
token_hex = '6653d92e6319ad89d2d49c79d78df8a380ac8c910e0e8cb455beec9ebc84a58b'
# payload = Payload(alert="Hello World!", sound="default", badge=1)
payload = Payload(alert="New Message！", custom = {'longitude':'127.000','latitude':'30.200','task_id':'1321432532','discover_time':'2015-06-02 16:10'})
apns.gateway_server.send_notification(token_hex, payload)

# Send multiple notifications in a single transmission
# frame = Frame()
# identifier = 1
# expiry = time.time()+3600
# priority = 10
# frame.add_item('b5bb9d8014a0f9b1d61e21e796d78dccdf1352f23cd32812f4850b87', payload, identifier, expiry, priority)
# apns.gateway_server.send_notification_multiple(frame)
