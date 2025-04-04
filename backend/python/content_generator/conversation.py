import json
import logging
import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationGenerator:
    """
    Générateur de conversations et de dialogues pour l'assistant interactif.
    Utilise des APIs d'IA comme Claude pour créer des conversations naturelles.
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialise le générateur de conversation avec la configuration
        
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
        
        # Paramètres de conversation
        self.max_turns = self.ai_config["conversations"]["max_turns"]
        self.available_topics = self.ai_config["conversations"]["topics"]
        
        # Historique des conversations
        self.conversation_history = {}
        
        # État de la conversation en cours
        self.current_conversation_id = None
        self.current_turn = 0
        
        logger.info(f"Générateur de conversation initialisé avec le fournisseur: {self.provider}")
    
    def start_conversation(self, topic: str = None, user_id: str = None, context: Dict = None) -> Dict:
        """
        Démarre une nouvelle conversation sur un sujet donné
        
        Args:
            topic: Sujet de la conversation (optionnel)
            user_id: Identifiant de l'utilisateur (optionnel)
            context: Contexte supplémentaire pour la conversation (optionnel)
            
        Returns:
            Dictionnaire contenant les informations de la conversation démarrée
        """
        # Générer un nouvel identifiant de conversation
        import uuid
        conversation_id = str(uuid.uuid4())
        self.current_conversation_id = conversation_id
        self.current_turn = 0
        
        # Si aucun sujet n'est spécifié, en choisir un au hasard
        import random
        if topic is None or topic not in self.available_topics:
            topic = random.choice(self.available_topics)
        
        # Initialiser l'historique de cette conversation
        self.conversation_history[conversation_id] = {
            "user_id": user_id,
            "topic": topic,
            "context": context or {},
            "turns": []
        }
        
        # Créer le message d'introduction basé sur le sujet
        introduction = self._generate_introduction(topic, context)
        
        # Enregistrer ce tour dans l'historique
        self.conversation_history[conversation_id]["turns"].append({
            "turn": self.current_turn,
            "role": "assistant",
            "content": introduction
        })
        
        # Préparer la réponse
        response = {
            "conversation_id": conversation_id,
            "message": introduction,
            "topic": topic,
            "turn": self.current_turn
        }
        
        return response
    
    def continue_conversation(self, conversation_id: str, user_input: str = None) -> Dict:
        """
        Continue une conversation existante
        
        Args:
            conversation_id: Identifiant de la conversation
            user_input: Entrée utilisateur (optionnel)
            
        Returns:
            Dictionnaire contenant la réponse de l'assistant
        """
        # Vérifier si la conversation existe
        if conversation_id not in self.conversation_history:
            logger.error(f"Conversation {conversation_id} non trouvée")
            return {"error": "Conversation non trouvée"}
        
        # Récupérer la conversation
        conversation = self.conversation_history[conversation_id]
        self.current_conversation_id = conversation_id
        
        # Incrémenter le tour
        self.current_turn = len(conversation["turns"])
        
        # Si l'utilisateur a fourni une entrée, l'ajouter à l'historique
        if user_input:
            conversation["turns"].append({
                "turn": self.current_turn,
                "role": "user",
                "content": user_input
            })
            self.current_turn += 1
        
        # Vérifier si nous avons atteint le nombre maximum de tours
        if self.current_turn >= self.max_turns:
            return self._end_conversation(conversation_id)
        
        # Générer la réponse de l'assistant
        response_content = self._generate_response(conversation)
        
        # Enregistrer ce tour dans l'historique
        conversation["turns"].append({
            "turn": self.current_turn,
            "role": "assistant",
            "content": response_content
        })
        
        # Préparer la réponse
        response = {
            "conversation_id": conversation_id,
            "message": response_content,
            "topic": conversation["topic"],
            "turn": self.current_turn
        }
        
        return response
    
    def _generate_introduction(self, topic: str, context: Optional[Dict]) -> str:
        """
        Génère une introduction pour démarrer la conversation
        
        Args:
            topic: Sujet de la conversation
            context: Contexte supplémentaire (activités récentes, etc.)
            
        Returns:
            Message d'introduction formaté
        """
        # Construire le prompt pour l'API
        activity = "inconnu"
        if context and "activity" in context:
            activity = context["activity"]
        
        time_of_day = "journée"
        if context and "time_context" in context and "time_of_day" in context["time_context"]:
            time_of_day = context["time_context"]["time_of_day"]
            if time_of_day == "morning":
                time_of_day = "matinée"
            elif time_of_day == "afternoon":
                time_of_day = "après-midi"
            elif time_of_day == "evening":
                time_of_day = "soirée"
            elif time_of_day == "night":
                time_of_day = "nuit"
        
        prompt = f"""Tu es un assistant virtuel amical et engageant qui démarre une conversation avec une personne. 
La personne est actuellement en train de '{activity}'. 
Nous sommes en {time_of_day}.
Démarre une conversation amicale et naturelle sur le sujet '{topic}'. 
Sois chaleureux, bref (1-2 phrases maximum) et pose une question ouverte pour encourager la discussion.
Ne te présente pas, commence directement par ton message d'introduction."""
        
        # Générer la réponse
        return self._call_ai_api(prompt)
    
    def _generate_response(self, conversation: Dict) -> str:
        """
        Génère une réponse de l'assistant basée sur l'historique de la conversation
        
        Args:
            conversation: Données de la conversation en cours
            
        Returns:
            Réponse générée
        """
        # Extraire les tours précédents pour construire le contexte
        conversation_context = ""
        for turn in conversation["turns"]:
            role = "Assistant" if turn["role"] == "assistant" else "Personne"
            conversation_context += f"{role}: {turn['content']}\n"
        
        # Construire le prompt pour l'API
        topic = conversation["topic"]
        prompt = f"""Tu es un assistant virtuel amical et engageant qui parle avec une personne.
Voici l'historique de la conversation sur le sujet '{topic}':

{conversation_context}

Réponds de manière naturelle et concise (1-3 phrases maximum). 
Sois chaleureux et pose des questions ouvertes pour encourager la discussion.
Évite de répéter ce que tu as déjà dit précédemment.
Reste sur le sujet mais permets une évolution naturelle de la conversation."""
        
        # Générer la réponse
        return self._call_ai_api(prompt)
    
    def _end_conversation(self, conversation_id: str) -> Dict:
        """
        Termine proprement une conversation ayant atteint le nombre maximum de tours
        
        Args:
            conversation_id: Identifiant de la conversation
            
        Returns:
            Message de conclusion
        """
        conversation = self.conversation_history[conversation_id]
        
        # Générer un message de conclusion
        prompt = f"""Tu es un assistant virtuel qui doit conclure une conversation sur le sujet '{conversation["topic"]}'. 
Formule une conclusion chaleureuse et positive en 1-2 phrases.
Ne propose pas de prolonger la conversation."""
        
        conclusion = self._call_ai_api(prompt)
        
        # Enregistrer ce tour final dans l'historique
        conversation["turns"].append({
            "turn": self.current_turn,
            "role": "assistant",
            "content": conclusion
        })
        
        # Marquer la conversation comme terminée
        conversation["completed"] = True
        
        # Préparer la réponse
        response = {
            "conversation_id": conversation_id,
            "message": conclusion,
            "topic": conversation["topic"],
            "turn": self.current_turn,
            "completed": True
        }
        
        return response
    
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
                return "Je ne sais pas quoi dire pour le moment. Pouvons-nous parler d'autre chose ?"
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à l'API {self.provider}: {str(e)}")
            return "Désolé, j'ai du mal à trouver mes mots en ce moment. Pouvons-nous essayer un autre sujet ?"
    
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
            "system": "Tu es un assistant virtuel amical qui génère des conversations naturelles et engageantes. Tes réponses sont toujours concises, chaleureuses et appropriées au contexte.",
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
                {"role": "system", "content": "Tu es un assistant virtuel amical qui génère des conversations naturelles et engageantes. Tes réponses sont toujours concises, chaleureuses et appropriées au contexte."},
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
            
            return story
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'histoire: {str(e)}")
            return {
                "story_id": "error",
                "error": str(e),
                "content": "Je suis désolé, je n'arrive pas à raconter cette histoire maintenant. Essayons autre chose."
            }
