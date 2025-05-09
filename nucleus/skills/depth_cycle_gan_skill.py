from nucleus.skill_manager import Skill
import torch
import cv2
import numpy as np
import os
from PIL import Image
import shutil
import tempfile

class DepthCycleGANSkill(Skill):
    """
    This skill generates depth maps for all images in a folder and can upload to HuggingFace.
    If you want batch depth for your dataset, this does the trick.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="depth_cycle_gan",
            description="Batch generates depth maps for images using Depth Anything V2.",
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
                "intent": "Batch depth",
                "desc": "Batch generates depth maps for folder of images.",
                "input_type": "folder",
                "output_type": "folder",
                "tags": ["depth", "cycle_gan", "batch"]
            },
            {
                "intent": "Upload to HuggingFace",
                "desc": "Uploads images and depth maps to HuggingFace dataset.",
                "input_type": "folder",
                "output_type": "repo",
                "tags": ["huggingface", "upload", "depth"]
            }
        ]

    def load_model(self, encoder):
        if self.current_encoder != encoder:
            from depth_anything_v2.dpt import DepthAnythingV2
            model_configs = {
                'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
                'vitb': {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]},
                'vitl': {'encoder': 'vitl', 'features': 256, 'out_channels': [256, 512, 1024, 1024]}
            }
            self.model = DepthAnythingV2(**model_configs[encoder])
            weights_path = f'./checkpoints/depth_anything_v2_{encoder}.pth'
            if not os.path.exists(weights_path):
                raise FileNotFoundError(f"Model weights not found at {weights_path}.")
            self.model.load_state_dict(torch.load(weights_path, map_location='cpu'))
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model = self.model.to(device).eval()
            self.current_encoder = encoder
        return self.model

    def predict_depth(self, image, encoder):
        model = self.load_model(encoder)
        depth = model.infer_image(image)
        depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
        depth = depth.astype(np.uint8)
        return depth

    def process_images(self, folder_path, encoder):
        images = []
        depth_maps = []
        temp_dir = tempfile.mkdtemp()
        for filename in os.listdir(folder_path):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(folder_path, filename)
                temp_image_path = os.path.join(temp_dir, filename)
                shutil.copy(image_path, temp_image_path)
                image = Image.open(temp_image_path).convert('RGB')
                image_np = np.array(image)
                depth_map = self.predict_depth(image_np, encoder)
                depth_map_colored = cv2.applyColorMap(depth_map, cv2.COLORMAP_JET)
                image.save(temp_image_path)
                depth_map_path = os.path.join(temp_dir, f"depth_{filename}")
                Image.fromarray(depth_map_colored).save(depth_map_path, format="PNG")
                images.append(temp_image_path)
                depth_maps.append(depth_map_path)
        return images, depth_maps, temp_dir

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me intent ("Batch depth" or "Upload to HuggingFace"), folder_path, model_name, and I'll process or upload.
        """
        intent = step.get("intent", "").lower()
        folder_path = step.get("folder_path", "")
        model_name = step.get("model_name", "vits")
        encoder2name = {'vits': 'Small', 'vitb': 'Base', 'vitl': 'Large'}
        name2encoder = {v: k for k, v in encoder2name.items()}
        encoder = name2encoder.get(model_name, "vits")
        if "batch" in intent:
            images, depth_maps, temp_dir = self.process_images(folder_path, encoder)
            return {"images": images, "depth_maps": depth_maps, "temp_dir": temp_dir}
        elif "huggingface" in intent:
            # For brevity, uploading logic omitted here — integrate huggingface_hub as needed.
            return {"message": "Upload to HuggingFace not implemented in this stub."}
        else:
            return {"error": "Unknown depth cycle gan intent."}