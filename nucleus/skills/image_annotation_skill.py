from nucleus.skill_manager import Skill
import os
import csv
import shutil
from pathlib import Path

class ImageAnnotationSkill(Skill):
    """
    This skill processes image files and their text annotations, then generates a metadata CSV for HuggingFace.
    If your files are a mess, at least you'll get an error message.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="image_annotation",
            description="Processes images and text annotations, creates metadata.csv for HuggingFace.",
            capability=None
        )
        self.event_bus = event_bus

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Process files",
                "desc": "Pairs images and text files, copies images to output, returns mapping.",
                "input_type": "dir",
                "output_type": "dict",
                "tags": ["image", "annotation", "csv"]
            },
            {
                "intent": "Generate metadata CSV",
                "desc": "Processes files and generates metadata.csv.",
                "input_type": "dir",
                "output_type": "csv",
                "tags": ["image", "annotation", "csv", "huggingface"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me input_dir and output_dir, and I'll try to process or generate metadata.
        """
        input_dir = Path(step.get("input_dir", "."))
        output_dir = Path(step.get("output_dir", "./output"))
        intent = step.get("intent", "").lower()
        if "process" in intent:
            return self.process_files(input_dir, output_dir)
        elif "csv" in intent:
            return self.generate_metadata_csv(input_dir, output_dir)
        else:
            return {"error": "Unknown image annotation intent."}

    def process_files(self, input_dir: Path, output_dir: Path):
        image_extensions = ['.png', '.jpg', '.jpeg', '.heic']
        text_extension = '.txt'
        os.makedirs(output_dir, exist_ok=True)
        file_pairs = []
        all_files = list(input_dir.glob('*'))
        image_files = [f for f in all_files if f.suffix.lower() in image_extensions]
        text_files = {f.stem: f for f in all_files if f.suffix.lower() == text_extension}
        for img_file in image_files:
            if img_file.stem in text_files:
                file_pairs.append((img_file, text_files[img_file.stem]))
        metadata = {}
        for img_path, txt_path in file_pairs:
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    annotation = f.read().strip()
                shutil.copy2(img_path, output_dir)
                metadata[img_path.name] = annotation
            except Exception as e:
                metadata[img_path.name] = f"ERROR: {e}"
        return metadata

    def generate_metadata_csv(self, input_dir: Path, output_dir: Path):
        metadata = self.process_files(input_dir, output_dir)
        csv_path = output_dir / 'metadata.csv'
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['file_name', 'text'])
                for filename, text in metadata.items():
                    writer.writerow([filename, text])
            return str(csv_path)
        except Exception as e:
            return f"ERROR: {e}"