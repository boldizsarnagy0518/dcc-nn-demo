import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "office_rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def column_name(cell_ref):
    match = re.match(r"([A-Z]+)", cell_ref or "")
    return match.group(1) if match else ""


def row_number(cell_ref):
    match = re.search(r"(\d+)", cell_ref or "")
    return int(match.group(1)) if match else 0


def load_shared_strings(zf):
    try:
        raw = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(raw)
    values = []
    for item in root.findall("main:si", NS):
        parts = []
        for text in item.findall(".//main:t", NS):
            parts.append(text.text or "")
        values.append("".join(parts))
    return values


def workbook_sheet_path(zf, sheet_name):
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("rel:Relationship", NS)}

    for sheet in workbook.findall("main:sheets/main:sheet", NS):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(f"{{{NS['office_rel']}}}id")
            target = rel_map[rel_id]
            if target.startswith("/"):
                return target.lstrip("/")
            return f"xl/{target}" if not target.startswith("xl/") else target
    raise ValueError(f"Sheet not found: {sheet_name}")


def cell_value(cell, shared_strings):
    cell_type = cell.attrib.get("t")
    value_node = cell.find("main:v", NS)
    inline_node = cell.find("main:is/main:t", NS)

    if cell_type == "inlineStr" and inline_node is not None:
        return inline_node.text or ""
    if value_node is None:
        return ""
    raw = value_node.text or ""
    if cell_type == "s":
        return shared_strings[int(raw)] if raw else ""
    return raw


def read_prompt_rows(path, sheet_name="PROMPTS", prompt_col="A", category_col="B"):
    with zipfile.ZipFile(path) as zf:
        shared_strings = load_shared_strings(zf)
        sheet_path = workbook_sheet_path(zf, sheet_name)
        root = ET.fromstring(zf.read(sheet_path))

        rows = []
        for row in root.findall("main:sheetData/main:row", NS):
            values = {}
            for cell in row.findall("main:c", NS):
                col = column_name(cell.attrib.get("r", ""))
                values[col] = cell_value(cell, shared_strings)
            rows.append(values)

    prompts = []
    for row in rows[1:]:  # first row is header
        prompt = str(row.get(prompt_col, "")).strip()
        if not prompt:
            continue
        category = str(row.get(category_col, "")).strip() or "Excel prompt"
        prompts.append(
            {
                "id": f"p{len(prompts) + 1:02d}",
                "category": category,
                "prompt": prompt,
            }
        )
    return prompts


def main():
    parser = argparse.ArgumentParser(description="Import benchmark prompts from an Excel PROMPTS sheet.")
    parser.add_argument("excel_path", help="Path to .xlsx file, for example data/n8n_DCC.xlsx")
    parser.add_argument("--sheet", default="PROMPTS", help="Worksheet name. Default: PROMPTS")
    parser.add_argument("--prompt-col", default="A", help="Column containing prompts. Default: A")
    parser.add_argument("--category-col", default="B", help="Optional category column. Default: B")
    parser.add_argument("--output", default="data/prompts.json", help="Output JSON path. Default: data/prompts.json")
    args = parser.parse_args()

    prompts = read_prompt_rows(
        Path(args.excel_path),
        sheet_name=args.sheet,
        prompt_col=args.prompt_col.upper(),
        category_col=args.category_col.upper(),
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(prompts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Imported {len(prompts)} prompts from {args.excel_path} -> {output}")
    print("First prompt:", prompts[0]["prompt"] if prompts else "N/A")


if __name__ == "__main__":
    main()
