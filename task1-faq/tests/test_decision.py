"""Qaror qoidalari: javob, variantlar yoki "topilmadi". Model kerak emas."""
from app.search import Candidate, final_status

R_ANSWER, R_SUGGEST = 0.25, 0.002


def cand(answer_id, score, stage1):
    return Candidate(answer_id, score, "matn", "question", stage1)


def test_off_topic_gets_no_suggestions():
    cands = [cand(1, 0.004, 0.58), cand(2, 0.003, 0.57), cand(3, 0.002, 0.55)]
    assert final_status("Bu foydalimi yoki foydali emasmi", cands, False, R_ANSWER, R_SUGGEST) == ("not_found", "off_topic")


def test_related_topic_keeps_suggestions():
    cands = [cand(1, 0.02, 0.70), cand(2, 0.01, 0.65), cand(3, 0.005, 0.62)]
    assert final_status("Chet elda tug'ilgan bolani qanday ro'yxatdan o'tkazaman", cands, False, R_ANSWER, R_SUGGEST)[0] == "unsure"


def test_confident_answer_is_not_touched():
    cands = [cand(1, 0.62, 0.598), cand(2, 0.01, 0.55)]                # reranker ishonchli, 1-bosqich past
    assert final_status("Uy-joy subsidiyasini olish uchun qayerga borish kerak", cands, False, R_ANSWER, R_SUGGEST)[0] == "answered"
