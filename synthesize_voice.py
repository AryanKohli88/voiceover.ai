import requests
import base64
from typing import Optional, Union

def synthesize_voice(
    api_key: str,
    text: str,
    output_path,
    input_language,
    endpoint_url,
    model_name,
    input_speaker: str = "male",
    timeout: int = 30,
) -> Union[str, bytes]:
    if not api_key:
        raise ValueError("api_key is required")
    if not text:
        raise ValueError("text is required")

    url = endpoint_url

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "modelName": model_name,
        "input_text": text,
        "input_language": input_language,
        "input_speaker": input_speaker
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()

    result = resp.json()
    if "output" not in result:
        raise KeyError("API response missing 'output' field")

    base64_audio = result["output"]
    audio_data = base64.b64decode(base64_audio)

    if output_path:
        with open(output_path, "wb") as f:
            f.write(audio_data)
        return output_path
    else:
        return audio_data
