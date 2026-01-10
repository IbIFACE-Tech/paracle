"""Audio processing capability for MetaAgent.

Provides audio-related operations:
- Speech-to-text transcription (Whisper, AssemblyAI)
- Text-to-speech synthesis (OpenAI TTS, ElevenLabs)
- Audio analysis (duration, format, language detection)
- Audio conversion and manipulation

Requires optional dependencies:
- openai: For Whisper and TTS
- pydub: For audio manipulation
- speech_recognition: For local transcription
"""

import base64
import io
import os
import shutil
import tempfile
import time
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
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None  # type: ignore

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore


class TTSVoice(str, Enum):
    """OpenAI TTS voices."""

    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class TTSModel(str, Enum):
    """TTS models."""

    TTS_1 = "tts-1"
    TTS_1_HD = "tts-1-hd"


class AudioFormat(str, Enum):
    """Audio output formats."""

    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    OGG = "ogg"
    AAC = "aac"
    OPUS = "opus"


class AudioConfig(CapabilityConfig):
    """Configuration for audio capability."""

    # API keys
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key (uses OPENAI_API_KEY env if not set)",
    )
    elevenlabs_api_key: str | None = Field(
        default=None,
        description="ElevenLabs API key",
    )
    assemblyai_api_key: str | None = Field(
        default=None,
        description="AssemblyAI API key",
    )

    # Transcription settings
    transcription_model: str = Field(
        default="whisper-1",
        description="Whisper model for transcription",
    )
    default_language: str | None = Field(
        default=None,
        description="Default language for transcription",
    )

    # TTS settings
    default_voice: str = Field(default="alloy", description="Default TTS voice")
    default_tts_model: str = Field(default="tts-1", description="Default TTS model")
    default_speed: float = Field(
        default=1.0, ge=0.25, le=4.0, description="TTS speed"
    )

    # Output settings
    output_format: str = Field(default="mp3", description="Default audio format")
    temp_dir: str | None = Field(default=None, description="Temp directory")


class AudioResult:
    """Result of an audio operation."""

    def __init__(
        self,
        success: bool,
        operation: str,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        audio_path: str | None = None,
        audio_base64: str | None = None,
        text: str | None = None,
        duration_ms: float = 0,
    ):
        self.success = success
        self.operation = operation
        self.data = data or {}
        self.error = error
        self.audio_path = audio_path
        self.audio_base64 = audio_base64
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
        if self.audio_path:
            result["audio_path"] = self.audio_path
        if self.audio_base64:
            result["audio_base64"] = self.audio_base64
        if self.text:
            result["text"] = self.text
        return result


class AudioCapability(BaseCapability):
    """Audio processing capability.

    Provides comprehensive audio operations including:
    - Speech-to-text transcription with Whisper
    - Text-to-speech synthesis with OpenAI TTS
    - Audio format conversion
    - Audio analysis (duration, format info)
    - Audio manipulation (trim, merge, volume)

    Example:
        >>> audio = AudioCapability()
        >>> await audio.initialize()

        >>> # Transcribe audio to text
        >>> result = await audio.transcribe("recording.mp3")
        >>> print(result.output["text"])

        >>> # Generate speech from text
        >>> result = await audio.speak("Hello, world!", voice="nova")

        >>> # Get audio info
        >>> result = await audio.info("audio.wav")

        >>> # Convert format
        >>> result = await audio.convert("input.wav", format="mp3")
    """

    name = "audio"
    description = "Audio transcription, TTS, conversion, and analysis"

    def __init__(self, config: AudioConfig | None = None):
        """Initialize audio capability."""
        super().__init__(config or AudioConfig())
        self.config: AudioConfig = self.config
        self._temp_dir: Path | None = None
        self._openai_client: Any = None
        self._http_client: Any = None

    async def initialize(self) -> None:
        """Initialize audio capability."""
        # Create temp directory
        if self.config.temp_dir:
            self._temp_dir = Path(self.config.temp_dir)
            self._temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="paracle_audio_"))

        # Initialize HTTP client
        if HTTPX_AVAILABLE:
            self._http_client = httpx.AsyncClient(timeout=300.0)

        # Initialize OpenAI client
        try:
            import openai

            api_key = self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self._openai_client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError:
            pass

        await super().initialize()

    async def shutdown(self) -> None:
        """Cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute audio operation.

        Args:
            action: Operation (transcribe, speak, convert, info, trim, merge)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "transcribe")
        start_time = time.time()

        try:
            if action == "transcribe":
                result = await self._transcribe(**kwargs)
            elif action == "speak":
                result = await self._speak(**kwargs)
            elif action == "convert":
                result = await self._convert(**kwargs)
            elif action == "info":
                result = await self._get_info(**kwargs)
            elif action == "trim":
                result = await self._trim(**kwargs)
            elif action == "merge":
                result = await self._merge(**kwargs)
            elif action == "volume":
                result = await self._adjust_volume(**kwargs)
            elif action == "speed":
                result = await self._adjust_speed(**kwargs)
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

    async def _transcribe(
        self,
        audio: str,
        language: str | None = None,
        prompt: str | None = None,
        response_format: str = "json",
        provider: str = "openai",
        **kwargs,
    ) -> AudioResult:
        """Transcribe audio to text.

        Args:
            audio: Path to audio file
            language: Language code (e.g., 'en', 'fr')
            prompt: Optional prompt to guide transcription
            response_format: Output format (json, text, srt, vtt)
            provider: Transcription provider (openai, assemblyai)

        Returns:
            AudioResult with transcribed text
        """
        start_time = time.time()
        language = language or self.config.default_language

        if provider == "openai" and self._openai_client:
            with open(audio, "rb") as audio_file:
                params = {
                    "model": self.config.transcription_model,
                    "file": audio_file,
                    "response_format": response_format,
                }
                if language:
                    params["language"] = language
                if prompt:
                    params["prompt"] = prompt

                response = await self._openai_client.audio.transcriptions.create(
                    **params
                )

            if response_format == "json":
                text = response.text
                data = {"text": text}
            else:
                text = response
                data = {"text": text}

            duration_ms = (time.time() - start_time) * 1000
            return AudioResult(
                success=True,
                operation="transcribe",
                text=text,
                data={
                    "language": language,
                    "provider": "openai",
                    "model": self.config.transcription_model,
                },
                duration_ms=duration_ms,
            )

        elif provider == "assemblyai":
            api_key = self.config.assemblyai_api_key or os.getenv("ASSEMBLYAI_API_KEY")
            if not api_key:
                raise RuntimeError("AssemblyAI API key not configured")

            headers = {"Authorization": api_key}

            # Upload file
            with open(audio, "rb") as f:
                upload_response = await self._http_client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers=headers,
                    content=f.read(),
                )
            upload_url = upload_response.json()["upload_url"]

            # Start transcription
            transcript_request = {"audio_url": upload_url}
            if language:
                transcript_request["language_code"] = language

            response = await self._http_client.post(
                "https://api.assemblyai.com/v2/transcript",
                headers=headers,
                json=transcript_request,
            )
            transcript_id = response.json()["id"]

            # Poll for completion
            while True:
                response = await self._http_client.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers=headers,
                )
                status = response.json()["status"]
                if status == "completed":
                    text = response.json()["text"]
                    break
                elif status == "error":
                    raise RuntimeError(f"AssemblyAI error: {response.json()['error']}")
                await asyncio.sleep(1)

            duration_ms = (time.time() - start_time) * 1000
            return AudioResult(
                success=True,
                operation="transcribe",
                text=text,
                data={"language": language, "provider": "assemblyai"},
                duration_ms=duration_ms,
            )

        else:
            raise RuntimeError(f"No transcription provider available: {provider}")

    async def _speak(
        self,
        text: str,
        voice: str | None = None,
        model: str | None = None,
        speed: float | None = None,
        output_path: str | None = None,
        response_format: str = "mp3",
        provider: str = "openai",
        **kwargs,
    ) -> AudioResult:
        """Generate speech from text (TTS).

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model (tts-1, tts-1-hd)
            speed: Speech speed (0.25 to 4.0)
            output_path: Path to save audio file
            response_format: Audio format (mp3, opus, aac, flac, wav, pcm)
            provider: TTS provider (openai, elevenlabs)

        Returns:
            AudioResult with generated audio
        """
        start_time = time.time()
        voice = voice or self.config.default_voice
        model = model or self.config.default_tts_model
        speed = speed or self.config.default_speed

        if provider == "openai" and self._openai_client:
            response = await self._openai_client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed,
                response_format=response_format,
            )

            audio_data = response.content

            # Save audio
            if not output_path and self._temp_dir:
                output_path = str(
                    self._temp_dir / f"speech_{int(time.time())}.{response_format}"
                )

            if output_path:
                Path(output_path).write_bytes(audio_data)

            audio_base64 = base64.b64encode(audio_data).decode()

            duration_ms = (time.time() - start_time) * 1000
            return AudioResult(
                success=True,
                operation="speak",
                audio_path=output_path,
                audio_base64=audio_base64,
                data={
                    "text_length": len(text),
                    "voice": voice,
                    "model": model,
                    "speed": speed,
                    "format": response_format,
                    "provider": "openai",
                },
                duration_ms=duration_ms,
            )

        elif provider == "elevenlabs":
            api_key = self.config.elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                raise RuntimeError("ElevenLabs API key not configured")

            # Default voice ID (Rachel)
            voice_id = voice if len(voice) > 10 else "21m00Tcm4TlvDq8ikWAM"

            response = await self._http_client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5,
                    },
                },
            )

            if response.status_code != 200:
                raise RuntimeError(f"ElevenLabs error: {response.text}")

            audio_data = response.content

            if not output_path and self._temp_dir:
                output_path = str(self._temp_dir / f"speech_{int(time.time())}.mp3")

            if output_path:
                Path(output_path).write_bytes(audio_data)

            audio_base64 = base64.b64encode(audio_data).decode()

            duration_ms = (time.time() - start_time) * 1000
            return AudioResult(
                success=True,
                operation="speak",
                audio_path=output_path,
                audio_base64=audio_base64,
                data={
                    "text_length": len(text),
                    "voice_id": voice_id,
                    "provider": "elevenlabs",
                },
                duration_ms=duration_ms,
            )

        else:
            raise RuntimeError(f"No TTS provider available: {provider}")

    async def _convert(
        self,
        audio: str,
        format: str = "mp3",
        bitrate: str = "192k",
        output_path: str | None = None,
        **kwargs,
    ) -> AudioResult:
        """Convert audio format.

        Args:
            audio: Path to audio file
            format: Target format (mp3, wav, flac, ogg, aac)
            bitrate: Audio bitrate
            output_path: Output file path

        Returns:
            AudioResult with converted audio
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub required: pip install pydub")

        start_time = time.time()

        # Load audio
        audio_segment = AudioSegment.from_file(audio)

        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"converted_{int(time.time())}.{format}")

        # Export with format
        audio_segment.export(output_path, format=format, bitrate=bitrate)

        # Read as base64
        audio_data = Path(output_path).read_bytes()
        audio_base64 = base64.b64encode(audio_data).decode()

        duration_ms = (time.time() - start_time) * 1000
        return AudioResult(
            success=True,
            operation="convert",
            audio_path=output_path,
            audio_base64=audio_base64,
            data={
                "source_format": Path(audio).suffix[1:],
                "target_format": format,
                "bitrate": bitrate,
                "duration_seconds": len(audio_segment) / 1000,
            },
            duration_ms=duration_ms,
        )

    async def _get_info(self, audio: str, **kwargs) -> AudioResult:
        """Get audio file information.

        Args:
            audio: Path to audio file

        Returns:
            AudioResult with audio info
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub required: pip install pydub")

        start_time = time.time()

        audio_segment = AudioSegment.from_file(audio)

        info = {
            "duration_seconds": len(audio_segment) / 1000,
            "duration_ms": len(audio_segment),
            "channels": audio_segment.channels,
            "sample_width": audio_segment.sample_width,
            "frame_rate": audio_segment.frame_rate,
            "frame_width": audio_segment.frame_width,
            "rms": audio_segment.rms,
            "dBFS": audio_segment.dBFS,
            "max_dBFS": audio_segment.max_dBFS,
            "file_size_bytes": Path(audio).stat().st_size,
            "format": Path(audio).suffix[1:],
        }

        duration_ms = (time.time() - start_time) * 1000
        return AudioResult(
            success=True,
            operation="info",
            data=info,
            duration_ms=duration_ms,
        )

    async def _trim(
        self,
        audio: str,
        start_ms: int = 0,
        end_ms: int | None = None,
        output_path: str | None = None,
        **kwargs,
    ) -> AudioResult:
        """Trim audio to specified range.

        Args:
            audio: Path to audio file
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds (None = end of file)
            output_path: Output file path

        Returns:
            AudioResult with trimmed audio
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub required: pip install pydub")

        start_time = time.time()

        audio_segment = AudioSegment.from_file(audio)
        original_duration = len(audio_segment)

        if end_ms is None:
            end_ms = len(audio_segment)

        trimmed = audio_segment[start_ms:end_ms]

        format = Path(audio).suffix[1:] or "mp3"
        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"trimmed_{int(time.time())}.{format}")

        trimmed.export(output_path, format=format)

        audio_data = Path(output_path).read_bytes()
        audio_base64 = base64.b64encode(audio_data).decode()

        duration_ms = (time.time() - start_time) * 1000
        return AudioResult(
            success=True,
            operation="trim",
            audio_path=output_path,
            audio_base64=audio_base64,
            data={
                "original_duration_ms": original_duration,
                "trimmed_duration_ms": len(trimmed),
                "start_ms": start_ms,
                "end_ms": end_ms,
            },
            duration_ms=duration_ms,
        )

    async def _merge(
        self,
        audio_files: list[str],
        output_path: str | None = None,
        crossfade_ms: int = 0,
        **kwargs,
    ) -> AudioResult:
        """Merge multiple audio files.

        Args:
            audio_files: List of audio file paths
            output_path: Output file path
            crossfade_ms: Crossfade duration between clips

        Returns:
            AudioResult with merged audio
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub required: pip install pydub")

        if not audio_files:
            raise ValueError("No audio files provided")

        start_time = time.time()

        # Load and merge
        merged = AudioSegment.from_file(audio_files[0])
        for audio_file in audio_files[1:]:
            segment = AudioSegment.from_file(audio_file)
            if crossfade_ms > 0:
                merged = merged.append(segment, crossfade=crossfade_ms)
            else:
                merged = merged + segment

        format = Path(audio_files[0]).suffix[1:] or "mp3"
        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"merged_{int(time.time())}.{format}")

        merged.export(output_path, format=format)

        audio_data = Path(output_path).read_bytes()
        audio_base64 = base64.b64encode(audio_data).decode()

        duration_ms = (time.time() - start_time) * 1000
        return AudioResult(
            success=True,
            operation="merge",
            audio_path=output_path,
            audio_base64=audio_base64,
            data={
                "input_files": len(audio_files),
                "total_duration_ms": len(merged),
                "crossfade_ms": crossfade_ms,
            },
            duration_ms=duration_ms,
        )

    async def _adjust_volume(
        self,
        audio: str,
        change_db: float,
        output_path: str | None = None,
        **kwargs,
    ) -> AudioResult:
        """Adjust audio volume.

        Args:
            audio: Path to audio file
            change_db: Volume change in dB (positive = louder, negative = quieter)
            output_path: Output file path

        Returns:
            AudioResult with adjusted audio
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub required: pip install pydub")

        start_time = time.time()

        audio_segment = AudioSegment.from_file(audio)
        adjusted = audio_segment + change_db

        format = Path(audio).suffix[1:] or "mp3"
        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"volume_{int(time.time())}.{format}")

        adjusted.export(output_path, format=format)

        audio_data = Path(output_path).read_bytes()
        audio_base64 = base64.b64encode(audio_data).decode()

        duration_ms = (time.time() - start_time) * 1000
        return AudioResult(
            success=True,
            operation="volume",
            audio_path=output_path,
            audio_base64=audio_base64,
            data={
                "change_db": change_db,
                "original_dBFS": audio_segment.dBFS,
                "new_dBFS": adjusted.dBFS,
            },
            duration_ms=duration_ms,
        )

    async def _adjust_speed(
        self,
        audio: str,
        speed: float = 1.0,
        output_path: str | None = None,
        **kwargs,
    ) -> AudioResult:
        """Adjust audio playback speed.

        Args:
            audio: Path to audio file
            speed: Speed multiplier (0.5 = half speed, 2.0 = double speed)
            output_path: Output file path

        Returns:
            AudioResult with speed-adjusted audio
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub required: pip install pydub")

        start_time = time.time()

        audio_segment = AudioSegment.from_file(audio)
        original_duration = len(audio_segment)

        # Change speed by adjusting frame rate
        new_frame_rate = int(audio_segment.frame_rate * speed)
        adjusted = audio_segment._spawn(
            audio_segment.raw_data, overrides={"frame_rate": new_frame_rate}
        )
        # Convert back to original frame rate
        adjusted = adjusted.set_frame_rate(audio_segment.frame_rate)

        format = Path(audio).suffix[1:] or "mp3"
        if not output_path and self._temp_dir:
            output_path = str(self._temp_dir / f"speed_{int(time.time())}.{format}")

        adjusted.export(output_path, format=format)

        audio_data = Path(output_path).read_bytes()
        audio_base64 = base64.b64encode(audio_data).decode()

        duration_ms = (time.time() - start_time) * 1000
        return AudioResult(
            success=True,
            operation="speed",
            audio_path=output_path,
            audio_base64=audio_base64,
            data={
                "speed": speed,
                "original_duration_ms": original_duration,
                "new_duration_ms": len(adjusted),
            },
            duration_ms=duration_ms,
        )

    # Convenience methods
    async def transcribe(self, audio: str, **kwargs) -> CapabilityResult:
        """Transcribe audio to text."""
        return await self.execute(action="transcribe", audio=audio, **kwargs)

    async def speak(self, text: str, **kwargs) -> CapabilityResult:
        """Generate speech from text."""
        return await self.execute(action="speak", text=text, **kwargs)

    async def convert(self, audio: str, format: str = "mp3", **kwargs) -> CapabilityResult:
        """Convert audio format."""
        return await self.execute(action="convert", audio=audio, format=format, **kwargs)

    async def info(self, audio: str) -> CapabilityResult:
        """Get audio file information."""
        return await self.execute(action="info", audio=audio)

    async def trim(self, audio: str, start_ms: int = 0, end_ms: int = None, **kwargs) -> CapabilityResult:
        """Trim audio to specified range."""
        return await self.execute(action="trim", audio=audio, start_ms=start_ms, end_ms=end_ms, **kwargs)

    async def merge(self, audio_files: list[str], **kwargs) -> CapabilityResult:
        """Merge multiple audio files."""
        return await self.execute(action="merge", audio_files=audio_files, **kwargs)
