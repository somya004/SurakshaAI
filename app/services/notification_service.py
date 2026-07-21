from dataclasses import dataclass


@dataclass
class NotificationResult:
    success: bool
    channel: str
    recipient_role: str
    message: str


async def send_notification(
    channel: str,
    recipient_role: str,
    title: str,
    message: str,
) -> NotificationResult:
    """
    Temporary notification adapter.

    It currently simulates notification delivery.
    Later, email, SMS and WhatsApp providers can be
    connected inside this function.
    """

    supported_channels = {
        "dashboard",
        "email",
        "sms",
        "whatsapp",
    }

    if channel not in supported_channels:
        return NotificationResult(
            success=False,
            channel=channel,
            recipient_role=recipient_role,
            message=f"Unsupported notification channel: {channel}",
        )

    print(
        "\n--- SURAKSHA AI ALERT ---"
        f"\nChannel: {channel}"
        f"\nRecipient role: {recipient_role}"
        f"\nTitle: {title}"
        f"\nMessage: {message}"
        "\n-------------------------\n"
    )

    return NotificationResult(
        success=True,
        channel=channel,
        recipient_role=recipient_role,
        message="Notification simulated successfully.",
    )