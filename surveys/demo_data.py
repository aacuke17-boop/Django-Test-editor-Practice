from decimal import Decimal


def question(text, points, *options):
    return {
        "text": text,
        "points": Decimal(points),
        "options": [(option.rstrip("*"), option.endswith("*")) for option in options],
    }


def material(title, description, restricted, *questions):
    return {
        "title": title,
        "description": description,
        "restricted": restricted,
        "questions": list(questions),
    }


AUTHOR_TESTS = [
    material(
        "Python basics",
        "Check your knowledge of basic Python.",
        False,
        question("Which of these are Python data types?", 2, "list*", "tuple*", "struct", "pointer"),
        question("What does len([1, 2, 3]) return?", 1, "3*", "2", "4", "None"),
        question("Which keywords start a loop?", 2, "for*", "while*", "loop", "repeat"),
    ),
    material(
        "World capitals",
        "A short quiz about capital cities.",
        False,
        question("What is the capital of France?", 1, "Paris*", "Lyon", "Marseille"),
        question("Which of these are capitals in Europe?", 2, "Berlin*", "Madrid*", "Sydney", "Toronto"),
        question("What is the capital of Japan?", 1, "Tokyo*", "Osaka", "Kyoto", "Seoul"),
    ),
    material(
        "Basic math",
        "Primes, products and even numbers.",
        False,
        question("Which numbers are prime?", 3, "2*", "3*", "4", "9"),
        question("What is 12 x 12?", 1, "144*", "124", "132"),
        question("Which numbers are even?", 2, "10*", "24*", "7", "15"),
    ),
    material(
        "Databases and SQL",
        "Private test for a selected user.",
        True,
        question("Which of these are SQL commands?", 2, "SELECT*", "INSERT*", "RUNQ", "SHOWALL"),
        question("Which clause filters rows?", 1, "WHERE*", "ORDER BY", "GROUP BY"),
        question("Which keys identify a row uniquely?", 2, "Primary key*", "Unique key*", "Foreign key", "Index"),
    ),
    material(
        "Web development",
        "Private test for a selected user.",
        True,
        question("Which of these are network protocols?", 2, "HTTP*", "HTTPS*", "HTML", "CSS"),
        question("Which language adds interactivity in browsers?", 1, "JavaScript*", "SQL", "Python"),
        question("Which HTTP methods change data?", 2, "POST*", "DELETE*", "GET", "HEAD"),
    ),
]

AUTHOR_SURVEYS = [
    material(
        "Student satisfaction survey",
        "Tell us what you think about the course.",
        False,
        question("How satisfied are you with the course?", 0, "Very satisfied", "Satisfied", "Neutral", "Dissatisfied"),
        question("Which parts did you enjoy?", 0, "Lectures", "Practice", "Projects", "Discussions"),
        question("Would you recommend the course?", 0, "Yes", "Maybe", "No"),
    ),
    material(
        "Favourite tools",
        "Which tools do you use every day?",
        False,
        question("Which editors do you use?", 0, "PyCharm", "VS Code", "Vim", "Notepad++"),
        question("Which operating system do you use?", 0, "Windows", "Linux", "macOS"),
    ),
    material(
        "Work from home habits",
        "How do you organize your working day?",
        False,
        question("Where do you work most often?", 0, "Home", "Office", "Cafe"),
        question("Which things help you stay focused?", 0, "Music", "Timer", "Notes", "Nothing"),
        question("How many hours do you work daily?", 0, "Under 4", "4 to 6", "6 to 8", "Over 8"),
    ),
    material(
        "Team feedback",
        "Private survey for a selected user.",
        True,
        question("How is communication in the team?", 0, "Excellent", "Good", "Poor"),
        question("What should be improved?", 0, "Meetings", "Documentation", "Planning", "Tools"),
    ),
    material(
        "Event planning poll",
        "Private survey for a selected user.",
        True,
        question("Which day suits you best?", 0, "Friday", "Saturday", "Sunday"),
        question("Which format do you prefer?", 0, "Online", "Offline", "Hybrid"),
    ),
]

GHOST_TESTS = [
    material(
        "Retro games quiz",
        "A test created by a user who was deleted later.",
        False,
        question("Which company made the NES?", 1, "Nintendo*", "Sega", "Atari"),
        question("Which characters are from Super Mario?", 2, "Luigi*", "Bowser*", "Sonic", "Pac-Man"),
    ),
]

GHOST_SURVEYS = [
    material(
        "Weekend plans poll",
        "A survey created by a user who was deleted later.",
        False,
        question("What will you do this weekend?", 0, "Rest", "Travel", "Study", "Meet friends"),
        question("How do you usually relax?", 0, "Reading", "Sport", "Games", "Movies"),
    ),
]

DEMO_TITLES = [
    item["title"]
    for item in AUTHOR_TESTS + AUTHOR_SURVEYS + GHOST_TESTS + GHOST_SURVEYS
]