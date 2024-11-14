import os
import json
import numpy as np
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from .error_handler import RootBotError

class AnomalyDetectorError(RootBotError):
    """Raised for anomaly detection related errors"""
    pass

class AnomalyDetector:
    """Detects system anomalies using machine learning"""
    
    def __init__(self, model_path: str = "models/anomaly_model.pkl"):
        self.logger = logging.getLogger('RootBot.anomaly')
        self.model_path = model_path
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.training_data: List[Dict[str, float]] = []
        self.is_trained = False
        
    def _prepare_features(self, metrics: Dict[str, Any]) -> np.ndarray:
        """Convert metrics to feature vector"""
        return np.array([
            metrics['cpu']['percent'],
            metrics['memory']['percent'],
            metrics['disk']['percent'],
            metrics['memory'].get('swap_percent', 0),
            metrics['cpu'].get('load_avg', [0])[0]
        ]).reshape(1, -1)
        
    def train(self, historical_data: List[Dict[str, Any]]) -> None:
        """Train the anomaly detection model"""
        try:
            if len(historical_data) < 100:
                raise AnomalyDetectorError("Insufficient training data")
                
            features = np.array([
                self._prepare_features(metrics)[0]
                for metrics in historical_data
            ])
            
            self.model.fit(features)
            self.is_trained = True
            self.logger.info("Anomaly detection model trained successfully")
            
        except Exception as e:
            raise AnomalyDetectorError(f"Failed to train model: {str(e)}")
            
    def detect_anomalies(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in current metrics"""
        if not self.is_trained:
            raise AnomalyDetectorError("Model not trained")
            
        try:
            features = self._prepare_features(metrics)
            prediction = self.model.predict(features)
            
            is_anomaly = prediction[0] == -1
            if is_anomaly:
                score = self.model.score_samples(features)[0]
                return {
                    'is_anomaly': True,
                    'score': float(score),
                    'metrics': {
                        k: v for k, v in metrics.items()
                        if isinstance(v, (int, float))
                    },
                    'timestamp': datetime.now().isoformat()
                }
            return {'is_anomaly': False}
            
        except Exception as e:
            raise AnomalyDetectorError(f"Anomaly detection failed: {str(e)}")
            
    def save_model(self) -> None:
        """Save the trained model"""
        if not self.is_trained:
            raise AnomalyDetectorError("Cannot save untrained model")
            
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                import pickle
                pickle.dump(self.model, f)
            self.logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            raise AnomalyDetectorError(f"Failed to save model: {str(e)}")
            
    def load_model(self) -> None:
        """Load a trained model"""
        try:
            if not os.path.exists(self.model_path):
                raise AnomalyDetectorError("Model file not found")
                
            with open(self.model_path, 'rb') as f:
                import pickle
                self.model = pickle.load(f)
            self.is_trained = True
            self.logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            raise AnomalyDetectorError(f"Failed to load model: {str(e)}")
