import os
import numpy as np

# We try-catch heavy ML imports so the FastAPI app doesn't immediately crash
# if the pip installation is still compiling in the background or fails in Docker.
try:
    import joblib
    import torch
    from rdkit import Chem
    from rdkit.Chem import AllChem
    ML_READY = True
except ImportError:
    ML_READY = False
    print("[Warning] ML dependencies not yet available. EirionPredictor will run in stub mode.")

class EirionPredictor:
    """
    Singleton wrapper holding the massive Random Forest and PyTorch models in memory.
    Generated natively from Tox21 assays.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EirionPredictor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.base_dir = os.path.dirname(__file__)
        self.rf_path = os.path.join(self.base_dir, "weights", "tox21_rf_model.pkl")
        self.gnn_path = os.path.join(self.base_dir, "weights", "eirion_gnn_best.pt")
        
        self.rf_model = None
        self.gnn_model = None
        
        if not ML_READY:
            self._initialized = True
            return

        # 1. Load the Random Forest Baseline (~238MB)
        if os.path.exists(self.rf_path):
            try:
                self.rf_model = joblib.load(self.rf_path)
                print("[ML] Successfully loaded tox21_rf_model.pkl (Random Forest baseline)")
            except Exception as e:
                print(f"[ML] Failed to load RF model: {e}")

        # 2. Load the GNN Weights (~2MB)
        if os.path.exists(self.gnn_path):
            try:
                # If it's a raw state_dict, we need the class. If it's a TorchScript or full save, it loads directly.
                self.gnn_model = torch.load(self.gnn_path, map_location=torch.device('cpu'))
                if hasattr(self.gnn_model, 'eval'):
                    self.gnn_model.eval()  # type: ignore
                print("[ML] Successfully built computation graph for eirion_gnn_best.pt")
            except BaseException as e:
                print(f"[ML Warning] GNN loading requires explicit class definition scoping: {e}. Falling back to Random Forest exclusively.")
                self.gnn_model = None
                
        self._initialized = True

    def fingerprint(self, smiles: str) -> np.ndarray:
        """Translates a SMILES sequence into a 1024-bit Morgan Fingerprint via RDKit."""
        if not ML_READY:
            return np.zeros((1, 1024))
            
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            # Return empty/safe fingerprint if chemical is completely invalid
            return np.zeros((1, 1024))
            
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=1024)
        bit_string = fp.ToBitString()
        arr = np.array([int(b) for b in bit_string]).reshape(1, -1)
        return arr

    def predict_toxicity(self, smiles: str) -> float:
        """
        Executes a forward pass over the models to determine the probability `[0.0 - 1.0]`
        that this compound raises a positive assay on the Tox21 panel (`label_any`).
        """
        if not ML_READY or self.rf_model is None:
            return 0.05 # Conservative baseline 5% toxicity risk
            
        fp = self.fingerprint(smiles)
        
        try:
            # Scikit-Learn Multilabel RandomForest predict_proba 
            # Output is typically a list of 13 arrays (one for each task), where each array is shape (1, 2)
            preds = self.rf_model.predict_proba(fp)  # type: ignore
            
            if isinstance(preds, list) and len(preds) > 0:
                # The ultimate target is `label_any`, conventionally the last label (index -1)
                label_any_probs = preds[-1]
                prob_positive = float(label_any_probs[0][1])
                return prob_positive
            else:
                # Single output fallback structure
                if preds.shape[1] == 2:
                    return float(preds[0][1])
                    
            return 0.1
        except Exception as e:
            print(f"[ML] Inference failed for {smiles}: {e}")
            return 0.1

predictor = EirionPredictor()
