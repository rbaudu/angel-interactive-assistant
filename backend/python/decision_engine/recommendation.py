import json
import logging
from typing import Dict, List, Optional, Tuple, Any
import random
import numpy as np
from datetime import datetime, time

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialise le moteur de recommandation avec les paramètres de configuration
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        # Chargement de la configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Paramètres de décision
        self.decision_rules = self.config["decision_engine"]["decision_rules"]
        self.threshold_confidence = self.config["decision_engine"]["threshold_confidence"]
        self.learning_rate = self.config["decision_engine"]["learning_rate"]
        self.user_feedback_weight = self.config["decision_engine"]["user_feedback_weight"]
        
        # État interne
        self.last_recommendations = {}
        self.user_profile = None
        self.recommendation_history = []
        
        logger.info("Moteur de recommandation initialisé avec succès")
    
    def load_user_profile(self, user_id: str) -> Dict:
        """
        Charge le profil de l'utilisateur depuis la base de données
        
        Args:
            user_id: Identifiant unique de l'utilisateur
            
        Returns:
            Dictionnaire contenant le profil de l'utilisateur
        """
        # En production, ceci chargerait le profil depuis la base de données
        # Simulation d'un profil utilisateur pour l'exemple
        self.user_profile = {
            "id": user_id,
            "preferences": {
                "music_genres": ["classique", "jazz", "ambiance"],
                "tv_programs": ["documentaires", "films", "actualités"],
                "story_topics": ["aventure", "histoire", "science"]
            },
            "activity_history": [],
            "feedback_history": {}
        }
        return self.user_profile
    
    def get_time_context(self) -> Dict[str, Any]:
        """
        Détermine le contexte temporel pour les recommandations
        
        Returns:
            Dictionnaire avec les informations de contexte temporel
        """
        now = datetime.now()
        current_time = now.time()
        
        # Définition des périodes de la journée
        morning = time(6, 0) <= current_time < time(12, 0)
        afternoon = time(12, 0) <= current_time < time(18, 0)
        evening = time(18, 0) <= current_time < time(22, 0)
        night = time(22, 0) <= current_time or current_time < time(6, 0)
        
        return {
            "time_of_day": "morning" if morning else "afternoon" if afternoon else "evening" if evening else "night",
            "hour": now.hour,
            "weekday": now.weekday(),  # 0-6 (lundi-dimanche)
            "weekend": now.weekday() >= 5,  # 5-6 (samedi-dimanche)
        }
    
    def analyze_activity(self, activity_data: Dict) -> Tuple[str, float]:
        """
        Analyse les données d'activité détectées
        
        Args:
            activity_data: Données d'activité provenant d'Angel-server-capture
            
        Returns:
            Tuple contenant l'activité détectée et son niveau de confiance
        """
        # Extraction de l'activité et de la confiance
        activity = activity_data.get("activity", "inconnu")
        confidence = activity_data.get("confidence", 0.0)
        
        # Enregistrer dans l'historique des activités
        if self.user_profile:
            self.user_profile["activity_history"].append({
                "timestamp": datetime.now().isoformat(),
                "activity": activity,
                "confidence": confidence
            })
        
        return activity, confidence
    
    def get_recommendations(self, activity_data: Dict) -> List[Dict]:
        """
        Génère des recommandations en fonction de l'activité détectée
        
        Args:
            activity_data: Données d'activité provenant d'Angel-server-capture
            
        Returns:
            Liste des recommandations avec leurs détails
        """
        # Analyse de l'activité
        activity, confidence = self.analyze_activity(activity_data)
        
        # Si la confiance est trop faible, utiliser une activité par défaut
        if confidence < self.threshold_confidence:
            logger.info(f"Confiance trop faible ({confidence}) pour l'activité '{activity}', utilisation de 'default'")
            activity = "default"
        
        # Obtenir le contexte temporel
        time_context = self.get_time_context()
        
        # Obtenir les recommandations basées sur les règles
        rule_based_recommendations = self.decision_rules.get(activity, self.decision_rules["default"])
        
        # Appliquer des ajustements basés sur le contexte
        context_adjusted_recommendations = self._adjust_for_context(rule_based_recommendations, time_context, activity)
        
        # Personnaliser les recommandations en fonction du profil utilisateur
        if self.user_profile:
            personalized_recommendations = self._personalize_recommendations(context_adjusted_recommendations)
        else:
            personalized_recommendations = context_adjusted_recommendations
        
        # Formatage des recommandations
        recommendations = []
        for rec_type in personalized_recommendations:
            rec_details = self._get_recommendation_details(rec_type, activity)
            recommendations.append(rec_details)
        
        # Enregistrement des recommandations pour feedback futur
        self.last_recommendations = {
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "confidence": confidence,
            "recommendations": recommendations
        }
        self.recommendation_history.append(self.last_recommendations)
        
        return recommendations
    
    def _adjust_for_context(self, recommendations: List[str], time_context: Dict, activity: str) -> List[str]:
        """
        Ajuste les recommandations en fonction du contexte temporel
        
        Args:
            recommendations: Liste initiale de recommandations
            time_context: Contexte temporel actuel
            activity: Activité détectée
            
        Returns:
            Liste ajustée de recommandations
        """
        adjusted_recommendations = recommendations.copy()
        
        # Exemples d'ajustements basés sur le temps
        if time_context["time_of_day"] == "night":
            # Éviter le bruit la nuit
            if "diffuser_musique" in adjusted_recommendations and activity != "manger":
                adjusted_recommendations.remove("diffuser_musique")
            
            # Favoriser les activités calmes la nuit
            if "raconter_histoire" not in adjusted_recommendations and activity == "inactif":
                adjusted_recommendations.append("raconter_histoire")
        
        elif time_context["time_of_day"] == "morning":
            # Suggestions du matin
            if "suggerer_actualites" not in adjusted_recommendations and activity == "inactif":
                adjusted_recommendations.append("suggerer_actualites")
        
        # Ajustement pour le weekend
        if time_context["weekend"]:
            if "suggerer_activite_exterieure" not in adjusted_recommendations and activity == "inactif":
                adjusted_recommendations.append("suggerer_activite_exterieure")
        
        return adjusted_recommendations
    
    def _personalize_recommendations(self, recommendations: List[str]) -> List[str]:
        """
        Personnalise les recommandations en fonction du profil utilisateur
        
        Args:
            recommendations: Liste initiale de recommandations
            
        Returns:
            Liste personnalisée de recommandations
        """
        personalized = recommendations.copy()
        
        # Exemple de personnalisation
        if self.user_profile:
            # Si l'utilisateur préfère les documentaires et que la recommandation est de regarder la TV
            if "recommander_programme" in personalized and "documentaires" in self.user_profile["preferences"]["tv_programs"]:
                personalized[personalized.index("recommander_programme")] = "recommander_documentaire"
            
            # Si l'utilisateur aime la musique classique et que la recommandation est de diffuser de la musique
            if "diffuser_musique" in personalized and "classique" in self.user_profile["preferences"]["music_genres"]:
                personalized[personalized.index("diffuser_musique")] = "diffuser_musique_classique"
        
        return personalized
    
    def _get_recommendation_details(self, rec_type: str, activity: str) -> Dict:
        """
        Génère les détails d'une recommandation spécifique
        
        Args:
            rec_type: Type de recommandation
            activity: Activité détectée
            
        Returns:
            Dictionnaire avec les détails de la recommandation
        """
        # Structure de base de la recommandation
        recommendation = {
            "type": rec_type,
            "priority": self._calculate_priority(rec_type, activity),
            "params": {}
        }
        
        # Détails spécifiques selon le type de recommandation
        if rec_type == "diffuser_musique" or rec_type == "diffuser_musique_classique":
            genres = ["classique"] if rec_type == "diffuser_musique_classique" else ["ambiance", "jazz", "pop"]
            playlists = self.config["devices"]["music_player"]["playlists"]
            playlist_key = "repas" if activity == "manger" else "ambiance"
            
            recommendation["params"] = {
                "genre": random.choice(genres),
                "playlist": playlists.get(playlist_key, "playlist_ambiance"),
                "volume": 40 if activity == "manger" else 30
            }
            
        elif rec_type == "raconter_histoire":
            topics = []
            if self.user_profile and "story_topics" in self.user_profile["preferences"]:
                topics = self.user_profile["preferences"]["story_topics"]
            if not topics:
                topics = ["aventure", "humour", "culture"]
                
            recommendation["params"] = {
                "topic": random.choice(topics),
                "duration_min": 2,
                "complexity": "medium"
            }
            
        elif rec_type == "engager_conversation":
            topics = []
            if self.user_profile and "preferences" in self.user_profile:
                if "tv_programs" in self.user_profile["preferences"]:
                    topics.extend(self.user_profile["preferences"]["tv_programs"])
                if "story_topics" in self.user_profile["preferences"]:
                    topics.extend(self.user_profile["preferences"]["story_topics"])
            
            if not topics:
                topics = ["actualités", "santé", "loisirs", "culture"]
                
            recommendation["params"] = {
                "topic": random.choice(topics),
                "style": "casual",
                "max_turns": self.config["content_generation"]["conversations"]["max_turns"]
            }
            
        elif rec_type == "recommander_programme" or rec_type == "recommander_documentaire":
            category = "documentaire" if rec_type == "recommander_documentaire" else "divertissement"
            
            recommendation["params"] = {
                "category": category,
                "duration_min": 30,
                "rating_min": 4.0
            }
        
        return recommendation
    
    def _calculate_priority(self, rec_type: str, activity: str) -> float:
        """
        Calcule la priorité d'une recommandation
        
        Args:
            rec_type: Type de recommandation
            activity: Activité détectée
            
        Returns:
            Score de priorité entre 0 et 1
        """
        # Priorités de base
        base_priorities = {
            "diffuser_musique": 0.7,
            "diffuser_musique_classique": 0.7,
            "raconter_histoire": 0.8,
            "engager_conversation": 0.9,
            "recommander_programme": 0.6,
            "recommander_documentaire": 0.6,
            "suggerer_activite": 0.5,
            "suggerer_boisson": 0.4,
            "suggerer_actualites": 0.5,
            "suggerer_activite_exterieure": 0.5
        }
        
        # Priorité de base pour ce type
        priority = base_priorities.get(rec_type, 0.5)
        
        # Ajustement basé sur l'historique (éviter de répéter la même recommandation)
        if len(self.recommendation_history) > 0:
            recent_recommendations = [r["recommendations"] for r in self.recommendation_history[-3:]]
            flat_list = [item["type"] for sublist in recent_recommendations for item in sublist]
            
            # Réduire la priorité si cette recommandation est apparue récemment
            if rec_type in flat_list:
                count = flat_list.count(rec_type)
                priority -= 0.1 * count  # Réduction progressive
                priority = max(0.1, priority)  # Ne pas descendre en dessous de 0.1
        
        # Ajustement contextuel basé sur l'activité
        if activity == "manger" and rec_type in ["diffuser_musique", "diffuser_musique_classique"]:
            priority += 0.2  # Priorité plus élevée pour la musique pendant les repas
        elif activity == "inactif" and rec_type in ["raconter_histoire", "engager_conversation"]:
            priority += 0.3  # Priorité plus élevée pour l'engagement si inactif
        
        # Normaliser entre 0 et 1
        priority = min(1.0, max(0.0, priority))
        
        return priority
    
    def process_feedback(self, recommendation_id: str, feedback: Dict) -> None:
        """
        Traite le feedback utilisateur pour améliorer les recommandations futures
        
        Args:
            recommendation_id: Identifiant de la recommandation
            feedback: Dictionnaire contenant le feedback (accepté, rejeté, etc.)
        """
        # Trouver la recommandation dans l'historique
        for rec in self.recommendation_history:
            if rec.get("id") == recommendation_id:
                # Enregistrer le feedback
                if self.user_profile:
                    self.user_profile["feedback_history"][recommendation_id] = feedback
                
                # Ajuster les poids futurs basés sur ce feedback
                self._adjust_weights_from_feedback(rec, feedback)
                break
    
    def _adjust_weights_from_feedback(self, recommendation: Dict, feedback: Dict) -> None:
        """
        Ajuste les poids internes basés sur le feedback utilisateur
        
        Args:
            recommendation: Recommandation originale
            feedback: Feedback de l'utilisateur
        """
        # Exemple simple d'ajustement - en production, ce serait plus sophistiqué
        is_positive = feedback.get("accepted", False)
        activity = recommendation.get("activity", "default")
        
        # Ici, on pourrait utiliser un modèle d'apprentissage comme un réseau de neurones
        # Pour simplifier, nous utilisons une approche basée sur des règles
        if is_positive:
            # Renforcer cette combinaison activité-recommandation
            logger.info(f"Feedback positif enregistré pour {activity}, ajustement des poids")
        else:
            # Diminuer cette combinaison activité-recommandation
            logger.info(f"Feedback négatif enregistré pour {activity}, ajustement des poids")
