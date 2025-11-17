import json
import logging
import sys
from pathlib import Path
from threading import Lock
from typing import Any, Dict

from django.conf import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

try:
    from LangGraph.graph import create_graph_flow  # type: ignore
except Exception as exc:  # pragma: no cover - import guard
    logger.exception("Failed to import LangGraph.graph: {exc}")
    raise

_graph_lock = Lock()
_graph_app = None


def get_graph_app():
    global _graph_app
    with _graph_lock:
        if _graph_app is None:
            logger.info("Bootstrapping LangGraph flow")
            _graph_app = create_graph_flow()
    return _graph_app


def build_user_profile(profile: Dict[str, Any]) -> str:
    name = profile.get("name") or "알 수 없음"
    stage = profile.get("careerStage") or "미정"
    stage_type = profile.get("stageType") or "student"
    major = profile.get("major") or ("해당 없음" if stage_type != "student" else "미정")
    interests = profile.get("interests") or []
    if isinstance(interests, str):
        interests = [interests]

    interest_str = ", ".join(interests) if interests else "선택 없음"
    hints = []
    if stage_type == "student":
        hints.append("고등학생")
    else:
        hints.append("취업/면접 준비생")

    return (
        f"이름: {name} | 단계: {stage} ({', '.join(hints)}) | "
        f"전공 계열: {major} | 관심: {interest_str}"
    )


def run_chat_flow(user_profile: str, question: str) -> Dict[str, Any]:
    graph = get_graph_app()
    result = graph.invoke({"user": user_profile, "question": question})
    return result or {}
