/**
 * AvatarController - Gère l'affichage et l'animation de l'avatar humain 
 * sur l'interface utilisateur
 */

class AvatarController {
  /**
   * Initialise le contrôleur d'avatar
   * @param {Object} config - Configuration de l'avatar
   * @param {HTMLElement} container - Conteneur DOM où l'avatar sera affiché
   */
  constructor(config, container) {
    this.config = config;
    this.container = container;
    this.currentAnimation = null;
    this.currentExpression = 'neutral';
    this.isSpeaking = false;
    this.avatarType = config.type || '3d';
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.model = null;
    this.mixer = null;
    this.animations = {};
    this.expressions = {};
    this.lipSync = null;
    this.audioContext = null;
    
    // Initialisation de l'avatar
    this._initialize();
  }
  
  /**
   * Initialise l'avatar en fonction du type spécifié
   * @private
   */
  _initialize() {
    if (this.avatarType === '3d') {
      this._initialize3DAvatar();
    } else {
      this._initialize2DAvatar();
    }
    
    // Initialiser l'audio context
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
      console.error('Le navigateur ne supporte pas Web Audio API', e);
    }
    
    console.log('Avatar initialisé avec succès');
  }
  
  /**
   * Initialise un avatar 3D avec Three.js
   * @private
   */
  _initialize3DAvatar() {
    // Créer la scène
    this.scene = new THREE.Scene();
    
    // Créer la caméra
    this.camera = new THREE.PerspectiveCamera(
      45, 
      this.container.clientWidth / this.container.clientHeight, 
      0.1, 
      1000
    );
    this.camera.position.z = 5;
    
    // Créer le renderer
    this.renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true 
    });
    this.renderer.setSize(
      this.container.clientWidth, 
      this.container.clientHeight
    );
    this.renderer.setClearColor(0x000000, 0);
    this.container.appendChild(this.renderer.domElement);
    
    // Ajouter éclairage
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    this.scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(0, 1, 1);
    this.scene.add(directionalLight);
    
    // Charger le modèle 3D
    this._loadModel();
    
    // Gestion du redimensionnement
    window.addEventListener('resize', this._onResize.bind(this));
    
    // Démarrer la boucle de rendu
    this._animate();
  }
  
  /**
   * Initialise un avatar 2D avec CSS/DOM pour les systèmes moins puissants
   * @private
   */
  _initialize2DAvatar() {
    // Créer les éléments HTML pour l'avatar 2D
    this.container.innerHTML = `
      <div class="avatar-2d">
        <div class="avatar-head">
          <div class="avatar-face">
            <div class="avatar-eyes">
              <div class="avatar-eye left"></div>
              <div class="avatar-eye right"></div>
            </div>
            <div class="avatar-mouth"></div>
          </div>
        </div>
      </div>
    `;
    
    // Référencer les éléments
    this.faceElement = this.container.querySelector('.avatar-face');
    this.mouthElement = this.container.querySelector('.avatar-mouth');
    
    // Charger les expressions
    this._load2DExpressions();
  }
  
  /**
   * Charge les expressions pour l'avatar 2D
   * @private
   */
  _load2DExpressions() {
    // Définir les classes CSS pour chaque expression
    this.expressions = {
      neutral: 'expression-neutral',
      happy: 'expression-happy',
      concerned: 'expression-concerned',
      thinking: 'expression-thinking'
    };
    
    // Définir les animations pour chaque état
    this.animations = {
      idle: 'anim-idle',
      talking: 'anim-talking',
      listening: 'anim-listening',
      thinking: 'anim-thinking'
    };
    
    // Appliquer l'expression par défaut
    this.setExpression('neutral');
  }
  
  /**
   * Charge le modèle 3D et ses animations
   * @private
   */
  _loadModel() {
    try {
      // Importer le chargeur GLB
      const loader = new THREE.GLTFLoader();
      
      if (!this.config.model_path) {
        console.error("Chemin du modèle 3D non spécifié dans la configuration");
        this._createPlaceholderModel();
        return;
      }
      
      loader.load(
        this.config.model_path,
        (gltf) => {
          this.model = gltf.scene;
          this.scene.add(this.model);
          
          // Centrer et ajuster le modèle
          this._centerModel();
          
          // Configurer les animations
          if (gltf.animations && gltf.animations.length) {
            this.mixer = new THREE.AnimationMixer(this.model);
            
            // Mapper les animations
            gltf.animations.forEach(clip => {
              const name = clip.name.toLowerCase();
              if (name.includes('idle')) {
                this.animations.idle = clip;
              } else if (name.includes('talk')) {
                this.animations.talking = clip;
              } else if (name.includes('listen')) {
                this.animations.listening = clip;
              } else if (name.includes('think')) {
                this.animations.thinking = clip;
              }
            });
            
            // Lancer l'animation par défaut
            this.playAnimation('idle');
          }
        },
        (xhr) => {
          console.log(`Chargement du modèle: ${(xhr.loaded / xhr.total) * 100}%`);
        },
        (error) => {
          console.error('Erreur lors du chargement du modèle:', error);
          this._createPlaceholderModel();
        }
      );
    } catch (error) {
      console.error('Erreur lors du chargement du modèle:', error);
      this._createPlaceholderModel();
    }
  }
  
  /**
   * Crée un modèle 3D de remplacement simple
   * @private
   */
  _createPlaceholderModel() {
    // Créer une tête simple
    const geometry = new THREE.SphereGeometry(1, 32, 32);
    const material = new THREE.MeshLambertMaterial({ color: 0xffdbb4 });
    const head = new THREE.Mesh(geometry, material);
    
    // Ajouter les yeux
    const eyeGeometry = new THREE.SphereGeometry(0.1, 16, 16);
    const eyeMaterial = new THREE.MeshBasicMaterial({ color: 0x000000 });
    
    const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    leftEye.position.set(-0.3, 0.2, 0.85);
    head.add(leftEye);
    
    const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    rightEye.position.set(0.3, 0.2, 0.85);
    head.add(rightEye);
    
    // Ajouter la bouche
    const mouthGeometry = new THREE.BoxGeometry(0.5, 0.1, 0.1);
    const mouthMaterial = new THREE.MeshBasicMaterial({ color: 0xcc4444 });
    this.mouth = new THREE.Mesh(mouthGeometry, mouthMaterial);
    this.mouth.position.set(0, -0.3, 0.85);
    head.add(this.mouth);
    
    this.model = head;
    this.scene.add(this.model);
  }
  
  /**
   * Centre le modèle 3D dans la scène
   * @private
   */
  _centerModel() {
    if (!this.model) return;
    
    // Calculer la boîte englobante
    const box = new THREE.Box3().setFromObject(this.model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    
    // Centrer le modèle
    this.model.position.x = -center.x;
    this.model.position.y = -center.y;
    this.model.position.z = -center.z;
    
    // Ajuster la taille
    const maxDim = Math.max(size.x, size.y, size.z);
    const scale = 3 / maxDim;
    this.model.scale.set(scale, scale, scale);
  }
  
  /**
   * Gère le redimensionnement de la fenêtre
   * @private
   */
  _onResize() {
    if (this.avatarType === '3d' && this.renderer && this.camera) {
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    }
  }
  
  /**
   * Boucle d'animation pour le rendu 3D
   * @private
   */
  _animate() {
    if (this.avatarType !== '3d') return;
    
    requestAnimationFrame(this._animate.bind(this));
    
    // Mettre à jour les animations
    if (this.mixer) {
      this.mixer.update(0.016); // ~60fps
    }
    
    // Animation de la bouche pour le modèle de remplacement
    if (this.mouth && this.isSpeaking) {
      this.mouth.scale.y = Math.random() * 3;
    }
    
    // Rendu de la scène
    this.renderer.render(this.scene, this.camera);
  }
  
  /**
   * Joue une animation spécifique
   * @param {string} animationName - Nom de l'animation ('idle', 'talking', etc.)
   * @param {boolean} loop - Si l'animation doit boucler
   */
  playAnimation(animationName, loop = true) {
    if (this.avatarType === '3d') {
      // Arrêter l'animation précédente
      if (this.currentAnimation) {
        this.currentAnimation.stop();
      }
      
      // Jouer la nouvelle animation si elle existe
      const animation = this.animations[animationName];
      if (animation && this.mixer) {
        this.currentAnimation = this.mixer.clipAction(animation);
        this.currentAnimation.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce);
        this.currentAnimation.clampWhenFinished = !loop;
        this.currentAnimation.reset().play();
      } else {
        console.warn(`Animation '${animationName}' non trouvée`);
      }
    } else {
      // Animation 2D via CSS
      if (this.faceElement) {
        // Retirer toutes les classes d'animation
        for (const anim of Object.values(this.animations)) {
          this.faceElement.classList.remove(anim);
        }
        
        // Ajouter la nouvelle classe d'animation si elle existe
        if (this.animations[animationName]) {
          this.faceElement.classList.add(this.animations[animationName]);
        }
      }
    }
  }
  
  /**
   * Définit l'expression de l'avatar
   * @param {string} expressionName - Nom de l'expression ('neutral', 'happy', etc.)
   */
  setExpression(expressionName) {
    this.currentExpression = expressionName;
    
    if (this.avatarType === '3d') {
      // Pour le 3D, chercher les morphTargets ou les os de visage
      if (this.model) {
        // Exemple simple - en production, il faudrait une bibliothèque comme FacialAR
        this.model.traverse(child => {
          if (child.isMesh && child.morphTargetDictionary) {
            // Réinitialiser tous les morphTargets
            for (let i = 0; i < child.morphTargetInfluences.length; i++) {
              child.morphTargetInfluences[i] = 0;
            }
            
            // Appliquer l'expression appropriée
            if (expressionName === 'happy' && child.morphTargetDictionary.smile !== undefined) {
              child.morphTargetInfluences[child.morphTargetDictionary.smile] = 1;
            } else if (expressionName === 'concerned' && child.morphTargetDictionary.sad !== undefined) {
              child.morphTargetInfluences[child.morphTargetDictionary.sad] = 0.7;
            }
          }
        });
      }
    } else {
      // Pour le 2D, modifier les classes CSS
      if (this.faceElement) {
        // Retirer toutes les classes d'expression
        for (const expr of Object.values(this.expressions)) {
          this.faceElement.classList.remove(expr);
        }
        
        // Ajouter la nouvelle classe d'expression si elle existe
        if (this.expressions[expressionName]) {
          this.faceElement.classList.add(this.expressions[expressionName]);
        }
      }
    }
  }
  
  /**
   * Commence à parler et synchronise les lèvres avec l'audio
   * @param {ArrayBuffer} audioData - Données audio à synchroniser
   * @returns {Promise} - Promise résolue quand l'audio est terminé
   */
  speak(audioData) {
    return new Promise((resolve, reject) => {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      
      this.isSpeaking = true;
      
      // Jouer l'animation de parole
      this.playAnimation('talking');
      
      try {
        // Décoder les données audio
        this.audioContext.decodeAudioData(audioData, (buffer) => {
          // Créer une source audio
          const source = this.audioContext.createBufferSource();
          source.buffer = buffer;
          
          // Créer un analyseur pour la synchronisation labiale
          const analyser = this.audioContext.createAnalyser();
          analyser.fftSize = 256;
          
          // Connecter la source à l'analyseur puis à la destination
          source.connect(analyser);
          analyser.connect(this.audioContext.destination);
          
          // Fonction pour mettre à jour la synchronisation labiale
          const updateLipSync = () => {
            if (!this.isSpeaking) return;
            
            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(dataArray);
            
            // Calculer l'amplitude moyenne
            const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
            
            // Mettre à jour l'animation des lèvres
            this._updateMouth(average / 255);
            
            // Continuer la mise à jour
            requestAnimationFrame(updateLipSync);
          };
          
          // Démarrer l'audio
          source.start(0);
          updateLipSync();
          
          // Nettoyer à la fin
          source.onended = () => {
            this.isSpeaking = false;
            this.playAnimation('idle');
            resolve();
          };
        }, (error) => {
          console.error('Erreur lors du décodage audio:', error);
          this.isSpeaking = false;
          this.playAnimation('idle');
          reject(error);
        });
      } catch (error) {
        console.error('Erreur lors de la lecture audio:', error);
        this.isSpeaking = false;
        this.playAnimation('idle');
        reject(error);
      }
    });
  }
  
  /**
   * Met à jour l'animation de la bouche en fonction de l'amplitude audio
   * @param {number} amplitude - Amplitude audio entre 0 et 1
   * @private
   */
  _updateMouth(amplitude) {
    if (this.avatarType === '3d') {
      if (this.model) {
        if (this.mouth) {
          // Pour le modèle de remplacement simple
          this.mouth.scale.y = 1 + amplitude * 2;
        } else {
          // Pour un modèle 3D complet avec morphTargets
          this.model.traverse(child => {
            if (child.isMesh && child.morphTargetDictionary && 
                child.morphTargetDictionary.mouth_open !== undefined) {
              child.morphTargetInfluences[child.morphTargetDictionary.mouth_open] = amplitude * 0.8;
            }
          });
        }
      }
    } else {
      // Animation 2D via CSS
      if (this.mouthElement) {
        const openAmount = Math.min(100, Math.floor(amplitude * 100));
        this.mouthElement.style.height = `${5 + openAmount * 0.15}px`;
      }
    }
  }
  
  /**
   * Arrête de parler
   */
  stopSpeaking() {
    this.isSpeaking = false;
    this.playAnimation('idle');
  }
  
  /**
   * Passe en mode écoute
   */
  startListening() {
    this.playAnimation('listening');
  }
  
  /**
   * Passe en mode réflexion
   */
  startThinking() {
    this.playAnimation('thinking');
    this.setExpression('thinking');
  }
  
  /**
   * Retourne à l'état par défaut
   */
  reset() {
    this.playAnimation('idle');
    this.setExpression('neutral');
  }
  
  /**
   * Nettoie les ressources lors de la destruction
   */
  dispose() {
    // Arrêter les animations
    if (this.mixer) {
      this.mixer.stopAllAction();
    }
    
    // Supprimer les écouteurs d'événements
    window.removeEventListener('resize', this._onResize.bind(this));
    
    // Nettoyer Three.js
    if (this.renderer) {
      this.renderer.dispose();
      this.container.removeChild(this.renderer.domElement);
    }
    
    // Nettoyer l'audio
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
  }
}

export default AvatarController;