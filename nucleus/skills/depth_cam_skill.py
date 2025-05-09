from nucleus.skill_manager import Skill
import torch
import cv2
import numpy as np
import os

class DepthCamSkill(Skill):
    """
    This skill streams webcam depth using Depth Anything V2.
    If you want to see the world in 3D, this is your thing.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="depth_cam",
            description="Streams webcam depth using Depth Anything V2 model.",
            capability=None
        )
        self.event_bus = event_bus
        self.model = None
        self.current_encoder = None

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Stream depth",
                "desc": "Streams webcam with depth visualization.",
                "input_type": "model",
                "output_type": "image",
                "tags": ["depth", "webcam", "stream"]
            }
        ]

    def load_model(self, encoder):
        if self.current_encoder != encoder:
            try:
                from depth_anything_v2.dpt import DepthAnythingV2
                model_configs = {
                    'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
                    'vitb': {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]},
                    'vitl': {'encoder': 'vitl', 'features': 256, 'out_channels': [256, 512, 1024, 1024]},
                    'vitg': {'encoder': 'vitg', 'features': 384, 'out_channels': [1536, 1536, 1536, 1536]}
                }
                self.model = DepthAnythingV2(**model_configs[encoder])
                weights_path = f'./checkpoints/depth_anything_v2_{encoder}.pth'
                if not os.path.exists(weights_path):
                    raise FileNotFoundError(f"Model weights not found at {weights_path}.")
                self.model.load_state_dict(torch.load(weights_path, map_location='cpu'))
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                self.model = self.model.to(device).eval()
                self.current_encoder = encoder
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                raise e
        return self.model

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me an intent "Stream depth" and model_name, and I'll start the webcam stream.
        """
        intent = step.get("intent", "").lower()
        model_name = step.get("model_name", "vits")
        if "stream" in intent:
            return self.webcam_stream(model_name)
        else:
            return {"error": "Unknown depth cam intent."}

    def predict_depth(self, image, encoder):
        model = self.load_model(encoder)
        depth = model.infer_image(image)
        depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
        depth = depth.astype(np.uint8)
        return depth

    def process_frame(self, frame, encoder):
        try:
            frame_resized = cv2.resize(frame, (384, 288))
            depth = self.predict_depth(frame_resized, encoder)
            depth_colored = cv2.applyColorMap(depth, cv2.COLORMAP_JET)
            depth_colored = cv2.resize(depth_colored, (frame.shape[1], frame.shape[0]))
            return depth_colored
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            return None

    def webcam_stream(self, model_name):
        encoder2name = {
            'vits': 'Small', 'vitb': 'Base', 'vitl': 'Large', 'vitg': 'Giant'
        }
        name2encoder = {v: k for k, v in encoder2name.items()}
        encoder = name2encoder.get(model_name, "vits")
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            return None
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                depth_colored = self.process_frame(frame, encoder)
                if depth_colored is not None:
                    yield depth_colored
        finally:
            cap.release()