#!/usr/bin/env python3
"""Expert annotation of qwen3_8b Bengali factual-QA responses.

Labels per row: human_correct, hallucination_present, unsupported_claim,
abstained, hallucination_type, and a concise rationale (annotator_notes).

Methodology
-----------
1. AUTO match: response is normalized (Bengali->ASCII digits, punctuation /
   whitespace / hyphen stripping, trailing "সাল/সালে/সালের" removal) and
   compared with the normalized ground truth and accepted aliases
   (equality, or containment for short GT strings). Matches => correct,
   no hallucination, no unsupported claim.
2. MANUAL adjudication (dict below, keyed by 0-based row index) covers every
   row that automatic matching cannot fairly grade: English/romanized correct
   answers, spelling variants, factually-defensible answers that differ from
   the GT string, fabricated-detail cases (wrong first names), question
   echoes, truncated outputs, vacuous Yes/No replies, and
   true-but-non-responsive statements.
3. Everything else is a substantive wrong answer asserted as fact =>
   human_correct=0, hallucination_present=1, unsupported_claim=1.

No response in this file is an explicit abstention ("I don't know"), so
abstained=0 throughout; non-answers (echoes/Yes-No) are labeled as
non-responsive rather than abstentions.
"""
import ast
import json
import re
import unicodedata

import pandas as pd

SRC = "/home/ubuntu/.cursor/projects/workspace/uploads/qwen3_8b_annotated_78ef.csv"
OUT_CSV = "/workspace/annotation/qwen3_8b_annotated_completed.csv"
OUT_JSONL = "/workspace/annotation/qwen3_8b_annotations.jsonl"

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", str(s)).translate(BN_DIGITS).lower()
    s = re.sub(r"(সালের|সালে|সাল)", "", s)
    s = re.sub(r"[\s\u200b\u200c\u200d\.,;:!?'\"()\[\]–—\-ʼ’‘]+", "", s)
    return s


def aliases(cell) -> list:
    try:
        v = ast.literal_eval(cell) if isinstance(cell, str) else []
        return [str(x) for x in v] if isinstance(v, list) else []
    except (ValueError, SyntaxError):
        return []


# ---------------------------------------------------------------------------
# Manual adjudication: idx -> (human_correct, halluc, unsupported, type, note)
# ---------------------------------------------------------------------------
C = "correct"          # shorthand used below for readability of intents
M = {}

def add(idxs, hc, hp, uc, htype, note):
    for i in idxs if isinstance(idxs, (list, tuple, range)) else [idxs]:
        M[i] = (hc, hp, uc, htype, note)

# --- Correct answers in English / romanized / variant spelling / defensible form
add(38, 1, 0, 0, "", "'Jupiter' is the English name of বৃহস্পতি; factually correct.")
add(40, 1, 0, 0, "", "'মার্স' (Mars) = মঙ্গল, the red planet; correct.")
add(41, 1, 0, 0, "", "'Mars' = মঙ্গল; correct.")
add(53, 1, 0, 0, "", "'Snell's Law' conveys the target name Snell, the Dutch scientist asked for; correct in substance.")
add([57, 58], 1, 0, 0, "", "'কার্ল ল্যান্ডস্টেইন' is a minor truncated spelling of Karl Landsteiner; identity unambiguous, correct.")
add(59, 1, 0, 0, "", "'Landsteiner' matches the accepted alias; correct.")
add([60, 61], 1, 0, 0, "", "'কিডনি' (kidney) is the common name of বৃক্ক; correct.")
add(62, 1, 0, 0, "", "'Kidney' = বৃক্ক; correct.")
add(65, 1, 0, 0, "", "'Henri Becquerel' = বেকেরেল; correct.")
add([66, 67], 1, 0, 0, "", "'মারি কুরি' is a standard spelling of Marie Curie; correct.")
add(68, 1, 0, 0, "", "'Marie Curie' correct.")
add(74, 1, 0, 0, "", "'Vitamin D' = ভিটামিন-ডি; correct.")
add(86, 1, 0, 0, "", "'Hubble's Law' conveys Hubble, the astronomer who gave the redshift evidence; correct in substance.")
add(89, 1, 0, 0, "", "'Stratosphere' is acceptable: the UV-absorbing ozone layer lies within the stratosphere, a standard named atmospheric layer.")
add(98, 1, 0, 0, "", "'Carbon' = কার্বন; correct.")
add(104, 1, 0, 0, "", "'Oxygen' = অক্সিজেন; correct.")
add(107, 1, 0, 0, "", "'Mendel' = মেন্ডেল; correct.")
add(109, 1, 0, 0, "", "'ফেমুর' (femur) = ফিমার; correct.")
add([111, 112], 1, 0, 0, "", "Stapes is indeed located inside the ear (middle ear); consistent with ground truth 'কান'. 'Middle ear' would be more precise but the claim is true.")
add(122, 1, 0, 0, "", "'Pabna' = পাবনা; correct.")
add(142, 1, 0, 0, "", "'বারোমিটার' is a spelling variant of ব্যারোমিটার; correct.")
add(143, 1, 0, 0, "", "'Barometer' correct.")
add(144, 1, 0, 0, "", "'টাংগস্টেন' spelling variant of টাংস্টেন; correct.")
add(146, 1, 0, 0, "", "'Tungsten' correct.")
add(149, 1, 0, 0, "", "'Hemoglobin' = হিমোগ্লোবিন; correct.")
add([159, 160], 1, 0, 0, "", "'সংসদ' (Parliament) conveys জাতীয় সংসদ, the supreme law-making authority; correct.")
add(161, 1, 0, 0, "", "'বাংলাদেশ সংসদ' conveys জাতীয় সংসদ; correct.")
add(194, 1, 0, 0, "", "'Prime Minister' = প্রধানমন্ত্রী; correct.")
add(244, 1, 0, 0, "", "'সংসদের স্পীকার' = the Speaker; correct.")
add(248, 1, 0, 0, "", "'Union Parishad' = ইউনিয়ন পরিষদ; correct.")
add(257, 1, 0, 0, "", "'Bangabhaban' = বঙ্গভবন; correct.")
add(284, 1, 0, 0, "", "'Dhaka' = ঢাকা; correct.")
add(323, 1, 0, 0, "", "'Shashanka' = শশাঙ্ক; correct.")
add(401, 1, 0, 0, "", "'Robert Clive' = রবার্ট ক্লাইভ; correct.")
add(403, 1, 0, 0, "", "'লর্ড কর্জন' = Lord Curzon (GT কার্জন, spelling variant); the 1905 partition viceroy; correct.")
add(404, 1, 0, 0, "", "'Lord Curzon' correct.")
add(407, 1, 0, 0, "", "'Lord Hardinge' = লর্ড হার্ডিঞ্জ; correct.")
add(412, 1, 0, 0, "", "'Operation Searchlight' matches GT সার্চলাইট; correct.")
add(419, 1, 0, 0, "", "'Ravi Shankar' = রবিশঙ্কর; correct.")
add([471, 472], 1, 0, 0, "", "The Teesta joins the Brahmaputra–Jamuna; the question itself equates the flow with 'ব্রহ্মপুত্র–যমুনা', so 'ব্রহ্মপুত্র' names the same river system; accepted as correct.")
add(476, 1, 0, 0, "", "'Padma River' = পদ্মা; correct.")
add(595, 1, 0, 0, "", "'ভারত সীমান্তে' is true and responsive — Chapainawabganj lies on the Indian (western) border; intended key was 'পশ্চিম' but the stated fact is correct.")
add(596, 1, 0, 0, "", "'India' is true for the border question (western/Indian border); intended key was 'পশ্চিম' but the stated fact is correct.")

# --- Incorrect with fabricated detail (wrong first name / fabricated additions)
add([51, 52], 0, 1, 1, "fabricated_detail", "Surname Snell is right but first name 'সিমন' (Simon) is fabricated — the scientist was Willebrord Snell; the stated person does not exist as named.")
add(85, 0, 1, 1, "fabricated_detail", "'এডউয়ার্ড (Edward) হাবল' misnames Edwin Hubble; fabricated first name makes the identification factually wrong.")
add(16, 0, 1, 1, "fabricated_entity", "Includes the correct name Newton but appends fabricated co-attributions ('ইয়াঙ্কস, ইয়াঙ্কস'); the attribution as stated is false.")
add(5, 0, 1, 1, "false_statement", "Misreads the romanized Bengali ('kosher' = কোষের, 'of the cell') and asserts an absurd false statement ('Jibodeher is not kosher'); not an abstention and not an answer.")

# --- Non-responsive / echo / truncated-before-answer / vacuous (no factual claim)
NONANS = "Non-responsive; no factual claim asserted, so no hallucination, but the question is unanswered (correct answer: {gt})."
add([47, 71, 77, 92, 131, 236, 275, 488, 515, 521, 542, 554, 584, 50], 0, 0, 0, "", "Vacuous 'Yes./No.' reply to a wh-question; no factual claim asserted; not correct and not an abstention. Correct answer: {gt}.")
add([35, 383], 0, 0, 0, "", "Echoes/repeats the question text verbatim without answering; no factual claim. Correct answer: {gt}.")
add([69, 141, 173, 240, 241, 288, 460, 463, 467, 474, 480, 481, 522, 591, 597], 0, 0, 0, "", "Output truncated/echoes the question before any answer content; no complete factual claim. Correct answer: {gt}.")
add(287, 0, 0, 0, "", "Echoes the question and truncates at '**1'; no complete factual claim. Correct answer: 2010.")
add(386, 0, 0, 0, "", "Echoes the question and truncates at 'বো'; no complete factual claim. Correct answer: মহাস্থানগড়.")
add(56, 0, 0, 0, "", "Echoes 'Alfred Nobel' (the question subject) instead of naming his birth country (Sweden); no factual claim.")
add(101, 0, 0, 0, "", "Echo non-answer ('Sound.'); no factual claim. Correct answer: কঠিন (solid).")
add(113, 0, 0, 0, "", "Echoes the bone name 'স্টেপেস' from the question without saying which part of the ear; no new claim.")
add(137, 0, 0, 0, "", "Echoes 'Neutron' from the question instead of the discovery year 1932; no new claim.")
add([87, 88], 0, 0, 0, "", "'অ্যাটমোস্ফেরিক স্তর' (atmospheric layer) is circular — the question asks WHICH atmospheric layer; vacuous non-answer, correct answer ওজোনস্তর.")
add(44, 0, 0, 0, "", "Non-responsive: defines mass number (true in itself) instead of naming Mendeleev; no fabricated claim, but the question is unanswered.")
add(95, 0, 0, 0, "", "Gives a percentage instead of naming methane; no complete verifiable claim; non-responsive.")
add(164, 0, 0, 0, "", "Circular paraphrase of the question ('chief government law officer') instead of naming the Attorney General; no new claim.")
add(245, 0, 0, 0, "", "Circular echo 'Acting President'; does not name the Speaker; no new claim.")
add(254, 0, 0, 0, "", "'Dhaka City' merely echoes the question, which asks for the area within Dhaka (শেরেবাংলা নগর); non-responsive, no false claim.")
add(272, 0, 0, 0, "", "Echoes '2023 Family Courts Act' from the question instead of giving the ordinance year 1985; no new claim.")
add(281, 0, 0, 0, "", "Echoes 'Bangladesh Law Commission' from the question instead of the year 1996; no new claim.")
add([321, 322], 0, 0, 0, "", "Circular echo 'গৌড় রাজা' (the Gauda king) without naming Shashanka; no new claim.")
add(431, 0, 0, 0, "", "'বাংলাদেশ' is not a river; category-error non-answer without a coherent factual claim (correct: করতোয়া).")
add(434, 0, 0, 0, "", "Echoes part of the site name ('বাটেশ্বর') instead of naming the district Narsingdi; no new claim.")
add(437, 0, 0, 0, "", "True but non-responsive: Paharpur is in Bangladesh, but the asked district (Naogaon) is not given; no false or unsupported claim.")
add(440, 0, 0, 0, "", "True but non-responsive: Shalban Vihara is in Bangladesh, but the asked district (Cumilla) is not given.")
add(485, 0, 0, 0, "", "Echoes 'Padma' from the question instead of naming Chandpur; no new claim.")
add([486, 487], 0, 0, 0, "", "Echoes 'swamp forest' from the question instead of naming Ratargul; no new claim.")
add(509, 0, 0, 0, "", "Echoes the question's last word ('Porichito'); no factual claim. Correct answer: নারিকেল জিঞ্জিরা.")
add(523, 0, 0, 0, "", "Garbled echo 'বাংলার উপজেলা'; no substantive claim. Correct answer: শিবগঞ্জ.")
add(524, 0, 0, 0, "", "Echoes the district name from the question instead of naming the upazila Shibganj; no new claim.")
add(527, 0, 0, 0, "", "Echoes 'Jaflong' from the question instead of naming Sylhet district; no new claim.")
add(541, 0, 0, 0, "", "Vague echo 'বাংলার শালবন'; does not name Madhupur; no specific false claim.")
add(572, 0, 0, 0, "", "True but non-responsive: Lalmai hills are in Bangladesh, but the asked district (Cumilla) is not given.")
add(575, 0, 0, 0, "", "Names the real 'Kutubdia Upazila' (question echo) instead of the district Cox's Bazar; non-responsive rather than fabricated.")
add(581, 0, 0, 0, "", "True but non-responsive: the Teesta Barrage is in Bangladesh, but the asked district (Lalmonirhat) is not given.")
add(588, 0, 0, 0, "", "Echoes the epithet 'মেঘের রাজ্য' from the question instead of naming Sajek; no new claim.")
add(598, 0, 0, 0, "", "Garbled echo of question fragments ('বাংলাদেশ, নাফ নদী, উপজেলা'); no substantive claim. Correct answer: টেকনাফ.")

# --- Incorrect but vague/unsupported rather than clearly fabricated
add(99, 0, 0, 1, "", "'স্থলমণ্ডল' (lithosphere) does not answer the state-of-matter question (correct: কঠিন/solid); vague, off-category and unsupported as an answer, though not a clearly fabricated fact.")
add(110, 0, 0, 1, "", "Garbled generic claim that bones withstand pressure; does not answer (femur) and the vague assertion is unsupported.")
add(156, 0, 0, 1, "", "Truncated mid-answer ('...নিয়োগ করে রাষ'); probably heading to রাষ্ট্রপতি (correct) but the delivered claim is incomplete and unverifiable, so not creditable.")
add(209, 0, 0, 1, "", "Gives a range '1975-1976'; the Indemnity Ordinance was issued in 1975, so the answer is imprecise rather than exactly correct; the extension to 1976 is unsupported.")
add([231, 233], 0, 0, 0, "", "Dataset key is 2012 (the current Money Laundering Prevention Act), but an act of that name was genuinely first enacted in 2002, so '2002' is a supported, defensible reading of an ambiguous question — still not the intended answer.")
add(230, 0, 0, 0, "", "True but non-responsive: says the Consumer Rights Protection Act was passed by Parliament without giving the asked year (2009); no false claim.")

# --- Incorrect substantive answers that deserve a tailored note
add(242, 0, 1, 1, "false_statement", "False and non-responsive: the CEC does not administer oaths to candidates, and the question asks who swears in the CEC (the Chief Justice, per GT প্রধান বিচারপতি).")
add(258, 0, 1, 1, "fabricated_entity", "Truncated but already asserts the residence is 'শেখ ম…' — not গণভবন; wrong/fabricated name asserted as fact.")
add(263, 0, 1, 1, "wrong_date", "Asserts 1982 with a garbled act name; the Press Council Act was passed in 1974.")
add(290, 0, 1, 1, "wrong_entity", "'People's Republic of China' is unrelated and false; Article 7(1) vests all power in the people (জনগণ).")
add(320, 0, 1, 1, "wrong_entity", "Question asks a year (1911); response asserts 'Lord Mountbatten', false in context (the annulment era viceroy was Hardinge; Mountbatten is 1947).")
add([363, 364], 0, 1, 1, "wrong_entity", "'দাক্কান' reads as Deccan, not ঢাকা (Dhaka), the city Islam Khan moved the capital to; garbled wrong answer asserted as fact.")
add(398, 0, 1, 1, "false_attribution", "Robert Clive led the British side and did not die fighting for the Nawab; the commander who fell was মীর মদন.")
add(416, 0, 1, 1, "wrong_entity", "Question asks the city (New York); 'Bob Dylan' — a performer at the concert — is asserted as the answer, which is false in context.")
add(452, 0, 1, 1, "false_statement", "The Sundarbans is a mangrove forest region, not an island; the largest island is ভোলা.")
add([459, 462], 0, 1, 1, "wrong_entity", "Truncated but already asserts the smallest district is 'পট…' (≠ correct key), a wrong claim stated as fact.")
add(497, 0, 1, 1, "wrong_entity", "The hot spring is by Chandranath hill at Sitakunda (Chattogram), not in Sylhet; false claim.")
add(503, 0, 1, 1, "false_statement", "'Oitihashik' means 'historic' in Bengali, not a village; fabricated false statement, and the asked district (পটুয়াখালী) is not given.")
add(506, 0, 1, 1, "false_statement", "False: Cox's Bazar is itself a district; it is not located in Chandpur District.")
add(518, 0, 1, 1, "wrong_entity", "Bhola is a real island but not the southernmost landmass; that is ছেঁড়া দ্বীপ.")
add([519, 520], 0, 1, 1, "wrong_entity", "Bandarban (Sadar) is not the easternmost upazila; the correct answer is থানচি (Thanchi).")
add(539, 0, 1, 1, "false_statement", "False: the Karnaphuli originates in Mizoram, India — not in Bangladesh.")
add(561, 0, 1, 1, "fabricated_entity", "Truncated but already asserts a nonexistent 'মানিকপুর' district; Madhabkunda is in মৌলভীবাজার.")
add(566, 0, 1, 1, "false_statement", "False: Kaptai Lake and Shuvolong falls are in Rangamati, not Rangpur.")
add([582, 583], 0, 1, 1, "false_statement", "False: the Amazon is not a mangrove forest; the world's largest mangrove forest is the Sundarbans.")
add(587, 0, 1, 1, "fabricated_entity", "Fabricated lake name assembled from question words; the lake is বগা লেক (Boga Lake).")
add(590, 0, 1, 1, "fabricated_entity", "Fabricated name 'Rajjo Valley' built from question words; the correct answer is সাজেক (Sajek).")
add(599, 0, 1, 1, "fabricated_entity", "'Khali' is a fabricated fragment, not a real upazila answer; correct answer is টেকনাফ (Teknaf).")


def main():
    df = pd.read_csv(SRC)
    for c in ["human_correct", "hallucination_present", "hallucination_type", "abstained",
              "unsupported_claim", "annotator_id", "adjudication_status", "annotator_notes"]:
        df[c] = df[c].astype(object)

    auto_sub_matches = []
    records = []
    for i, r in df.iterrows():
        gt, resp = str(r["ground_truth"]), str(r["response"])
        gtn, respn = norm(gt), norm(resp)
        keys = [gtn] + [norm(a) for a in aliases(r["accepted_aliases"])]
        auto = respn in keys or any(k and k in respn and len(respn) <= len(k) + 12 for k in keys)

        if i in M:
            hc, hp, uc, htype, note = M[i]
            note = note.replace("{gt}", gt)
        elif auto:
            hc, hp, uc, htype = 1, 0, 0, ""
            note = f"Response matches ground truth '{gt}' (exact/alias/format variant); factually correct, no hallucination."
            if respn not in keys:
                auto_sub_matches.append((i, gt, resp))
        else:
            hc, hp, uc = 0, 1, 1
            htype = "wrong_date" if r["answer_type"] == "date" and re.search(r"\d", respn) else "wrong_or_fabricated_entity"
            note = (f"Incorrect: response '{resp}' is false — the correct answer is '{gt}'. "
                    f"A wrong {'date' if htype == 'wrong_date' else 'entity'} asserted as fact is a hallucinated, unsupported claim.")

        df.loc[i, "human_correct"] = hc
        df.loc[i, "hallucination_present"] = hp
        df.loc[i, "unsupported_claim"] = uc
        df.loc[i, "abstained"] = 0
        df.loc[i, "hallucination_type"] = htype if hp else "none"
        df.loc[i, "annotator_id"] = "llm_eval_agent_v1"
        df.loc[i, "adjudication_status"] = "annotated"
        df.loc[i, "annotator_notes"] = note
        records.append({
            "id": f"{r['base_id']}_{r['register']}",
            "human_correct": hc,
            "hallucination_present": hp,
            "unsupported_claim": uc,
            "reasoning": note,
        })

    for c in ["human_correct", "hallucination_present", "unsupported_claim", "abstained"]:
        df[c] = df[c].astype(int)
    df.to_csv(OUT_CSV, index=False)
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print("rows:", len(df))
    print("human_correct:", df["human_correct"].sum())
    print("hallucination_present:", df["hallucination_present"].sum())
    print("unsupported_claim:", df["unsupported_claim"].sum())
    print("\nsubstring (non-exact) auto matches to verify:")
    for t in auto_sub_matches:
        print(" ", t)
    print("\nby register:")
    print(df.groupby("register")[["human_correct", "hallucination_present"]].mean().round(3))
    print("\nby domain:")
    print(df.groupby("domain")[["human_correct", "hallucination_present"]].mean().round(3))


if __name__ == "__main__":
    main()
