import json
import os
from typing import List, Dict, Any

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextBoxHorizontal, LTTextLineHorizontal, LTChar


def extract_layout(pdf_path: str) -> Dict[str, Any]:
    pages_out: List[Dict[str, Any]] = []
    for page_layout in extract_pages(pdf_path):
        width = getattr(page_layout, 'width', None)
        height = getattr(page_layout, 'height', None)
        items = []
        for element in page_layout:
            if isinstance(element, (LTTextContainer, LTTextBoxHorizontal)):
                for line in element:
                    if isinstance(line, LTTextLineHorizontal):
                        text = line.get_text().rstrip('\n')
                        if not text.strip():
                            continue
                        # infer average font size and dominant font name for the line
                        sizes = [ch.size for ch in line if isinstance(ch, LTChar)]
                        avg_size = sum(sizes) / len(sizes) if sizes else None
                        fontnames = [getattr(ch, 'fontname', None) for ch in line if isinstance(ch, LTChar)]
                        dominant_font = None
                        if fontnames:
                            # pick the most frequent font name in the line
                            counts = {}
                            for fn in fontnames:
                                counts[fn] = counts.get(fn, 0) + 1
                            dominant_font = max(counts.items(), key=lambda kv: kv[1])[0]
                        items.append({
                            'type': 'text',
                            'text': text,
                            'x0': line.x0,
                            'y0': line.y0,
                            'x1': line.x1,
                            'y1': line.y1,
                            'size': avg_size,
                            'font': dominant_font,
                        })
        pages_out.append({'width': width, 'height': height, 'items': items})
    return {'pages': pages_out}


def main():
    pdf_path = os.path.join(os.getcwd(), 'exemplo-locação.pdf')
    if not os.path.exists(pdf_path):
        raise SystemExit(f'PDF not found: {pdf_path}')
    data = extract_layout(pdf_path)
    out_path = os.path.join(os.getcwd(), 'assets', 'layouts')
    os.makedirs(out_path, exist_ok=True)
    out_file = os.path.join(out_path, 'locacao_layout.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('Wrote', out_file)


if __name__ == '__main__':
    main()

