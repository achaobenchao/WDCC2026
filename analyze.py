import re
from pathlib import Path


EVENT_TERMS = {
    "采访": "采访", "开幕": "开幕式", "闭幕": "闭幕式", "致辞": "嘉宾致辞",
    "演讲": "主题演讲", "论坛": "论坛", "座谈": "座谈", "会议": "会议",
    "参观": "参观", "调研": "调研", "签约": "签约", "揭牌": "揭牌",
    "启动": "启动仪式", "发布": "发布会", "展示": "项目展示", "颁奖": "颁奖",
    "合影": "合影", "交流": "现场交流", "互动": "嘉宾互动", "展览": "展览", "表演": "表演",
}
ROLE_TERMS = "董事长|总经理|主任|主席|教授|院长|书记|局长|部长|负责人|创始人|主持人|设计师|嘉宾|老师"
SURNAME = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳唐罗薛雷贺倪汤滕殷郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣邓郁单杭洪包左石崔吉龚程嵇邢裴陆荣翁荀羊甄曲封芮储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲台从鄂索咸籍赖卓蔺屠蒙池乔阴郁胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公"


def _unique(values):
    seen, out = set(), []
    for value in values:
        value = value.strip(" ，。；：:、\t\n")
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _time(seconds):
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def _clean_term(value):
    for marker in ("来自", "关于", "介绍", "选用", "两个", "一个是", "这次我在", "我在"):
        if marker in value:
            value = value.split(marker)[-1]
    return value.strip("的了一个两个这次相关作品展品里面内，。 ")


def fuse(file_info, ocr_data, transcript):
    ocr_obs = []
    for frame in ocr_data.get("frames", []):
        for line in frame.get("lines", []):
            ocr_obs.append((line["text"], frame["timestamp"], line.get("score")))
    ocr_texts = _unique([x[0] for x in ocr_obs])
    segments = transcript.get("segments", [])
    spoken = sum(len(s["text"]) for s in segments)
    speech_text = " ".join(s["text"] for s in segments)
    all_text = " ".join(ocr_texts + [speech_text])
    context = " ".join([file_info["filename"], file_info["relative_path"], all_text])

    persons = []
    person_seen = set()
    intro = re.compile(
        rf'(?:下面)?有请[：:，, ]*([{SURNAME}][\u4e00-\u9fff]{{1,2}})'
        rf'(?=先生|女士|老师|教授|主席|主任|董事长|总经理|院长|书记|局长|部长|上台|为我们|发表)'
        rf'|(?:采访对象|受访者|主持人)(?:是|为|叫|：|:)[：:，, ]*([{SURNAME}][\u4e00-\u9fff]{{1,2}})'
    )
    named_role = re.compile(rf'([{SURNAME}][\u4e00-\u9fff]{{1,2}})(?:先生|女士)?[ ，,：:]*(?:是|担任|任)?({ROLE_TERMS})')
    role_then_name = re.compile(rf'(?:我是|我叫)[^，。]{{0,14}}?({ROLE_TERMS})([{SURNAME}][\u4e00-\u9fff]{{1,2}})(?=$|[，。,. ])')
    invalid_name_endings = set("的在中式计")
    for segment in segments:
        for match in intro.finditer(segment["text"]):
            name = match.group(1) or match.group(2)
            if name not in person_seen:
                person_seen.add(name)
                role_match = re.search(ROLE_TERMS, segment["text"])
                persons.append({"name": name, "role": role_match.group(0) if role_match else "",
                                "first_seen": _time(segment["start"]), "time_ranges": [f'{_time(segment["start"])}-{_time(segment["end"])}'],
                                "related_events": [], "evidence": [f'语音明确介绍：{segment["text"]}'], "confidence": "高"})
        for match in named_role.finditer(segment["text"]):
            name, role = match.group(1), match.group(2)
            if name[-1] in invalid_name_endings or "设计" in name or "原创" in name:
                continue
            if name not in person_seen:
                person_seen.add(name)
                persons.append({"name": name, "role": role, "first_seen": _time(segment["start"]),
                                "time_ranges": [f'{_time(segment["start"])}-{_time(segment["end"])}'],
                                "related_events": [], "evidence": [f'语音姓名与身份：{segment["text"]}'], "confidence": "高"})
        for match in role_then_name.finditer(segment["text"]):
            role, name = match.group(1), match.group(2)
            if name not in person_seen:
                person_seen.add(name)
                persons.append({"name": name, "role": role, "first_seen": _time(segment["start"]),
                                "time_ranges": [f'{_time(segment["start"])}-{_time(segment["end"])}'],
                                "related_events": [], "evidence": [f'语音自我介绍：{segment["text"]}'], "confidence": "高"})
    for text, stamp, score in ocr_obs:
        match = re.fullmatch(rf'([{SURNAME}][\u4e00-\u9fff]{{1,3}})', text)
        if match and match.group(1) not in person_seen and match.group(1)[-1] not in invalid_name_endings and "设计" not in match.group(1):
            nearby_roles = [t for t, ts, _ in ocr_obs if abs(ts - stamp) < 1 and len(t) <= 24 and re.search(ROLE_TERMS, t)]
            if nearby_roles:
                name = match.group(1)
                person_seen.add(name)
                persons.append({"name": name, "role": nearby_roles[0], "first_seen": _time(stamp),
                                "time_ranges": [_time(stamp)], "related_events": [],
                                "evidence": [f'画面姓名条：{text}；{nearby_roles[0]}'], "confidence": "高" if (score or 0) >= .8 else "中"})

    if not persons and spoken >= 40 and "采访" in file_info["relative_path"]:
        folder_match = re.search(rf'(?:^|/)([{SURNAME}][\u4e00-\u9fff]{{1,3}})(?=生生不息|主题展|采访)', file_info["relative_path"])
        if folder_match:
            persons.append({"name": folder_match.group(1), "role": "", "first_seen": _time(segments[0]["start"]),
                            "time_ranges": [f'{_time(segments[0]["start"])}-{_time(segments[-1]["end"])}'],
                            "related_events": [], "evidence": ["素材文件夹命名：" + file_info["folder"],
                            "连续第一人称展览介绍语音"], "confidence": "中"})
            person_seen.add(folder_match.group(1))

    events = []
    for keyword, kind in EVENT_TERMS.items():
        hits = [s for s in segments if keyword in s["text"]]
        ocr_hits = [(t, ts) for t, ts, _ in ocr_obs if keyword in t]
        path_hit = keyword in file_info["relative_path"]
        if not (hits or ocr_hits or path_hit):
            continue
        if path_hit and not hits and not ocr_hits and spoken >= 40 and keyword != "采访" and "采访" in file_info["relative_path"]:
            continue
        starts = [s["start"] for s in hits] + [ts for _, ts in ocr_hits]
        ends = [s["end"] for s in hits] + [ts for _, ts in ocr_hits]
        if keyword == "采访" and path_hit and spoken >= 40 and not starts:
            starts = [segments[0]["start"]]; ends = [segments[-1]["end"]]
        start = min(starts) if starts else 0.0
        end = min(file_info.get("duration", 0), max(ends) + 8) if ends else file_info.get("duration", 0)
        evidence = []
        if hits: evidence.append("语音：" + hits[0]["text"])
        elif keyword == "采访" and path_hit and spoken >= 40: evidence.append("连续采访口述：" + speech_text[:100])
        if ocr_hits: evidence.append("画面文字：" + ocr_hits[0][0])
        if path_hit: evidence.append("文件/目录名：" + file_info["relative_path"])
        confidence = "高" if len(evidence) >= 3 else ("中" if len(evidence) >= 2 or hits or ocr_hits else "低")
        involved = [p["name"] for p in persons]
        events.append({"type": kind, "name": f'WDCC{kind}', "start": _time(start), "end": _time(end),
                       "persons": involved, "description": f'{"；".join(involved) + "参与" if involved else "素材记录"}WDCC相关{kind}内容。',
                       "evidence": evidence, "confidence": confidence})
    numeric_specs = [t for t in ocr_texts if re.search(r'\d+(?:\.\d+)?(?:%|g/cm|kg|mm|cm|W|V)', t, re.I)]
    if not events and len(numeric_specs) >= 2 and any(term in file_info["relative_path"] for term in ("展馆", "展区", "展示")):
        events.append({"type": "产品展示", "name": "WDCC展馆产品参数展示", "start": "00:00:00",
                       "end": _time(file_info.get("duration", 0)), "persons": [],
                       "description": f'WDCC展馆产品参数展示画面，包含{"、".join(numeric_specs[:4])}等屏幕信息。',
                       "evidence": ["目录位置：" + file_info["folder"], "画面参数文字：" + "；".join(numeric_specs[:4])], "confidence": "中"})

    if not persons and spoken >= 40:
        event_kinds = {e["type"] for e in events}
        label = "未知采访对象" if "采访" in event_kinds or "采访" in context else "未知演讲者"
        persons.append({"name": label, "role": "", "first_seen": _time(segments[0]["start"]),
                        "time_ranges": [f'{_time(segments[0]["start"])}-{_time(segments[-1]["end"])}'],
                        "related_events": [e["type"] for e in events], "evidence": ["持续中文语音，未发现可靠姓名依据"], "confidence": "低"})
    for person in persons:
        person["related_events"] = _unique(person.get("related_events", []) + [e["type"] for e in events])
    for event in events:
        event["persons"] = [p["name"] for p in persons]
        if event["type"] == "采访" and persons:
            event["description"] = f'{"；".join(event["persons"])}在WDCC现场接受采访并介绍相关展览或项目内容。'

    organizations = _unique(re.findall(r'[\u4e00-\u9fffA-Za-z0-9]{2,20}(?:公司|集团|协会|学院|大学|研究院|中心|机构)', all_text))
    activities = _unique([e["type"] for e in events])
    locations = _unique([_clean_term(x) for x in re.findall(r'[\u4e00-\u9fff]{2,12}(?:馆|展区|会场|中心|园区|大厅)', all_text)])
    topics = []
    corpus = speech_text + " " + " ".join(ocr_texts)
    for fixed in ("人工智能", "机器人", "主题馆", "主题展", "艺术车", "电解水", "碳达峰", "碳中和", "蓝色经济"):
        if fixed in corpus: topics.append(fixed)
    topics += [_clean_term(x) for x in re.findall(r'[\u4e00-\u9fff]{2,6}科技', corpus)]
    topics = _unique(topics)
    keywords = _unique([p["name"] for p in persons if not p["name"].startswith("未知")] + organizations + activities + locations + topics + ["WDCC"])
    if len(events) == 1 and events[0]["type"] == "采访" and spoken:
        who = "；".join(events[0]["persons"]) if events[0]["persons"] else "受访者"
        subject = "、".join(topics[:6]) if topics else "相关展览或项目"
        summary = f'WDCC现场采访素材，{who}介绍{subject}。'
    elif events:
        summary = events[0]["description"] if len(events) == 1 else f'WDCC素材，主要包含{"、".join(activities)}。'
    elif spoken:
        summary = "WDCC现场有声素材，未从现有证据确认具体重要事件，建议人工复核。"
    else:
        summary = "WDCC现场画面素材，未识别到可靠语音或明确重要事件。"
    confidence = "高" if any(p["confidence"] == "高" for p in persons) or any(e["confidence"] == "高" for e in events) else ("中" if events else "低")
    return {"persons": persons, "events": events, "organizations": organizations, "locations": locations,
            "activities": activities, "ocr_keywords": ocr_texts[:30],
            "speech_keywords": _unique([m.group(0) for m in re.finditer(r'[\u4e00-\u9fff]{2,8}', speech_text)])[:30],
            "search_keywords": keywords, "summary": summary, "confidence": confidence,
            "needs_review": confidence == "低" or any(p["name"].startswith("未知") or p["confidence"] != "高" for p in persons)}
