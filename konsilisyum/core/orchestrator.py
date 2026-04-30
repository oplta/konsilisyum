from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime

from konsilisyum.api.keypool import KeyPool
from konsilisyum.api.mistral import MistralClient
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.models import (
    Agent,
    AgentStatus,
    Message,
    Session,
    SessionStatus,
    SpeakerType,
    Summary,
    TopicMode,
)


SYSTEM_PROMPT_TEMPLATE = """Sen {name}'sin. Rolun: {role}.

Amac: {goal}
Kor noktan: {blind_spot} — Buna dikkat et, ama bunun icin ozur dileme.
Konuşma stilin: {style}
Tetikleyicin: {trigger}

Konsil Kurallari:
- 500 kelimeyi gecme.
- Kendi gorusunu savun ama digerlerini dinle.
- Tekrar yapmaktan kacin. Daha once soyledigin bir seyi tekrar soyleme.
- Diger ajanlara isimleriyle hitap et.
- Tartismaya yapici katki yap. Sadece sesini duyurmak icin konusma.
- Eger bir sey soylenecek yeni bir sey yoksa, "Pas" de.
- Turkce konus.

Senin kisisel notlarin:
{memory}"""

MEMORY_UPDATE_PROMPT = """Sen {name}'sin. Tartismanin su ana kadar olan bolumunu degerlendir.

Kendi notlarini guncelle. Sadece sana onemli gelen noktalari,
senin icin kritik olan anlasmazliklari ve kisisel izlenimlerini yaz.

Format:
- [ANAHTAR NOKTA] ...
- [ITIRAZ] ...
- [IZLENIM] ...

Mevcut notlarin:
{memory}

Son 5 tur:
{messages}

Guncellenmis notlarin:"""

SUMMARY_PROMPT = """Asagidaki tartismayi ozetle.

Konu: {topic}
Tur araligi: {turn_range}

Tartisma:
{messages}

Ozet:"""


@dataclass
class TurnResult:
    message: Message | None = None
    is_pas: bool = False
    error: str | None = None
    summary: Summary | None = None


class Orchestrator:
    def __init__(
        self,
        session: Session,
        memory: MemoryManager,
        api_client: MistralClient,
        key_pool: KeyPool,
        turn_delay: float = 2.0,
        max_auto_turns: int = 50,
    ):
        self.session = session
        self.memory = memory
        self.api_client = api_client
        self.key_pool = key_pool
        self.turn_delay = turn_delay
        self.max_auto_turns = max_auto_turns

        self._pending_reply_to: str | None = None
        self._user_message_pending: str | None = None

    def pause(self):
        self.session.status = SessionStatus.PAUSED

    def resume(self):
        self.session.status = SessionStatus.RUNNING

    def is_paused(self) -> bool:
        return self.session.status == SessionStatus.PAUSED

    def set_pending_reply(self, agent_name: str):
        self._pending_reply_to = agent_name

    def set_user_message(self, message: str):
        self._user_message_pending = message

    def select_speaker(self) -> Agent:
        candidates = self.session.active_agents
        if not candidates:
            raise RuntimeError("Konuşacak aktif ajan yok")

        scores: dict[str, float] = {}
        for agent in candidates:
            score = 0.0

            if self._pending_reply_to and agent.name == self._pending_reply_to:
                score += 5.0

            if self._user_message_pending:
                score += 1.0

            turns_silent = self.session.current_turn - agent.last_turn
            score += min(turns_silent * 0.5, 2.0)

            if self.session.messages:
                last_speaker = None
                for m in reversed(self.session.messages):
                    if m.speaker_type == SpeakerType.AGENT:
                        last_speaker = m.speaker
                        break
                if last_speaker == agent.name:
                    score -= 3.0

            score += random.uniform(0, 0.5)

            scores[agent.id] = score

        winner_id = max(scores, key=scores.get)
        self._pending_reply_to = None
        return next(a for a in candidates if a.id == winner_id)

    def _build_system_prompt(self, agent: Agent) -> str:
        memory_text = self.memory.get_agent_memory(agent.id)
        return SYSTEM_PROMPT_TEMPLATE.format(
            name=agent.name,
            role=agent.role,
            goal=agent.goal,
            blind_spot=agent.blind_spot,
            style=agent.style,
            trigger=agent.trigger,
            memory=memory_text,
        )

    def _build_user_prompt(self, agent: Agent) -> str:
        context = self.memory.build_context_window()

        directive_parts: list[str] = []
        topic_text = self.session.current_topic.content if self.session.current_topic else "Serbest tartisma"
        directive_parts.append(f"Konu: {topic_text}")

        if self._user_message_pending:
            directive_parts.append(
                f"Kullanici bir mesaj birakti: \"{self._user_message_pending}\""
            )
            directive_parts.append("Buna tepki ver.")
            self._user_message_pending = None

        if self._pending_reply_to:
            directive_parts.append(f"{self._pending_reply_to} sana direkt sordu. Cevap ver.")

        turns_silent = self.session.current_turn - agent.last_turn
        if turns_silent > 3:
            directive_parts.append("Uzun suredir konusmadın. Gorusunu belirt.")

        if not self.session.messages:
            directive_parts.append("Bu tartismanin ilk turu. Perspektifini ortaya koy.")

        directive = "\n".join(directive_parts)
        return f"{context}\n\n---\n{directive}"

    async def execute_turn(self) -> TurnResult:
        if self.session.auto_turns_since_user >= self.max_auto_turns:
            self.pause()
            return TurnResult(error="max_auto_turns")

        agent = self.select_speaker()

        system_prompt = self._build_system_prompt(agent)
        user_prompt = self._build_user_prompt(agent)

        try:
            result = await self.api_client.complete_with_retry(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                get_key=lambda: self.key_pool.get_raw_key(agent),
            )
        except Exception as e:
            self.pause()
            # Mask any secrets that might be in the exception message
            error_msg = self.key_pool.mask_secrets(str(e))
            return TurnResult(error=error_msg)

        content = result.content

        is_pas = content.strip().lower() == "pas"
        if is_pas:
            agent.last_turn = self.session.current_turn
            return TurnResult(message=None, is_pas=True)

        if len(content.split()) > 500:
            content = " ".join(content.split()[:500]) + " [...kesildi]"

        topic_text = self.session.current_topic.content if self.session.current_topic else ""
        msg = Message(
            turn=self.session.current_turn,
            speaker=agent.name,
            content=content,
            speaker_type=SpeakerType.AGENT,
            topic=topic_text,
            metadata={
                "tokens_in": result.tokens_in,
                "tokens_out": result.tokens_out,
                "model": result.model,
            },
        )

        self.memory.add_message(msg)
        self.session.messages.append(msg)

        agent.turn_count += 1
        agent.last_turn = self.session.current_turn

        self.session.current_turn += 1
        self.session.auto_turns_since_user += 1

        await asyncio.sleep(self.turn_delay)

        if self.memory.should_summarize(self.session.current_turn):
            summary = await self._generate_summary()
            if summary:
                return TurnResult(message=msg, summary=summary)

        if self.memory.should_update_memory(self.session.current_turn):
            await self._update_agent_memories()

        return TurnResult(message=msg)

    async def _generate_summary(self) -> Summary | None:
        last_turn = self.summaries[-1].turn_range[1] if self.summaries else 0
        messages = self.memory.get_messages_since(last_turn)
        if not messages:
            return None

        messages_text = "\n".join(
            f"[Tur {m.turn}] {m.speaker}: {m.content}" for m in messages
        )
        topic = self.session.current_topic.content if self.session.current_topic else ""
        prompt = SUMMARY_PROMPT.format(
            topic=topic,
            turn_range=f"{last_turn + 1}-{self.session.current_turn}",
            messages=messages_text,
        )

        try:
            result = await self.api_client.complete_with_retry(
                system_prompt="Sen bir tartisma ozetleyicisisin. Turkce ozetle.",
                user_prompt=prompt,
                get_key=lambda: self.key_pool.get_raw_key(),
            )
        except Exception:
            return None

        summary = Summary(
            content=result.content,
            turn_range=(last_turn + 1, self.session.current_turn),
        )
        self.memory.add_summary(summary)
        return summary

    async def _update_agent_memories(self):
        """
        Guncelleme islemlerini paralel yaparak zaman kazanıyoruz.
        O(N_ajan * gecikme) yerine O(gecikme) sürede tamamlanıyor.
        """
        async def update_single_agent(agent: Agent):
            current_memory = self.memory.get_agent_memory(agent.id)
            recent = self.memory.history[-5:]
            messages_text = "\n".join(
                f"[Tur {m.turn}] {m.speaker}: {m.content}" for m in recent if not m.is_summary
            )

            prompt = MEMORY_UPDATE_PROMPT.format(
                name=agent.name,
                memory=current_memory,
                messages=messages_text,
            )

            try:
                result = await self.api_client.complete_with_retry(
                    system_prompt="Sen bir hafiza asistanisin. Notlari guncelle.",
                    user_prompt=prompt,
                    get_key=lambda: self.key_pool.get_raw_key(agent),
                )
                self.memory.update_agent_memory(agent.id, result.content)
            except Exception:
                pass

        tasks = [update_single_agent(agent) for agent in self.session.active_agents]
        if tasks:
            await asyncio.gather(*tasks)

    @property
    def summaries(self) -> list[Summary]:
        return self.memory.summaries
