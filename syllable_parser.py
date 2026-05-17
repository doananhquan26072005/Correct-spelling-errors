import re
from pprint import pprint

def remove_tonemark(string: str):
    chars = [
        'aàảãáạ', 'ăằẳẵắặ', 'âầẩẫấậ',
        'eèẻẽéẹ', 'êềểễếệ', 'iìỉĩíị',
        'oòỏõóọ', 'ôồổỗốộ', 'ơờởỡớợ',
        'uùủũúụ', 'ưừửữứự', 'yỳỷỹýỵ',
        'AÀẢÃÁẠ', 'ĂẰẲẴẮẶ', 'ÂẦẨẪẤẬ',
        'EÈẺẼÉẸ', 'ÊỀỂỄẾỆ', 'IÌỈĨÍỊ',
        'OÒỎÕÓỌ', 'ÔỒỔỖỐỘ', 'ƠỜỞỠỚỢ',
        'UÙỦŨÚỤ', 'ƯỪỬỮỨỰ', 'YỲỶỸÝỴ',
    ]

    for c in chars:
        string = re.sub(rf"[{c}]", c[0], string)
    return string

def syllable_parser(syllable, verbose=False):
    """ Parse a Vietnamese syllable (accented or unaccented) """

    syllable = syllable.strip()
    pattern = "[aàảãáạăằẳẵắặâầẩẫấậeèẻẽéẹêềểễếệiìỉĩíịoòỏõóọôồổỗốộơờởỡớợuùủũúụưừửữứựyỳỷỹýỵ]"

    if re.search(rf"^([b-zđ]+)?{pattern}{{1,7}}([c-y]+)?$", syllable, re.I) is None:
        if verbose:
            print('Not look like a syllable')
        return False

    syllable = syllable.lower()

    # Ngoại lệ cơ bản
    if syllable == 'gịa':
        return ['gịa', '6', 'gi', '', 'ia', '', 'ia']
    if syllable == 'quốc':
        return ['quốc', '5', 'q', '', 'uô', 'c', 'uôc']
        
    # [CẬP NHẬT TONE 0]: Chữ 'quoc' thuần ASCII không dấu mang Tone 0
    if syllable == 'quoc':
        return ['quoc', '0', 'q', '', 'uo', 'c', 'uoc']

    tones = {
        '2': '[àằầèềìòồờùừỳ]',
        '3': '[ảẳẩẻểỉỏổởủửỷ]',
        '4': '[ãẵẫẽễĩõỗỡũữỹ]',
        '5': '[áắấéếíóốớúứý]',
        '6': '[ạặậẹệịọộợụựỵ]',
    }
    
    # [CẬP NHẬT TONE 0]: Khởi tạo mặc định là Tone 0 thay vì 1
    tone = '0'
    has_tone_mark = False

    # 1. Kiểm tra dấu thanh (2, 3, 4, 5, 6)
    for key, val in tones.items():
        if re.search(rf"{val}", syllable):
            tone = key
            has_tone_mark = True
            break
            
    # 2. [CẬP NHẬT TONE 0]: Phân biệt Tone 1 (Thanh ngang chuẩn) và Tone 0 (Không xác định/ASCII)
    if tone == '0':
        # Các ký tự này chứng tỏ người dùng CÓ sử dụng bộ gõ tiếng Việt để gõ thanh ngang
        vietnamese_specific_chars = r"[ăâêôơưđ]"
        if re.search(vietnamese_specific_chars, syllable):
            tone = '1'
        else:
            tone = '0' # Giữ nguyên là 0 để báo hiệu từ này cần được đưa vào mô hình dự đoán dấu

    syllable_ = remove_tonemark(syllable)

    sets = {
        'onset': ['b', 'c', 'ch', 'd', 'đ', 'g', 'gh', 'gi', 'h',
                'k', 'kh', 'l', 'm', 'n', 'ng', 'ngh', 'nh', 'p',
                'ph', 'qu', 'r', 's', 't', 'th', 'tr', 'v', 'x'],
        'coda': ['c', 'ch', 'i', 'm', 'n', 'ng', 'nh', 'o', 'p', 't', 'u', 'y']
    }

    onsets = ('|').join(sets['onset'])
    glides = '[uo]'
    nucleuses = '[aăâeêioôơuưy]|[iy]ê|ươ|[iyuư]a|[uô]ô|oo|[iy]e|uo'
    codas = ('|').join(sets['coda'])

    regex_pattern = re.compile(rf"\b({onsets})?({glides})?({nucleuses})({codas})?\b")
    s = regex_pattern.search(syllable_)

    if s:
        _onset = s[1] or ''
        _glide = s[2] or ''
        _nucleus = s[3]
        _coda = s[4] or ''

        # Q-
        if _onset == 'qu':
            _onset = 'q'
            _glide = 'u'
            if _nucleus == 'ô':
                return False

        # GI-
        if _onset == 'g' and _nucleus in ['i', 'ia', 'iê', 'ie']:
            _onset = 'gi'
            if _nucleus == 'ia':
                _nucleus = 'a'

        # -UA, -UÔ-
        if _glide == 'u' and _nucleus in ['a', 'ô', 'o'] and _onset != 'q':
            _glide = ''
            _nucleus = 'u' + _nucleus

        # -OO-
        if _glide == 'o' and _nucleus == 'o':
            _glide = ''
            _nucleus = 'oo'
        
        # -UI, -OI
        if _glide != '' and _nucleus == 'i':
            _coda = _nucleus
            _nucleus = _glide
            _glide = ''

        # Ẩn cảnh báo tone 5/6 nếu đây là một từ gõ thuần không dấu (Tone 0)
        if tone not in ['5', '6'] and _coda in ['c', 'ch', 'p', 't'] and verbose and has_tone_mark:
            print("Invalid tone mark")

        rhyme = _glide + _nucleus + _coda
        return [syllable, tone, _onset, _glide, _nucleus, _coda, rhyme]

    return False

# ----- Test thử sự khác biệt Tone 1 và Tone 0 -----
if __name__ == '__main__':
    print("--- NHÓM THIẾU DẤU / THUẦN ASCII (TONE 0) ---")
    print(syllable_parser("tuyen"))   # Tone 0
    print(syllable_parser("dao"))     # Tone 0
    print(syllable_parser("truong"))  # Tone 0
    print(syllable_parser("quoc"))    # Tone 0

    print("\n--- NHÓM THANH NGANG CÓ CHỦ ĐÍCH (TONE 1) ---")
    print(syllable_parser("tuyên"))   # Tone 1 (Nhờ chữ ê)
    print(syllable_parser("đao"))     # Tone 1 (Nhờ chữ đ)
    print(syllable_parser("trương"))  # Tone 1 (Nhờ chữ ư, ơ)