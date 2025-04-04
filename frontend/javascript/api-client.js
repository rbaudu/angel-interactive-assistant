/**
 * Client API pour communiquer avec le backend
 */
class ApiClient {
  /**
   * Initialise le client API
   * @param {string} baseUrl - URL de base de l'API
   */
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }
  
  /**
   * Envoie une requête GET
   * @param {string} endpoint - Endpoint de l'API
   * @param {Object} params - Paramètres de la requête
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async get(endpoint, params = {}) {
    try {
      // Construire l'URL avec les paramètres
      const url = new URL(this.baseUrl + endpoint);
      
      // Ajouter les paramètres à l'URL
      Object.keys(params).forEach(key => {
        url.searchParams.append(key, params[key]);
      });
      
      // Effectuer la requête
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      });
      
      // Vérifier la réponse
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      // Extraire les données JSON
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Erreur lors de la requête GET sur ${endpoint}:`, error);
      throw error;
    }
  }
  
  /**
   * Envoie une requête POST
   * @param {string} endpoint - Endpoint de l'API
   * @param {Object} data - Données à envoyer
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async post(endpoint, data = {}) {
    try {
      // Construire l'URL
      const url = this.baseUrl + endpoint;
      
      // Effectuer la requête
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      // Vérifier la réponse
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      // Extraire les données JSON
      const responseData = await response.json();
      return responseData;
    } catch (error) {
      console.error(`Erreur lors de la requête POST sur ${endpoint}:`, error);
      throw error;
    }
  }
  
  /**
   * Envoie une requête PUT
   * @param {string} endpoint - Endpoint de l'API
   * @param {Object} data - Données à envoyer
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async put(endpoint, data = {}) {
    try {
      // Construire l'URL
      const url = this.baseUrl + endpoint;
      
      // Effectuer la requête
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      // Vérifier la réponse
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      // Extraire les données JSON
      const responseData = await response.json();
      return responseData;
    } catch (error) {
      console.error(`Erreur lors de la requête PUT sur ${endpoint}:`, error);
      throw error;
    }
  }
  
  /**
   * Envoie une requête DELETE
   * @param {string} endpoint - Endpoint de l'API
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async delete(endpoint) {
    try {
      // Construire l'URL
      const url = this.baseUrl + endpoint;
      
      // Effectuer la requête
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json'
        }
      });
      
      // Vérifier la réponse
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      // Extraire les données JSON
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Erreur lors de la requête DELETE sur ${endpoint}:`, error);
      throw error;
    }
  }
  
  /**
   * Récupère les recommandations basées sur une activité
   * @param {string} activity - Activité détectée
   * @param {number} confidence - Niveau de confiance
   * @param {string} userId - Identifiant de l'utilisateur (optionnel)
   * @returns {Promise<Object>} - Réponse de l'API avec les recommandations
   */
  async getRecommendations(activity, confidence, userId = null) {
    const timestamp = new Date().toISOString();
    
    const data = {
      activity_data: {
        activity,
        confidence,
        timestamp,
        user_id: userId
      }
    };
    
    return this.post('/recommendations', data);
  }
  
  /**
   * Envoie un feedback sur une recommandation
   * @param {string} recommendationId - Identifiant de la recommandation
   * @param {Object} feedback - Données de feedback
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async sendFeedback(recommendationId, feedback) {
    const data = {
      recommendation_id: recommendationId,
      feedback
    };
    
    return this.post('/feedback', data);
  }
  
  /**
   * Démarre une conversation
   * @param {string} topic - Sujet de conversation (optionnel)
   * @param {string} userId - Identifiant de l'utilisateur (optionnel)
   * @param {Object} context - Contexte supplémentaire (optionnel)
   * @returns {Promise<Object>} - Réponse de l'API avec l'ID de conversation
   */
  async startConversation(topic = null, userId = null, context = null) {
    const data = {
      topic,
      user_id: userId,
      context
    };
    
    return this.post('/conversations/start', data);
  }
  
  /**
   * Continue une conversation existante
   * @param {string} conversationId - Identifiant de la conversation
   * @param {string} userInput - Message de l'utilisateur
   * @returns {Promise<Object>} - Réponse de l'API avec le message de l'assistant
   */
  async continueConversation(conversationId, userInput) {
    const data = {
      conversation_id: conversationId,
      user_input: userInput
    };
    
    return this.post(`/conversations/${conversationId}/respond`, data);
  }
  
  /**
   * Génère une histoire
   * @param {string} topic - Sujet de l'histoire
   * @param {number} durationMin - Durée approximative en minutes
   * @param {string} complexity - Niveau de complexité
   * @returns {Promise<Object>} - Réponse de l'API avec l'histoire générée
   */
  async generateStory(topic, durationMin = 2, complexity = 'medium') {
    const data = {
      topic,
      duration_min: durationMin,
      complexity
    };
    
    return this.post('/stories', data);
  }
  
  /**
   * Exécute une action sur un appareil
   * @param {string} actionType - Type d'action
   * @param {string} deviceType - Type d'appareil
   * @param {Object} params - Paramètres supplémentaires (optionnel)
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async executeDeviceAction(actionType, deviceType, params = null) {
    const data = {
      action_type: actionType,
      device_type: deviceType,
      params
    };
    
    return this.post('/devices/action', data);
  }
  
  /**
   * Exécute un scénario
   * @param {string} scenarioName - Nom du scénario
   * @param {Object} params - Paramètres supplémentaires (optionnel)
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async executeScenario(scenarioName, params = null) {
    const data = {
      scenario_name: scenarioName,
      params
    };
    
    return this.post('/devices/scenario', data);
  }
  
  /**
   * Récupère l'état des appareils
   * @returns {Promise<Object>} - Réponse de l'API avec l'état des appareils
   */
  async getDevicesStatus() {
    return this.get('/devices/status');
  }
}

export default ApiClient;