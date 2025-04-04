import json
import logging
import os
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Importer nos modules personnalisés
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from decision_engine.recommendation import RecommendationEngine
from content_generator.conversation import ConversationGenerator
from content_generator.story_generator import StoryGenerator
from device_control.device_manager import DeviceManager
from api.websocket_manager import WebSocketManager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger la configuration
CONFIG_PATH = "config/config.json"
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Créer l'application FastAPI
app = FastAPI(title="Angel Interactive Assistant API", 
              description="API pour l'assistant interactif basé sur Angel-server-capture",
              version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["server"]["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestionnaire de WebSockets
ws_manager = WebSocketManager()

# Initialisation des composants principaux
recommendation_engine = RecommendationEngine(CONFIG_PATH)
conversation_generator = ConversationGenerator(CONFIG_PATH)
story_generator = StoryGenerator(CONFIG_PATH)
device_manager = DeviceManager(CONFIG_PATH)

# Cache pour les résultats de Angel-server-capture
last_activity_results = {}

# Classes de modèles de données
class ActivityData(BaseModel):
    activity: str
    confidence: float
    timestamp: str
    details: Optional[Dict] = None
    user_id: Optional[str] = None

class RecommendationRequest(BaseModel):
    activity_data: ActivityData
    user_id: Optional[str] = None
    context: Optional[Dict] = None

class ConversationRequest(BaseModel):
    topic: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict] = None

class ConversationResponse(BaseModel):
    conversation_id: str
    user_input: Optional[str] = None

class StoryRequest(BaseModel):
    topic: str
    duration_min: Optional[int] = 2
    complexity: Optional[str] = "medium"
    user_id: Optional[str] = None

class DeviceActionRequest(BaseModel):
    action_type: str
    device_type: str
    params: Optional[Dict] = None

class ScenarioRequest(BaseModel):
    scenario_name: str
    params: Optional[Dict] = None

class FeedbackRequest(BaseModel):
    recommendation_id: str
    feedback: Dict

# Points de terminaison de l'API
@app.get("/")
async def root():
    """
    Point d'entrée racine, renvoie un message de bienvenue
    """
    return {"message": "Bienvenue sur l'API de l'assistant interactif Angel"}

@app.get("/status")
async def get_status():
    """
    Renvoie l'état actuel du système
    """
    return {
        "status": "online",
        "components": {
            "recommendation_engine": "active",
            "conversation_generator": "active",
            "story_generator": "active",
            "device_manager": "active"
        },
        "last_activity": last_activity_results.get("activity", "unknown")
    }

# Routes pour le moteur de recommandation
@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Génère des recommandations basées sur l'activité détectée
    """
    try:
        # Mettre à jour le cache d'activité
        last_activity_results.update(request.activity_data.dict())
        
        # Charger le profil utilisateur si disponible
        if request.user_id:
            user_profile = recommendation_engine.load_user_profile(request.user_id)
        
        # Obtenir les recommandations
        recommendations = recommendation_engine.get_recommendations(request.activity_data.dict())
        
        return {
            "success": True,
            "recommendations": recommendations,
            "activity": request.activity_data.activity,
            "confidence": request.activity_data.confidence
        }
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def process_feedback(request: FeedbackRequest):
    """
    Traite le feedback utilisateur sur les recommandations
    """
    try:
        recommendation_engine.process_feedback(request.recommendation_id, request.feedback)
        return {"success": True, "message": "Feedback traité avec succès"}
    except Exception as e:
        logger.error(f"Erreur lors du traitement du feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes pour le générateur de conversation
@app.post("/conversations/start")
async def start_conversation(request: ConversationRequest):
    """
    Démarre une nouvelle conversation
    """
    try:
        # Préparer le contexte
        context = request.context or {}
        if not context and last_activity_results:
            context["activity"] = last_activity_results.get("activity")
        
        # Ajouter le contexte temporel
        time_context = recommendation_engine.get_time_context()
        context["time_context"] = time_context
        
        # Démarrer la conversation
        response = conversation_generator.start_conversation(
            topic=request.topic,
            user_id=request.user_id,
            context=context
        )
        
        return response
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de la conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations/{conversation_id}/respond")
async def respond_to_conversation(conversation_id: str, request: ConversationResponse):
    """
    Continue une conversation existante
    """
    try:
        response = conversation_generator.continue_conversation(
            conversation_id=conversation_id,
            user_input=request.user_input
        )
        
        if "error" in response:
            raise HTTPException(status_code=404, detail=response["error"])
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération de réponse: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes pour le générateur d'histoires
@app.post("/stories")
async def generate_story(request: StoryRequest):
    """
    Génère une histoire sur un sujet donné
    """
    try:
        story = story_generator.generate_story(
            topic=request.topic,
            duration_min=request.duration_min,
            complexity=request.complexity
        )
        
        if "error" in story:
            raise HTTPException(status_code=500, detail=story["error"])
        
        return story
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération d'histoire: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Routes pour le contrôle des appareils
@app.post("/devices/action")
async def execute_device_action(request: DeviceActionRequest):
    """
    Exécute une action sur un appareil
    """
    try:
        result = device_manager.execute_action(
            action_type=request.action_type,
            device_type=request.device_type,
            params=request.params
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de l'action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/devices/scenario")
async def execute_scenario(request: ScenarioRequest):
    """
    Exécute un scénario prédéfini
    """
    try:
        result = device_manager.execute_scenario(
            scenario_name=request.scenario_name,
            params=request.params
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Scenario failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du scénario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices/status")
async def get_devices_status():
    """
    Récupère l'état de tous les appareils
    """
    try:
        statuses = device_manager.get_all_devices_status()
        return {"success": True, "statuses": statuses}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statuts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint pour recevoir les données d'Angel-server-capture
@app.post("/angel-capture")
async def receive_angel_data(activity_data: ActivityData, background_tasks: BackgroundTasks):
    """
    Reçoit les données de détection d'activité d'Angel-server-capture
    """
    try:
        # Mettre à jour le cache d'activité
        last_activity_results.update(activity_data.dict())
        
        # Traiter l'activité en arrière-plan
        background_tasks.add_task(process_activity_data, activity_data)
        
        return {"success": True, "message": "Données reçues"}
    except Exception as e:
        logger.error(f"Erreur lors de la réception des données: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_activity_data(activity_data: ActivityData):
    """
    Traite les données d'activité en arrière-plan
    """
    try:
        # Générer des recommandations
        recommendations = recommendation_engine.get_recommendations(activity_data.dict())
        
        # Envoyer aux clients connectés
        payload = {
            "type": "activity_update",
            "activity": activity_data.activity,
            "confidence": activity_data.confidence,
            "recommendations": recommendations
        }
        
        await ws_manager.broadcast(json.dumps(payload))
        
        logger.info(f"Activité traitée: {activity_data.activity}")
    except Exception as e:
        logger.error(f"Erreur lors du traitement d'activité: {str(e)}")

# WebSocket pour les mises à jour en temps réel
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Point de terminaison WebSocket pour les mises à jour en temps réel
    """
    await ws_manager.connect(websocket)
    try:
        # Envoyer l'état initial
        initial_status = {
            "type": "initial_status",
            "last_activity": last_activity_results.get("activity", "unknown"),
            "devices": device_manager.get_all_devices_status()
        }
        await websocket.send_text(json.dumps(initial_status))
        
        # Boucle de réception
        while True:
            data = await websocket.receive_text()
            
            # Traiter les commandes du client
            try:
                command = json.loads(data)
                if command.get("type") == "get_status":
                    await websocket.send_text(json.dumps({
                        "type": "status_update",
                        "last_activity": last_activity_results.get("activity", "unknown"),
                        "devices": device_manager.get_all_devices_status()
                    }))
            except json.JSONDecodeError:
                logger.error(f"Données WebSocket invalides: {data}")
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Point d'entrée principal
if __name__ == "__main__":
    import uvicorn
    
    host = config["server"]["host"]
    port = config["server"]["port"]
    
    logger.info(f"Démarrage du serveur sur {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
