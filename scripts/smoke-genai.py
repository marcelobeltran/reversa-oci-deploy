"""Bounded inference check. Reads credentials privately; prints no keys or responses."""
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', default='us-chicago-1')
    parser.add_argument('--model', default='xai.grok-4.6')
    parser.add_argument('--outputs', type=Path, default=Path('local/outputs.json'))
    parser.add_argument('--checkpoint', type=Path, default=Path('local/runtime.private.json'))
    args = parser.parse_args()
    outputs = json.loads(args.outputs.read_text())
    private = json.loads(args.checkpoint.read_text())
    payload = {'model': args.model, 'max_tokens': 32,
               'messages': [{'role': 'user', 'content': 'Reply only with OK.'}]}
    request = urllib.request.Request(
        f'https://inference.generativeai.{args.region}.oci.oraclecloud.com/openai/v1/chat/completions',
        data=json.dumps(payload).encode(), headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+private['api_key']['keys'][0]['key'],
            'OpenAI-Project': outputs['genai_project_ocid']['value']})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
        print(json.dumps({'success': bool(result.get('choices')), 'model': result.get('model'),
                          'usage': result.get('usage')}))
    except urllib.error.HTTPError as error:
        # Do not echo request headers, response bodies or SDK credential objects.
        print(json.dumps({'success': False, 'http_status': error.code}))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
