"""Notification capability for MetaAgent.

Provides notification operations:
- Email (SMTP, SendGrid, SES)
- Slack (webhooks and API)
- Discord (webhooks)
- Microsoft Teams (webhooks)
- SMS (Twilio)
- Generic webhooks

Requires optional dependencies:
- aiosmtplib: For SMTP email
- httpx: For webhook calls
"""

import json
import os
import time
from enum import Enum
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)

# Optional imports
try:
    import aiosmtplib

    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False
    aiosmtplib = None  # type: ignore

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore

try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders

    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False


class NotificationChannel(str, Enum):
    """Notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationConfig(CapabilityConfig):
    """Configuration for notification capability."""

    # Email (SMTP) settings
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: str | None = Field(default=None, description="SMTP username")
    smtp_password: str | None = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    smtp_from_email: str | None = Field(default=None, description="Default from email")

    # SendGrid settings
    sendgrid_api_key: str | None = Field(default=None, description="SendGrid API key")

    # Slack settings
    slack_webhook_url: str | None = Field(default=None, description="Slack webhook URL")
    slack_token: str | None = Field(default=None, description="Slack Bot token")

    # Discord settings
    discord_webhook_url: str | None = Field(default=None, description="Discord webhook URL")

    # Teams settings
    teams_webhook_url: str | None = Field(default=None, description="Teams webhook URL")

    # Twilio settings
    twilio_account_sid: str | None = Field(default=None, description="Twilio Account SID")
    twilio_auth_token: str | None = Field(default=None, description="Twilio Auth Token")
    twilio_from_number: str | None = Field(default=None, description="Twilio phone number")

    # Request settings
    timeout: float = Field(default=30.0, description="Request timeout in seconds")


class NotificationResult:
    """Result of a notification operation."""

    def __init__(
        self,
        success: bool,
        channel: str,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        message_id: str | None = None,
        duration_ms: float = 0,
    ):
        self.success = success
        self.channel = channel
        self.data = data or {}
        self.error = error
        self.message_id = message_id
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "channel": self.channel,
            "duration_ms": self.duration_ms,
        }
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.message_id:
            result["message_id"] = self.message_id
        return result


class NotificationCapability(BaseCapability):
    """Notification capability for MetaAgent.

    Provides multi-channel notifications:
    - Email via SMTP or SendGrid
    - Slack messages via webhooks or API
    - Discord messages via webhooks
    - Microsoft Teams via webhooks
    - SMS via Twilio
    - Generic webhooks

    Example:
        >>> notif = NotificationCapability()
        >>> await notif.initialize()

        >>> # Send email
        >>> result = await notif.email(
        ...     to="user@example.com",
        ...     subject="Alert",
        ...     body="Something happened!"
        ... )

        >>> # Send Slack message
        >>> result = await notif.slack("Deployment completed!")

        >>> # Send to webhook
        >>> result = await notif.webhook(
        ...     url="https://example.com/webhook",
        ...     data={"event": "completed"}
        ... )
    """

    name = "notification"
    description = "Multi-channel notifications: email, Slack, Discord, Teams, SMS"

    def __init__(self, config: NotificationConfig | None = None):
        """Initialize notification capability."""
        super().__init__(config or NotificationConfig())
        self.config: NotificationConfig = self.config
        self._http_client: Any = None

    async def initialize(self) -> None:
        """Initialize notification capability."""
        if HTTPX_AVAILABLE:
            self._http_client = httpx.AsyncClient(timeout=self.config.timeout)
        await super().initialize()

    async def shutdown(self) -> None:
        """Cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute notification operation.

        Args:
            action: Notification channel (email, slack, discord, teams, sms, webhook)
            **kwargs: Channel-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "email")
        start_time = time.time()

        try:
            if action == "email":
                result = await self._send_email(**kwargs)
            elif action == "slack":
                result = await self._send_slack(**kwargs)
            elif action == "discord":
                result = await self._send_discord(**kwargs)
            elif action == "teams":
                result = await self._send_teams(**kwargs)
            elif action == "sms":
                result = await self._send_sms(**kwargs)
            elif action == "webhook":
                result = await self._send_webhook(**kwargs)
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

    async def _send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: bool = False,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        from_email: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
        provider: str = "smtp",
        **kwargs,
    ) -> NotificationResult:
        """Send email notification.

        Args:
            to: Recipient email(s)
            subject: Email subject
            body: Email body
            html: Whether body is HTML
            cc: CC recipients
            bcc: BCC recipients
            from_email: Sender email
            attachments: List of attachments [{filename, content, mime_type}]
            provider: Email provider (smtp, sendgrid)

        Returns:
            NotificationResult
        """
        start_time = time.time()
        to_list = [to] if isinstance(to, str) else to
        from_email = from_email or self.config.smtp_from_email or self.config.smtp_user

        if provider == "smtp":
            if not SMTP_AVAILABLE:
                raise RuntimeError("aiosmtplib required: pip install aiosmtplib")

            # Create message
            if attachments or html:
                msg = MIMEMultipart("alternative" if html else "mixed")
                if html:
                    msg.attach(MIMEText(body, "html"))
                else:
                    msg.attach(MIMEText(body, "plain"))

                # Add attachments
                for attachment in (attachments or []):
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment["content"])
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{attachment["filename"]}"',
                    )
                    msg.attach(part)
            else:
                msg = MIMEText(body, "plain")

            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = ", ".join(to_list)
            if cc:
                msg["Cc"] = ", ".join(cc)

            # Send via SMTP
            smtp_user = self.config.smtp_user or os.getenv("SMTP_USER")
            smtp_password = self.config.smtp_password or os.getenv("SMTP_PASSWORD")

            await aiosmtplib.send(
                msg,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                start_tls=self.config.smtp_use_tls,
                username=smtp_user,
                password=smtp_password,
            )

            duration_ms = (time.time() - start_time) * 1000
            return NotificationResult(
                success=True,
                channel="email",
                data={"to": to_list, "subject": subject, "provider": "smtp"},
                duration_ms=duration_ms,
            )

        elif provider == "sendgrid":
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx required for SendGrid")

            api_key = self.config.sendgrid_api_key or os.getenv("SENDGRID_API_KEY")
            if not api_key:
                raise RuntimeError("SendGrid API key not configured")

            payload = {
                "personalizations": [{"to": [{"email": e} for e in to_list]}],
                "from": {"email": from_email},
                "subject": subject,
                "content": [{"type": "text/html" if html else "text/plain", "value": body}],
            }

            if cc:
                payload["personalizations"][0]["cc"] = [{"email": e} for e in cc]
            if bcc:
                payload["personalizations"][0]["bcc"] = [{"email": e} for e in bcc]

            response = await self._http_client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code not in (200, 202):
                raise RuntimeError(f"SendGrid error: {response.text}")

            message_id = response.headers.get("X-Message-Id")

            duration_ms = (time.time() - start_time) * 1000
            return NotificationResult(
                success=True,
                channel="email",
                message_id=message_id,
                data={"to": to_list, "subject": subject, "provider": "sendgrid"},
                duration_ms=duration_ms,
            )

        else:
            raise ValueError(f"Unknown email provider: {provider}")

    async def _send_slack(
        self,
        message: str,
        channel: str | None = None,
        blocks: list[dict[str, Any]] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        webhook_url: str | None = None,
        use_api: bool = False,
        **kwargs,
    ) -> NotificationResult:
        """Send Slack notification.

        Args:
            message: Message text
            channel: Channel ID (for API mode)
            blocks: Slack Block Kit blocks
            attachments: Slack attachments
            webhook_url: Webhook URL (overrides config)
            use_api: Use Slack API instead of webhook

        Returns:
            NotificationResult
        """
        start_time = time.time()

        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx required: pip install httpx")

        if use_api:
            token = self.config.slack_token or os.getenv("SLACK_TOKEN")
            if not token:
                raise RuntimeError("Slack token not configured")

            payload = {"channel": channel, "text": message}
            if blocks:
                payload["blocks"] = blocks
            if attachments:
                payload["attachments"] = attachments

            response = await self._http_client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )

            data = response.json()
            if not data.get("ok"):
                raise RuntimeError(f"Slack API error: {data.get('error')}")

            duration_ms = (time.time() - start_time) * 1000
            return NotificationResult(
                success=True,
                channel="slack",
                message_id=data.get("ts"),
                data={"channel": channel, "method": "api"},
                duration_ms=duration_ms,
            )

        else:
            url = webhook_url or self.config.slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")
            if not url:
                raise RuntimeError("Slack webhook URL not configured")

            payload = {"text": message}
            if blocks:
                payload["blocks"] = blocks
            if attachments:
                payload["attachments"] = attachments

            response = await self._http_client.post(url, json=payload)

            if response.status_code != 200:
                raise RuntimeError(f"Slack webhook error: {response.text}")

            duration_ms = (time.time() - start_time) * 1000
            return NotificationResult(
                success=True,
                channel="slack",
                data={"method": "webhook"},
                duration_ms=duration_ms,
            )

    async def _send_discord(
        self,
        message: str,
        username: str | None = None,
        avatar_url: str | None = None,
        embeds: list[dict[str, Any]] | None = None,
        webhook_url: str | None = None,
        **kwargs,
    ) -> NotificationResult:
        """Send Discord notification.

        Args:
            message: Message content
            username: Override webhook username
            avatar_url: Override webhook avatar
            embeds: Discord embeds
            webhook_url: Webhook URL (overrides config)

        Returns:
            NotificationResult
        """
        start_time = time.time()

        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx required: pip install httpx")

        url = webhook_url or self.config.discord_webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not url:
            raise RuntimeError("Discord webhook URL not configured")

        payload = {"content": message}
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if embeds:
            payload["embeds"] = embeds

        response = await self._http_client.post(url, json=payload)

        if response.status_code not in (200, 204):
            raise RuntimeError(f"Discord webhook error: {response.text}")

        duration_ms = (time.time() - start_time) * 1000
        return NotificationResult(
            success=True,
            channel="discord",
            data={"username": username},
            duration_ms=duration_ms,
        )

    async def _send_teams(
        self,
        message: str,
        title: str | None = None,
        color: str = "0076D7",
        sections: list[dict[str, Any]] | None = None,
        webhook_url: str | None = None,
        **kwargs,
    ) -> NotificationResult:
        """Send Microsoft Teams notification.

        Args:
            message: Message text
            title: Card title
            color: Theme color (hex)
            sections: MessageCard sections
            webhook_url: Webhook URL (overrides config)

        Returns:
            NotificationResult
        """
        start_time = time.time()

        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx required: pip install httpx")

        url = webhook_url or self.config.teams_webhook_url or os.getenv("TEAMS_WEBHOOK_URL")
        if not url:
            raise RuntimeError("Teams webhook URL not configured")

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": title or message[:50],
            "sections": sections
            or [
                {
                    "activityTitle": title,
                    "text": message,
                }
            ],
        }

        response = await self._http_client.post(url, json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Teams webhook error: {response.text}")

        duration_ms = (time.time() - start_time) * 1000
        return NotificationResult(
            success=True,
            channel="teams",
            data={"title": title},
            duration_ms=duration_ms,
        )

    async def _send_sms(
        self,
        to: str,
        message: str,
        from_number: str | None = None,
        **kwargs,
    ) -> NotificationResult:
        """Send SMS via Twilio.

        Args:
            to: Recipient phone number
            message: SMS message
            from_number: Sender phone number

        Returns:
            NotificationResult
        """
        start_time = time.time()

        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx required: pip install httpx")

        account_sid = self.config.twilio_account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = self.config.twilio_auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        from_number = from_number or self.config.twilio_from_number or os.getenv("TWILIO_FROM_NUMBER")

        if not all([account_sid, auth_token, from_number]):
            raise RuntimeError("Twilio credentials not configured")

        response = await self._http_client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            auth=(account_sid, auth_token),
            data={"From": from_number, "To": to, "Body": message},
        )

        if response.status_code not in (200, 201):
            raise RuntimeError(f"Twilio error: {response.text}")

        data = response.json()

        duration_ms = (time.time() - start_time) * 1000
        return NotificationResult(
            success=True,
            channel="sms",
            message_id=data.get("sid"),
            data={"to": to, "status": data.get("status")},
            duration_ms=duration_ms,
        )

    async def _send_webhook(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        method: str = "POST",
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> NotificationResult:
        """Send generic webhook notification.

        Args:
            url: Webhook URL
            data: Payload data
            method: HTTP method (POST, PUT)
            headers: Additional headers

        Returns:
            NotificationResult
        """
        start_time = time.time()

        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx required: pip install httpx")

        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        if method.upper() == "POST":
            response = await self._http_client.post(
                url, headers=request_headers, json=data or {}
            )
        elif method.upper() == "PUT":
            response = await self._http_client.put(
                url, headers=request_headers, json=data or {}
            )
        else:
            raise ValueError(f"Unsupported method: {method}")

        duration_ms = (time.time() - start_time) * 1000
        return NotificationResult(
            success=True,
            channel="webhook",
            data={
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "response": response.text[:500] if response.text else None,
            },
            duration_ms=duration_ms,
        )

    # Convenience methods
    async def email(self, to: str, subject: str, body: str, **kwargs) -> CapabilityResult:
        """Send email notification."""
        return await self.execute(action="email", to=to, subject=subject, body=body, **kwargs)

    async def slack(self, message: str, **kwargs) -> CapabilityResult:
        """Send Slack notification."""
        return await self.execute(action="slack", message=message, **kwargs)

    async def discord(self, message: str, **kwargs) -> CapabilityResult:
        """Send Discord notification."""
        return await self.execute(action="discord", message=message, **kwargs)

    async def teams(self, message: str, **kwargs) -> CapabilityResult:
        """Send Teams notification."""
        return await self.execute(action="teams", message=message, **kwargs)

    async def sms(self, to: str, message: str, **kwargs) -> CapabilityResult:
        """Send SMS notification."""
        return await self.execute(action="sms", to=to, message=message, **kwargs)

    async def webhook(self, url: str, data: dict[str, Any] = None, **kwargs) -> CapabilityResult:
        """Send webhook notification."""
        return await self.execute(action="webhook", url=url, data=data, **kwargs)
