import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .backend_client import build_user_profile, run_chat_flow

logger = logging.getLogger(__name__)


def chatbot_home(request):
    """Render the static chatbot landing page."""
    return render(request, "chatbot/index.html")


def chatbot_chat(request):
    """Render the quick prompt selection chat screen (v2)."""
    return render(request, "chatbot/chat_v2.html")


def chatbot_conversation(request):
    """Render the full conversation interface (v3)."""
    return render(request, "chatbot/chat_v3.html")


@require_POST
def chatbot_ask(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    question = (payload.get("question") or "").strip()
    profile = payload.get("profile") or {}

    if not question:
        return JsonResponse({"error": "질문을 입력해주세요."}, status=400)

    user_profile = build_user_profile(profile)

    try:
        result = run_chat_flow(user_profile, question)
    except Exception as exc:  # pragma: no cover - runtime safeguard
        logger.exception("Chat flow execution failed")
        return JsonResponse({"error": "답변을 생성하는 중 문제가 발생했습니다."}, status=500)

    answer = (
        result.get("final_answer")
        or result.get("answer")
        or "답변을 생성하지 못했습니다. 다시 시도해 주세요."
    )

    response = {
        "answer": answer,
        "category": result.get("category"),
        "query_type": result.get("interview_query_type"),
        "metadata": {
            "classification_reason": result.get("classification_reason"),
            "evaluation": result.get("answer_eval", {}),
        },
    }
    return JsonResponse(response)
