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
        1: "how_i_built",
        2: "hot_take",
        3: "lesson_learned",
    }
    if week_parity == 1:
        mapping = {
            1: "data_numbers",
            2: "progress_journey",
            3: "how_i_built",
        }
    return TEMPLATES.get(mapping.get(weekday_int, "how_i_built"), TEMPLATES["how_i_built"])
