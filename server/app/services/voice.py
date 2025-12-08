def process_voice_command(command: str) -> str:
    """
    Process a voice command (for demo, just echo/paraphrase).
    Ready for future STT/command parsing integration.
    """
    if command.strip().lower().startswith("sell"):
        return f"Processing sale: {command[5:].strip()}"
    if command.strip().lower().startswith("report"):
        return f"Generating report: {command[7:].strip()}"
    return f"You said: {command} (voice processing ready)"
