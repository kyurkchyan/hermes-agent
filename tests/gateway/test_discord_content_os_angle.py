"""Tests for Content OS Discord angle selection context binding."""

import sys
from pathlib import Path

_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)

from plugins.platforms.discord.adapter import DiscordAdapter  # noqa: E402
from gateway.config import PlatformConfig  # noqa: E402


PAGE_A = "11111111-1111-1111-1111-111111111111"
PAGE_B = "22222222-2222-2222-2222-222222222222"


def _artifact(page_id: str, title: str) -> str:
    compact = page_id.replace("-", "")
    return f"""Summary:
{title}

Post:
```text
Post body for {title}
```

Angles:
1. **First** — First angle. RAG used: Voice Bank because relevant.
2. **Second** — Second angle. RAG used: My Posts because relevant.
3. **Third** — Third angle for {title}. RAG used: My Comments because relevant.
4. **Fourth** — Fourth angle. RAG used: static voice references only.
5. **Fifth** — Fifth angle. RAG used: Voice Bank because relevant.

Reply with 1-5, click an angle button, or pick an angle and add what you want to highlight.
URL: https://www.linkedin.com/feed/update/urn:li:activity:{compact[:8]}/

Pick an angle:
URL: https://www.linkedin.com/feed/update/urn:li:activity:{compact[:8]}/
External Post URL: https://www.notion.so/{compact}
"""


def test_parse_content_os_angle_custom_id_is_post_scoped():
    assert DiscordAdapter._parse_content_os_angle_custom_id(
        f"contentos_angle:select:{PAGE_A}:3"
    ) == (PAGE_A, 3)
    assert DiscordAdapter._parse_content_os_angle_custom_id(
        f"contentos_angle:select:{PAGE_A}:6"
    ) is None
    assert DiscordAdapter._parse_content_os_angle_custom_id(
        f"contentos_comment:post:{PAGE_A}"
    ) is None


def test_recovers_matching_artifact_by_notion_page_not_thread_latest():
    texts = [_artifact(PAGE_A, "Post A"), _artifact(PAGE_B, "Post B")]

    recovered = DiscordAdapter._recover_content_os_angle_artifact_from_texts(texts, PAGE_A)

    assert "Post A" in recovered
    assert "Post B" not in recovered
    assert PAGE_A.replace("-", "") in recovered


def test_manual_numeric_reply_uses_nearest_angle_artifact_when_no_page_id():
    texts = [_artifact(PAGE_A, "Post A"), "some discussion", _artifact(PAGE_B, "Post B")]

    recovered = DiscordAdapter._recover_content_os_angle_artifact_from_texts(texts)

    assert "Post B" in recovered
    assert "Post A" not in recovered


def test_prompt_carries_post_scope_and_selected_angle_text():
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="test-token", extra={}))
    artifact = _artifact(PAGE_A, "Post A")

    prompt = adapter._build_content_os_angle_selection_prompt(
        selected_angle=3,
        notion_page_id=PAGE_A,
        artifact=artifact,
        source="Discord angle button",
    )

    assert "Source: Discord angle button" in prompt
    assert f"External Posts Notion page ID: {PAGE_A}" in prompt
    assert "Selected angle number: 3" in prompt
    assert "Third angle for Post A" in prompt
    assert "not merely to the Discord creator thread" in prompt


def test_extracts_compact_notion_page_id_from_artifact():
    compact = PAGE_A.replace("-", "")
    assert DiscordAdapter._extract_content_os_notion_page_id_from_artifact(_artifact(PAGE_A, "Post A")) == compact
