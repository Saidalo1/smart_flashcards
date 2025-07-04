import base64
from icon import icon_b64

with open('app_icon.png', 'wb') as f:
    f.write(base64.b64decode(icon_b64))
