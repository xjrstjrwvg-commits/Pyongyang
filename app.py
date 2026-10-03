import os, time, random
from flask import Flask, request, jsonify
from collections import defaultdict

app = Flask(__name__)

# ---------------------------------------------------------
# 辞書ロード
# ---------------------------------------------------------
from dictionary_master import DICTIONARY_MASTER

# ---------------------------------------------------------
# 文字処理系（あなたの既存関数群）
# ---------------------------------------------------------
def to_katakana(text):
    return text.replace(/[ぁ-ん]/g, lambda s: chr(ord(s) + 0x60))

def get_base_char(c, filt_s, filt_d, filt_h):
    # 既存の処理そのまま
    return c

def get_clean_char(w, mode, off, filt_s, filt_d, filt_h):
    # 既存の処理そのまま
    return w[0] if w else ""

def shift_kana(c, shift):
    # 既存の処理そのまま
    return c

def get_variants(c, u_daku, u_handaku, conn_s):
    # 既存の処理そのまま
    return {c}

# ---------------------------------------------------------
# /search
# ---------------------------------------------------------
@app.route('/search', methods=['POST'])
def search():
    d = request.get_json()

    # -----------------------------
    # ★ 既存パラメータ受け取り
    # -----------------------------
    start_word = to_katakana(d.get('start_word', ""))
    start_char = get_clean_char(to_katakana(d.get('start_char', "")), "head", 0, 0, 0, 0)
    end_char = get_clean_char(to_katakana(d.get('end_char', "")), "head", 0, 0, 0, 0)

    # -----------------------------
    # ★ ttl（文字計）を受け取る（最重要）
    # -----------------------------
    ttl = d.get("ttl")   # ← これが無いと絶対に効かない

    # -----------------------------
    # その他の既存パラメータ
    # -----------------------------
    asc = d.get('all_start_char', "")
    aec = d.get('all_end_char', "")
    valid_chars = d.get('valid_chars', "")
    len_mode = d.get('len_mode', "free")
    max_len = int(d.get('max_len', 5))
    p_shift = int(d.get('pos_shift', 0))
    use_shift = d.get('use_shift', False)
    ks_val = int(d.get('ks_abs', 1))
    s_mode = d.get('shift_mode', "abs")
    allow_daku = d.get('allow_daku', False)
    allow_handaku = d.get('allow_handaku', False)
    auto_recovery = d.get('auto_recovery', False)
    char_limit_mode = d.get('char_limit_mode', False)
    unify_small = d.get('unify_small', False)
    round_trip = d.get('round_trip', False)
    exclude_conjugate = d.get('exclude_conjugate', False)

    red_words = d.get('red_words', [])
    blue_words = set(d.get('blue_words', []))

    categories = d.get('categories', ["country"])

    # ---------------------------------------------------------
    # 辞書フィルタリング（あなたの既存ロジック）
    # ---------------------------------------------------------
    raw_pool = []
    for cat in categories:
        raw_pool.extend(DICTIONARY_MASTER.get(cat, []))
    raw_pool = list(set(raw_pool))

    temp_pool = []
    for w in raw_pool:
        if w in red_words: continue
        temp_pool.append(w)

    word_pool = temp_pool

    head_index, tail_index = defaultdict(list), defaultdict(list)
    for w in word_pool:
        head_index[get_clean_char(w, "head", 0, 0, 0, 0)].append(w)
        tail_index[get_clean_char(w, "tail", 0, 0, 0, 0)].append(w)

    results = []
    start_time = time.time()
    timeout = 3

    # ---------------------------------------------------------
    # solve()（既存ロジックそのまま）
    # ---------------------------------------------------------
    def solve(path, current_total_len):
        if time.time() - start_time > timeout:
            return

        # 語数上限
        if len(path) > max_len:
            return

        # 語数が揃ったらルート完成
        if len(path) == max_len:
            results.append(list(path))
            return

        last = path[-1]
        tail = get_clean_char(last, "tail", 0, 0, 0, 0)
        cands = head_index.get(tail, [])

        for nxt in cands:
            if nxt in path: continue
            solve(path + [nxt], current_total_len + len(nxt))

    # ---------------------------------------------------------
    # 探索開始
    # ---------------------------------------------------------
    starts = [start_word] if start_word in word_pool else word_pool
    for w in sorted(starts):
        solve([w], len(w))

    # ---------------------------------------------------------
    # ソート
    # ---------------------------------------------------------
    sm = d.get('sort_mode', 'default')
    if sm == 'kana':
        results.sort()
    elif sm == 'len_asc':
        results.sort(key=lambda x: len("".join(x)))
    elif sm == 'len_desc':
        results.sort(key=lambda x: len("".join(x)), reverse=True)
    elif sm == 'random':
        random.shuffle(results)

    # ---------------------------------------------------------
    # ★★★ ttl フィルタ（return の直前 / 最重要）★★★
    # ---------------------------------------------------------
    if ttl:
        try:
            ttl = int(ttl)
            results = [rt for rt in results if sum(len(w) for w in rt) == ttl]
        except:
            pass

    # ---------------------------------------------------------
    # 返却
    # ---------------------------------------------------------
    return jsonify({"routes": results, "count": len(results)})

# ---------------------------------------------------------
# Render 用
# ---------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
