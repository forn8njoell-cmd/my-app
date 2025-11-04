from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class PromptGenerate(BaseModel):
    subject: str
    setting: Optional[str] = ""
    lighting: Optional[str] = ""
    camera_angle: Optional[str] = ""
    style: Optional[str] = ""
    mood: Optional[str] = ""
    additional_details: Optional[str] = ""

class AIEnhanceRequest(BaseModel):
    basic_prompt: str

class ImageGenerateRequest(BaseModel):
    prompt: str

class PromptSave(BaseModel):
    prompt_text: str
    prompt_type: str
    parameters: Optional[Dict[str, Any]] = None
    image_data: Optional[str] = None

class PromptResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    prompt_text: str
    prompt_type: str
    parameters: Optional[Dict[str, Any]] = None
    image_data: Optional[str] = None
    created_at: datetime
    is_favorite: bool = False

class PromptResponseModel(BaseModel):
    prompt: str

class ImageResponse(BaseModel):
    image_data: str
    mime_type: str

# Routes
@api_router.get("/")
async def root():
    return {"message": "Master Prompt Generator API"}

@api_router.post("/prompts/generate-form", response_model=PromptResponseModel)
async def generate_prompt_from_form(data: PromptGenerate):
    """Generate photorealistic prompt from structured form data"""
    try:
        # Build detailed photorealistic prompt
        prompt_parts = []
        
        # Start with subject
        prompt_parts.append(f"Professional commercial photography of {data.subject}")
        
        # Add setting if provided
        if data.setting:
            prompt_parts.append(f"in {data.setting}")
        
        # Add lighting details
        lighting_map = {
            "natural": "natural daylight, soft shadows",
            "studio": "professional studio lighting, three-point lighting setup",
            "golden_hour": "golden hour lighting, warm tones, soft glow",
            "dramatic": "dramatic lighting with strong contrast, chiaroscuro effect",
            "soft": "soft diffused lighting, even illumination",
            "backlit": "backlit with rim lighting, glowing edges"
        }
        lighting_desc = lighting_map.get(data.lighting.lower(), data.lighting) if data.lighting else "professional lighting"
        prompt_parts.append(f"{lighting_desc}")
        
        # Add camera details
        camera_map = {
            "eye_level": "shot at eye-level, straight-on perspective",
            "top_down": "top-down flat lay perspective, bird's eye view",
            "close_up": "extreme close-up macro shot, detailed textures",
            "wide": "wide-angle shot, environmental context",
            "45_degree": "shot at 45-degree angle, dynamic composition",
            "low_angle": "low-angle hero shot, powerful perspective"
        }
        camera_desc = camera_map.get(data.camera_angle.lower(), data.camera_angle) if data.camera_angle else "professional camera angle"
        prompt_parts.append(f"{camera_desc}")
        
        # Add style/mood
        style_additions = []
        if data.style:
            style_map = {
                "minimalist": "clean minimalist aesthetic, simple composition",
                "luxury": "luxury premium aesthetic, high-end feel",
                "vibrant": "vibrant saturated colors, energetic mood",
                "muted": "muted tones, sophisticated color palette",
                "modern": "modern contemporary style, sleek design",
                "rustic": "rustic organic aesthetic, natural materials"
            }
            style_additions.append(style_map.get(data.style.lower(), data.style))
        
        if data.mood:
            style_additions.append(f"{data.mood} atmosphere")
        
        if style_additions:
            prompt_parts.append(", ".join(style_additions))
        
        # Add photorealistic quality markers
        prompt_parts.append("captured with professional DSLR camera, 50mm lens, f/2.8 aperture")
        prompt_parts.append("8K resolution, ultra-detailed, photorealistic, sharp focus")
        prompt_parts.append("professional color grading, commercial quality")
        prompt_parts.append("no artificial elements, natural product placement")
        
        # Add additional details
        if data.additional_details:
            prompt_parts.append(data.additional_details)
        
        # Construct final prompt
        final_prompt = ", ".join(prompt_parts)
        
        return PromptResponseModel(prompt=final_prompt)
    
    except Exception as e:
        logger.error(f"Error generating form prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/prompts/enhance", response_model=PromptResponseModel)
async def enhance_prompt(data: AIEnhanceRequest):
    """Use AI to enhance basic prompt into detailed photorealistic prompt"""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        # Create LLM chat instance for text generation
        chat = LlmChat(
            api_key=api_key,
            session_id=f"enhance_{uuid.uuid4()}",
            system_message="You are an expert in creating photorealistic image generation prompts for commercial advertising. Transform basic ideas into detailed, professional prompts that will produce images indistinguishable from real photographs."
        )
        chat.with_model("openai", "gpt-4o-mini")
        
        enhancement_request = f"""Transform this basic prompt into a highly detailed, photorealistic commercial photography prompt:

"{data.basic_prompt}"

Include:
- Specific subject details and product placement
- Professional lighting setup (type, direction, quality)
- Camera specifications (angle, lens, aperture, focal length)
- Composition and framing details
- Color palette and mood
- Texture and material details
- Environmental context and setting
- Professional quality markers (8K, sharp focus, etc.)
- Natural, non-AI aesthetic descriptors

Make it sound like a professional photographer's shot list. Return ONLY the enhanced prompt, no explanations."""
        
        msg = UserMessage(text=enhancement_request)
        response = await chat.send_message_and_wait_response(msg)
        enhanced_prompt = response.text.strip()
        
        return PromptResponseModel(prompt=enhanced_prompt)
    
    except Exception as e:
        logger.error(f"Error enhancing prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/prompts/generate-image", response_model=ImageResponse)
async def generate_image(data: ImageGenerateRequest):
    """Generate image using Nano Banana (Gemini imagen)"""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        # Create LLM chat instance for image generation
        chat = LlmChat(
            api_key=api_key,
            session_id=f"image_{uuid.uuid4()}",
            system_message="Generate photorealistic commercial images"
        )
        chat.with_model("gemini", "gemini-2.5-flash-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=data.prompt)
        text, images = await chat.send_message_multimodal_response(msg)
        
        if not images or len(images) == 0:
            raise HTTPException(status_code=500, detail="No image generated")
        
        # Return first generated image
        return ImageResponse(
            image_data=images[0]['data'],
            mime_type=images[0]['mime_type']
        )
    
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/prompts/save", response_model=PromptResponse)
async def save_prompt(data: PromptSave):
    """Save prompt to history"""
    try:
        prompt_obj = {
            "id": str(uuid.uuid4()),
            "prompt_text": data.prompt_text,
            "prompt_type": data.prompt_type,
            "parameters": data.parameters,
            "image_data": data.image_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_favorite": False
        }
        
        await db.prompts.insert_one(prompt_obj)
        
        prompt_obj['created_at'] = datetime.fromisoformat(prompt_obj['created_at'])
        return PromptResponse(**prompt_obj)
    
    except Exception as e:
        logger.error(f"Error saving prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/prompts/history", response_model=List[PromptResponse])
async def get_history():
    """Get all prompts history"""
    try:
        prompts = await db.prompts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        for prompt in prompts:
            if isinstance(prompt.get('created_at'), str):
                prompt['created_at'] = datetime.fromisoformat(prompt['created_at'])
        
        return prompts
    
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/prompts/{prompt_id}/favorite")
async def toggle_favorite(prompt_id: str):
    """Toggle favorite status"""
    try:
        prompt = await db.prompts.find_one({"id": prompt_id}, {"_id": 0})
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        new_favorite_status = not prompt.get('is_favorite', False)
        await db.prompts.update_one(
            {"id": prompt_id},
            {"$set": {"is_favorite": new_favorite_status}}
        )
        
        return {"success": True, "is_favorite": new_favorite_status}
    
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/prompts/favorites", response_model=List[PromptResponse])
async def get_favorites():
    """Get favorite prompts"""
    try:
        prompts = await db.prompts.find({"is_favorite": True}, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        for prompt in prompts:
            if isinstance(prompt.get('created_at'), str):
                prompt['created_at'] = datetime.fromisoformat(prompt['created_at'])
        
        return prompts
    
    except Exception as e:
        logger.error(f"Error fetching favorites: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()