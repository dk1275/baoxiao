#!/usr/bin/env python3
"""行程预估 + 凭证缺失体检（只读）。

用法：
    python estimate_trip.py <报销根目录> [--from 10.1] [--to 11.05] [--out 行程预估.md]

只读脚本：不移动、不删除任何票据，只产出一份 Markdown 报告（默认写到报销根目录）。
数据来源优先级：文件名里的日期/城市/金额 → 票面文本（pymupdf，可选）。
票面读不到就标「未标注」，**不猜、不补**。

分级：
    必须补   —— 单晚住宿断档、城际移动缺票、打车缺行程单
    建议确认 —— 首日无到达票、末日无返程票、连续多晚无住宿（疑似常驻地）、
                连续空档日、住宿票无入离日期、区间外票据
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

CATS = ["酒店", "请客户", "打车", "高铁", "机票"]
SKIP_DIRS = {"_原始邮件附件", "_work", "_staging", "_tmp_extract", "__pycache__"}

# 常见出差城市（够用即可；未命中不报错，只是判不出城市）
CITIES = [
    "北京", "上海", "广州", "深圳", "天津", "重庆", "成都", "杭州", "南京", "武汉",
    "西安", "苏州", "无锡", "宁波", "温州", "合肥", "长沙", "郑州", "济南", "青岛",
    "大连", "沈阳", "长春", "哈尔滨", "石家庄", "太原", "呼和浩特", "兰州", "西宁",
    "银川", "乌鲁木齐", "拉萨", "昆明", "贵阳", "南宁", "海口", "三亚", "福州", "厦门",
    "泉州", "南昌", "赣州", "东莞", "佛山", "珠海", "中山", "惠州", "汕头", "常州",
    "南通", "徐州", "扬州", "绍兴", "嘉兴", "金华", "台州", "芜湖", "洛阳", "宜昌",
    "襄阳", "株洲", "衡阳", "九江", "上饶", "莆田", "漳州", "柳州", "桂林", "北海",
    "绵阳", "德阳", "宜宾", "遵义", "曲靖", "大理", "丽江", "咸阳", "宝鸡", "唐山",
    "保定", "廊坊", "秦皇岛", "邯郸", "烟台", "潍坊", "临沂", "淄博", "济宁", "威海",
    "盐城", "泰州", "镇江", "湖州", "衢州", "丽水", "舟山", "安庆", "蚌埠", "阜阳",
]

DATE_RE = re.compile(r"^(\d{2})(\d{2})(?:-(\d{2})(\d{2}))?")
MONEY_RE = re.compile(r"(\d+(?:\.\d+)?)\s*元")
ROUTE_RE = re.compile(r"([\u4e00-\u9fa5]{2,4})\s*[-—–→]\s*([\u4e00-\u9fa5]{2,4})")
FLIGHT_RE = re.compile(r"\b([A-Z]{2}\d{3,4})\b")
TRAIN_RE = re.compile(r"\b([GDCZTK]\d{1,4})\b")


@dataclass
class Item:
    cat: str
    path: Path
    date: dt.date | None = None
    end_date: dt.date | None = None
    amount: float | None = None
    city: str = ""
    city_to: str = ""
    cities: list[str] = field(default_factory=list)
    code: str = ""
    note: str = ""
    text: str = ""

    @property
    def cross_day(self) -> bool:
        return bool(self.end_date and self.date and self.end_date > self.date)


def text_of(pdf: Path) -> str:
    try:
        import pymupdf  # noqa: WPS433
    except Exception:
        return ""
    try:
        with pymupdf.open(str(pdf)) as doc:
            return "\n".join(page.get_text() for page in doc[:2])
    except Exception:
        return ""


def cities_in(s: str) -> list[str]:
    hits = [(s.find(c), c) for c in CITIES if c in s]
    return [c for _, c in sorted(hits)]


def parse_item(cat: str, p: Path, base_year: int) -> Item:
    it = Item(cat=cat, path=p)
    stem = p.stem

    m = DATE_RE.match(stem)
    if m:
        mm, dd, mm2, dd2 = m.groups()
        try:
            it.date = dt.date(base_year, int(mm), int(dd))
        except ValueError:
            it.date = None
        if mm2 and dd2:
            try:
                end = dt.date(base_year, int(mm2), int(dd2))
                it.end_date = end if end >= (it.date or end) else end.replace(year=end.year + 1)
            except (ValueError, AttributeError):
                it.end_date = None

    money = MONEY_RE.findall(stem)
    if money:
        try:
            it.amount = float(money[-1])
        except ValueError:
            pass

    it.cities = cities_in(stem)
    if cat in ("机票", "高铁"):
        r = ROUTE_RE.search(stem)
        if r and r.group(1) in CITIES and r.group(2) in CITIES:
            it.city, it.city_to = r.group(1), r.group(2)
        fm = FLIGHT_RE.search(stem) or TRAIN_RE.search(stem)
        it.code = fm.group(1) if fm else ""
    elif it.cities:
        it.city = it.cities[0]

    n = re.search(r"(\d+)\s*笔", stem)
    if n:
        it.note = f"{n.group(1)}笔"

    if cat in ("机票", "高铁", "酒店", "请客户") and not it.city:
        it.text = text_of(p)
        c = cities_in(it.text[:800])
        if c:
            it.city = c[0]
            if len(c) > 1 and cat in ("机票", "高铁") and not it.city_to:
                it.city_to = c[1]
    return it


def collect(root: Path, base_year: int) -> list[Item]:
    items: list[Item] = []
    for cat in CATS:
        d = root / cat
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.pdf")):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if cat == "打车" and "行程单" in p.parts:
                continue
            items.append(parse_item(cat, p, base_year))
    return items


def parse_md(s: str) -> dt.date | None:
    s = s.strip()
    m = re.fullmatch(r"(\d{1,2})[.\-/](\d{1,2})", s) or re.fullmatch(r"(\d{1,2})月(\d{1,2})[日号]?", s)
    if not m:
        return None
    return dt.date(dt.date.today().year, int(m.group(1)), int(m.group(2)))


def weekday(d: dt.date) -> str:
    return "一二三四五六日"[d.weekday()]


def money(v: float | None) -> str:
    return "—" if v is None else f"{v:,.2f}"


def dstr(d: dt.date) -> str:
    return f"{d:%m.%d}（周{weekday(d)}）"


def runs(days: list[dt.date]) -> list[list[dt.date]]:
    """把连续日期分组。"""
    out: list[list[dt.date]] = []
    for d in days:
        if out and d == out[-1][-1] + dt.timedelta(days=1):
            out[-1].append(d)
        else:
            out.append([d])
    return out


def build(root: Path, start: dt.date | None, end: dt.date | None) -> str:
    items = [i for i in collect(root, (start or dt.date.today()).year) if i.date]
    items.sort(key=lambda x: (x.date, x.cat))

    stay = [i for i in items if i.cat == "酒店"]
    move = [i for i in items if i.cat in ("机票", "高铁")]
    taxi = [i for i in items if i.cat == "打车"]
    meal = [i for i in items if i.cat == "请客户"]

    if not start or not end:
        ds = [i.date for i in items]
        start = start or (min(ds) if ds else dt.date.today())
        end = end or (max([i.end_date or i.date for i in items]) if items else start)
    if end < start:
        end = end.replace(year=end.year + 1)
    days = [start + dt.timedelta(days=n) for n in range((end - start).days + 1)]

    # 逐日城市：住宿覆盖的夜晚 → 当日到达的交通 → 当日打车（跨日打车不参与，避免把首日钉错城市）
    city_of: dict[dt.date, str] = {}
    for h in stay:
        if not h.city:
            continue
        n, last = h.date, (h.end_date or h.date)
        while n < last:
            city_of.setdefault(n, h.city)
            n += dt.timedelta(days=1)
    for t in move:
        if t.city_to:
            city_of[t.date] = t.city_to
    for t in taxi:
        if t.city and not t.cross_day:
            city_of.setdefault(t.date, t.city)

    last_known = ""
    for d in days:
        if d in city_of:
            last_known = city_of[d]
        elif last_known:
            city_of[d] = last_known

    must: list[str] = []
    hint: list[str] = []

    # 1) 住宿断档
    covered: set[dt.date] = set()
    for h in stay:
        n, last = h.date, (h.end_date or h.date)
        while n < last:
            covered.add(n)
            n += dt.timedelta(days=1)
    check_nights = days[:-1] if len(days) > 1 else days
    uncovered = [d for d in check_nights if d not in covered]
    for run in runs(uncovered):
        cities = {city_of.get(d, "") for d in run}
        if len(run) >= 2 and len(cities) == 1 and "" not in cities:
            hint.append(f"**{run[0]:%m.%d}-{run[-1]:%m.%d} 连续 {len(run)} 晚在 {cities.pop()} 无住宿凭证**："
                        f"疑似常驻地 / 客户统一安排住宿 —— 若确实住酒店则是整段漏票")
        else:
            for d in run:
                must.append(f"**{dstr(d)}住宿断档**：当晚无住宿发票（城市 {city_of.get(d, '未标注')}）"
                            f" —— 当晚返程 / 住亲友 / 客户安排请说明后忽略")

    # 2) 城际移动缺票
    for prev, cur in zip(days, days[1:]):
        a, b = city_of.get(prev, ""), city_of.get(cur, "")
        if a and b and a != b and not any(t.date == cur and t.city_to for t in move):
            taxi_there = any(t.date == cur and t.city == b and not t.cross_day for t in taxi)
            extra = "；当天在到达城市已有打车记录，说明位移确实发生，缺的是位移票据本身" if taxi_there else ""
            must.append(f"**{dstr(cur)}{a} → {b} 城际交通缺票**：当天无机票 / 高铁发票{extra}")

    # 3) 末日无返程
    if len(days) > 1 and not any(t.date == end for t in move):
        hint.append(f"**{dstr(end)}无返程交通票**：当天没有离开 {city_of.get(end, '当地') or '当地'} 的机票 / 高铁"
                    f" —— 当地即常驻地或另有安排可忽略")

    # 4) 首日无到达交通
    if not any(t.date == start for t in move) and stay:
        hint.append(f"**{dstr(start)}无到达交通票**：当天只有住宿凭证 —— 本地出发 / 自驾 / 客户接送可忽略")

    # 5) 空档日（连续合并）
    busy = {i.date for i in items}
    empties = [d for d in days if d not in busy]
    for run in runs(empties):
        if len(run) == 1:
            hint.append(f"**{dstr(run[0])}整天无任何凭证**：确认当天是否无需发生费用")
        else:
            hint.append(f"**{run[0]:%m.%d}-{run[-1]:%m.%d} 连续 {len(run)} 天无任何凭证**："
                        f"确认这段时间是否在当地办公 / 无费用发生")

    # 6) 打车缺行程单
    taxi_dir, itin_dir = root / "打车", root / "打车" / "行程单"
    itin = {p.stem.replace("_行程单", "") for p in itin_dir.glob("*.pdf")} if itin_dir.is_dir() else set()
    for t in taxi:
        if t.path.stem.replace("_发票", "") not in itin:
            must.append(f"**打车缺行程单**：`{t.path.name}` 在 `打车/行程单/` 里没有同名行程单")

    # 7) 住宿票无入离日期
    for h in stay:
        if not h.end_date:
            hint.append(f"**住宿票未标注入离日期**：`{h.path.name}` —— 间夜数无法确认，按结账单或系统记录补")

    # 8) 同日多城打车（同一张票里的多城已按跨日处理，这里只抓"同一天两张票、两个城市"）
    day_taxi_cities: dict[dt.date, set[str]] = {}
    for t in taxi:
        if t.city and not t.cross_day:
            day_taxi_cities.setdefault(t.date, set()).add(t.city)
    for d, cs in sorted(day_taxi_cities.items()):
        if len(cs) > 1:
            detail = "；".join(f"{t.city} ¥{money(t.amount)}" for t in taxi
                              if t.date == d and t.city and not t.cross_day)
            hint.append(f"**{dstr(d)}同日出现 {len(cs)} 个城市的打车记录（{' / '.join(sorted(cs))}）**："
                        f"{detail} —— 当天可能有多段城际移动，行程归属与位移票据都要确认")

    # 9) 区间外
    outside = [i for i in items if not (start <= i.date <= end)]

    # ---- 报告 ----
    total = sum(i.amount or 0 for i in items)
    chain: list[str] = []
    for d in days:
        c = city_of.get(d, "")
        if c and (not chain or chain[-1] != c):
            chain.append(c)
    headline = " → ".join(chain) or "（城市无法判定）"

    L: list[str] = []
    L.append(f"# 行程预估与凭证体检 · {start:%m.%d}-{end:%m.%d}")
    L.append("")
    inside = [i for i in items if start <= i.date <= end]
    if outside:
        L.append(f"- 区间：{start:%Y-%m-%d} ~ {end:%Y-%m-%d}（{len(days)} 天）"
                 f"｜区间内 {len(inside)} 张 ¥{sum(i.amount or 0 for i in inside):,.2f}"
                 f"｜区间外 {len(outside)} 张 ¥{sum(i.amount or 0 for i in outside):,.2f}"
                 f"｜合计 {len(items)} 张 ¥{total:,.2f}")
    else:
        L.append(f"- 区间：{start:%Y-%m-%d} ~ {end:%Y-%m-%d}（{len(days)} 天）"
                 f"｜票据 {len(items)} 张｜合计 ¥{total:,.2f}")
    L.append(f"- 预估行程：**{headline}**")
    L.append("- 口径：只统计五类发票；城市取自文件名或票面，读不到标「未标注」，全程不推测。")
    L.append("")
    L.append("## 一、逐日行程")
    L.append("")
    L.append("| 日期 | 城市 | 住宿 | 交通 | 其他 | 凭证数 |")
    L.append("| --- | --- | --- | --- | --- | --- |")
    for d in days:
        h = [x for x in stay if x.date <= d < (x.end_date or x.date)]
        mv = [x for x in move if x.date == d]
        tx = [x for x in taxi if x.date == d]
        me = [x for x in meal if x.date == d]
        h_txt = f"{h[0].city or '未标注'} ¥{money(h[0].amount)}" if h else ""
        mv_txt = "；".join(f"{'✈' if x.cat == '机票' else '🚄'} {x.city}→{x.city_to or '未标注'} ¥{money(x.amount)}"
                          for x in mv)
        tx_txt = "；".join(
            (f"{x.city or '未标注'}打车 ¥{money(x.amount)}" if not x.cross_day
             else f"跨日打车 {'/'.join(x.cities) or '未标注'} ¥{money(x.amount)}（{x.date:%m.%d}-{x.end_date:%m.%d}）")
            for x in tx)
        me_txt = "；".join(f"{x.city or '未标注'}餐饮 ¥{money(x.amount)}" for x in me)
        other = "；".join(t for t in [tx_txt, me_txt] if t)
        n = len(h) + len(mv) + len(tx) + len(me)
        cs = day_taxi_cities.get(d) or set()
        shown = " / ".join(sorted(cs)) + "（待确认）" if len(cs) > 1 else city_of.get(d, "未标注")
        L.append(f"| {d:%m.%d} 周{weekday(d)} | {shown} | {h_txt} | {mv_txt} | "
                 f"{other} | {n or '**0**'} |")
    L.append("")

    sec = 2
    L.append(f"## 二、必须补（{len(must)} 项）")
    L.append("")
    L.extend([f"- [ ] {x}" for x in must] or ["- 无"])
    L.append("")
    sec += 1
    L.append(f"## 三、建议确认（{len(hint)} 项）")
    L.append("")
    L.extend([f"- {x}" for x in hint] or ["- 无"])
    L.append("")
    if outside:
        L.append("## 四、区间外票据（按规则仍纳入合计，不剔除）")
        L.append("")
        for i in outside:
            L.append(f"- {i.date:%Y-%m-%d} {i.cat} {i.path.name} ¥{money(i.amount)}")
        L.append("")
        nxt = "五"
    else:
        nxt = "四"
    L.append(f"## {nxt}、判定依据")
    L.append("")
    L.append("- 住宿断档：按区间逐晚比对住宿票覆盖的夜晚；末日视为返程日，不要求住宿。")
    L.append("- 常驻地判定：连续 2 晚以上同一城市无住宿 → 归入「建议确认」，不当作缺票逐条报。")
    L.append("- 城际缺票：相邻两日城市不同，且当日无机票 / 高铁凭证。")
    L.append("- 跨日打车（如 10.1-10.5 一张票含多城多笔）不参与逐日城市判定，避免把首日钉错城市。")
    L.append("- 打车行程单：`打车/` 与 `打车/行程单/` 文件名需同名成对。")
    L.append("- 本报告只读，未移动或删除任何文件。")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="报销根目录（含 酒店/打车/高铁/机票/请客户）")
    ap.add_argument("--from", dest="frm", help="起始日期，如 10.1")
    ap.add_argument("--to", dest="to", help="结束日期，如 11.05")
    ap.add_argument("--out", help="报告输出路径，默认 <root>/行程预估.md")
    ap.add_argument("--json", dest="json_out", help="同时输出结构化 JSON")
    a = ap.parse_args()

    root = Path(a.root).expanduser()
    if not root.is_dir():
        print(f"目录不存在：{root}")
        return 2

    start = parse_md(a.frm) if a.frm else None
    end = parse_md(a.to) if a.to else None
    report = build(root, start, end)

    out = Path(a.out) if a.out else root / "行程预估.md"
    out.write_text(report, encoding="utf-8")
    print(f"已写入 {out}")

    if a.json_out:
        items = [i for i in collect(root, (start or dt.date.today()).year) if i.date]
        payload = [{
            "cat": i.cat, "file": i.path.name, "date": i.date.isoformat(),
            "end_date": i.end_date.isoformat() if i.end_date else None,
            "amount": i.amount, "city": i.city, "city_to": i.city_to, "code": i.code,
        } for i in items]
        Path(a.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已写入 {a.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
