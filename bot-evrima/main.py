import discord
from discord import app_commands
import os
import json
import random
import asyncio

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

LEVELS_FILE = "data/levels.json"
WALLETS_FILE = "data/wallets.json"

os.makedirs("data", exist_ok=True)
if not os.path.exists(LEVELS_FILE):
    with open(LEVELS_FILE, "w") as f:
        json.dump({}, f)
if not os.path.exists(WALLETS_FILE):
    with open(WALLETS_FILE, "w") as f:
        json.dump({}, f)

def load_data(file):
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

levels = load_data(LEVELS_FILE)
wallets = load_data(WALLETS_FILE)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Zalogowano jako {client.user}")

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="┆powitania")
    if channel:
        embed = discord.Embed(
            title="👋 Witaj!",
            description=f"Użytkownik **{member.name}** dołączył na serwer!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await channel.send(embed=embed)

@client.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="┆pożegnania")
    if channel:
        embed = discord.Embed(
            title="👋 Żegnaj!",
            description=f"Użytkownik **{member.name}** opuścił serwer.",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)

@tree.command(name="ping", description="Sprawdza, czy bot działa.")
async def ping_command(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=True)

@tree.command(name="setup", description="Tworzy kanały i role.")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    guild = interaction.guild
    await interaction.response.send_message("🔧 Konfigurowanie serwera...", ephemeral=True)

    role_names = ["🌿 Użytkownik", "🌟 VIP", "🔧 Moderator", "⚙️ Administrator"]
    for name in role_names:
        if not discord.utils.get(guild.roles, name=name):
            await guild.create_role(name=name)

    categories = {
        "📘┇Informacje": [
            ("📜┃regulamin", False),
            ("📢┃ogłoszenia", False),
            ("👤┃role", False),
            ("📌┃status-serwera", False),
        ],
        "🎮┇Społeczność": [
            ("💬┃ogólny", True),
            ("📸┃zdjęcia", True),
            ("🎨┃fanarty", True),
            ("🦖┃ewrima-czat", True),
        ],
        "📊┇Ekonomia": [
            ("💰┃saldo", True),
            ("🎁┃nagrody", True),
            ("🏆┃poziomy", True),
        ],
        "🛠┇Admin": [
            ("🔒┃logi", False),
            ("📄┃raporty", False),
        ],
        "👋┇Wejścia": [
            ("┆powitania", False),
            ("┆pożegnania", False),
        ]
    }

    for category_name, channels in categories.items():
        cat = discord.utils.get(guild.categories, name=category_name)
        if not cat:
            cat = await guild.create_category(category_name)

        for channel_name, is_public in channels:
            if not discord.utils.get(guild.text_channels, name=channel_name):
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=is_public)
                }
                await guild.create_text_channel(channel_name, category=cat, overwrites=overwrites)

    voice_categories = {
        "🎧┇Głosowe": [
            "🔊┃Ogólny",
            "🎮┃Evrima Team",
            "🦕┃Dino Spotkania",
            "🎤┃Pogadanki",
            "🎲┃AFK",
        ],
        "⚙️┇Admin Głos": [
            "🔧┃Staff Chat",
            "👑┃Zarząd",
        ],
        "🎉┇Eventy": [
            "🎯┃Turniej",
            "🕹┃Mini-gry",
        ]
    }

    for category_name, channel_names in voice_categories.items():
        cat = discord.utils.get(guild.categories, name=category_name)
        if not cat:
            cat = await guild.create_category(category_name)

        for vc_name in channel_names:
            if not discord.utils.get(guild.voice_channels, name=vc_name):
                await guild.create_voice_channel(vc_name, category=cat)

@tree.command(name="delete", description="Usuwa wszystkie kanały.")
@app_commands.checks.has_permissions(administrator=True)
async def delete_channels(interaction: discord.Interaction):
    await interaction.response.send_message("⚠️ Usuwanie wszystkich kanałów...", ephemeral=True)
    for channel in interaction.guild.channels:
        try:
            await channel.delete()
        except:
            pass

# system XP działa niezależnie od slash
@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in levels:
        levels[user_id] = {"xp": 0, "level": 1}

    xp_gain = random.randint(1, 3)
    levels[user_id]["xp"] += xp_gain

    current_level = levels[user_id]["level"]
    required_xp = current_level * 100

    if levels[user_id]["xp"] >= required_xp:
        levels[user_id]["level"] += 1
        levels[user_id]["xp"] = 0

        channel = discord.utils.get(message.guild.text_channels, name="🏆┃poziomy")
        if channel:
            embed = discord.Embed(
                title="🎉 Gratulacje!",
                description=f"{message.author.mention} zdobył **poziom {levels[user_id]['level']}**!",
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)

    save_data(LEVELS_FILE, levels)
    await client.process_commands(message)

# 📁 Kontynuacja main.py...

# =====================
# 💰 EKONOMIA (DNA)
# =====================

# 🏦 /saldo – sprawdzenie własnego stanu konta
@tree.command(name="saldo", description="Sprawdź swoje DNA.")
async def saldo(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in wallets:
        wallets[user_id] = 0
        save_data(WALLETS_FILE, wallets)

    saldo = wallets[user_id]
    await interaction.response.send_message(
        f"🧬 Twój stan konta: **{saldo} DNA**", ephemeral=True
    )

# 🎁 /daily – odbiór codziennej nagrody
DAILY_REWARD = 25

@tree.command(name="daily", description="Odbierz codzienną nagrodę DNA.")
async def daily(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in wallets:
        wallets[user_id] = 0

    # cooldown – tylko raz dziennie
    cooldown_file = f"data/cooldown_{user_id}.txt"
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    if os.path.exists(cooldown_file):
        with open(cooldown_file, "r") as f:
            last_time = datetime.fromisoformat(f.read().strip())
            if now - last_time < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_time)
                minutes = int(remaining.total_seconds() // 60)
                return await interaction.response.send_message(
                    f"🕒 Musisz poczekać **{minutes} min** na kolejne DNA.", ephemeral=True
                )

    wallets[user_id] += DAILY_REWARD
    save_data(WALLETS_FILE, wallets)
    with open(cooldown_file, "w") as f:
        f.write(now.isoformat())

    await interaction.response.send_message(
        f"🎉 Odebrano codzienną nagrodę: **+{DAILY_REWARD} DNA**", ephemeral=True
    )

# 💸 /pay – przelew DNA do innego użytkownika
@tree.command(name="pay", description="Przelej DNA innemu użytkownikowi.")
@app_commands.describe(użytkownik="Odbiorca", kwota="Ilość DNA do wysłania")
async def pay(interaction: discord.Interaction, użytkownik: discord.Member, kwota: int):
    nadawca_id = str(interaction.user.id)
    odbiorca_id = str(użytkownik.id)

    if kwota <= 0:
        return await interaction.response.send_message("❌ Nieprawidłowa kwota.", ephemeral=True)

    if nadawca_id not in wallets:
        wallets[nadawca_id] = 0
    if odbiorca_id not in wallets:
        wallets[odbiorca_id] = 0

    if wallets[nadawca_id] < kwota:
        return await interaction.response.send_message("❌ Nie masz tyle DNA!", ephemeral=True)

    wallets[nadawca_id] -= kwota
    wallets[odbiorca_id] += kwota
    save_data(WALLETS_FILE, wallets)

    await interaction.response.send_message(
        f"💸 Przesłano **{kwota} DNA** do {użytkownik.mention}!"
    )

# 🏆 /top – ranking DNA
@tree.command(name="top", description="Pokaż ranking DNA.")
async def top(interaction: discord.Interaction):
    sorted_wallets = sorted(wallets.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(
        title="🏆 Ranking DNA",
        color=discord.Color.purple()
    )

    for i, (user_id, dna) in enumerate(sorted_wallets, start=1):
        user = await client.fetch_user(int(user_id))
        embed.add_field(
            name=f"{i}. {user.name}",
            value=f"🧬 {dna} DNA",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# 👑 /give – dodanie DNA innemu użytkownikowi (dla admina)
@tree.command(name="give", description="Dodaj DNA użytkownikowi (dla adminów).")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(użytkownik="Użytkownik", kwota="Ilość DNA do dodania")
async def give(interaction: discord.Interaction, użytkownik: discord.Member, kwota: int):
    if kwota <= 0:
        return await interaction.response.send_message("❌ Nieprawidłowa kwota.", ephemeral=True)

    user_id = str(użytkownik.id)
    if user_id not in wallets:
        wallets[user_id] = 0

    wallets[user_id] += kwota
    save_data(WALLETS_FILE, wallets)

    await interaction.response.send_message(
        f"✅ Dodano **{kwota} DNA** dla {użytkownik.mention}.", ephemeral=True
    )
# 🎭 Role dostępne w sklepie (ID dodamy dynamicznie)
SHOP_ROLES = {
    "🧬 Nowicjusz DNA": 50,
    "🧪 Badacz DNA": 150,
    "🔬 Genetyk DNA": 300,
    "👑 VIP DNA": 1000,
}

# 🎓 Role za poziomy
LEVEL_ROLES = {
    5: "📘 Początkujący",
    10: "📗 Doświadczony",
    20: "📙 Ekspert",
    30: "📕 Legendarny"
}

@tree.command(name="shop", description="Pokaż sklep z rolami.")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 Sklep z rolami (DNA)",
        description="Użyj `/buy <nazwa>` aby kupić.",
        color=discord.Color.blue()
    )
    for role_name, price in SHOP_ROLES.items():
        embed.add_field(name=role_name, value=f"{price} DNA", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="buy", description="Kup rolę za DNA.")
@app_commands.describe(nazwa="Dokładna nazwa roli ze sklepu")
async def buy(interaction: discord.Interaction, nazwa: str):
    user_id = str(interaction.user.id)
    if user_id not in wallets:
        wallets[user_id] = 0

    if nazwa not in SHOP_ROLES:
        return await interaction.response.send_message("❌ Taka rola nie istnieje w sklepie.", ephemeral=True)

    cena = SHOP_ROLES[nazwa]
    if wallets[user_id] < cena:
        return await interaction.response.send_message("❌ Nie masz wystarczająco DNA.", ephemeral=True)

    role = discord.utils.get(interaction.guild.roles, name=nazwa)
    if not role:
        role = await interaction.guild.create_role(name=nazwa)

    await interaction.user.add_roles(role)
    wallets[user_id] -= cena
    save_data(WALLETS_FILE, wallets)

    await interaction.response.send_message(f"✅ Kupiono rolę **{nazwa}** za {cena} DNA!")

@tree.command(name="inventory", description="Sprawdź swoje zakupione role.")
async def inventory(interaction: discord.Interaction):
    roles = [role.name for role in interaction.user.roles if role.name in SHOP_ROLES]
    if not roles:
        await interaction.response.send_message("🔍 Nie masz żadnych ról ze sklepu.", ephemeral=True)
    else:
        await interaction.response.send_message(f"🎒 Twoje role: {', '.join(roles)}", ephemeral=True)

# 🔁 aktualizacja roli po awansie
async def sprawdz_role_poziomu(member: discord.Member, level: int):
    for lvl, role_name in LEVEL_ROLES.items():
        if level >= lvl:
            role = discord.utils.get(member.guild.roles, name=role_name)
            if not role:
                role = await member.guild.create_role(name=role_name)
            await member.add_roles(role)

# Modyfikacja systemu XP (dodajemy przyznawanie ról)
@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in levels:
        levels[user_id] = {"xp": 0, "level": 1}

    xp_gain = random.randint(1, 3)
    levels[user_id]["xp"] += xp_gain

    current_level = levels[user_id]["level"]
    required_xp = current_level * 100

    if levels[user_id]["xp"] >= required_xp:
        levels[user_id]["level"] += 1
        levels[user_id]["xp"] = 0

        new_level = levels[user_id]["level"]
        await sprawdz_role_poziomu(message.author, new_level)

        channel = discord.utils.get(message.guild.text_channels, name="🏆┃poziomy")
        if channel:
            embed = discord.Embed(
                title="🎉 Gratulacje!",
                description=f"{message.author.mention} osiągnął **poziom {new_level}**!",
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)

    save_data(LEVELS_FILE, levels)
    await client.process_commands(message)

# 📝 Automatyczne wysłanie listy komend po /setup
async def wyslij_komendy_kanal(guild):
    kanal = discord.utils.get(guild.text_channels, name="📜┃komendy")
    if not kanal:
        kat = discord.utils.get(guild.categories, name="📘┇Informacje")
        kanal = await guild.create_text_channel("📜┃komendy", category=kat)

    tekst = """
## 📖 Dostępne komendy (używaj przez `/`)
- `/setup` – konfiguracja kanałów i ról
- `/delete` – usuń wszystkie kanały
- `/ping` – sprawdź, czy bot działa
- `/saldo` – sprawdź swoje DNA
- `/daily` – odbierz codzienną nagrodę
- `/pay` – przelej DNA komuś
- `/top` – zobacz ranking
- `/shop` – zobacz dostępne role
- `/buy` – kup wybraną rolę
- `/inventory` – sprawdź swoje role
"""
    await kanal.send(tekst)

# Modyfikacja /setup – dodaje też role i kanał komendy
@tree.command(name="setup", description="Tworzy kanały, role i systemy.")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    guild = interaction.guild
    await interaction.response.send_message("🔧 Konfigurowanie serwera...", ephemeral=True)

    # Role systemowe i progresu
    role_names = [
        "🌿 Użytkownik", "🌟 VIP", "🔧 Moderator", "⚙️ Administrator",
        "📘 Początkujący", "📗 Doświadczony", "📙 Ekspert", "📕 Legendarny"
    ] + list(SHOP_ROLES.keys())

    for name in role_names:
        if not discord.utils.get(guild.roles, name=name):
            await guild.create_role(name=name)

    # Kanały tekstowe + głosowe jak wcześniej (pomijamy tu dla skrótu)

    await wyslij_komendy_kanal(guild)
@tree.command(name="quiz", description="Sprawdź swoją wiedzę i wygraj DNA!")
async def quiz(interaction: discord.Interaction):
    pytania = [
        {
            "pyt": "🦖 Ile nóg ma T-Rex?",
            "odp": "2",
            "nagroda": 30
        },
        {
            "pyt": "🌍 Jaki kontynent dominował w grze The Isle?",
            "odp": "Ameryka",
            "nagroda": 40
        },
        {
            "pyt": "⚡ Czy dinozaury mogły biegać?", 
            "odp": "tak",
            "nagroda": 25
        },
    ]

    q = random.choice(pytania)

    await interaction.response.send_message(
        f"{q['pyt']} *(odpowiedz wpisując: `/answer <odpowiedź>` w ciągu 30 sekund)*", ephemeral=True
    )

    def check(i):
        return i.user == interaction.user and i.command.name == "answer"

    try:
        res = await client.wait_for("interaction", check=check, timeout=30.0)
        ans = res.data["options"][0]["value"].lower()
        if ans == q["odp"].lower():
            user_id = str(interaction.user.id)
            if user_id not in wallets:
                wallets[user_id] = 0
            wallets[user_id] += q["nagroda"]
            save_data(WALLETS_FILE, wallets)
            await res.response.send_message(f"✅ Poprawnie! Otrzymujesz {q['nagroda']} DNA!", ephemeral=True)
        else:
            await res.response.send_message("❌ Zła odpowiedź!", ephemeral=True)
    except asyncio.TimeoutError:
        await interaction.followup.send("⏱ Czas minął!", ephemeral=True)

# Rejestracja pomocniczej komendy /answer
@tree.command(name="answer", description="Odpowiedz na quiz.")
@app_commands.describe(odpowiedz="Twoja odpowiedź")
async def answer(interaction: discord.Interaction, odpowiedz: str):
    pass  # obsługuje to quiz
@tree.command(name="arena", description="Wyzwanie innego gracza na pojedynek!")
@app_commands.describe(przeciwnik="Z kim chcesz walczyć?")
async def arena(interaction: discord.Interaction, przeciwnik: discord.Member):
    user1 = interaction.user
    user2 = przeciwnik
    wynik = random.choice([user1, user2])

    embed = discord.Embed(
        title="⚔️ Arena",
        description=f"{user1.mention} walczy z {user2.mention}...",
        color=discord.Color.orange()
    )
    msg = await interaction.response.send_message(embed=embed)
    await asyncio.sleep(3)

    dna = random.randint(10, 50)
    winner_id = str(wynik.id)
    if winner_id not in wallets:
        wallets[winner_id] = 0
    wallets[winner_id] += dna
    save_data(WALLETS_FILE, wallets)

    await interaction.followup.send(f"🏆 **{wynik.mention}** wygrał i zdobywa **{dna} DNA**!")
CODES = {
    "DNAFREE2025": 100,
    "EVRIMAQUIZ": 75,
    "STARTDNA": 50
}
USED_CODES = set()

@tree.command(name="code", description="Wpisz kod DNA, aby odebrać nagrodę.")
@app_commands.describe(kod="Kod promocyjny")
async def code(interaction: discord.Interaction, kod: str):
    kod = kod.upper()
    user_id = str(interaction.user.id)

    if f"{user_id}:{kod}" in USED_CODES:
        return await interaction.response.send_message("❌ Już użyłeś tego kodu.", ephemeral=True)

    if kod in CODES:
        dna = CODES[kod]
        if user_id not in wallets:
            wallets[user_id] = 0
        wallets[user_id] += dna
        USED_CODES.add(f"{user_id}:{kod}")
        save_data(WALLETS_FILE, wallets)
        await interaction.response.send_message(f"✅ Kod zaakceptowany! Otrzymujesz **{dna} DNA**.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Nieprawidłowy kod.", ephemeral=True)
bot.run(os.getenv("TOKEN"))
