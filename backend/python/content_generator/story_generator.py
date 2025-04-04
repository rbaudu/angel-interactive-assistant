import json
import logging
import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoryGenerator:
    """
    Générateur d'histoires pour l'assistant interactif.
    Utilise des APIs d'IA comme Claude pour créer des histoires engageantes.
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialise le générateur d'histoires avec la configuration
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        # Chargement de la configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Extraire les paramètres de configuration
        self.ai_config = self.config["content_generation"]
        self.provider = self.ai_config["ai_provider"]
        self.api_key = self.ai_config["api_key"]
        self.max_tokens = self.ai_config["max_tokens"]
        self.temperature = self.ai_config["temperature"]
        
        # Paramètres des histoires
        self.max_duration_sec = self.ai_config["stories"]["max_duration_sec"]
        self.categories = self.ai_config["stories"]["categories"]
        
        # Historique des histoires générées
        self.story_history = {}
        
        logger.info(f"Générateur d'histoires initialisé avec le fournisseur: {self.provider}")
    
    def generate_story(self, topic: str, duration_min: int = 2, complexity: str = "medium") -> Dict:
        """
        Génère une histoire complète sur un sujet donné
        
        Args:
            topic: Sujet de l'histoire
            duration_min: Durée approximative de l'histoire en minutes
            complexity: Niveau de complexité ("simple", "medium", "complex")
            
        Returns:
            Dictionnaire contenant l'histoire générée
        """
        # Validation des paramètres
        if duration_min * 60 > self.max_duration_sec:
            logger.warning(f"Durée demandée ({duration_min} min) supérieure à la limite configurée ({self.max_duration_sec/60} min)")
            duration_min = int(self.max_duration_sec / 60)
        
        # Ajuster la longueur en fonction de la durée souhaitée (approximatif)
        # En moyenne, 150 mots = 1 minute de parole
        words_count = duration_min * 150
        
        # Ajuster la complexité
        if complexity == "simple":
            complexity_instructions = "Utilise un vocabulaire simple et des phrases courtes. L'histoire doit être facile à suivre."
        elif complexity == "complex":
            complexity_instructions = "Tu peux utiliser un vocabulaire riche et des structures narratives plus complexes."
        else:  # medium
            complexity_instructions = "Utilise un niveau de langage intermédiaire, accessible à la plupart des adultes."
        
        prompt = f"""Génère une histoire engageante sur le thème "{topic}".
L'histoire doit faire environ {words_count} mots pour une durée de lecture d'environ {duration_min} minutes.
{complexity_instructions}
L'histoire doit avoir un début clair, un développement et une conclusion satisfaisante.
Ne mentionne pas la durée ou le nombre de mots dans ton récit.
Commence directement par l'histoire sans introduction."""
        
        try:
            story_content = self._call_ai_api(prompt)
            
            # Générer un identifiant unique pour l'histoire
            import uuid
            story_id = str(uuid.uuid4())
            
            story = {
                "story_id": story_id,
                "topic": topic,
                "content": story_content,
                "duration_min": duration_min,
                "complexity": complexity,
                "created_at": datetime.now().isoformat()
            }
            
            # Ajouter à l'historique
            self.story_history[story_id] = story
            
            return story
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'histoire: {str(e)}")
            return {
                "story_id": "error",
                "error": str(e),
                "content": "Je suis désolé, je n'arrive pas à raconter cette histoire maintenant. Essayons autre chose."
            }
    
    def get_story(self, story_id: str) -> Optional[Dict]:
        """
        Récupère une histoire précédemment générée
        
        Args:
            story_id: Identifiant de l'histoire
            
        Returns:
            Histoire demandée ou None si non trouvée
        """
        return self.story_history.get(story_id)
    
    def _call_ai_api(self, prompt: str) -> str:
        """
        Appelle l'API d'IA pour générer du contenu
        
        Args:
            prompt: Prompt textuel à envoyer à l'API
            
        Returns:
            Réponse générée par l'API
        """
        try:
            if self.provider == "claude":
                return self._call_claude_api(prompt)
            elif self.provider == "gpt":
                return self._call_gpt_api(prompt)
            else:
                logger.error(f"Fournisseur non pris en charge: {self.provider}")
                return "Il était une fois... Désolé, je n'arrive pas à trouver l'inspiration pour raconter cette histoire."
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à l'API {self.provider}: {str(e)}")
            return "Il était une fois... Désolé, je n'arrive pas à continuer cette histoire pour le moment."
    
    def _call_claude_api(self, prompt: str) -> str:
        """
        Appelle l'API Claude d'Anthropic
        
        Args:
            prompt: Prompt textuel à envoyer
            
        Returns:
            Réponse générée
        """
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": "Tu es un conteur d'histoires créatif. Tu crées des histoires originales, engageantes et adaptées au sujet demandé. Tes histoires ont un début, un milieu et une fin clairement définis.",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            logger.error(f"Erreur Claude API: {response.status_code}, {response.text}")
            raise Exception(f"Erreur API: {response.status_code}")
    
    def _call_gpt_api(self, prompt: str) -> str:
        """
        Appelle l'API GPT d'OpenAI
        
        Args:
            prompt: Prompt textuel à envoyer
            
        Returns:
            Réponse générée
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": "Tu es un conteur d'histoires créatif. Tu crées des histoires originales, engageantes et adaptées au sujet demandé. Tes histoires ont un début, un milieu et une fin clairement définis."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"Erreur GPT API: {response.status_code}, {response.text}")
            raise Exception(f"Erreur API: {response.status_code}")
    
    def get_story_recommendations(self, user_preferences: Optional[List[str]] = None) -> List[Dict]:
        """
        Génère des recommandations d'histoires basées sur les préférences utilisateur
        
        Args:
            user_preferences: Liste des catégories préférées de l'utilisateur
            
        Returns:
            Liste de suggestions d'histoires
        """
        # Si aucune préférence n'est fournie, utiliser toutes les catégories
        if not user_preferences:
            user_preferences = self.categories
        
        # Filtrer les préférences existantes dans notre configuration
        valid_preferences = [pref for pref in user_preferences if pref in self.categories]
        
        # Si aucune préférence valide, utiliser toutes les catégories
        if not valid_preferences:
            valid_preferences = self.categories
        
        # Générer des suggestions d'histoires
        import random
        suggestions = []
        
        for category in valid_preferences[:3]:  # Limiter à 3 suggestions
            # Générer des idées de sujets pour cette catégorie
            if category == "aventure":
                topics = ["Une aventure en forêt tropicale", "La quête du trésor perdu", "L'exploration d'une grotte mystérieuse"]
            elif category == "humour":
                topics = ["Une journée catastrophique", "Le malentendu comique", "L'animal qui parlait trop"]
            elif category == "culture":
                topics = ["La légende du village ancien", "Le secret de la bibliothèque", "La découverte archéologique"]
            elif category == "science":
                topics = ["Le voyage dans l'espace", "L'invention révolutionnaire", "La découverte scientifique"]
            elif category == "histoire":
                topics = ["L'aventure au temps des chevaliers", "Le mystère de l'Égypte ancienne", "La vie à la cour royale"]
            else:
                topics = [f"Une histoire sur {category}"]
            
            # Choisir un sujet au hasard
            topic = random.choice(topics)
            
            suggestions.append({
                "category": category,
                "topic": topic,
                "duration_min": random.choice([2, 3, 5]),
                "complexity": random.choice(["simple", "medium"])
            })
        
        return suggestions
