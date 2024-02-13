import requests
import json
import time


token = None

messages = []


def setup():
    resp = requests.post('https://github.com/login/device/code', headers={
            'accept': 'application/json',
            'editor-version': 'Neovim/0.6.1',
            'editor-plugin-version': 'copilot.vim/1.16.0',
            'content-type': 'application/json',
            'user-agent': 'GithubCopilot/1.155.0',
            'accept-encoding': 'gzip,deflate,br'
        }, data='{"client_id":"Iv1.b507a08c87ecfe98","scope":"read:user"}')


    # Parse the response json, isolating the device_code, user_code, and verification_uri
    resp_json = resp.json()
    device_code = resp_json.get('device_code')
    user_code = resp_json.get('user_code')
    verification_uri = resp_json.get('verification_uri')

    # Print the user code and verification uri
    print(f'Please visit {verification_uri} and enter code {user_code} to authenticate.')


    while True:
        time.sleep(5)
        resp = requests.post('https://github.com/login/oauth/access_token', headers={
            'accept': 'application/json',
            'editor-version': 'Neovim/0.6.1',
            'editor-plugin-version': 'copilot.vim/1.16.0',
            'content-type': 'application/json',
            'user-agent': 'GithubCopilot/1.155.0',
            'accept-encoding': 'gzip,deflate,br'
            }, data=f'{{"client_id":"Iv1.b507a08c87ecfe98","device_code":"{device_code}","grant_type":"urn:ietf:params:oauth:grant-type:device_code"}}')

        # Parse the response json, isolating the access_token
        resp_json = resp.json()
        access_token = resp_json.get('access_token')

        if access_token:
            break

    # Save the access token to a file
    with open('.copilot_token', 'w') as f:
        f.write(access_token)

    print('Authentication success!')


def get_token():
    global token
        # Check if the .copilot_token file exists
    while True:
        try:
            with open('.copilot_token', 'r') as f:
                access_token = f.read()
                break
        except FileNotFoundError:
            setup()
    # Get a session with the access token
    resp = requests.get('https://api.github.com/copilot_internal/v2/token', headers={
        'authorization': f'token {access_token}',
        'editor-version': 'Neovim/0.6.1',
        'editor-plugin-version': 'copilot.vim/1.16.0',
        'user-agent': 'GithubCopilot/1.155.0'
    })

    # Parse the response json, isolating the token
    resp_json = resp.json()
    token = resp_json.get('token')

def chat(message):
    global token, messages
    # If the token is None, get a new one
    if token is None:
        get_token()

    messages.append({
        "content": str(message),
        "role": "user"
    })

    try:
        resp = requests.post('https://api.githubcopilot.com/chat/completions', headers={
                'authorization': f'Bearer {token}',
                'Editor-Version': 'vscode/1.80.1',
            }, json={
                'intent': False,
                'model': 'gpt-4-1106-preview',
                'temperature': 0,
                'top_p': 1,
                'n': 1,
                'stream': True,
                'messages': messages
            })
    except requests.exceptions.ConnectionError:
        return ''

    result = ''

    # Parse the response text, splitting it by newlines
    resp_text = resp.text.split('\n')
    for line in resp_text:
        # If the line contains a completion, print it
        if line.startswith('data: {'):
            # Parse the completion from the line as json
            json_completion = json.loads(line[6:])
            try:
                completion = json_completion.get('choices')[0].get('delta').get('content')
                if completion:
                    result += completion
                else:
                    result += '\n'
            except:
                pass

    messages.append({
        "content": result,
        "role": "assistant"
    })
    
    if result == '':
        print(resp.status_code)
        print(resp.text)
    return result



def main():
    get_token()
    while True:
        print(chat(input('>>> ')))


if __name__ == '__main__':
    main()