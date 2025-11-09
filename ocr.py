import logging
import cv2

def fuzzy_match(ocr_text, options_list, config):
    equivalences = config.get('ocr_corrections', {}).get('character_equivalences', {})
    
    def get_substitution_cost(c1, c2):
        if c1 == c2:
            return 0
        if equivalences.get(c1) and c2 in equivalences.get(c1):
            return 0.1
        if equivalences.get(c2) and c1 in equivalences.get(c2):
            return 0.1
        return 1

    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + get_substitution_cost(c1, c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    ocr_text_lower = ocr_text.lower()
    
    best_match = None
    highest_similarity = 0

    for option in options_list:
        if option is None:
            continue
        option_lower = option.lower()
        distance = levenshtein_distance(ocr_text_lower, option_lower)
        max_len = max(len(ocr_text_lower), len(option_lower))
        if max_len == 0:
            similarity = 1.0
        else:
            similarity = 1.0 - (distance / max_len)

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = option
    
    if highest_similarity > 0.6:
        return best_match
    else:
        return None

def run_ocr_in_region(frame, x1, y1, x2, y2, ocr_reader, preprocess=False, allowlist=None, upscale=False):
    cropped_frame = frame[y1:y2, x1:x2]
    if cropped_frame.size == 0:
        logging.warning(f"Cannot OCR a region with zero size: {x1},{y1},{x2},{y2}")
        return ""

    processed_frame = cropped_frame
    if preprocess:
        gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
        processed_frame = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    frame_to_ocr = processed_frame
    if upscale:
        scale_factor = 2
        frame_to_ocr = cv2.resize(processed_frame, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    easyocr_params = {}
    if allowlist:
        easyocr_params['allowlist'] = allowlist
    
    result = ocr_reader.readtext(frame_to_ocr, **easyocr_params)
    text = ' '.join([item[1] for item in result])
    return text.strip()

def ocr_region(frame, region_name, ocr_regions, ocr_reader):
    x1, y1, x2, y2 = ocr_regions[region_name]
    preprocess = region_name in ['p1_team_select_text']
    return run_ocr_in_region(frame, x1, y1, x2, y2, ocr_reader, preprocess=preprocess)
