TEMPLATES = {
    "how_i_built": {
        "key": "how_i_built",
        "name": "How I Built X",
        "description": "Project deep-dive with architecture and lessons",
        "day": "tuesday",
    },
    "hot_take": {
        "key": "hot_take",
        "name": "Hot Take / Philosophy",
        "description": "Contrarian opinion about AI, dev tools, or free tech",
        "day": "wednesday",
    },
    "lesson_learned": {
        "key": "lesson_learned",
        "name": "Lesson Learned",
        "description": "Mistake, challenge, or insight from building",
        "day": "thursday",
    },
    "data_numbers": {
        "key": "data_numbers",
        "name": "Data & Numbers",
        "description": "Performance metrics, cost breakdowns, benchmarks",
        "day": "tuesday_alt",
    },
    "progress_journey": {
        "key": "progress_journey",
        "name": "Progress / Journey",
        "description": "Daily series update, learning progress",
        "day": "wednesday_alt",
    },
}

def get_template_for_day(weekday_int, week_parity):
    mapping = {
        0: "progress_journey",
        1: "how_i_built",
        2: "hot_take",
        3: "lesson_learned",
        4: "data_numbers",
        5: "progress_journey",
    }
    if week_parity == 1:
        mapping = {
            0: "data_numbers",
            1: "progress_journey",
            2: "how_i_built",
            3: "hot_take",
            4: "lesson_learned",
            5: "data_numbers",
        }
    return TEMPLATES.get(mapping.get(weekday_int, "how_i_built"), TEMPLATES["how_i_built"])
