"""Image processing capability for MetaAgent.

Provides image-related operations:
- Vision analysis (GPT-4V, Claude Vision)
- Image generation (DALL-E 3, Stable Diffusion)
- Image editing (crop, resize, filters)
- Screenshot capture
- OCR text extraction

Requires optional dependencies:
- openai: For DALL-E and GPT-4V
- anthropic: For Claude Vision
- pillow: For image manipulation
- pytesseract: For OCR
"""

import base64
import io
import os
import shutil
import tempfile
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)

# Optional imports
try:
    from PIL import Image, ImageFilter, ImageEnhance

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None  # type: ignore

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore


class ImageProvider(str, Enum):
    """Supported image providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    STABILITY = "stability"
    LOCAL = "local"


class ImageSize(str, Enum):
    """Standard image sizes for generation."""

    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "1024x1024"
    WIDE = "1792x1024"
    TALL = "1024x1792"


class ImageConfig(CapabilityConfig):
    """Configuration for image capability."""

    # Provider settings
    default_provider: str = Field(
        default="openai",
        description="Default provider for image operations",
    )
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key (uses OPENAI_API_KEY env if not set)",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key (uses ANTHROPIC_API_KEY env if not set)",
    )
    stability_api_key: str | None = Field(
        default=None,
        description="Stability AI API key",
    )

    # Generation settings
    default_size: str = Field(default="1024x1024", description="Default image size")
    default_quality: str = Field(
        default="standard", description="Image quality (standard, hd)"
    )
    default_style: str = Field(
        default="natural", description="Image style (natural, vivid)"
    )

    # Vision settings
    vision_model: str = Field(
        default="gpt-4o", description="Model for vision analysis"
    )
    max_tokens: int = Field(default=1000, description="Max tokens for vision response")

    # Local settings
    temp_dir: str | None = Field(default=None, description="Temp directory for images")
    tesseract_path: str | None = Field(
        default=None, description="Path to tesseract executable"
    )


class ImageResult:
    """Result of an image operation."""

    def __init__(
        self,
        success: bool,
        operation: str,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        image_path: str | None = None,
        image_url: str | None = None,
        image_base64: str | None = None,
        text: str | None = None,
        duration_ms: float = 0,
    ):
        self.success = success
        self.operation = operation
        self.data = data or {}
        self.error = error
        self.image_path = image_path
        self.image_url = image_url
        self.image_base64 = image_base64
        self.text = text
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "operation": self.operation,
            "duration_ms": self.duration_ms,
        }
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.image_path:
            result["image_path"] = self.image_path
        if self.image_url:
            result["image_url"] = self.image_url
        if self.image_base64:
            result["image_base64"] = self.image_base64
        if self.text:
            result["text"] = self.text
        return result


class ImageCapability(BaseCapability):
    """Image processing capability.

    Provides comprehensive image operations including:
    - Vision analysis with GPT-4V or Claude Vision
    - Image generation with DALL-E 3 or Stable Diffusion
    - Image editing (crop, resize, rotate, filters)
    - Screenshot capture
    - OCR text extraction

    Example:
        >>> img = ImageCapability()
        >>> await img.initialize()

        >>> # Analyze an image
        >>> result = await img.analyze("path/to/image.png", "What's in this image?")

        >>> # Generate an image
        >>> result = await img.generate("A sunset over mountains")

        >>> # Edit an image
        >>> result = await img.resize("image.png", width=800, height=600)

        >>> # Extract text (OCR)
        >>> result = await img.ocr("screenshot.png")
    """

    name = "image"
    description = "Image vision, generation, editing, and OCR capabilities"

    def __init__(self, config: ImageConfig | None = None):
        """Initialize image capability."""
        super().__init__(config or ImageConfig())
        self.config: ImageConfig = self.config
        self._temp_dir: Path | None = None
        self._openai_client: Any = None
        self._anthropic_client: Any = None
        self._http_client: Any = None

    async def initialize(self) -> None:
        """Initialize image capability."""
        # Create temp directory
        if self.config.temp_dir:
            self._temp_dir = Path(self.config.temp_dir)
            self._temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="paracle_image_"))

        # Initialize HTTP client
        if HTTPX_AVAILABLE:
            self._http_client = httpx.AsyncClient(timeout=120.0)

        # Initialize OpenAI client if available
        try:
            import openai

            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self._openai_client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError:
            pass

        # Initialize Anthropic client if available
        try:
            import anthropic

            api_key = self.config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self._anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            pass

        # Configure tesseract path
        if self.config.tesseract_path and TESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_path

        await super().initialize()

    async def shutdown(self) -> None:
        """Cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        # Clean temp directory
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute image operation.

        Args:
            action: Operation to perform (analyze, generate, edit, ocr, screenshot)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "analyze")
        start_time = time.time()

        try:
            if action == "analyze":
                result = await self._analyze(**kwargs)
            elif action == "generate":
                result = await self._generate(**kwargs)
            elif action == "edit":
                result = await self._edit(**kwargs)
            elif action == "ocr":
                result = await self._ocr(**kwargs)
            elif action == "screenshot":
                result = await self._screenshot(**kwargs)
            elif action == "resize":
                result = await self._resize(**kwargs)
            elif action == "crop":
                result = await self._crop(**kwargs)
            elif action == "convert":
                result = await self._convert(**kwargs)
            elif action == "info":
                result = await self._get_info(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result.to_dict(),
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _analyze(
        self,
        image: str,
        prompt: str = "Describe this image in detail.",
        provider: str | None = None,
        **kwargs,
    ) -> ImageResult:
        """Analyze an image using vision AI.

        Args:
            image: Path to image or URL or base64
            prompt: Question or instruction about the image
            provider: Vision provider (openai, anthropic)

        Returns:
            ImageResult with analysis
        """
        provider = provider or self.config.default_provider
        start_time = time.time()

        # Load and encode image
        image_data = await self._load_image(image)

        if provider == "openai" and self._openai_client:
            response = await self._openai_client.chat.completions.create(
                model=self.config.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data['base64']}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=self.config.max_tokens,
            )
            analysis = response.choices[0].message.content

        elif provider == "anthropic" and self._anthropic_client:
            response = await self._anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=self.config.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_data["mime_type"],
                                    "data": image_data["base64"],
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            analysis = response.content[0].text

        else:
            raise RuntimeError(f"No vision provider available for: {provider}")

        duration_ms = (time.time() - start_time) * 1000
        return ImageResult(
            success=True,
            operation="analyze",
            text=analysis,
            data={"prompt": prompt, "provider": provider},
            duration_ms=duration_ms,
        )

    async def _generate(
        self,
        prompt: str,
        size: str | None = None,
        quality: str | None = None,
        style: str | None = None,
        n: int = 1,
        provider: str = "openai",
        save_path: str | None = None,
        **kwargs,
    ) -> ImageResult:
        """Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate
            size: Image size (256x256, 512x512, 1024x1024, etc.)
            quality: Image quality (standard, hd)
            style: Image style (natural, vivid)
            n: Number of images to generate
            provider: Generation provider (openai, stability)
            save_path: Optional path to save the image

        Returns:
            ImageResult with generated image
        """
        size = size or self.config.default_size
        quality = quality or self.config.default_quality
        style = style or self.config.default_style
        start_time = time.time()

        if provider == "openai" and self._openai_client:
            response = await self._openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=n,
                response_format="url",
            )

            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt

            # Download and save if path specified
            image_path = None
            image_base64 = None
            if save_path or self._temp_dir:
                if HTTPX_AVAILABLE and self._http_client:
                    img_response = await self._http_client.get(image_url)
                    img_data = img_response.content
                    image_base64 = base64.b64encode(img_data).decode()

                    if save_path:
                        image_path = save_path
                    else:
                        image_path = str(
                            self._temp_dir / f"generated_{int(time.time())}.png"
                        )
                    Path(image_path).write_bytes(img_data)

            duration_ms = (time.time() - start_time) * 1000
            return ImageResult(
                success=True,
                operation="generate",
                image_url=image_url,
                image_path=image_path,
                image_base64=image_base64,
                data={
                    "prompt": prompt,
                    "revised_prompt": revised_prompt,
                    "size": size,
                    "quality": quality,
                    "style": style,
                },
                duration_ms=duration_ms,
            )

        elif provider == "stability":
            # Stability AI API
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx required for Stability AI")

            api_key = self.config.stability_api_key or os.getenv("STABILITY_API_KEY")
            if not api_key:
                raise RuntimeError("Stability AI API key not configured")

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }

            response = await self._http_client.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers=headers,
                json={
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": 7,
                    "height": int(size.split("x")[1]),
                    "width": int(size.split("x")[0]),
                    "samples": n,
                },
            )

            if response.status_code != 200:
                raise RuntimeError(f"Stability API error: {response.text}")

            data = response.json()
            image_base64 = data["artifacts"][0]["base64"]

            # Save image
            image_path = None
            if save_path or self._temp_dir:
                if save_path:
                    image_path = save_path
                else:
                    image_path = str(
                        self._temp_dir / f"generated_{int(time.time())}.png"
                    )
                Path(image_path).write_bytes(base64.b64decode(image_base64))

            duration_ms = (time.time() - start_time) * 1000
            return ImageResult(
                success=True,
                operation="generate",
                image_path=image_path,
                image_base64=image_base64,
                data={"prompt": prompt, "size": size, "provider": "stability"},
                duration_ms=duration_ms,
            )

        else:
            raise RuntimeError(f"No generation provider available for: {provider}")

    async def _edit(
        self,
        image: str,
        operation: str,
        **kwargs,
    ) -> ImageResult:
        """Edit an image.

        Args:
            image: Path to image
            operation: Edit operation (blur, sharpen, brightness, contrast, grayscale)
            **kwargs: Operation-specific parameters

        Returns:
            ImageResult with edited image
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow required for image editing: pip install pillow")

        start_time = time.time()
        img = Image.open(image)
        output_path = kwargs.get("output_path")

        if operation == "blur":
            radius = kwargs.get("radius", 2)
            img = img.filter(ImageFilter.GaussianBlur(radius=radius))

        elif operation == "sharpen":
            img = img.filter(ImageFilter.SHARPEN)

        elif operation == "brightness":
            factor = kwargs.get("factor", 1.5)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(factor)

        elif operation == "contrast":
            factor = kwargs.get("factor", 1.5)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(factor)

        elif operation == "grayscale":
            img = img.convert("L")

        elif operation == "rotate":
            angle = kwargs.get("angle", 90)
            img = img.rotate(angle, expand=True)

        elif operation == "flip":
            direction = kwargs.get("direction", "horizontal")
            if direction == "horizontal":
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            else:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)

        else:
            raise ValueError(f"Unknown edit operation: {operation}")

        # Save result
        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"edited_{int(time.time())}.png")

        if output_path:
            img.save(output_path)

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        duration_ms = (time.time() - start_time) * 1000
        return ImageResult(
            success=True,
            operation="edit",
            image_path=output_path,
            image_base64=image_base64,
            data={"original": image, "edit_operation": operation, **kwargs},
            duration_ms=duration_ms,
        )

    async def _resize(
        self,
        image: str,
        width: int | None = None,
        height: int | None = None,
        maintain_aspect: bool = True,
        output_path: str | None = None,
        **kwargs,
    ) -> ImageResult:
        """Resize an image.

        Args:
            image: Path to image
            width: Target width
            height: Target height
            maintain_aspect: Maintain aspect ratio
            output_path: Output file path

        Returns:
            ImageResult with resized image
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow required: pip install pillow")

        start_time = time.time()
        img = Image.open(image)
        original_size = img.size

        if maintain_aspect:
            if width and not height:
                ratio = width / img.width
                height = int(img.height * ratio)
            elif height and not width:
                ratio = height / img.height
                width = int(img.width * ratio)
            elif width and height:
                # Fit within bounds
                ratio = min(width / img.width, height / img.height)
                width = int(img.width * ratio)
                height = int(img.height * ratio)

        if width and height:
            img = img.resize((width, height), Image.LANCZOS)

        # Save result
        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"resized_{int(time.time())}.png")

        if output_path:
            img.save(output_path)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        duration_ms = (time.time() - start_time) * 1000
        return ImageResult(
            success=True,
            operation="resize",
            image_path=output_path,
            image_base64=image_base64,
            data={
                "original_size": original_size,
                "new_size": img.size,
            },
            duration_ms=duration_ms,
        )

    async def _crop(
        self,
        image: str,
        left: int,
        top: int,
        right: int,
        bottom: int,
        output_path: str | None = None,
        **kwargs,
    ) -> ImageResult:
        """Crop an image.

        Args:
            image: Path to image
            left: Left coordinate
            top: Top coordinate
            right: Right coordinate
            bottom: Bottom coordinate
            output_path: Output file path

        Returns:
            ImageResult with cropped image
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow required: pip install pillow")

        start_time = time.time()
        img = Image.open(image)
        img = img.crop((left, top, right, bottom))

        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"cropped_{int(time.time())}.png")

        if output_path:
            img.save(output_path)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        duration_ms = (time.time() - start_time) * 1000
        return ImageResult(
            success=True,
            operation="crop",
            image_path=output_path,
            image_base64=image_base64,
            data={"crop_box": (left, top, right, bottom), "size": img.size},
            duration_ms=duration_ms,
        )

    async def _convert(
        self,
        image: str,
        format: str = "PNG",
        output_path: str | None = None,
        **kwargs,
    ) -> ImageResult:
        """Convert image format.

        Args:
            image: Path to image
            format: Target format (PNG, JPEG, WEBP, etc.)
            output_path: Output file path

        Returns:
            ImageResult with converted image
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow required: pip install pillow")

        start_time = time.time()
        img = Image.open(image)

        # Handle RGBA to RGB for JPEG
        if format.upper() == "JPEG" and img.mode == "RGBA":
            img = img.convert("RGB")

        if not output_path and self._temp_dir:
            ext = format.lower()
            if ext == "jpeg":
                ext = "jpg"
            output_path = str(self._temp_dir / f"converted_{int(time.time())}.{ext}")

        if output_path:
            img.save(output_path, format=format.upper())

        buffer = io.BytesIO()
        img.save(buffer, format=format.upper())
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        duration_ms = (time.time() - start_time) * 1000
        return ImageResult(
            success=True,
            operation="convert",
            image_path=output_path,
            image_base64=image_base64,
            data={"format": format, "size": img.size},
            duration_ms=duration_ms,
        )

    async def _ocr(
        self,
        image: str,
        language: str = "eng",
        **kwargs,
    ) -> ImageResult:
        """Extract text from image using OCR.

        Args:
            image: Path to image
            language: OCR language (eng, fra, deu, etc.)

        Returns:
            ImageResult with extracted text
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("pytesseract required: pip install pytesseract")
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow required: pip install pillow")

        start_time = time.time()
        img = Image.open(image)
        text = pytesseract.image_to_string(img, lang=language)

        # Get detailed data
        data = pytesseract.image_to_data(img, lang=language, output_type="dict")
        words = [w for w in data["text"] if w.strip()]

        duration_ms = (time.time() - start_time) * 1000
        return ImageResult(
            success=True,
            operation="ocr",
            text=text.strip(),
            data={
                "language": language,
                "word_count": len(words),
                "confidence": sum(data["conf"]) / len(data["conf"]) if data["conf"] else 0,
            },
            duration_ms=duration_ms,
        )

    async def _screenshot(
        self,
        region: tuple[int, int, int, int] | None = None,
        output_path: str | None = None,
        **kwargs,
    ) -> ImageResult:
        """Capture a screenshot.

        Args:
            region: Optional region (x, y, width, height)
            output_path: Output file path

        Returns:
            ImageResult with screenshot
        """
        try:
            import pyautogui

            PYAUTOGUI_AVAILABLE = True
        except ImportError:
            PYAUTOGUI_AVAILABLE = False

        if not PYAUTOGUI_AVAILABLE:
            raise RuntimeError("pyautogui required: pip install pyautogui")

        start_time = time.time()

        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"screenshot_{int(time.time())}.png")

        if output_path:
            screenshot.save(output_path)

        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        duration_ms = (time.time() - start_time) * 1000
        return ImageResult(
            success=True,
            operation="screenshot",
            image_path=output_path,
            image_base64=image_base64,
            data={"size": screenshot.size, "region": region},
            duration_ms=duration_ms,
        )

    async def _get_info(self, image: str, **kwargs) -> ImageResult:
        """Get image information.

        Args:
            image: Path to image

        Returns:
            ImageResult with image info
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow required: pip install pillow")

        start_time = time.time()
        img = Image.open(image)

        info = {
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "width": img.width,
            "height": img.height,
        }

        # Get file size
        if Path(image).exists():
            info["file_size_bytes"] = Path(image).stat().st_size

        # Get EXIF data if available
        if hasattr(img, "_getexif") and img._getexif():
            exif = img._getexif()
            info["has_exif"] = True
            info["exif_tags"] = len(exif) if exif else 0
        else:
            info["has_exif"] = False

        duration_ms = (time.time() - start_time) * 1000
        return ImageResult(
            success=True,
            operation="info",
            data=info,
            duration_ms=duration_ms,
        )

    async def _load_image(self, image: str) -> dict[str, Any]:
        """Load image and return as base64 with metadata."""
        if image.startswith("data:"):
            # Already base64 data URL
            parts = image.split(",", 1)
            mime_type = parts[0].split(":")[1].split(";")[0]
            return {"base64": parts[1], "mime_type": mime_type}

        elif image.startswith(("http://", "https://")):
            # URL - download first
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx required for URL images")

            response = await self._http_client.get(image)
            content_type = response.headers.get("content-type", "image/png")
            return {
                "base64": base64.b64encode(response.content).decode(),
                "mime_type": content_type,
            }

        else:
            # File path
            path = Path(image)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {image}")

            data = path.read_bytes()
            ext = path.suffix.lower()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".bmp": "image/bmp",
            }
            mime_type = mime_types.get(ext, "image/png")

            return {"base64": base64.b64encode(data).decode(), "mime_type": mime_type}

    # Convenience methods
    async def analyze(self, image: str, prompt: str = "Describe this image.") -> CapabilityResult:
        """Analyze an image using vision AI."""
        return await self.execute(action="analyze", image=image, prompt=prompt)

    async def generate(self, prompt: str, **kwargs) -> CapabilityResult:
        """Generate an image from a text prompt."""
        return await self.execute(action="generate", prompt=prompt, **kwargs)

    async def resize(self, image: str, width: int = None, height: int = None, **kwargs) -> CapabilityResult:
        """Resize an image."""
        return await self.execute(action="resize", image=image, width=width, height=height, **kwargs)

    async def crop(self, image: str, left: int, top: int, right: int, bottom: int, **kwargs) -> CapabilityResult:
        """Crop an image."""
        return await self.execute(action="crop", image=image, left=left, top=top, right=right, bottom=bottom, **kwargs)

    async def ocr(self, image: str, language: str = "eng") -> CapabilityResult:
        """Extract text from image using OCR."""
        return await self.execute(action="ocr", image=image, language=language)

    async def screenshot(self, **kwargs) -> CapabilityResult:
        """Capture a screenshot."""
        return await self.execute(action="screenshot", **kwargs)

    async def info(self, image: str) -> CapabilityResult:
        """Get image information."""
        return await self.execute(action="info", image=image)
