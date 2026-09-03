import io
import base64
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
import edge_tts

from app.database.connection import get_db
from app.config import get_settings
from app.auth.rbac import get_current_user
from app.models.user import User
from app.models.personnel import Personnel

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    text: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    is_voice: bool = False

@router.post("")
async def chat_with_ai(request: ChatRequest, req: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Fetch personnel for name
    p = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    user_name = f"{p.first_name} {p.last_name}" if p else current_user.username

    lang = req.headers.get("Accept-Language", "en").split(",")[0]
    lang_map = {'hi': 'Hindi', 'bn': 'Bengali', 'pa': 'Punjabi', 'en': 'English'}
    target_language = lang_map.get(lang.split('-')[0], 'English')

    # We use a system prompt to define the AI's persona
    system_instruction = (
        f"You are the SAATHI Assistant, a supportive, positive wellness companion for military personnel. "
        f"The user you are speaking to is {user_name}. "
        f"Your goal is to provide brief, warm, and positive affirmations. "
        f"You also help them navigate the SAATHI dashboard. "
        f"Here are the rules:\n"
        f"1. Keep responses EXTREMELY short, simple, and empathetic. Never exceed 2 sentences or 30 words.\n"
        f"2. If they ask about their risk score, tell them a lower score is better and to check the contributing factors chart.\n"
        f"3. If they ask how to check in, tell them to click the 'Weekly wellbeing check-in' card at the bottom of the dashboard, or navigate to /p/checkin.\n"
        f"4. If they express distress, stress, or sadness, FIRST offer warm, empathetic positive affirmation and a very brief wellness recommendation. ONLY direct them to the 'Need support?' card or /p/support if they explicitly ask how to contact someone or if they are in severe crisis.\n"
        f"5. If they say their operational data is wrong, tell them to click the 'Think your operational data is incorrect?' link under their score.\n"
        f"6. If they ask about privacy or consent settings, explain them briefly: 'Wellness Check-ins' allows SAATHI to use their weekly answers for personalized recommendations. 'Unit Reporting' shares their data in strictly anonymized, unit-wide statistics where Commanders NEVER see their individual answers or identity. They have full control in the 'Data Privacy' section.\n"
        f"7. If they ask ANY off-topic or random questions (e.g., coding, recipes, general knowledge), politely refuse to answer and remind them you are here for SAATHI wellness support.\n"
        f"8. IMPORTANT: You MUST reply in the EXACT same language the user is speaking to you in. If they type in Bengali, reply in Bengali. If they type in Hindi, reply in Hindi. If their language is ambiguous, default to {target_language}.\n"
        f"Do not use markdown formatting unless absolutely necessary. Be very encouraging."
    )

    try:
        # Convert history format
        history = []
        for msg in request.messages[:-1]: # exclude the last message which is the prompt
            role = "model" if msg.role == "ai" else "user"
            history.append({"role": role, "parts": [{"text": msg.text}]})

        chat = client.chats.create(
            model="gemini-3.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            history=history
        )
        
        # Send the latest message
        latest_message = request.messages[-1].text
        response = chat.send_message(latest_message)
        
        audio_base64 = None
        if request.is_voice:
            try:
                import re
                if re.search(r'[\u0900-\u097F]', response.text):
                    voice = 'hi-IN-SwaraNeural'
                    tts_lang = 'hi'
                elif re.search(r'[\u0980-\u09FF]', response.text):
                    voice = 'bn-IN-TanishaaNeural'
                    tts_lang = 'bn'
                elif re.search(r'[\u0A00-\u0A7F]', response.text):
                    voice = 'en-IN-NeerjaExpressiveNeural' # Edge TTS fallback for Punjabi
                    tts_lang = 'pa'
                else:
                    voice = 'en-IN-NeerjaExpressiveNeural'
                    tts_lang = 'en'
                
                communicate = edge_tts.Communicate(response.text, voice)
                audio_data = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            except Exception as e:
                print(f"Edge TTS Error: {e}. Falling back to gTTS...")
                try:
                    from gtts import gTTS
                    fallback_lang = tts_lang if tts_lang in ['en', 'hi', 'bn', 'pa'] else 'en'
                    tts = gTTS(text=response.text, lang=fallback_lang, slow=False)
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    audio_base64 = base64.b64encode(fp.getvalue()).decode('utf-8')
                except Exception as fallback_err:
                    print(f"Fallback TTS Error: {fallback_err}")
        
        return {"text": response.text, "audio": audio_base64}
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response from AI")
