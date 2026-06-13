import asyncio
import json
import sys

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from konsilisyum.core.models import SessionStatus
from konsilisyum.web.routes import get_bootstrapper

ws_router = APIRouter()


@ws_router.websocket("/ws/session/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str):
    bootstrapper = get_bootstrapper(session_id)
    if not bootstrapper:
        from konsilisyum.web.routes import _register_session
        bootstrapper = _register_session(session_id)
    if not bootstrapper:
        await websocket.close(code=4004, reason="Oturum bulunamadi")
        return

    await websocket.accept()

    assert bootstrapper.session is not None
    assert bootstrapper.orchestrator is not None
    assert bootstrapper.cmd_handler is not None
    assert bootstrapper.session_manager is not None

    session = bootstrapper.session
    orchestrator = bootstrapper.orchestrator
    cmd_handler = bootstrapper.cmd_handler
    session_manager = bootstrapper.session_manager

    await websocket.send_json({
        "type": "session_state",
        "agents": [
            {
                "name": a.name,
                "role": a.role,
                "goal": a.goal,
                "blind_spot": a.blind_spot,
                "style": a.style,
                "trigger": a.trigger,
                "color": a.color,
                "status": a.status.value,
                "turn_count": a.turn_count,
                "last_turn": a.last_turn,
            }
            for a in session.agents
        ],
        "topic": session.current_topic.content if session.current_topic else "",
        "turn": session.current_turn,
        "status": session.status.value,
    })

    council_task = asyncio.create_task(_run_council(websocket, orchestrator, session))
    listen_task = asyncio.create_task(_listen_commands(websocket, cmd_handler, orchestrator, session, session_manager))

    try:
        done, pending = await asyncio.wait(
            [council_task, listen_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except Exception:
        pass
    finally:
        session_manager.save(session)


async def _send_agent_message(websocket: WebSocket, result, session):
    agent = result.speaker or next((a for a in session.agents if a.name == result.message.speaker), None)
    mentioned = [a.name for a in session.agents if f"@{a.name}" in result.message.content]
    await websocket.send_json({
        "type": "agent_message",
        "turn": result.message.turn,
        "speaker": result.message.speaker,
        "role": agent.role if agent else "",
        "content": result.message.content,
        "color": agent.color if agent else "#ffffff",
        "reply_to": result.message.reply_to,
        "mentions": mentioned,
    })


async def _run_council(websocket: WebSocket, orchestrator, session):
    print(f"[WS] council_basladı session={session.id}", flush=True, file=sys.stderr)
    try:
        while session.status != SessionStatus.ENDED:
            if session.status == SessionStatus.PAUSED:
                await asyncio.sleep(0.5)
                continue

            if not session.active_agents:
                await websocket.send_json({"type": "error", "message": "Aktif ajan yok"})
                orchestrator.pause()
                continue

            try:
                next_agent = orchestrator.select_speaker()
                print(f"[WS] konuşmacı_seçildi agent={next_agent.name}", flush=True, file=sys.stderr)
                await websocket.send_json({"type": "agent_typing", "agent": next_agent.name})

                result = await orchestrator.execute_turn()
                print(f"[WS] tur tamamlandı agent={next_agent.name} error={result.error} is_pas={result.is_pas}", flush=True, file=sys.stderr)

                await websocket.send_json({"type": "agent_done_typing", "agent": next_agent.name})
            except Exception as e:
                print(f"[WS] tur_hatası: {e}", flush=True, file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                try:
                    await websocket.send_json({"type": "error", "message": str(e)})
                except Exception:
                    pass
                await asyncio.sleep(1)
                continue

            if result.error == "max_auto_turns":
                await websocket.send_json({"type": "status", "status": "paused", "turn": session.current_turn})
                orchestrator.pause()
                continue

            if result.error == "tekrar_tespit":
                continue

            if result.is_pas:
                continue

            if result.message:
                await _send_agent_message(websocket, result, session)

            if result.summary:
                await websocket.send_json({"type": "summary", "content": result.summary.content})

            await websocket.send_json({
                "type": "status",
                "status": session.status.value,
                "turn": session.current_turn,
            })

    except WebSocketDisconnect:
        pass
    except Exception:
        pass


async def _listen_commands(websocket: WebSocket, cmd_handler, orchestrator, session, session_manager):
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") != "command":
                continue

            cmd = msg.get("cmd")
            args = msg.get("args", {})

            if cmd == "quit":
                session.status = SessionStatus.ENDED
                session_manager.save(session)
                await websocket.send_json({"type": "status", "status": "ended", "turn": session.current_turn})
                break

            result = await cmd_handler.handle(cmd, args)

            if cmd in ("say", "ask", "think"):
                if session.status == SessionStatus.PAUSED:
                    orchestrator.resume()
                await websocket.send_json({"type": "command_result", "success": True, "message": "✓ Mesajınız iletildi. Ajanlar yanıt verecek."})

            if result.message:
                await websocket.send_json({"type": "command_result", "success": result.success, "message": result.message})

            if cmd in ("pause", "resume"):
                await websocket.send_json({"type": "status", "status": session.status.value, "turn": session.current_turn})

            if cmd == "topic" and session.current_topic:
                await websocket.send_json({"type": "topic_changed", "topic": session.current_topic.content})

            if cmd in ("spawn", "kick", "mute", "unmute"):
                await websocket.send_json({
                    "type": "agents_update",
                    "agents": [
                        {
                            "name": a.name,
                            "role": a.role,
                            "goal": a.goal,
                            "blind_spot": a.blind_spot,
                            "style": a.style,
                            "trigger": a.trigger,
                            "color": a.color,
                            "status": a.status.value,
                            "turn_count": a.turn_count,
                            "last_turn": a.last_turn,
                        }
                        for a in session.agents
                    ],
                })

            if cmd in ("summary", "decisions", "actions", "map") and result.message:
                await websocket.send_json({"type": "analysis", "kind": cmd, "content": result.message})

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
