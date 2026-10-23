import json
import re
from pathlib import Path
from typing import Dict, Any, List

class ChatHistoryParser:
    """Parses chat exports from ChatGPT, Claude, and Gemini to extract engineering skills,
    real-world project discussions, architectural decisions, and the user's authentic tone."""

    TECHNICAL_INDICATORS = [
        "code", "function", "class", "algorithm", "architecture", "database",
        "api", "system", "deploy", "server", "model", "cad", "circuit",
        "sensor", "embedded", "framework", "optimization", "debug", "pipeline",
        "docker", "kubernetes", "cloud", "aws", "azure", "gcp", "mechanical",
        "electrical", "civil", "structural", "analysis", "protocol", "git",
        "backend", "frontend", "iot", "firmware", "simulation", "design"
    ]

    def parse_chatgpt_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parses OpenAI's conversations.json export format."""
        insights = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            if isinstance(data, list):
                for conv in data:
                    title = conv.get("title", "")
                    mapping = conv.get("mapping", {})
                    user_messages = []
                    technical_score = 0

                    for node_id, node in mapping.items():
                        msg = node.get("message")
                        if not msg:
                            continue
                        author_role = msg.get("author", {}).get("role", "")
                        content = msg.get("content", {})
                        parts = content.get("parts", [])
                        text = " ".join([str(p) for p in parts if isinstance(p, str)])

                        if author_role == "user" and text.strip():
                            user_messages.append(text)
                            # Check technical density
                            words = set(re.findall(r"\b\w+\b", text.lower()))
                            matches = [w for w in words if w in self.TECHNICAL_INDICATORS]
                            technical_score += len(matches)

                    if technical_score >= 3 and user_messages:
                        insights.append({
                            "source": "ChatGPT",
                            "topic": title or "Technical Discussion",
                            "technical_score": technical_score,
                            "user_snippets": user_messages[:5],  # top excerpts
                            "summary": f"User explored: {title}. Discussed topics: {', '.join(user_messages[0].split()[:20])}..."
                        })
        except Exception as e:
            print(f"Error parsing ChatGPT export: {e}")
        return insights

    def parse_claude_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parses Claude conversation JSON exports."""
        insights = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            conversations = data if isinstance(data, list) else data.get("conversations", [])
            for conv in conversations:
                name = conv.get("name", conv.get("title", "Claude Conversation"))
                messages = conv.get("chat_messages", conv.get("messages", []))
                user_snippets = []
                technical_score = 0

                for msg in messages:
                    sender = msg.get("sender", msg.get("role", ""))
                    text = msg.get("text", msg.get("content", ""))
                    if isinstance(text, list):
                        text = " ".join([str(item) for item in text])
                    
                    if sender in ["human", "user"] and text.strip():
                        user_snippets.append(text)
                        words = set(re.findall(r"\b\w+\b", text.lower()))
                        matches = [w for w in words if w in self.TECHNICAL_INDICATORS]
                        technical_score += len(matches)

                if technical_score >= 2 and user_snippets:
                    insights.append({
                        "source": "Claude",
                        "topic": name,
                        "technical_score": technical_score,
                        "user_snippets": user_snippets[:5],
                        "summary": f"Claude discussion on {name}"
                    })
        except Exception as e:
            print(f"Error parsing Claude export: {e}")
        return insights

    def parse_gemini_or_text(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parses Gemini JSON or generic exported chat transcripts in TXT/MD/JSON."""
        insights = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Attempt JSON first
            if file_path.suffix.lower() == ".json":
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            title = item.get("title", "Gemini Conversation")
                            snippets = [str(item.get("content", ""))]
                            insights.append({
                                "source": "Gemini",
                                "topic": title,
                                "technical_score": 3,
                                "user_snippets": snippets,
                                "summary": f"Gemini export item: {title}"
                            })
                        return insights
                except Exception:
                    pass

            # Fallback to text parsing (blocks separated by user/assistant or newlines)
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 40]
            for p in paragraphs:
                words = set(re.findall(r"\b\w+\b", p.lower()))
                matches = [w for w in words if w in self.TECHNICAL_INDICATORS]
                if len(matches) >= 3:
                    insights.append({
                        "source": "Chat Log",
                        "topic": "Engineering Problem Solving",
                        "technical_score": len(matches),
                        "user_snippets": [p[:400]],
                        "summary": f"Discussion involving: {', '.join(list(matches)[:5])}"
                    })
        except Exception as e:
            print(f"Error parsing chat text: {e}")
        return insights

    def parse_any(self, file_path: Path) -> List[Dict[str, Any]]:
        name_lower = file_path.name.lower()
        if "conversations.json" in name_lower or "chatgpt" in name_lower:
            res = self.parse_chatgpt_json(file_path)
            if res:
                return res
        if "claude" in name_lower:
            res = self.parse_claude_json(file_path)
            if res:
                return res
        return self.parse_gemini_or_text(file_path)
