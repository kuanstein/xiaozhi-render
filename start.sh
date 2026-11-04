#!/bin/bash
cd /app/main/xiaozhi-server
mkdir -p data tmp
cat > data/.config.yaml <<CFG
server:
  ip: 127.0.0.1
  port: 8000
  http_port: 8003
  websocket: ${PUBLIC_WS_URL:-wss://${RENDER_EXTERNAL_HOSTNAME}/xiaozhi/v1/}
selected_module:
  VAD: SileroVAD
  ASR: GroqASR
  LLM: SiliconFlowLLM
  TTS: EdgeTTS
  Memory: mem_local_short
LLM:
  SiliconFlowLLM:
    type: openai
    model_name: Qwen/Qwen2.5-7B-Instruct
    url: https://api.siliconflow.com/v1
    api_key: ${SILICONFLOW_API_KEY}
ASR:
  GroqASR:
    type: openai
    api_key: ${GROQ_API_KEY}
    base_url: https://api.groq.com/openai/v1/audio/transcriptions
    model_name: whisper-large-v3-turbo
    output_dir: tmp/
TTS:
  EdgeTTS:
    type: edge
    voice: zh-CN-XiaoxiaoNeural
    output_dir: tmp/
CFG
python - <<'PY'
p="core/utils/dialogue.py"; s=open(p,encoding="utf-8").read()
old="        actual_messages = [m for m in non_system_messages if not m.is_temporary]\n"
new=old+"        if len(actual_messages) > 16:\n            actual_messages = actual_messages[-16:]\n            while actual_messages and actual_messages[0].role != 'user':\n                actual_messages = actual_messages[1:]\n"
if s.count(old)==1 and "len(actual_messages) > 16" not in s: open(p,"w",encoding="utf-8").write(s.replace(old,new))
PY
python app.py &
exec python /app/proxy.py
