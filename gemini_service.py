"""
Gemini AI service for generating analytics and answering questions.
"""
import logging
from typing import List, Dict
from google import genai
import os

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    def _format_messages_for_context(self, messages: List[Dict]) -> str:
        """Format messages into a readable context string."""
        if not messages:
            return "No messages available."
        
        formatted = []
        for msg in messages:
            timestamp = msg['created_at'].strftime('%Y-%m-%d %H:%M')
            user = msg['user_name'] or msg['user_id']
            text = msg['message_text']
            formatted.append(f"[{timestamp}] {user}: {text}")
        
        return "\n".join(formatted)

    def _detect_language(self, messages: List[Dict]) -> str:
        """Detect the primary language used in messages."""
        if not messages:
            return "English"
        
        # Sample last 50 messages to detect language
        sample_messages = messages[-50:] if len(messages) > 50 else messages
        sample_text = " ".join([msg['message_text'] for msg in sample_messages])
        
        # Simple heuristic: check for Cyrillic characters (Russian, Ukrainian, etc.)
        cyrillic_count = sum(1 for c in sample_text if '\u0400' <= c <= '\u04FF')
        total_letters = sum(1 for c in sample_text if c.isalpha())
        
        if total_letters > 0 and (cyrillic_count / total_letters) > 0.3:
            return "Russian"  # or the language of the messages
        
        # Could add more language detection here
        return "English"
    
    def _chunk_messages(self, messages: List[Dict], max_chars: int = 30000) -> List[str]:
        """Split messages into chunks to avoid token limits."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for msg in messages:
            msg_str = f"[{msg['created_at']}] {msg['user_name']}: {msg['message_text']}\n"
            msg_length = len(msg_str)
            
            if current_length + msg_length > max_chars and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(msg_str)
            current_length += msg_length
        
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks

    async def generate_daily_report(self, messages: List[Dict]) -> str:
        """
        Generate a comprehensive daily analytics report.
        Returns markdown-formatted report with topics, stats, and insights.
        """
        if not messages:
            return "📊 **Daily Report**\n\nNo messages were recorded in the last 24 hours."
        
        # Detect language from messages
        language = self._detect_language(messages)
        logger.info(f"Detected language: {language}")
        
        context = self._format_messages_for_context(messages)
        
        # If context is too large, summarize in chunks
        if len(context) > 30000:
            chunks = self._chunk_messages(messages, max_chars=30000)
            logger.info(f"Large context detected, processing {len(chunks)} chunks")
            
            # Summarize each chunk first
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=f"Summarize the key topics and discussions from these messages:\n\n{chunk}"
                    )
                    chunk_summaries.append(response.text)
                except Exception as e:
                    logger.error(f"Error processing chunk {i}: {e}")
            
            context = "\n\n".join(chunk_summaries)
        
        prompt = f"""You are analyzing Telegram group chat messages from the last 24 hours. Generate a MAXIMALLY DETAILED professional business report.

Messages:
{context}

IMPORTANT: Respond in {language}. Analyze the language used in the messages and reply in THE SAME LANGUAGE.

Generate a COMPREHENSIVE, DETAILED BUSINESS REPORT in Markdown format. Include ALL significant information:

## 📊 DETAILED ACTIVITY STATISTICS
- Total message count (exact number)
- Number of active participants (full list)
- TOP-5 most active participants with exact message counts
- Peak activity hours (specific time ranges)
- Average message length (in words)
- Longest and shortest messages
- Activity distribution by hours (if possible)

## 🎯 COMPREHENSIVE TOPICS & PROJECTS ANALYSIS
- Group ALL messages by work topics/projects
- For EACH topic specify:
  * Message count
  * Key participants in discussion
  * Main points and conclusions
  * Status of discussion
- Highlight priority tasks with full details
- Note completed tasks and who completed them
- Incomplete tasks and reasons

## 👥 FULL PARTICIPANT ANALYSIS
- COMPLETE list of ALL participants with message counts (sorted descending)
- For each active participant:
  * Number of messages
  * Main topics they discussed
  * Their role (initiator, executor, commentator)
- New participants (if any)
- Inactive participants (who stayed silent)
- Activity time for each participant

## 📈 KEY DECISIONS AND RESULTS
- ALL decisions made with full descriptions
- ALL assigned tasks specifying:
  * Who assigned
  * Assigned to whom
  * Deadlines
  * Current status
- Deadlines and important dates
- Achieved results (detailed)
- All problems and their solutions (detailed)
- Open questions requiring resolution

## 💬 DETAILED COMMUNICATION ANALYSIS
- Communication style (formal/informal)
- Discussion tone (positive/negative/neutral)
- Team engagement level
- Response speed to messages
- Feedback quality
- Conflicts or disagreements (if any)

## 🔍 DEEP INSIGHTS AND PATTERNS
- Recurring themes or questions
- Discussion trends
- Participant activity patterns
- Communication effectiveness (what works, what doesn't)
- Process bottlenecks and issues
- Improvement opportunities

## ⚡ IMPORTANT MOMENTS & HIGHLIGHTS
- Critically important messages or decisions
- Urgent matters requiring attention
- Risks and warnings
- Opportunities not to be missed

## 📋 PLANS AND NEXT STEPS
- All scheduled meetings with details (time, participants, purpose)
- All upcoming tasks with priorities
- Important dates and events
- Specific recommendations for tomorrow
- Action items for each participant

## 📝 EXECUTIVE SUMMARY
- Main achievements of the day
- Key problems
- Key takeaways
- Overall project progress

Be MAXIMALLY detailed and specific! Extract ALL valuable information. Don't skip details. Use {language} for all text.

FORMATTING RULES:
- Use simple Markdown formatting only
- Use **bold** for headers and important text
- Use | for tables (keep tables simple)
- Avoid underscores in emphasis, use asterisks instead
- Keep formatting safe for Telegram parsing
- Maximum 4000 characters"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"❌ Failed to generate report: {str(e)}"

    async def answer_question(self, question: str, messages: List[Dict]) -> str:
        """
        Answer a user question based on message history context.
        """
        if not messages:
            return "I don't have any message history to answer your question."
        
        # Detect language from messages
        language = self._detect_language(messages)
        logger.info(f"Detected language for Q&A: {language}")
        
        context = self._format_messages_for_context(messages)
        
        # Handle large contexts
        if len(context) > 40000:
            # Use only recent messages for context
            context = self._format_messages_for_context(messages[-500:])
            context = f"[Showing last 500 messages]\n\n{context}"
        
        prompt = f"""You are a helpful assistant analyzing Telegram group chat history.

Chat History (last 14 days):
{context}

User Question: {question}

IMPORTANT: Analyze the language used in the chat history and the question. Respond in THE SAME LANGUAGE as the user's question and chat messages ({language}).

Provide a helpful, accurate answer based on the chat history above. If the question cannot be answered from the available context, say so politely. Keep your response concise and relevant. Use {language} for your entire response.

FORMATTING RULES:
- Use simple text formatting only
- Avoid complex Markdown syntax
- Use **bold** only for important words
- Don't use underscores, brackets, or special characters
- Keep formatting simple and safe for Telegram"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"❌ I encountered an error while processing your question: {str(e)}"
