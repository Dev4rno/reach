import random

welcome_banners = [
    "Welcome to the indie dev journey! 👋"
    "Glad to have you along for the ride! 🚀"
    "Thanks for joining my builder's journal ✨"
    "Welcome aboard, fellow developer! 🛠️"
    "Hey there! Thanks for subscribing 👋"
    "Welcome to my dev chronicles 📓",
]

def get_random_welcome_banner() -> str:
    return random.choice(welcome_banners)

preferences_banners = [
    "Your preferences are updated ✨",
    "Updates saved! Thanks for customizing 🎯",
    "New settings confirmed ⚙️",
    "Preferences locked in! 🔐",
    "Changes saved successfully 💫",
    "Your updates are live ✅",
]

def get_random_preferences_banner() -> str:
    return random.choice(preferences_banners)

marketing_banners = [
    "Something new I built that might help you 🛠️",
    "New tool alert: built this for devs like us 🔨",
    "Just shipped: a new dev tool you might like 🚢",
    "Fresh from the code editor to you 💻",
    "Made something that could be useful 🎁",
    "New project launch (would love your feedback!) 🚀",
]

def get_random_marketing_banner() -> str:
    return random.choice(marketing_banners)

product_banners = [
    "New features shipped! 🚀",
    "Fresh updates deployed ✨",
    "Check out what's new in v{version} 🎉",
    "Just pushed some cool improvements 🔄",
    "Latest features are live! 📦",
    "Shipped some updates based on your feedback 🛠️",
]

def get_random_marketing_banner() -> str:
    return random.choice(marketing_banners)

newsletter = [
    "Latest dev adventures & learnings 📚",
    "New blog post: dev lessons learned 💡",
    "Fresh dev insights from the trenches 🔍",
    "Latest from my coding journey 🗺️",
    "New tutorial & dev thoughts 📝",
    "Weekly dev dispatch: learnings & updates 📬",
]