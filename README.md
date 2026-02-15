# Елена – универсальный самообучающийся AI-агент

Живёт локально на Linux Mint, использует:
- Qwen 2.5 14B (логика)
- Moondream (зрение)
- Whisper (слух)
- RHVoice (голос, профиль Елена)
- ChromaDB (векторная память)

## Установка

```bash
git clone https://github.com/yourusername/ai-agent.git
cd /mnt/ai_data/ai-agent
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt