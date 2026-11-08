"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import pytest
from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, confirm_deferred_tool_requests

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel(call_tools=sorted(BASE_TOOLS))
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    assert len(_parts(result, ToolReturnPart)) == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


@pytest.mark.parametrize("approved", [True, False])
def test_learning_log_is_saved_only_after_approval(tmp_path, monkeypatch, approved):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    result = agent.run_sync("学習記録を保存して", model=model)

    assert isinstance(result.output, DeferredToolRequests)
    assert list(tmp_path.iterdir()) == []

    approval = result.output.approvals[0]
    deferred_results = result.output.build_results(
        approvals={approval.tool_call_id: approved}
    )
    agent.run_sync(
        message_history=result.all_messages(),
        deferred_tool_results=deferred_results,
        model=TestModel(call_tools=[]),
    )

    files = list(tmp_path.glob("*.md"))
    if approved:
        assert len(files) == 1
        assert files[0].read_text(encoding="utf-8") == "a\n"
    else:
        assert files == []


@pytest.mark.parametrize(("answer", "expected"), [("y", True), ("n", False)])
def test_cli_confirmation_maps_user_answer_to_approval(monkeypatch, answer, expected):
    call = ToolCallPart(
        tool_name="save_learning_log",
        args={"content": "学習記録"},
        tool_call_id="save-log-call",
    )
    requests = DeferredToolRequests(approvals=[call])
    monkeypatch.setattr("builtins.input", lambda _: answer)

    results = confirm_deferred_tool_requests(requests)

    assert results.approvals == {call.tool_call_id: expected}
