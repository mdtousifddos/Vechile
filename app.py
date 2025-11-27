from flask import Flask, jsonify, request
import requests, re, binascii, json
from Crypto.Cipher import AES
import urllib3

app = Flask(__name__)
urllib3.disable_warnings()

def decrypt_cookie(a, b, c):
    a = binascii.unhexlify(a)
    b = binascii.unhexlify(b)
    c = binascii.unhexlify(c)
    return binascii.hexlify(AES.new(a, AES.MODE_CBC, b).decrypt(c)).decode()

def solve_aes(html):
    nums = re.findall(r'toNumbers\("([0-9a-f]+)"\)', html)
    if len(nums) >= 3:
        return decrypt_cookie(nums[0], nums[1], nums[2])
    return None

def get_vehicle_data(vehicle_number):
    session = requests.Session()
    session.verify = False
    url = f"https://hydrashop.in.net/vehicle_owner_number.php?q={vehicle_number}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36',
    }
    
    try:
        response = session.get(url, headers=headers, timeout=15)
        if "slowAES" in response.text:
            cookie_value = solve_aes(response.text)
            if cookie_value:
                session.cookies.set("__test", cookie_value)
                response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            mobile_match = re.search(r'[789]\d{9}', response.text)
            mobile_number = mobile_match.group() if mobile_match else None
            return {
                'success': True,
                'vehicle_number': vehicle_number,
                'owner_mobile_number': mobile_number,
                'response_length': len(response.text)
            }
        return {'success': False, 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/api/vehicle', methods=['GET'])
def api_vehicle():
    number = request.args.get('number')
    if not number:
        return jsonify({'error': 'Number parameter missing'})
    result = get_vehicle_data(number)
    return jsonify(result)

@app.route('/')
def home():
    return jsonify({
        'message': 'Vehicle Lookup API', 
        'usage': '/api/vehicle?number=UP64BB2558',
        'example': 'https://yourapp.onrender.com/api/vehicle?number=UP64BB2558'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
