#!/usr/bin/env python3
"""
TikTok Automation System - Content Generation Engine
Geeky Workflow Core v2.0
"""

import os
import json
import logging
import random
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import subprocess
import tempfile

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent / "config"))
from main_config import config

@dataclass
class ContentTemplate:
    """Content template structure"""
    name: str
    category: str
    duration: int
    style: str
    has_audio: bool = True
    text_overlay: bool = True
    transitions: List[str] = None
    
    def __post_init__(self):
        if self.transitions is None:
            self.transitions = ["fade", "slide", "zoom"]

@dataclass
class GeneratedContent:
    """Generated content metadata"""
    file_path: str
    title: str
    description: str
    hashtags: List[str]
    duration: float
    created_at: datetime
    template_used: str

class AIGenerator:
    """AI-powered content generation"""
    
    def __init__(self):
        self.openai_api_key = config.ai.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_caption(self, topic: str, style: str = "engaging") -> Dict[str, Any]:
        """Generate TikTok caption using AI"""
        prompt = f"""
        Generate an engaging TikTok caption about: {topic}
        Style: {style}
        
        Requirements:
        - Maximum 150 characters
        - Include 3-5 relevant hashtags
        - Make it catchy and viral-worthy
        - Include a call-to-action
        
        Return as JSON with keys: title, caption, hashtags
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": config.ai.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                logging.error(f"OpenAI API error: {response.status_code}")
                return self._fallback_caption(topic)
                
        except Exception as e:
            logging.error(f"AI caption generation failed: {e}")
            return self._fallback_caption(topic)
    
    def _fallback_caption(self, topic: str) -> Dict[str, Any]:
        """Fallback caption generation"""
        return {
            "title": f"Amazing {topic} Facts! 🤯",
            "caption": f"Did you know these incredible things about {topic}? #fyp #viral #{topic.replace(' ', '')}",
            "hashtags": ["#fyp", "#viral", f"#{topic.replace(' ', '')}", "#trending"]
        }
    
    def generate_script(self, topic: str, duration: int = 30) -> str:
        """Generate video script"""
        prompt = f"""
        Generate a {duration}-second TikTok video script about: {topic}
        
        Requirements:
        - Split into 3-5 scenes
        - Each scene should be 5-10 seconds
        - Include visual descriptions
        - Include text overlays
        - Make it fast-paced and engaging
        
        Return as JSON with scenes array containing: duration, visual, text
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": config.ai.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                return self._fallback_script(topic, duration)
                
        except Exception as e:
            logging.error(f"Script generation failed: {e}")
            return self._fallback_script(topic, duration)
    
    def _fallback_script(self, topic: str, duration: int) -> str:
        """Fallback script generation"""
        scenes = []
        scene_duration = duration // 3
        
        for i in range(3):
            scenes.append({
                "duration": scene_duration,
                "visual": f"Dynamic visuals about {topic}",
                "text": f"Amazing fact #{i+1} about {topic}!"
            })
        
        return {"scenes": scenes}

class VideoGenerator:
    """Video generation using FFmpeg and other tools"""
    
    def __init__(self):
        self.output_dir = Path(config.content.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required tools are installed"""
        required_tools = ["ffmpeg", "convert", "python3"]
        for tool in required_tools:
            try:
                subprocess.run([tool, "--version"], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logging.error(f"Missing required tool: {tool}")
                raise
    
    def create_video_from_images(self, 
                                image_paths: List[str], 
                                duration: int = 30,
                                output_path: Optional[str] = None) -> str:
        """Create video from image sequence"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"video_{timestamp}.mp4")
        
        # Calculate duration per image
        duration_per_image = duration / len(image_paths)
        
        # Create FFmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-framerate", "1/" + str(duration_per_image),
            "-i", f"concat:{'|'.join(image_paths)}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-r", "30",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logging.info(f"Video created: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logging.error(f"Video creation failed: {e}")
            raise
    
    def add_text_overlay(self, 
                        video_path: str, 
                        text: str, 
                        output_path: Optional[str] = None) -> str:
        """Add text overlay to video"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"video_text_{timestamp}.mp4")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=48:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:x=(w-text_w)/2:y=h-100",
            "-c:a", "copy",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logging.info(f"Text overlay added: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logging.error(f"Text overlay failed: {e}")
            raise
    
    def add_background_music(self, 
                           video_path: str, 
                           music_path: str,
                           output_path: Optional[str] = None) -> str:
        """Add background music to video"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"video_music_{timestamp}.mp4")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex", "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=first",
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logging.info(f"Background music added: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logging.error(f"Background music addition failed: {e}")
            raise

class ContentGenerator:
    """Main content generation orchestrator"""
    
    def __init__(self):
        self.ai_generator = AIGenerator()
        self.video_generator = VideoGenerator()
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, ContentTemplate]:
        """Load content templates"""
        templates = {
            "viral_facts": ContentTemplate(
                name="Viral Facts",
                category="education",
                duration=30,
                style="fast-paced",
                transitions=["cut", "zoom"]
            ),
            "lifestyle_tips": ContentTemplate(
                name="Lifestyle Tips",
                category="lifestyle",
                duration=45,
                style="inspirational",
                transitions=["fade", "slide"]
            ),
            "tech_reviews": ContentTemplate(
                name="Tech Reviews",
                category="tech",
                duration=60,
                style="professional",
                transitions=["slide", "dissolve"]
            ),
            "entertainment": ContentTemplate(
                name="Entertainment",
                category="entertainment",
                duration=30,
                style="fun",
                transitions=["cut", "spin"]
            )
        }
        return templates
    
    def generate_content(self, 
                        topic: str, 
                        template_name: str = "viral_facts",
                        count: int = 1) -> List[GeneratedContent]:
        """Generate multiple content pieces"""
        
        if template_name not in self.templates:
            logging.error(f"Unknown template: {template_name}")
            template_name = "viral_facts"
        
        template = self.templates[template_name]
        generated_content = []
        
        for i in range(count):
            try:
                # Generate AI content
                caption_data = self.ai_generator.generate_caption(topic, template.style)
                script_data = self.ai_generator.generate_script(topic, template.duration)
                
                # Create placeholder images (in real implementation, these would be generated)
                placeholder_images = self._create_placeholder_images(script_data)
                
                # Generate video
                video_path = self.video_generator.create_video_from_images(
                    placeholder_images, 
                    template.duration
                )
                
                # Add text overlay
                if template.text_overlay:
                    video_path = self.video_generator.add_text_overlay(
                        video_path, 
                        caption_data["title"]
                    )
                
                # Create content metadata
                content = GeneratedContent(
                    file_path=video_path,
                    title=caption_data["title"],
                    description=caption_data["caption"],
                    hashtags=caption_data["hashtags"],
                    duration=template.duration,
                    created_at=datetime.now(),
                    template_used=template_name
                )
                
                generated_content.append(content)
                logging.info(f"Generated content {i+1}/{count}: {content.title}")
                
            except Exception as e:
                logging.error(f"Content generation failed for item {i+1}: {e}")
                continue
        
        return generated_content
    
    def _create_placeholder_images(self, script_data: Dict[str, Any]) -> List[str]:
        """Create placeholder images for video generation"""
        # In a real implementation, this would use AI image generation
        # For now, create colored rectangles using ImageMagick
        
        temp_dir = tempfile.mkdtemp()
        image_paths = []
        
        if "scenes" in script_data:
            for i, scene in enumerate(script_data["scenes"]):
                image_path = os.path.join(temp_dir, f"scene_{i}.png")
                
                # Create a colored rectangle with text
                color = f"rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)})"
                cmd = [
                    "convert",
                    "-size", "1080x1920",
                    f"xc:{color}",
                    "-pointsize", "48",
                    "-fill", "white",
                    "-gravity", "center",
                    "-annotate", "+0+0", scene.get("text", f"Scene {i+1}"),
                    image_path
                ]
                
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    image_paths.append(image_path)
                except subprocess.CalledProcessError as e:
                    logging.error(f"Image creation failed: {e}")
        
        return image_paths

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate TikTok content")
    parser.add_argument("--topic", required=True, help="Content topic")
    parser.add_argument("--template", default="viral_facts", help="Template name")
    parser.add_argument("--count", type=int, default=1, help="Number of content pieces")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Generate content
    generator = ContentGenerator()
    content_list = generator.generate_content(args.topic, args.template, args.count)
    
    print(f"\nGenerated {len(content_list)} content pieces:")
    for content in content_list:
        print(f"- {content.title}")
        print(f"  File: {content.file_path}")
        print(f"  Hashtags: {', '.join(content.hashtags)}")
        print()
