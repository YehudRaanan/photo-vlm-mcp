from __future__ import annotations


def detail_instruction(detail: str) -> str:
    if detail == "brief":
        return "Be concise. Return only the most important observations."
    if detail == "exhaustive":
        return "Be exhaustive. Include small visible details and explicit uncertainty."
    return "Use moderate detail and include uncertainty where evidence is weak."


def analyze_photo_prompt(prompt: str | None, detail: str) -> str:
    base = prompt or (
        "Describe this photo in detail. Identify visible objects, scene context, text, "
        "condition, notable details, and uncertainty."
    )
    return f"{base}\n\n{detail_instruction(detail)}"


def photo_ocr_prompt(structured: bool, language: str | None) -> str:
    layout = "Preserve visible layout as markdown where possible." if structured else ""
    lang = f"The expected language hint is {language}." if language else ""
    return (
        "Transcribe all visible text exactly from this camera photo. Preserve reading order. "
        "Mark illegible or uncertain characters with [?]. Do not summarize the text. "
        f"{layout} {lang}"
    ).strip()


def inspect_scene_prompt(focus: str | None, include_uncertainty: bool) -> str:
    focus_text = f"Focus on: {focus}." if focus else "Inspect the whole photo."
    uncertainty = (
        "Include an uncertainties array for weak or ambiguous observations."
        if include_uncertainty
        else "Keep uncertainty notes minimal."
    )
    return (
        f"{focus_text}\n"
        "Return compact JSON with keys: summary, scene, objects, visible_text, "
        "risks_or_anomalies, uncertainties. For each object include type, label, "
        "attributes, condition, and approx_location. "
        f"{uncertainty}"
    )


def compare_photos_prompt(question: str | None, detail: str) -> str:
    ask = question or "Compare these two photos and list visible differences."
    return (
        f"{ask}\n\nReturn compact JSON with keys: summary, same_scene_or_subject, "
        f"differences, uncertainties. {detail_instruction(detail)}"
    )
