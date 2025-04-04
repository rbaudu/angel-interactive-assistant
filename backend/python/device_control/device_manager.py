import json
import logging
import requests
import time
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceController(ABC):
    """
    Classe abstraite pour le contrôle d'appareils
    """
    
    @abstractmethod
    def turn_on(self) -> bool:
        """Allume l'appareil"""
        pass
    
    @abstractmethod
    def turn_off(self) -> bool:
        """Éteint l'appareil"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict:
        """Récupère l'état de l'appareil"""
        pass


class TVController(DeviceController):
    """
    Contrôleur pour Smart TV
    """
    
    def __init__(self, config: Dict):
        """
        Initialise le contrôleur TV
        
        Args:
            config: Configuration de la TV
        """
        self.ip = config.get("ip", "")
        self.protocol = config.get("protocol", "http")
        self.port = config.get("port", 8080)
        self.base_url = f"{self.protocol}://{self.ip}:{self.port}/api"
        self.last_status = None
        self.available_channels = None
        
        logger.info(f"Contrôleur TV initialisé avec l'adresse: {self.ip}")
    
    def turn_on(self) -> bool:
        """
        Allume la télévision
        
        Returns:
            True si réussi, False sinon
        """
        try:
            response = requests.post(f"{self.base_url}/power", json={"state": "on"})
            success = response.status_code == 200
            if success:
                logger.info("TV allumée avec succès")
            else:
                logger.error(f"Erreur lors de l'allumage TV: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Exception lors de l'allumage TV: {str(e)}")
            return False
    
    def turn_off(self) -> bool:
        """
        Éteint la télévision
        
        Returns:
            True si réussi, False sinon
        """
        try:
            response = requests.post(f"{self.base_url}/power", json={"state": "off"})
            success = response.status_code == 200
            if success:
                logger.info("TV éteinte avec succès")
            else:
                logger.error(f"Erreur lors de l'extinction TV: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Exception lors de l'extinction TV: {str(e)}")
            return False
    
    def get_status(self) -> Dict:
        """
        Récupère l'état actuel de la TV
        
        Returns:
            Dictionnaire avec l'état de la TV
        """
        try:
            response = requests.get(f"{self.base_url}/status")
            if response.status_code == 200:
                self.last_status = response.json()
                return self.last_status
            else:
                logger.error(f"Erreur lors de la récupération du statut TV: {response.status_code}")
                return {"error": f"Status code: {response.status_code}"}
        except Exception as e:
            logger.error(f"Exception lors de la récupération du statut TV: {str(e)}")
            return {"error": str(e)}
    
    def change_channel(self, channel_id: str) -> bool:
        """
        Change la chaîne de télévision
        
        Args:
            channel_id: Identifiant de la chaîne
            
        Returns:
            True si réussi, False sinon
        """
        try:
            response = requests.post(f"{self.base_url}/channel", json={"channel_id": channel_id})
            success = response.status_code == 200
            if success:
                logger.info(f"Chaîne changée vers {channel_id}")
            else:
                logger.error(f"Erreur lors du changement de chaîne: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Exception lors du changement de chaîne: {str(e)}")
            return False
    
    def set_volume(self, volume: int) -> bool:
        """
        Définit le volume de la TV
        
        Args:
            volume: Niveau de volume (0-100)
            
        Returns:
            True si réussi, False sinon
        """
        try:
            # S'assurer que le volume est dans la plage correcte
            volume = max(0, min(100, volume))
            
            response = requests.post(f"{self.base_url}/volume", json={"level": volume})
            success = response.status_code == 200
            if success:
                logger.info(f"Volume défini à {volume}")
            else:
                logger.error(f"Erreur lors du réglage du volume: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Exception lors du réglage du volume: {str(e)}")
            return False
    
    def get_channels(self) -> List[Dict]:
        """
        Récupère la liste des chaînes disponibles
        
        Returns:
            Liste des chaînes avec leurs détails
        """
        try:
            if self.available_channels is None:
                response = requests.get(f"{self.base_url}/channels")
                if response.status_code == 200:
                    self.available_channels = response.json().get("channels", [])
                else:
                    logger.error(f"Erreur lors de la récupération des chaînes: {response.status_code}")
                    return []
            
            return self.available_channels
        except Exception as e:
            logger.error(f"Exception lors de la récupération des chaînes: {str(e)}")
            return []
    
    def search_programs(self, category: str = None, query: str = None) -> List[Dict]:
        """
        Recherche des programmes TV par catégorie ou requête
        
        Args:
            category: Catégorie de programme (documentaire, film, etc.)
            query: Terme de recherche
            
        Returns:
            Liste des programmes correspondants
        """
        try:
            params = {}
            if category:
                params["category"] = category
            if query:
                params["query"] = query
                
            response = requests.get(f"{self.base_url}/programs", params=params)
            
            if response.status_code == 200:
                return response.json().get("programs", [])
            else:
                logger.error(f"Erreur lors de la recherche de programmes: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception lors de la recherche de programmes: {str(e)}")
            return []
    
    def play_program(self, program_id: str) -> bool:
        """
        Lance la lecture d'un programme spécifique
        
        Args:
            program_id: Identifiant du programme
            
        Returns:
            True si réussi, False sinon
        """
        try:
            response = requests.post(f"{self.base_url}/play", json={"program_id": program_id})
            success = response.status_code == 200
            if success:
                logger.info(f"Programme {program_id} lancé avec succès")
            else:
                logger.error(f"Erreur lors du lancement du programme: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Exception lors du lancement du programme: {str(e)}")
            return False


class MusicPlayerController(DeviceController):
    """
    Contrôleur pour lecteur de musique (Sonos, etc.)
    """
    
    def __init__(self, config: Dict):
        """
        Initialise le contrôleur de lecteur de musique
        
        Args:
            config: Configuration du lecteur de musique
        """
        self.ip = config.get("ip", "")
        self.playlists = config.get("playlists", {})
        self.base_url = f"http://{self.ip}:1400/api"
        self.last_status = None
        
        logger.info(f"Contrôleur de musique initialisé avec l'adresse: {self.ip}")
    
    def turn_on(self) -> bool:
        """
        'Allume' le lecteur de musique (commence à jouer)
        
        Returns:
            True si réussi, False sinon
        """
        try:
            response = requests.post(f"{self.base_url}/play")
            success = response.status_code == 200
            if success:
                logger.info("Lecteur de musique démarré")
            else:
                logger.error(f"Erreur lors du démarrage du lecteur: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Exception lors du démarrage du lecteur: {str(e)}")
            return False
    
    def turn_off(self) -> bool:
        """
        'Éteint' le lecteur de musique (arrête la lecture)
        
        Returns:
            True si réussi, False sinon
        """
        try:
            response = requests.post(f"{self.base_url}/pause")
            success = response.status_code == 200
            if success:
                logger.info("Lecteur de musique arrêté")
            else:
                logger.error(f"Erreur lors de l'arrêt du lecteur: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Exception lors de l'arrêt du lecteur: {str(e)}")
            return False
    
    def get_status(self) -> Dict:
        """
        Récupère l'état actuel du lecteur de musique
        
        Returns:
            Dictionnaire avec l'état du lecteur
        """
        try:
            response = requests.get(f"{self.base_url}/status")
            if response.status_code == 200:
                self.last_status = response.json()
                return self.last_status
            else:
                logger.error(f"Erreur lors de la récupération du statut: {response.status_code}")
                return {"error": f"Status code: {response.status_code}"}
        except Exception as e:
            logger.error(f"Exception lors de la récupération du statut: {str(e)}")
            return {"error": str(e)}
    
    def play_playlist(self, playlist_name: str) -> bool:
        """
        Joue une playlist spécifique
        
        Args:
            playlist_name: Nom de la playlist
            
        Returns:
            True si réussi, False sinon
        """
        try:
            # Vérifier si la playlist existe dans notre configuration
            if playlist_name in self.playlists:
                playlist_id = self.playlists[playlist_name]
            else:
                playlist_id = playlist_name  # Utiliser le nom directement
            
            response = requests.post(f"{self.base_url}/playlist", json={"playlist_id": playlist_id})
            success = response.status_code == 200
            
            if success:
                logger.info(f"Playlist {playlist_name} lancée avec succès")
            else:
                logger.error(f"Erreur lors du lancement de la playlist: {response.status_code}")
            
            return success
        except Exception as e:
            logger.error(f"Exception lors du lancement de la playlist: {str(e)}")
            return False
    
    def set_volume(self, volume: int) -> bool:
        """
        Définit le volume du lecteur de musique
        
        Args:
            volume: Niveau de volume (0-100)
            
        Returns:
            True si réussi, False sinon
        """
        try:
            # S'assurer que le volume est dans la plage correcte
            volume = max(0, min(100, volume))
            
            response = requests.post(f"{self.base_url}/volume", json={"level": volume})
            success = response.status_code == 200
            
            if success:
                logger.info(f"Volume défini à {volume}")
            else:
                logger.error(f"Erreur lors du réglage du volume: {response.status_code}")
            
            return success
        except Exception as e:
            logger.error(f"Exception lors du réglage du volume: {str(e)}")
            return False
    
    def play_genre(self, genre: str) -> bool:
        """
        Joue de la musique d'un genre spécifique
        
        Args:
            genre: Genre musical
            
        Returns:
            True si réussi, False sinon
        """
        try:
            response = requests.post(f"{self.base_url}/genre", json={"genre": genre})
            success = response.status_code == 200
            
            if success:
                logger.info(f"Genre {genre} lancé avec succès")
            else:
                logger.error(f"Erreur lors du lancement du genre: {response.status_code}")
            
            return success
        except Exception as e:
            logger.error(f"Exception lors du lancement du genre: {str(e)}")
            return False


class LightController(DeviceController):
    """
    Contrôleur pour les lumières (Philips Hue, etc.)
    """
    
    def __init__(self, config: Dict):
        """
        Initialise le contrôleur de lumières
        
        Args:
            config: Configuration des lumières
        """
        self.bridge_ip = config.get("bridge_ip", "")
        self.username = config.get("username", "")
        self.base_url = f"http://{self.bridge_ip}/api/{self.username}"
        
        logger.info(f"Contrôleur de lumières initialisé avec l'adresse: {self.bridge_ip}")
    
    def turn_on(self) -> bool:
        """
        Allume toutes les lumières
        
        Returns:
            True si réussi, False sinon
        """
        return self.set_all_lights({"on": True})
    
    def turn_off(self) -> bool:
        """
        Éteint toutes les lumières
        
        Returns:
            True si réussi, False sinon
        """
        return self.set_all_lights({"on": False})
    
    def get_status(self) -> Dict:
        """
        Récupère l'état actuel des lumières
        
        Returns:
            Dictionnaire avec l'état des lumières
        """
        try:
            response = requests.get(f"{self.base_url}/lights")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erreur lors de la récupération du statut: {response.status_code}")
                return {"error": f"Status code: {response.status_code}"}
        except Exception as e:
            logger.error(f"Exception lors de la récupération du statut: {str(e)}")
            return {"error": str(e)}
    
    def set_all_lights(self, state: Dict) -> bool:
        """
        Définit l'état de toutes les lumières
        
        Args:
            state: État à définir (on, brightness, etc.)
            
        Returns:
            True si réussi, False sinon
        """
        try:
            # Obtenir la liste des lumières
            lights_response = requests.get(f"{self.base_url}/lights")
            if lights_response.status_code != 200:
                logger.error(f"Erreur lors de la récupération des lumières: {lights_response.status_code}")
                return False
            
            lights = lights_response.json()
            success = True
            
            # Définir l'état pour chaque lumière
            for light_id in lights:
                light_response = requests.put(f"{self.base_url}/lights/{light_id}/state", json=state)
                if light_response.status_code != 200:
                    logger.error(f"Erreur lors de la définition de l'état de la lumière {light_id}: {light_response.status_code}")
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Exception lors de la définition de l'état des lumières: {str(e)}")
            return False
    
    def set_scene(self, scene_name: str) -> bool:
        """
        Active une scène d'éclairage prédéfinie
        
        Args:
            scene_name: Nom de la scène
            
        Returns:
            True si réussi, False sinon
        """
        try:
            # Obtenir la liste des scènes
            scenes_response = requests.get(f"{self.base_url}/scenes")
            if scenes_response.status_code != 200:
                logger.error(f"Erreur lors de la récupération des scènes: {scenes_response.status_code}")
                return False
            
            scenes = scenes_response.json()
            scene_id = None
            
            # Trouver l'ID de la scène par son nom
            for id, scene in scenes.items():
                if scene.get("name", "").lower() == scene_name.lower():
                    scene_id = id
                    break
            
            if not scene_id:
                logger.error(f"Scène '{scene_name}' non trouvée")
                return False
            
            # Activer la scène
            response = requests.put(f"{self.base_url}/groups/0/action", json={"scene": scene_id})
            success = response.status_code == 200
            
            if success:
                logger.info(f"Scène '{scene_name}' activée avec succès")
            else:
                logger.error(f"Erreur lors de l'activation de la scène: {response.status_code}")
            
            return success
        except Exception as e:
            logger.error(f"Exception lors de l'activation de la scène: {str(e)}")
            return False


class DeviceManager:
    """
    Gestionnaire qui coordonne tous les contrôleurs d'appareils
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialise le gestionnaire d'appareils avec la configuration
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        # Chargement de la configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.device_controllers = {}
        self._initialize_controllers()
        
        logger.info("Gestionnaire d'appareils initialisé")
    
    def _initialize_controllers(self):
        """
        Initialise tous les contrôleurs d'appareils configurés
        """
        devices_config = self.config.get("devices", {})
        
        # Initialiser la TV si configurée
        if "tv" in devices_config:
            try:
                self.device_controllers["tv"] = TVController(devices_config["tv"])
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du contrôleur TV: {str(e)}")
        
        # Initialiser le lecteur de musique si configuré
        if "music_player" in devices_config:
            try:
                self.device_controllers["music_player"] = MusicPlayerController(devices_config["music_player"])
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du contrôleur de musique: {str(e)}")
        
        # Initialiser le contrôleur de lumières si configuré
        if "lights" in devices_config:
            try:
                self.device_controllers["lights"] = LightController(devices_config["lights"])
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du contrôleur de lumières: {str(e)}")
    
    def execute_action(self, action_type: str, device_type: str, params: Dict = None) -> Dict:
        """
        Exécute une action sur un appareil spécifique
        
        Args:
            action_type: Type d'action (turn_on, turn_off, play, etc.)
            device_type: Type d'appareil (tv, music_player, lights)
            params: Paramètres supplémentaires pour l'action
            
        Returns:
            Dictionnaire avec le résultat de l'action
        """
        if device_type not in self.device_controllers:
            logger.error(f"Appareil non pris en charge: {device_type}")
            return {"success": False, "error": f"Appareil non pris en charge: {device_type}"}
        
        controller = self.device_controllers[device_type]
        params = params or {}
        
        try:
            if action_type == "turn_on":
                success = controller.turn_on()
                return {"success": success}
            
            elif action_type == "turn_off":
                success = controller.turn_off()
                return {"success": success}
            
            elif action_type == "get_status":
                status = controller.get_status()
                return {"success": True, "status": status}
            
            # Actions spécifiques à la TV
            elif device_type == "tv":
                if action_type == "change_channel":
                    channel_id = params.get("channel_id")
                    if not channel_id:
                        return {"success": False, "error": "ID de chaîne requis"}
                    success = controller.change_channel(channel_id)
                    return {"success": success}
                
                elif action_type == "set_volume":
                    volume = params.get("volume")
                    if volume is None:
                        return {"success": False, "error": "Volume requis"}
                    success = controller.set_volume(volume)
                    return {"success": success}
                
                elif action_type == "get_channels":
                    channels = controller.get_channels()
                    return {"success": True, "channels": channels}
                
                elif action_type == "search_programs":
                    category = params.get("category")
                    query = params.get("query")
                    programs = controller.search_programs(category, query)
                    return {"success": True, "programs": programs}
                
                elif action_type == "play_program":
                    program_id = params.get("program_id")
                    if not program_id:
                        return {"success": False, "error": "ID de programme requis"}
                    success = controller.play_program(program_id)
                    return {"success": success}
            
            # Actions spécifiques au lecteur de musique
            elif device_type == "music_player":
                if action_type == "play_playlist":
                    playlist_name = params.get("playlist_name")
                    if not playlist_name:
                        return {"success": False, "error": "Nom de playlist requis"}
                    success = controller.play_playlist(playlist_name)
                    return {"success": success}
                
                elif action_type == "set_volume":
                    volume = params.get("volume")
                    if volume is None:
                        return {"success": False, "error": "Volume requis"}
                    success = controller.set_volume(volume)
                    return {"success": success}
                
                elif action_type == "play_genre":
                    genre = params.get("genre")
                    if not genre:
                        return {"success": False, "error": "Genre requis"}
                    success = controller.play_genre(genre)
                    return {"success": success}
            
            # Actions spécifiques aux lumières
            elif device_type == "lights":
                if action_type == "set_scene":
                    scene_name = params.get("scene_name")
                    if not scene_name:
                        return {"success": False, "error": "Nom de scène requis"}
                    success = controller.set_scene(scene_name)
                    return {"success": success}
                
                elif action_type == "set_state":
                    state = params.get("state")
                    if not state:
                        return {"success": False, "error": "État requis"}
                    success = controller.set_all_lights(state)
                    return {"success": success}
            
            logger.error(f"Action non prise en charge: {action_type} pour {device_type}")
            return {"success": False, "error": f"Action non prise en charge: {action_type}"}
            
        except Exception as e:
            logger.error(f"Exception lors de l'exécution de l'action {action_type} sur {device_type}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def execute_scenario(self, scenario_name: str, params: Dict = None) -> Dict:
        """
        Exécute un scénario prédéfini impliquant plusieurs appareils
        
        Args:
            scenario_name: Nom du scénario à exécuter
            params: Paramètres supplémentaires pour le scénario
            
        Returns:
            Dictionnaire avec le résultat du scénario
        """
        params = params or {}
        results = {}
        
        try:
            if scenario_name == "movie_time":
                # Scénario pour regarder un film: lumières tamisées, TV allumée, son configuré
                results["lights"] = self.execute_action("set_scene", "lights", {"scene_name": "movie"})
                results["tv"] = self.execute_action("turn_on", "tv")
                
                # Chercher un film si une catégorie est spécifiée
                category = params.get("category", "film")
                programs = self.execute_action("search_programs", "tv", {"category": category})
                
                if programs.get("success") and programs.get("programs"):
                    # Jouer le premier programme trouvé
                    first_program = programs["programs"][0]
                    results["program"] = self.execute_action("play_program", "tv", 
                                                            {"program_id": first_program["id"]})
                
                # Configurer le volume
                volume = params.get("volume", 50)
                results["volume"] = self.execute_action("set_volume", "tv", {"volume": volume})
                
                return {
                    "success": all(r.get("success", False) for r in results.values()),
                    "results": results
                }
            
            elif scenario_name == "dinner_music":
                # Scénario pour le dîner: musique d'ambiance, lumières appropriées
                results["lights"] = self.execute_action("set_scene", "lights", {"scene_name": "dinner"})
                results["music"] = self.execute_action("turn_on", "music_player")
                
                # Jouer une playlist de dîner
                playlist = params.get("playlist", "repas")
                results["playlist"] = self.execute_action("play_playlist", "music_player", 
                                                         {"playlist_name": playlist})
                
                # Configurer le volume
                volume = params.get("volume", 30)
                results["volume"] = self.execute_action("set_volume", "music_player", {"volume": volume})
                
                return {
                    "success": all(r.get("success", False) for r in results.values()),
                    "results": results
                }
            
            elif scenario_name == "relax_mode":
                # Scénario de relaxation: lumières douces, musique calme
                results["lights"] = self.execute_action("set_scene", "lights", {"scene_name": "relax"})
                results["music"] = self.execute_action("turn_on", "music_player")
                
                # Jouer une musique relaxante
                genre = params.get("genre", "classique")
                results["genre"] = self.execute_action("play_genre", "music_player", {"genre": genre})
                
                # Configurer le volume
                volume = params.get("volume", 20)
                results["volume"] = self.execute_action("set_volume", "music_player", {"volume": volume})
                
                return {
                    "success": all(r.get("success", False) for r in results.values()),
                    "results": results
                }
            
            elif scenario_name == "all_off":
                # Éteindre tous les appareils
                for device_type in self.device_controllers:
                    results[device_type] = self.execute_action("turn_off", device_type)
                
                return {
                    "success": all(r.get("success", False) for r in results.values()),
                    "results": results
                }
            
            logger.error(f"Scénario non pris en charge: {scenario_name}")
            return {"success": False, "error": f"Scénario non pris en charge: {scenario_name}"}
            
        except Exception as e:
            logger.error(f"Exception lors de l'exécution du scénario {scenario_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_all_devices_status(self) -> Dict:
        """
        Récupère l'état de tous les appareils configurés
        
        Returns:
            Dictionnaire avec l'état de chaque appareil
        """
        statuses = {}
        
        for device_type, controller in self.device_controllers.items():
            try:
                statuses[device_type] = controller.get_status()
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du statut de {device_type}: {str(e)}")
                statuses[device_type] = {"error": str(e)}
        
        return statuses